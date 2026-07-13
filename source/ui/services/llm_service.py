import uuid
import streamlit as st
import os
from transformers import AutoTokenizer, AutoModelForCausalLM, T5Tokenizer, T5ForConditionalGeneration
import constants as const
import sqlite3
import torch

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

def format_response(user_query, sql_result):
    message_tokenizer = get_response_tokenizer()
    message_model = get_response_model()

    if sql_result:
        product_summaries = []
        for product_name, product_category, quantity in sql_result:
            product_summaries.append(f"{quantity} units of {product_name}")
        
        formatted_results_string = ", ".join(product_summaries)

        # Craft a prompt for the LLM to generate a user-friendly message
        # Explicitly instruct the model not to output SQL and to provide a summary.
        prompt = f"As an inventory assistant, your task is to provide a concise, user-friendly summary of inventory levels. Based on the user's request and the inventory data, generate a natural language message. Do not output any SQL code. Always list each product and its quantity. If a product has 0 quantity, clearly state '0 units'.\n\nUser's Original Question: '{user_query}'\nSQL Query Used (for context, do not output this): '{sql_result}'\nInventory Details: '{formatted_results_string}'\n\nExample of desired output: 'There are 5 units of Arridx, 3 units of Degree, and 0 units of Mitchum left.'\n\nYour summary:"

        # print(f"\nSending to LLM for user-friendly message:")

        try:
            input_ids = message_tokenizer.encode(prompt, return_tensors="pt")
            outputs = message_model.generate(input_ids, max_new_tokens=100) # Increased max_new_tokens for longer summaries
            user_friendly_message = message_tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
            print(f"\nUser-friendly message: {user_friendly_message}")
        except Exception as e:
            print(f"Error generating user-friendly message: {e}")
    else:
        print("No results to generate a user-friendly message.")
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
        Follow the format of the examples exactly. For simple quantity queries, do not use aggregation (like SUM) unless explicitly asked.
        Use exact matches for product names. Where clause can only have either product_name or product_category.
        The values in product_category can be either Soap, Beverage, or Deo.
        Sometimes these can be referenced as Soaps, Beverages, or Deos as well in the user query, but in DB they are saved without s.

        Example 1:
        Question: What is the quantity of Arridx?
        SQL: SELECT product_name, product_category, quantity FROM Product WHERE product_name = 'Arridx'

        Example 2:
        Question: Get me the inventory of different Deo
        SQL: SELECT product_name, quantity FROM Product WHERE product_category = 'Deo'

        Example 3:
        Question: Which Deos are below threshold in the inventory?
        SQL: SELECT product_name, quantity FROM Product WHERE product_category = 'Deo' and quantity < threshold

        Example 4:
        Question: Which products are below threshold in the inventory?
        SQL: SELECT product_name, product_category, quantity FROM Product WHERE quantity < threshold
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
    prompt = get_llm_prompt(request_message)
    sql_query = get_sql_query_from_llm(prompt)
    query_result = execute_sql_query(sql_query)
    response = format_response(request_message, query_result)
    return str(uuid.uuid4()), response

def record_feedback(message_id:str, is_positive:bool) -> str:
    if is_positive:
        return "Glad it helped"
    else:
        return "Noted, we will work on it"