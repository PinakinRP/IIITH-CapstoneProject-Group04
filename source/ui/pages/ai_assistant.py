import streamlit as st
import constants as const
import streamlit.components.v1 as stc
from components.sidebar import render_sidebar
import services.llm_service as ls
import uuid

def render_chatbot():
    col1, col2 = st.columns([1, 11])
    with col1:
        st.image(
            str(const.IMAGE_DIR / "ai-assistant.png"), 
            use_container_width=True
        )
    with col2:
        st.header("AI Assistant")

    if "feedback" not in st.session_state:
        st.session_state.feedback = {}  # message_id -> feedback text

    if "messages" not in st.session_state:
        st.session_state.messages = []
        msg_id = str(uuid.uuid4())
        st.session_state.messages.append({
            "id": msg_id,
            "role": "assistant",
            "content": "How may I help you?"
        })
        st.session_state.feedback[msg_id] = ""

    # ---------------- CSS ----------------
    st.markdown("""
    <style>
    .user-container {
        display: flex;
        justify-content: flex-end;
        margin: 8px 0;
    }

    .user-message {
        background-color: #DCF8C6;
        color: black;
        padding: 10px 14px;
        border-radius: 12px;
        max-width: 70%;
    }

    .assistant-container {
        display: flex;
        justify-content: flex-start;
        margin: 8px 0;
    }

    .assistant-message {
        background-color: #F1F3F4;
        color: black;
        padding: 10px 14px;
        border-radius: 12px;
        max-width: 70%;
    }
                
    /* Background of message cell */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
    }
                            
    /* Hide the avatar */
    [data-testid="stChatMessageAvatarAssistant"] {
        display: none;
    }

    /* Hide the avatar */
    [data-testid="stChatMessageAvatarUser"] {
        display: none;
    }
                
    /* Remove the space reserved for the avatar */
    [data-testid="stChatMessage"] {
        grid-template-columns: auto !important;
    }

    [data-testid="stChatMessageContent"] {
        margin-left: 0 !important;
    }
                
    div.stButton {
        width: auto !important;
        margin: 0 !important;
    }

    div.stButton > button {
        padding: 0 !important;
        min-width: 0 !important;
        border: none !important;
        background: transparent !important;
        font-size: 10px !important;
        line-height: 1 !important;
        box-shadow: none !important;
    }

    div.stButton > button:hover {
        transform: scale(1.15);
        background: transparent !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ---------------- Chat history ----------------
    with st.container(height=390):
        for msg in st.session_state.messages:
            # USER MESSAGE
            if msg["role"] == "user":
                with st.chat_message("user", avatar=None):
                    st.markdown(f"""
                        <div class="user-container">
                            <b>Me</b>
                        </div>
                        <div class="user-container">
                            <div class="user-message">{msg["content"]}</div>
                        </div>
                    """, unsafe_allow_html=True)

            # ASSISTANT MESSAGE
            else:
                with st.chat_message("assistant", avatar=None):
                    st.markdown(f"""
                        <div class="assistant-container">
                            <b>Assistant</b>
                        </div>
                        <div class="assistant-container">
                            <div class="assistant-message">{msg["content"]}</div>
                        </div>
                    """, unsafe_allow_html=True)

                # ---------------- Feedback UI ----------------
                if "id" in msg:
                    msg_id = msg["id"]

                    # If feedback already given → show message instead of buttons
                    if msg_id in st.session_state.feedback:
                        if st.session_state.feedback[msg_id] != "":
                            st.info(st.session_state.feedback[msg_id])

                    else:
                        col1, col2, *_ = st.columns(10)

                        with col1:
                            if st.button("👍 Helpful", key=f"up_{msg_id}"):
                                st.session_state.feedback[msg_id] = ls.record_feedback(msg_id, True)
                                st.rerun()

                        with col2:
                            if st.button("👎 Not helpful", key=f"down_{msg_id}"):
                                st.session_state.feedback[msg_id] = ls.record_feedback(msg_id, False)
                                st.rerun()

    # ---------------- Input ----------------
    if prompt := st.chat_input("Ask something..."):

        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        message_id, response_message = ls.get_response(prompt)

        st.session_state.messages.append({
            "id": message_id,
            "role": "assistant",
            "content": response_message
        })

        st.rerun()


def render_page():
    st.set_page_config(
        page_title="AI Assistant",
        page_icon="🤖",
        layout="wide"
    )

    render_sidebar()

    render_chatbot()

if __name__ == "__main__":
    render_page()
