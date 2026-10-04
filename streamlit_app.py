import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Backend API URL
API_URL = os.getenv("RAG_API_URL", "http://127.0.0.1:9000/ask")


def call_rag_api(question: str):
    """Send a question to the FastAPI /ask endpoint."""
    try:
        resp = requests.post(
            API_URL,
            json={"question": question, "mode": st.session_state.get("answer_mode", "extractive")},
            headers={"X-API-Key": os.getenv("RAG_API_KEY", "")},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("answer"), data.get("context", [])
    except Exception as e:
        st.error(f"Error calling RAG API: {e}")
        return None, []


# ---------------- Streamlit UI ---------------- #

st.set_page_config(
    page_title="RAG Knowledge Assistant",
    page_icon="📚",
    layout="centered",
)

st.title("📚 RAG Knowledge Assistant")
st.write(
    "Ask questions about your indexed documents. "
    "View supporting excerpts locally, or select generated answers to use the configured LLM."
)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Sidebar info
with st.sidebar:
    st.selectbox("Answer mode", ["extractive", "generative"], key="answer_mode")
    st.caption("Generated answers require the server’s Groq API key.")
    st.header("About")
    st.markdown(
        """
        **Stack:**
        - BM25 retrieval over a versioned corpus
        - FastAPI backend (`/ask`)
        - Optional generation via Groq
        - Streamlit frontend

        **Tip:** Ask things like:
        - "How does a token bucket rate limiter work?"
        - "What's the difference between a Bloom filter and a hash set?"
        - "Why does column order matter in a composite database index?"
        """
    )
    if st.button("🧹 Clear chat"):
        st.session_state["messages"] = []
        st.rerun()

# Display chat history
for msg in st.session_state["messages"]:
    role = msg["role"]
    content = msg["content"]
    context = msg.get("context", [])

    with st.chat_message("user" if role == "user" else "assistant"):
        st.markdown(content)
        if role == "assistant" and context:
            with st.expander("🔍 View supporting context"):
                for i, chunk in enumerate(context):
                    text = chunk.get("text", "").strip()
                    meta = chunk.get("metadata", {})
                    source = meta.get("source", "unknown")
                    idx = meta.get("chunk_index", "?")
                    st.markdown(f"**Source:** `{source}` (chunk {idx})")
                    st.write(text)
                    if i < len(context) - 1:
                        st.markdown("---")

# Chat input
user_input = st.chat_input("Ask a question about your documents...")

if user_input:
    # Add user message to history
    st.session_state["messages"].append({"role": "user", "content": user_input})

    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Get assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer, context = call_rag_api(user_input)

        if answer is None:
            st.error("Could not get a response from the backend.")
        else:
            st.markdown(answer)
            # Save assistant message (with context) to history
            st.session_state["messages"].append(
                {
                    "role": "assistant",
                    "content": answer,
                    "context": context,
                }
            )
