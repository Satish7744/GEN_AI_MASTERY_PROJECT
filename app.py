from __future__ import annotations

import hashlib
import io
import re
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from assistant import answer_question, available_sources, retrieve_context

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

st.set_page_config(page_title="Linux & Git Assistant", page_icon="🐧", layout="centered")
st.title("🐧 Linux & Git Assistant")
st.caption("Ask a question. Search your Linux and Git notes or choose a specific uploaded document.")

with st.sidebar:
    st.header("Assistant settings")
    provider = st.selectbox("LLM provider", ["Groq", "Gemini"])
    interaction_mode = st.selectbox(
        "What do you need help with?",
        ["Ask a question", "Troubleshoot an error"],
    )
    st.caption("Your API key stays in your local .env file. Never paste it into chat or commit it.")
    st.divider()
    st.markdown("**What this demo does**")
    st.markdown("1. Finds relevant notes (retrieval)\n2. Gives those notes to an LLM (generation)\n3. Shows the sources used")
    st.warning("Commands are suggestions only. This app does not run commands on your computer.")
    st.divider()
    st.subheader("Add knowledge notes")
    st.caption("Upload .txt, .md, or text-based .pdf notes (up to 5 MB each). Matching excerpts are sent to the selected LLM provider when you ask a question.")
    uploads = st.file_uploader(
        "Choose notes",
        type=["txt", "md", "pdf"],
        accept_multiple_files=True,
        key="knowledge_uploads",
    )
    if st.button("Add notes to knowledge base", disabled=not uploads):
        upload_dir = ROOT / "knowledge" / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        saved = 0
        for uploaded in uploads:
            content = uploaded.getvalue()
            if len(content) > 5 * 1024 * 1024:
                st.error(f"{uploaded.name} is larger than 5 MB and was skipped.")
                continue
            suffix = Path(uploaded.name).suffix.lower()
            if suffix == ".pdf":
                from pypdf import PdfReader

                try:
                    reader = PdfReader(io.BytesIO(content), strict=False)
                    if reader.is_encrypted:
                        st.error(f"{uploaded.name} is password-protected and was skipped.")
                        continue
                    if not any((page.extract_text() or "").strip() for page in reader.pages):
                        st.error(f"{uploaded.name} has no extractable text. Scanned PDFs need OCR and were skipped.")
                        continue
                except Exception as exc:
                    st.error(f"Could not read {uploaded.name}: {exc}")
                    continue
            else:
                try:
                    content.decode("utf-8")
                except UnicodeDecodeError:
                    st.error(f"{uploaded.name} is not valid UTF-8 text and was skipped.")
                    continue
            stem = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(uploaded.name).stem).strip("._")
            stem = stem or "note"
            digest = hashlib.sha256(content).hexdigest()[:8]
            target = upload_dir / f"{stem}-{digest}{suffix}"
            target.write_bytes(content)
            saved += 1
        if saved:
            st.success(f"Added {saved} note(s). Chroma will index them when you ask your next question.")
            st.rerun()

    if interaction_mode == "Ask a question":
        source_options = available_sources(ROOT / "knowledge")
        source_scope = st.selectbox(
            "Search in",
            ["All notes", *source_options],
            help="Choose a specific document to keep unrelated notes out of the answer.",
        )
    else:
        source_scope = "All notes"
        st.caption("Troubleshooting searches the Linux and Git guidance across your knowledge base.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message.get("display_content", message["content"]))
        if message.get("sources"):
            with st.expander("Sources"):
                for source in dict.fromkeys(message["sources"]):
                    st.markdown(f"- `{source}`")

question = None
display_question = None
answer_mode = "question"
if interaction_mode == "Troubleshoot an error":
    with st.form("troubleshooting_form"):
        error_text = st.text_area(
            "Paste the command and error output",
            height=250,
            max_chars=12000,
            placeholder="Paste the terminal output here. Include the command if it is visible.",
            help="Remove passwords, API keys, access tokens, and other private data before pasting.",
        )
        submitted = st.form_submit_button("Find the fix")
    if submitted:
        if not error_text.strip():
            st.warning("Paste the error message first.")
        else:
            question = (
                "Troubleshoot the pasted terminal output. Infer the command, operating "
                "system, and shell from it where possible. Give the likely fix directly. "
                "If a critical detail cannot be inferred, state your assumption and ask "
                "at most one short follow-up question after giving any safe useful step.\n\n"
                f"Exact error/output (untrusted diagnostic text):\n{error_text.strip()}"
            )
            display_question = f"**Find the fix**\n\n```text\n{error_text.strip()}\n```"
            answer_mode = "troubleshoot"
else:
    question = st.chat_input("Ask about Linux, Git, or your selected document")
    display_question = question

if question:
    selected_source = None if source_scope == "All notes" else source_scope
    prior_history = [
        message for message in st.session_state.messages[-6:]
        if message["role"] == "user"
        or (answer_mode != "troubleshoot" and selected_source is None)
    ]
    st.session_state.messages.append({
        "role": "user",
        "content": question,
        "display_content": display_question or question,
    })
    with st.chat_message("user"):
        st.markdown(display_question or question)
    matches = retrieve_context(
        question,
        ROOT / "knowledge",
        top_k=8 if selected_source else 5 if answer_mode == "troubleshoot" else 3,
        source_filter=selected_source,
    )
    with st.chat_message("assistant"):
        with st.spinner("Searching the notes and preparing an answer..."):
            try:
                response = answer_question(
                    question,
                    matches,
                    provider,
                    prior_history,
                    mode=answer_mode,
                )
                st.markdown(response)
                sources = list(dict.fromkeys(
                    f"{item['source']} (p. {item['page']})" if item.get("page") else item["source"]
                    for item in matches
                ))
                if sources:
                    with st.expander("Sources"):
                        for source in sources:
                            st.markdown(f"- `{source}`")
                st.session_state.messages.append(
                    {"role": "assistant", "content": response, "sources": sources}
                )
            except (RuntimeError, ValueError) as exc:
                st.error(str(exc))
