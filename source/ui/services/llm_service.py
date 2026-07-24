import uuid
import streamlit as st
import os
from transformers import AutoTokenizer, AutoModelForCausalLM, T5Tokenizer, T5ForConditionalGeneration
import constants as const
import sqlite3
import torch
import re
from services.logging_service import Logger

@st.cache_resource
def get_request_tokenizer():
    return AutoTokenizer.from_pretrained("cycloneboy/SLM-SQL-0.6B")

@st.cache_resource
def get_request_model():
    return AutoModelForCausalLM.from_pretrained("cycloneboy/SLM-SQL-0.6B")

@st.cache_resource
def get_response_tokenizer():
    return T5Tokenizer.from_pretrained("google/flan-t5-large")

@st.cache_resource
def get_response_model():
    return T5ForConditionalGeneration.from_pretrained("google/flan-t5-large")

def format_response(sql_result, sql_query):
    user_friendly_message = None
    Logger.info(f"Generated Sql Query : {sql_query}")
    if sql_result:
        # 1. Parse sql_query to get selected columns
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql_query, re.IGNORECASE)
        selected_columns_raw = []
        if select_match:
            selected_columns_raw = [col.strip() for col in select_match.group(1).split(',')]
        
        Logger.info(f"Selected Columns : {', '.join(selected_columns_raw)}")
        # Clean up column names (remove aliases like P., and 'AS alias')
        cleaned_selected_columns = []
        for col in selected_columns_raw:
            clean_col = col.split('.')[-1].strip() # Remove table alias (e.g., P.product_name -> product_name)
            clean_col = clean_col.split(' AS ')[0].strip() # Remove 'AS alias' if present
            if clean_col.lower().startswith('distinct '):
                clean_col = clean_col[len('distinct '):].strip() # Remove 'DISTINCT ' keyword
            cleaned_selected_columns.append(clean_col)
        
        Logger.info(f"Clean Columns : {', '.join(cleaned_selected_columns)}")
        user_friendly_message = ""
        message_parts = []

        # Determine which columns are present in the query result
        has_product_name = 'product_name' in cleaned_selected_columns
        has_product_category = 'product_category' in cleaned_selected_columns
        has_quantity = 'quantity' in cleaned_selected_columns
        has_unit_price = 'unit_price' in cleaned_selected_columns

        # Iterate through the results to build message parts
        for row in sql_result:
            # Create a dictionary for easier access by column name
            # Assuming the number of columns in `row` matches `cleaned_selected_columns`
            row_data = {col_name: value for col_name, value in zip(cleaned_selected_columns, row)}

            # Apply logic based on column combinations
            if has_product_name and has_unit_price:
                message_parts.append(f"Product : {row_data.get('product_name', 'Unnamed Product')} and Price :{row_data.get('unit_price', 'unknown')}")
            elif has_product_name and has_quantity and has_product_category:
                message_parts.append(f"{row_data.get('quantity', 'unknown')} {row_data.get('product_name', 'Unnamed')} {row_data.get('product_category', 'Category')}")
            elif has_product_name and has_quantity:
                message_parts.append(f"{row_data.get('quantity', 'unknown')} units of {row_data.get('product_name', 'Unnamed Product')}")
            elif has_product_name and has_product_category:
                message_parts.append(f"{row_data.get('product_name', 'Unnamed Product')} ({row_data.get('product_category', 'Category')})")
            elif has_product_name:
                message_parts.append(row_data.get('product_name', 'Unnamed Product'))
            elif has_product_category:
                message_parts.append(row_data.get('product_category', 'Unnamed Category'))
            elif has_quantity:
                message_parts.append(str(row_data.get('quantity', 'unknown')))
            else:
                # Fallback for any other combination
                message_parts.append(", ".join([f"{k}: {v}" for k, v in row_data.items()]))

        Logger.info(f"Msg parts : {', '.join(message_parts)}")
        # Assemble the final user-friendly message based on the detected combination
        if 'quantity < threshold' in sql_query.lower():
            user_friendly_message = f"The following items are below threshold: {', '.join(message_parts)}."
        elif 'quantity > threshold' in sql_query.lower():
            user_friendly_message = f"The following items are above threshold: {', '.join(message_parts)}."
        elif has_product_name and has_unit_price:
            user_friendly_message = f"Result of the query -> {', '.join(message_parts)}"
        elif has_product_name and has_quantity and has_product_category:
            user_friendly_message = f"We have {', '.join(message_parts)} in the inventory."
        elif has_product_name and has_quantity:
            user_friendly_message = f"There are {', '.join(message_parts)} left."
        elif has_product_name and has_product_category:
            user_friendly_message = f"The items are {', '.join(message_parts)}."
        elif has_product_name:
            user_friendly_message = f"The products are {', '.join(message_parts)}."
        elif has_product_category:
            user_friendly_message = f"The categories are {', '.join(message_parts)}."
        elif has_quantity:
            user_friendly_message = f"The quantities are {', '.join(message_parts)}."
        else:
            user_friendly_message = f"Here are the details: {'; '.join(message_parts)}."

        print(f"\nUser-friendly message: {user_friendly_message}")
    else:
        user_friendly_message = "No results to generate a user-friendly message."
        print(user_friendly_message)
    return user_friendly_message

def execute_sql_query(sql_query:str):
    # Connect to the database
    conn = sqlite3.connect(const.DB_FILE_PATH)
    courser = conn.cursor()

    try:
        # Execute the generated SQL query
        courser.execute(sql_query)
        return courser.fetchall()

    except sqlite3.Error as e:
        print(f"\nError executing generated SQL: {e}")
        print(f"Attempted SQL: {sql_query}")
    finally:
        conn.close()

def get_llm_prompt(user_query:str) -> str:
    general_context = """You are given a database schema and a user's question.
        Your task is to generate ONLY the SQL query that answers the question based on the provided schema.
        Follow the format of the examples exactly. For simple quantity queries, do not use aggregation (like SUM) unless explicitly asked.  Do not include ORDER BY clauses or filter by threshold unless explicitly asked.
        Use exact matches for product names. Where clause can only have either product_name or product_category.
        The values in product_category can be either Soap, Beverage, or Deo.
        Sometimes these can be referenced as Soaps, Beverages, or Deos as well in the user query, but in DB they are saved without s.

        Example 1:
        Question: What is the quantity of Arridx?
        SQL: SELECT product_name, product_category, quantity FROM Product WHERE product_name = 'Arridx'

        Example 2:
        Question: What is the inventory of different deos?
        SQL: SELECT product_name, product_category, quantity FROM Product WHERE product_category = 'Deo'

        Example 3:
        Question: Which Deos are below threshold in the inventory?
        SQL: SELECT product_name, quantity FROM Product WHERE product_category = 'Deo' and quantity < threshold

        Example 4:
        Question: Which products are below threshold in the inventory?
        SQL: SELECT product_name, product_category, quantity FROM Product WHERE quantity < threshold

        Example 5:
        Question: What is the price of the Arridx deo?
        SQL: SELECT product_name, unit_price FROM Product WHERE product_name = 'Arridx' and product_category = 'Deo'

        Example 6:
        Question: Which is the cheapest deo in the inventory?
        SQL: SELECT product_name, unit_price FROM Product WHERE product_category = 'deo' ORDER BY unit_price ASC LIMIT 1;
        ---
        Given the following:
    """
    # Define the database schema for the 'Product' and 'Inventory' tables
    # This context is crucial for the LLM to generate correct SQL.
    database_schema = "CREATE TABLE Product ( product_code TEXT PRIMARY KEY, product_name TEXT NOT NULL, product_category TEXT NOT NULL, threshold INTEGER DEFAULT 3, quantity INTEGER DEFAULT 0); CREATE TABLE Inventory ( id TEXT PRIMARY KEY, product_code TEXT NOT NULL, shelf INTEGER, quantity INTEGER NOT NULL, FOREIGN KEY (product_code) REFERENCES Product(product_code));"

    # Combine the question and schema for the LLM input
    # The exact format might vary slightly depending on the model, but this is a common one.
    return f"{general_context} Question: {user_query}\nSchema: {database_schema}\nSQL:"

def get_sql_query_from_llm(prompt:str) -> str:
    
    tokenizer = get_request_tokenizer()
    model = get_request_model()

    # Encode the prompt
    encodeds = tokenizer(prompt, return_tensors="pt", add_special_tokens=True).input_ids

    # Move model and inputs to appropriate device (GPU if available)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model.to(device)
    inputs = encodeds.to(device)

    # Generate SQL tokens. Adjust max_new_tokens and temperature as needed.
    # For SQL generation, a lower temperature (less randomness) is generally preferred.
    generated_ids = model.generate(inputs, max_new_tokens=100, do_sample=True, temperature=0.1, pad_token_id=tokenizer.eos_token_id)

    # Decode the generated tokens
    decoded_output = tokenizer.decode(generated_ids[0], skip_special_tokens=True)

    # Extract the SQL part. The prompt ends with "SQL:", so we look for that.
    sql_start_index = decoded_output.rfind("SQL:")
    if sql_start_index != -1:
        # Extract everything after "SQL:" and strip whitespace
        generated_sql_manual = decoded_output[sql_start_index + len("SQL:"):].strip()
        # Further clean by stopping at the first newline if the model generates additional text.
        if '\n' in generated_sql_manual:
            generated_sql_manual = generated_sql_manual.split('\n')[0].strip()
    else:
        generated_sql_manual = "No SQL generated or 'SQL:' tag not found in output."

    return generated_sql_manual

def get_response(request_message:str) -> tuple[str, str]:
    keywords = [
        "update", "drop", "insert", "delete", "create", 
        "alter", "truncate", "rename", "grant", "revoke", 
        "commit", "savepoint"
    ]
    pattern = re.compile(r'\b(' + '|'.join(keywords) + r')\b', re.IGNORECASE)
    prompt = get_llm_prompt(request_message)
    sql_query = get_sql_query_from_llm(prompt)
    if pattern.search(sql_query):
        response = "Data manipulation/updation is not allowed. Reach out to the admin for these queries"
    else:
        query_result = execute_sql_query(sql_query)
        response = format_response(query_result, sql_query)
    return str(uuid.uuid4()), response

def record_feedback(message_id:str, is_positive:bool) -> str:
    if is_positive:
        return "Glad it helped"
    else:
        return "Noted, we will work on it"
