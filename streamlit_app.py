import os
import requests
import streamlit as st

# Backend API URL
API_URL = os.getenv("RAG_API_URL", "http://127.0.0.1:9000/ask")


def call_rag_api(question: str):
    """Send a question to the FastAPI /ask endpoint."""
    try:
        resp = requests.post(
            API_URL,
            json={"question": question},
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
    "Answers are generated using **retrieval-augmented generation** "
    "(Chroma vector store + LLM)."
)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Sidebar info
with st.sidebar:
    st.header("About")
    st.markdown(
        """
        **Stack:**
        - Chroma (vector store)
        - SentenceTransformers embeddings
        - FastAPI backend (`/ask`)
        - LLM via Groq (Llama 3.1)
        - Streamlit frontend

        **Tip:** Ask things like:
        - "Summarize my projects."
        - "What NLP work have I done?"
        - "What experience do I have with AWS and data engineering?"
        """
    )
    if st.button("🧹 Clear chat"):
        st.session_state["messages"] = []
        st.experimental_rerun()

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
    st.session_state["messages"].append(
        {"role": "user", "content": user_input}
    )

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

