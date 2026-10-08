from __future__ import annotations

from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from assistant import answer_question, retrieve_context

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

st.set_page_config(page_title="Linux & Git Assistant", page_icon="🐧", layout="centered")
st.title("🐧 Linux & Git Assistant")
st.caption("Ask a question. The assistant searches its Linux and Git notes, then explains an answer.")

with st.sidebar:
    st.header("Assistant settings")
    provider = st.selectbox("LLM provider", ["Groq", "Gemini"])
    st.caption("Your API key stays in your local .env file. Never paste it into chat or commit it.")
    st.divider()
    st.markdown("**What this demo does**")
    st.markdown("1. Finds relevant notes (retrieval)\n2. Gives those notes to an LLM (generation)\n3. Shows the sources used")
    st.warning("Commands are suggestions only. This app does not run commands on your computer.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Sources"):
                for source in message["sources"]:
                    st.markdown(f"- `{source}`")

question = st.chat_input("For example: How do I undo my last Git commit safely?")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    matches = retrieve_context(question, ROOT / "knowledge")
    with st.chat_message("assistant"):
        with st.spinner("Searching the notes and preparing an answer..."):
            try:
                response = answer_question(question, matches, provider)
                st.markdown(response)
                sources = [item["source"] for item in matches]
                if sources:
                    with st.expander("Sources"):
                        for source in sources:
                            st.markdown(f"- `{source}`")
                st.session_state.messages.append(
                    {"role": "assistant", "content": response, "sources": sources}
                )
            except (RuntimeError, ValueError) as exc:
                st.error(str(exc))
