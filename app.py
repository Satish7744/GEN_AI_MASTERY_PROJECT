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

<<<<<<< HEAD
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
=======
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "pending" not in st.session_state:
    st.session_state.pending = None

if "show_sources" not in st.session_state:
    st.session_state.show_sources = True

# =========================================================
# HELPER FUNCTIONS
# =========================================================

def set_pending(question):
    st.session_state.pending = question


def render_sources(sources):
    with st.expander(
        f"📚 Reference documents ({len(sources)})",
        expanded=False,
    ):
        if not sources:
            st.caption("No reference documents were retrieved.")
            return

        for index, source in enumerate(sources, start=1):
            name = html.escape(str(source.get("name", "Unknown source")))
            content = html.escape(str(source.get("text", "")))

            st.markdown(
                f"""
                <div class="source-card">
                    <div class="source-name">
                        📄 {index}. {name}
                    </div>
                    <div class="source-text">{content}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-brand">
            <h3>💻 Command Assistant</h3>
            <p>Git & Linux command help, explanations and troubleshooting.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### ⚙️ Settings")

    st.toggle(
        "Show reference documents",
        key="show_sources",
    )

    st.caption(f"Document retrieval: {DEFAULT_K} chunks")

    st.divider()

    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_history = []
        st.session_state.pending = None
        st.rerun()

    if st.session_state.messages:

        chat_text = "\n\n".join(
            f"{message['role'].upper()}: {message['content']}"
            for message in st.session_state.messages
        )

        st.download_button(
            "⬇️ Export conversation",
            data=chat_text,
            file_name="git_linux_assistant_chat.txt",
            mime="text/plain",
            use_container_width=True,
        )

    st.divider()

    st.markdown(
        """
        <div style="font-size:0.78rem; opacity:0.65; line-height:1.9;">
            <b>Supported topics</b><br>
            🔀 Git & version control<br>
            🐧 Linux commands<br>
            🛠️ Error troubleshooting<br>
            📖 Command explanations
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-badge">DEVELOPER PRODUCTIVITY ASSISTANT</div>
        <h1>Git & Linux Command Assistant</h1>
        <p>
            Find the right command, understand how it works, and
            troubleshoot common errors. Ask questions about Git,
            Linux terminal commands, and developer workflows.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# WELCOME SCREEN
# =========================================================

typed_question = st.chat_input(
    "Ask a Git or Linux question..."
)

question = typed_question or st.session_state.pending
st.session_state.pending = None

if not st.session_state.messages and not question:

    st.markdown(
        '<div class="section-title">What do you need help with?</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="section-subtitle">
            Select a topic to get started, or type your question below.
        </div>
        """,
        unsafe_allow_html=True,
    )

    examples = [
        {
            "icon": "🔀",
            "title": "Git Commands",
            "description": "Learn commits, branches, merging and remote repositories.",
            "question": "Explain the most useful Git commands with examples.",
        },
        {
            "icon": "🐧",
            "title": "Linux Commands",
            "description": "Explore files, directories, permissions and processes.",
            "question": "Explain essential Linux terminal commands with examples.",
        },
        {
            "icon": "🛠️",
            "title": "Fix an Error",
            "description": "Understand command errors and find possible solutions.",
            "question": "How do I troubleshoot common Git errors?",
        },
    ]

    columns = st.columns(3)

    for column, example in zip(columns, examples):

        with column:

            st.markdown(
                f"""
                <div class="suggestion-card">
                    <div class="suggestion-icon">{example['icon']}</div>
                    <h4>{example['title']}</h4>
                    <p>{example['description']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.button(
                "Explore topic →",
                key=f"example_{example['title']}",
                on_click=set_pending,
                args=(example["question"],),
                use_container_width=True,
            )

# =========================================================
# DISPLAY CHAT HISTORY
# =========================================================

for message in st.session_state.messages:

    avatar = "🧑‍💻" if message["role"] == "user" else "🤖"

    with st.chat_message(message["role"], avatar=avatar):

        st.markdown(message["content"])

        if message["role"] == "assistant":

            if message.get("time") is not None:
                st.caption(
                    f"⏱️ Response time: {message['time']:.1f}s"
                )

            if (
                message.get("sources")
                and st.session_state.show_sources
            ):
                render_sources(message["sources"])

# =========================================================
# HANDLE NEW QUESTION
# =========================================================

if question:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(question)

    with st.chat_message("assistant", avatar="🤖"):

        start = time.time()

        try:

            with st.spinner("🔎 Searching the command knowledge base..."):

                search_question = rag.rewrite_question(
                    question,
                    st.session_state.chat_history,
                )

                docs = rag.retrieve(
                    search_question,
                    DEFAULT_K,
                )

            answer = st.write_stream(
                rag.stream_answer(
                    question,
                    docs,
                    st.session_state.chat_history,
                )
            )

            elapsed = time.time() - start

            st.caption(f"⏱️ Response time: {elapsed:.1f}s")

            sources = [
                {
                    "name": document.metadata.get(
                        "source",
                        "Unknown source",
                    ),
                    "text": document.page_content[:250] + (
                        "..."
                        if len(document.page_content) > 250
                        else ""
                    ),
                }
                for document in docs
            ]

            if st.session_state.show_sources:
                render_sources(sources)

            # Update conversational history.

            from langchain_core.messages import HumanMessage, AIMessage

            st.session_state.chat_history.append(
                HumanMessage(content=question)
            )

            st.session_state.chat_history.append(
                AIMessage(content=answer)
            )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                    "time": elapsed,
                }
            )

        except Exception:

            # Avoid retaining a failed request as a completed exchange.
            if (
                st.session_state.messages
                and st.session_state.messages[-1]["role"] == "user"
                and st.session_state.messages[-1]["content"] == question
            ):
                st.session_state.messages.pop()

            st.error(
                "Unable to process your question. "
                "Check your LLM configuration and document index, "
                "then try again."
            )

# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="app-footer">
        Git & Linux Command Assistant
        <br>
        Built with Streamlit · Retrieval-Augmented Generation
    </div>
    """,
    unsafe_allow_html=True,
)
>>>>>>> 6b5faf3 (version 1)
