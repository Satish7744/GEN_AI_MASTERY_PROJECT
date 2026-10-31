"""Git & Linux Assistant: Streamlit front end.

The RAG backend is untouched. This file only uses the rag.py interface:
    rag.rewrite_question(question, chat_history) -> str
    rag.retrieve(search_question, k)             -> list[Document]
    rag.stream_answer(question, docs, history)   -> iterator[str]
    rag.DEFAULT_K
"""
from __future__ import annotations

import os
import time
import uuid

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

import ui

st.set_page_config(
    page_title="Git & Linux Assistant",
    page_icon="💻",
    layout="centered",
    initial_sidebar_state="expanded",
)
ui.inject_css()

try:
    import rag
except Exception as exc:  # missing API key, missing docs, etc.
    ui.render_error(f"Could not start the assistant: {exc}")
    st.stop()

K = rag.DEFAULT_K
HISTORY_TURNS = 6  # messages sent back to the model as conversation context

SUGGESTIONS = [
    (":material/help:", "What is Git?"),
    (":material/history:", "How do I undo my last commit?"),
    (":material/call_merge:", "How do I resolve merge conflicts?"),
    (":material/storage:", "How do I check disk space in Linux?"),
    (":material/memory:", "How do I find which process is using port 8080?"),
    (":material/lock:", "Explain Linux file permissions."),
]

TROUBLESHOOT_PROMPT = (
    "Troubleshoot this terminal output. Infer the command, OS and shell where possible. "
    "Answer with these markdown sections, in order: ### Diagnosis, ### Likely cause, "
    "### Fix (numbered steps; start with safe inspection commands; every command in a code block), "
    "### Verify. Put a line starting with 'Warning:' before any destructive command.\n\n"
    "Terminal output:\n"
)


# ----------------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------------
def init_state() -> None:
    defaults = {
        "conversations": {},  # id -> {"id", "title", "messages", "chat_history", "updated"}
        "active_id": None,
        "pending": None,
        "show_sources": True,
        "show_time": True,
        "troubleshoot": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def active_conv() -> dict | None:
    return st.session_state.conversations.get(st.session_state.active_id)


def new_chat() -> None:
    st.session_state.active_id = None
    st.session_state.pending = None


def open_chat(conv_id: str) -> None:
    st.session_state.active_id = conv_id


def delete_chat(conv_id: str) -> None:
    st.session_state.conversations.pop(conv_id, None)
    if st.session_state.active_id == conv_id:
        st.session_state.active_id = None


def clear_all_chats() -> None:
    st.session_state.conversations = {}
    st.session_state.active_id = None


def set_pending(text: str) -> None:
    st.session_state.pending = text


def make_title(text: str, troubleshoot: bool) -> str:
    first = " ".join(text.strip().split())
    title = first[:38] + ("…" if len(first) > 38 else "")
    return f"Error: {title}" if troubleshoot else title


def create_conv(title: str) -> dict:
    conv = {"id": uuid.uuid4().hex[:8], "title": title, "messages": [], "chat_history": [], "updated": time.time()}
    st.session_state.conversations[conv["id"]] = conv
    st.session_state.active_id = conv["id"]
    return conv


# ----------------------------------------------------------------------------
# Backend helpers (thin wrappers around rag.py)
# ----------------------------------------------------------------------------
def build_sources(docs) -> list[dict]:
    out = []
    for doc in docs:
        meta = doc.metadata
        file = os.path.basename(str(meta.get("source", "Unknown source")))
        title = meta.get("title") or file
        text = doc.page_content[:260] + ("…" if len(doc.page_content) > 260 else "")
        out.append({"title": title, "file": file, "category": meta.get("category", ""), "text": text})
    return out


def stream_into(placeholder, pieces) -> str:
    """Render streamed tokens smoothly (throttled) with a caret, return the full text."""
    text, last = "", 0.0
    for piece in pieces:
        text += piece
        now = time.time()
        if now - last > 0.04:
            placeholder.markdown(ui.format_answer(text) + " ▍")
            last = now
    placeholder.markdown(ui.format_answer(text))
    return text


# ----------------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------------
def render_sidebar() -> None:
    with st.sidebar:
        ui.render_brand()
        st.button("New chat", icon=":material/add:", key="newchat", on_click=new_chat, use_container_width=True)

        ui.side_label("Conversations")
        query = st.text_input(
            "Search conversations", key="conv_search", placeholder="Search conversations",
            label_visibility="collapsed",
        ).strip().lower()

        convs = sorted(st.session_state.conversations.values(), key=lambda c: c["updated"], reverse=True)
        if query:
            convs = [c for c in convs if query in c["title"].lower()
                     or any(query in m["content"].lower() for m in c["messages"])]
        if not convs:
            st.markdown(
                f'<div class="side-note">{"No matching conversations." if query else "Your chats will appear here."}</div>',
                unsafe_allow_html=True,
            )
        for conv in convs[:30]:
            left, right = st.columns([0.84, 0.16], gap="small", vertical_alignment="center")
            with left:
                st.button(
                    conv["title"], key=f"conv_{conv['id']}", on_click=open_chat, args=(conv["id"],),
                    type="primary" if conv["id"] == st.session_state.active_id else "secondary",
                    use_container_width=True,
                )
            with right:
                st.button("", icon=":material/close:", key=f"del_{conv['id']}", on_click=delete_chat,
                          args=(conv["id"],), help="Delete chat")

        st.divider()
        ui.side_label("Mode")
        st.toggle("Troubleshoot mode", key="troubleshoot",
                  help="Paste a command and its error output to get a structured diagnosis.")
        st.toggle("Show sources", key="show_sources", help="Show the documents each answer was based on.")

        st.divider()
        ui.side_label("Retrieval")
        st.markdown(
            f'<span class="side-chip">Top {K} chunks</span><span class="side-chip">Chroma</span>'
            f'<span class="side-chip">MiniLM-L6-v2</span>',
            unsafe_allow_html=True,
        )

        st.divider()
        with st.expander("Settings", icon=":material/settings:"):
            st.toggle("Show response time", key="show_time")
            model_name = getattr(rag, "MODEL_NAME", None)
            if model_name:
                st.caption(f"Model: {model_name}")
            st.button("Clear all chats", icon=":material/delete:", on_click=clear_all_chats, use_container_width=True)
        st.markdown(
            '<div class="side-note" style="margin-top:10px">Suggestions only. This app never runs commands on your computer.</div>',
            unsafe_allow_html=True,
        )


# ----------------------------------------------------------------------------
# Main area
# ----------------------------------------------------------------------------
def render_welcome() -> None:
    ui.render_welcome_header()
    with st.container(key="cards"):
        for row in (SUGGESTIONS[:3], SUGGESTIONS[3:]):
            cols = st.columns(3, gap="small")
            for col, (icon, text) in zip(cols, row):
                with col:
                    st.button(text, icon=icon, key=f"card_{text}", on_click=set_pending, args=(text,),
                              use_container_width=True)
    ui.render_welcome_hint()


def answer_question(conv: dict, model_question: str, search_override: str | None) -> None:
    """Run the RAG pipeline for one question and stream the reply into the chat."""
    with st.chat_message("assistant"):
        slot = st.empty()
        try:
            started = time.time()
            recent = conv["chat_history"][-HISTORY_TURNS:]
            slot.markdown(ui.thinking_html("Searching the knowledge base"), unsafe_allow_html=True)
            search_question = search_override or rag.rewrite_question(model_question, recent)
            docs = rag.retrieve(search_question, K)

            slot.markdown(ui.thinking_html("Writing the answer"), unsafe_allow_html=True)
            answer = stream_into(slot, rag.stream_answer(model_question, docs, recent))
            elapsed = time.time() - started
            if not answer.strip():
                raise RuntimeError("The model returned an empty response.")

            conv["chat_history"] += [HumanMessage(content=model_question), AIMessage(content=answer)]
            conv["messages"].append({
                "role": "assistant", "content": answer, "sources": build_sources(docs), "elapsed": elapsed,
            })
        except Exception as exc:  # keep the question, show a friendly error, don't pollute model history
            slot.empty()
            conv["messages"].append({"role": "assistant", "content": f"{type(exc).__name__}: {exc}", "error": True})
    conv["updated"] = time.time()
    st.rerun()  # re-render from state so sources, timing and callouts appear consistently


def main() -> None:
    init_state()
    render_sidebar()

    troubleshoot = st.session_state.troubleshoot
    typed = st.chat_input(
        "Paste a command and its error output..." if troubleshoot
        else "Ask anything about Git, Linux, commands or errors..."
    )
    question = typed or st.session_state.pending
    st.session_state.pending = None

    conv = active_conv()
    if question and conv is None:
        conv = create_conv(make_title(question, troubleshoot))

    ui.render_topbar(conv["title"] if conv else "New chat", troubleshoot)

    if conv is None:
        render_welcome()
        return

    for msg in conv["messages"]:
        ui.render_message(msg, st.session_state.show_sources, st.session_state.show_time)

    if question:
        if troubleshoot and typed:
            model_question = TROUBLESHOOT_PROMPT + question.strip()
            display, search_override = f"```text\n{question.strip()}\n```", question.strip()[:500]
        else:
            model_question, display, search_override = question, question, None
        user_msg = {"role": "user", "content": model_question, "display": display}
        conv["messages"].append(user_msg)
        ui.render_message(user_msg, False, False)
        answer_question(conv, model_question, search_override)  # ends with st.rerun()

    ui.scroll_to_bottom()


main()