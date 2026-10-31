"""UI layer for the Git & Linux Assistant: theme CSS and reusable components.

Nothing in here touches the RAG backend. app.py wires these pieces to rag.py.
"""
from __future__ import annotations

import html
import re

import streamlit as st
import streamlit.components.v1 as components

APP_NAME = "Git & Linux Assistant"

# ----------------------------------------------------------------------------
# Theme
# ----------------------------------------------------------------------------
THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --bg: #0d0e12;
  --sidebar: #111218;
  --surface: #161720;
  --surface-2: #1c1d28;
  --border: rgba(255,255,255,0.08);
  --border-strong: rgba(255,255,255,0.14);
  --text: #e7e8ee;
  --muted: #9aa0ae;
  --accent: #8b7cf6;
  --accent-soft: rgba(139,124,246,0.14);
  --warn: #f5a524;
  --radius: 14px;
}

html, body, [class*="css"], .stApp, .stMarkdown, button, input, textarea {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}
code, pre, kbd, samp, [data-testid="stCode"] * {
  font-family: 'JetBrains Mono', ui-monospace, 'Cascadia Code', Menlo, monospace !important;
}

.stApp { background: var(--bg); color: var(--text); }

/* Streamlit chrome */
#MainMenu, footer, [data-testid="stAppDeployButton"],
[data-testid="stDecoration"] { display: none !important; visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }

/* Main column */
.block-container {
  max-width: 820px;
  padding: 1.2rem 1.25rem 7rem;
}

/* ---------------- Sidebar ---------------- */
[data-testid="stSidebar"] {
  background: var(--sidebar);
  border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .block-container,
[data-testid="stSidebarUserContent"] { padding-top: 1rem; }

.brand { display: flex; align-items: center; gap: 10px; padding: 2px 4px 14px; }
.brand-mark {
  width: 32px; height: 32px; border-radius: 9px; background: var(--accent-soft);
  border: 1px solid rgba(139,124,246,0.4); display: grid; place-items: center; flex: none;
}
.brand-name { font-weight: 600; font-size: 0.98rem; letter-spacing: -0.01em; line-height: 1.15; }
.brand-sub { font-size: 0.72rem; color: var(--muted); }

.side-label {
  font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.09em;
  color: var(--muted); margin: 14px 4px 6px; font-weight: 500;
}
.side-note { font-size: 0.76rem; color: var(--muted); line-height: 1.5; padding: 0 4px; }
.side-chip {
  display: inline-block; font-size: 0.72rem; color: var(--muted); border: 1px solid var(--border);
  border-radius: 999px; padding: 2px 9px; margin: 2px 4px 2px 0;
}

/* Buttons (default = quiet) */
[data-testid="stSidebar"] .stButton > button {
  width: 100%; justify-content: flex-start; text-align: left; border-radius: 10px;
  background: transparent; border: 1px solid transparent; color: var(--text);
  font-size: 0.86rem; padding: 0.45rem 0.65rem; min-height: 0;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
[data-testid="stSidebar"] .stButton > button:hover { background: var(--surface-2); border-color: var(--border); }
[data-testid="stSidebar"] .stButton > button p { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Active conversation */
[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
  background: var(--accent-soft); border-color: rgba(139,124,246,0.35); color: #fff;
}

/* New chat */
.st-key-newchat button {
  background: var(--surface-2) !important; border: 1px solid var(--border-strong) !important;
  justify-content: center !important; font-weight: 500 !important;
}
.st-key-newchat button:hover { border-color: var(--accent) !important; }

/* Delete (x) buttons */
[class*="st-key-del_"] button { justify-content: center !important; color: var(--muted); padding: 0.4rem 0 !important; }
[class*="st-key-del_"] button:hover { color: #ff6b6b; }

/* Inputs in sidebar */
[data-testid="stSidebar"] input {
  background: var(--surface) !important; border: 1px solid var(--border) !important;
  border-radius: 10px !important; font-size: 0.85rem !important;
}
[data-testid="stSidebar"] input:focus { border-color: var(--accent) !important; box-shadow: none !important; }
[data-testid="stSidebar"] hr { border-color: var(--border); margin: 0.9rem 0; }
[data-testid="stSidebar"] [data-testid="stExpander"] {
  border: 1px solid var(--border); border-radius: 10px; background: var(--surface);
}

/* ---------------- Top bar ---------------- */
.topbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding-bottom: 10px; }
.topbar-title {
  font-weight: 500; font-size: 0.95rem; color: var(--text);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.pill {
  display: inline-flex; align-items: center; gap: 6px; font-size: 0.72rem; color: var(--muted);
  border: 1px solid var(--border); border-radius: 999px; padding: 3px 10px; white-space: nowrap;
}
.pill.on { color: #ffd9a0; border-color: rgba(245,165,36,0.45); background: rgba(245,165,36,0.08); }
.dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; display: inline-block; }

/* ---------------- Welcome ---------------- */
.welcome { text-align: center; padding: 4.2vh 0 1.6rem; }
.welcome-mark {
  width: 56px; height: 56px; margin: 0 auto 18px; border-radius: 16px; display: grid; place-items: center;
  background: var(--accent-soft); border: 1px solid rgba(139,124,246,0.4);
}
.welcome h1 { font-size: 2rem; font-weight: 600; letter-spacing: -0.02em; margin: 0 0 8px; padding: 0; }
.welcome p { color: var(--muted); font-size: 1rem; margin: 0 auto; max-width: 520px; line-height: 1.55; }

.st-key-cards button {
  width: 100%; min-height: 76px; justify-content: flex-start; text-align: left;
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 0.85rem 1rem; color: var(--text); font-size: 0.9rem; line-height: 1.35;
  transition: border-color .15s ease, background .15s ease;
}
.st-key-cards button:hover { border-color: rgba(139,124,246,0.55); background: var(--surface-2); }
.st-key-cards button p { white-space: normal; text-align: left; }
.st-key-cards [data-testid="stIconMaterial"] { color: var(--accent); }
.st-key-cards button { justify-content: flex-start !important; }
.st-key-cards button > div { justify-content: flex-start !important; width: 100%; }
.st-key-cards button [data-testid="stMarkdownContainer"] { text-align: left; flex: 1; }
.welcome-hint { text-align: center; color: var(--muted); font-size: 0.78rem; margin-top: 1.1rem; }

/* ---------------- Messages ---------------- */
[data-testid="stChatMessage"] {
  background: transparent; border: 0; padding: 0.55rem 0; gap: 0.85rem; align-items: flex-start;
}
[data-testid="stChatMessageAvatarUser"] {
  background: #2a2c3a !important; color: var(--text) !important; border-radius: 10px !important;
}
[data-testid="stChatMessageAvatarAssistant"] {
  background: var(--accent-soft) !important; color: var(--accent) !important;
  border: 1px solid rgba(139,124,246,0.4); border-radius: 10px !important;
}
/* User messages: right-aligned bubble */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { flex-direction: row-reverse; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
  background: var(--surface-2); border: 1px solid var(--border); border-radius: 16px 16px 4px 16px;
  padding: 0.65rem 0.95rem; max-width: 86%; flex: 0 1 auto;
}
[data-testid="stChatMessageContent"] { min-width: 0; }
[data-testid="stChatMessageContent"] p { line-height: 1.65; font-size: 0.96rem; }
[data-testid="stChatMessageContent"] h3 {
  font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--accent);
  font-weight: 600; margin: 1.2rem 0 0.4rem; padding: 0;
}
[data-testid="stChatMessageContent"] ol li, [data-testid="stChatMessageContent"] ul li { line-height: 1.6; }

/* Code */
[data-testid="stChatMessageContent"] pre, [data-testid="stCode"] {
  background: #090a0e !important; border: 1px solid var(--border); border-radius: 12px; font-size: 0.85rem;
}
[data-testid="stChatMessageContent"] :not(pre) > code {
  background: rgba(139,124,246,0.13); color: #cfc8ff; border-radius: 6px; padding: 0.12em 0.42em; font-size: 0.86em;
}

/* Callouts (warnings / notes arrive as blockquotes) */
[data-testid="stChatMessageContent"] blockquote {
  margin: 0.8rem 0; padding: 0.65rem 0.9rem; border: 1px solid var(--border);
  border-left: 3px solid var(--warn); border-radius: 10px; background: rgba(245,165,36,0.06);
}
[data-testid="stChatMessageContent"] blockquote p { margin: 0; font-size: 0.9rem; }

.meta { color: var(--muted); font-size: 0.72rem; margin-top: 4px; }

/* Sources */
[data-testid="stExpander"] { border: 1px solid var(--border); border-radius: 12px; background: var(--surface); }
[data-testid="stExpander"] summary { font-size: 0.82rem; color: var(--muted); }
.source-card {
  border: 1px solid var(--border); border-radius: 10px; padding: 0.6rem 0.8rem;
  margin: 0.4rem 0; background: var(--bg);
}
.source-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.source-idx {
  width: 20px; height: 20px; border-radius: 6px; display: grid; place-items: center; flex: none;
  background: var(--accent-soft); color: var(--accent); font-size: 0.7rem; font-weight: 600;
}
.source-name { font-weight: 500; font-size: 0.84rem; }
.source-file { color: var(--muted); font-size: 0.74rem; }
.source-text { color: var(--muted); font-size: 0.78rem; margin-top: 6px; white-space: pre-wrap; line-height: 1.5; }

/* Loading / typing indicator */
.thinking { display: flex; align-items: center; gap: 10px; color: var(--muted); font-size: 0.88rem; padding: 6px 0; }
.dots { display: inline-flex; gap: 4px; }
.dots i { width: 6px; height: 6px; border-radius: 50%; background: var(--accent); opacity: .35; animation: blink 1.2s infinite; }
.dots i:nth-child(2) { animation-delay: .2s; } .dots i:nth-child(3) { animation-delay: .4s; }
@keyframes blink { 0%, 80%, 100% { opacity: .25; } 40% { opacity: 1; } }

/* Error card */
.error-card {
  border: 1px solid rgba(255,107,107,0.4); background: rgba(255,107,107,0.07);
  border-radius: 12px; padding: 0.8rem 1rem; font-size: 0.9rem;
}
.error-card b { color: #ff9d9d; }
.error-card code { white-space: pre-wrap; word-break: break-word; }

/* ---------------- Composer ---------------- */
[data-testid="stBottom"] > div, [data-testid="stBottomBlockContainer"] { background: var(--bg); }
[data-testid="stChatInput"] {
  background: var(--surface); border: 1px solid var(--border-strong); border-radius: 22px;
  padding: 2px 4px; box-shadow: 0 6px 24px rgba(0,0,0,0.35);
}
[data-testid="stChatInput"]:focus-within { border-color: var(--accent); }
[data-testid="stChatInput"] textarea { font-size: 0.96rem; color: var(--text); background: transparent; }
[data-testid="stChatInput"] button { border-radius: 14px; }
[data-testid="stChatInput"] button:not(:disabled) { background: var(--accent); color: #0d0e12; }
.composer-note { text-align: center; color: var(--muted); font-size: 0.7rem; margin-top: 6px; }

/* hide the zero-height scroll helper iframe */
iframe[height="0"] { position: absolute; width: 0; height: 0; border: 0; }

/* ---------------- Responsive ---------------- */
@media (max-width: 900px) {
  .block-container { padding: 1rem 0.9rem 7rem; }
  .welcome h1 { font-size: 1.65rem; }
}
@media (max-width: 640px) {
  .welcome { padding-top: 1.5vh; }
  .welcome h1 { font-size: 1.4rem; }
  .welcome p { font-size: 0.92rem; }
  [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] { max-width: 100%; }
  .topbar-title { max-width: 55vw; }
  .st-key-cards button { min-height: 62px; }
}
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb { background: #2a2c3a; border-radius: 8px; }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb { background: #2a2c3a; border-radius: 8px; }

/* Always show the "open sidebar" arrow, in the accent colour */
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapsedControl"] {
  display: flex !important;
  visibility: visible !important;
}
[data-testid="stExpandSidebarButton"] button,
[data-testid="stSidebarCollapsedControl"] button {
  color: var(--accent) !important;
  background: var(--surface) !important;
  border: 1px solid var(--border-strong) !important;
  border-radius: 10px !important;
}
</style>
"""


# Lucide-style inline SVGs (no external icon dependency)
_TERMINAL_SVG = (
    '<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="#8b7cf6" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"/>'
    '<line x1="12" y1="19" x2="20" y2="19"/></svg>'
)


def inject_css() -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Components
# ----------------------------------------------------------------------------
def render_brand() -> None:
    st.markdown(
        f"""<div class="brand"><div class="brand-mark">{_TERMINAL_SVG.format(s=18)}</div>
        <div><div class="brand-name">{APP_NAME}</div><div class="brand-sub">RAG-powered command help</div></div></div>""",
        unsafe_allow_html=True,
    )


def side_label(text: str) -> None:
    st.markdown(f'<div class="side-label">{html.escape(text)}</div>', unsafe_allow_html=True)


def render_topbar(title: str, troubleshoot: bool) -> None:
    pill = (
        '<span class="pill on"><span class="dot"></span>Troubleshoot mode</span>'
        if troubleshoot
        else '<span class="pill"><span class="dot"></span>Q&amp;A mode</span>'
    )
    st.markdown(
        f'<div class="topbar"><div class="topbar-title">{html.escape(title)}</div>{pill}</div>',
        unsafe_allow_html=True,
    )


def render_welcome_header() -> None:
    st.markdown(
        f"""<div class="welcome"><div class="welcome-mark">{_TERMINAL_SVG.format(s=28)}</div>
        <h1>Your Git &amp; Linux Assistant</h1>
        <p>Your intelligent companion for Git workflows, Linux commands, and troubleshooting.</p></div>""",
        unsafe_allow_html=True,
    )


def render_welcome_hint() -> None:
    st.markdown(
        '<div class="welcome-hint">Tip: switch on <b>Troubleshoot mode</b> in the sidebar, '
        "then paste a command and its error output.</div>",
        unsafe_allow_html=True,
    )


def thinking_html(label: str) -> str:
    return f'<div class="thinking"><span class="dots"><i></i><i></i><i></i></span><span>{html.escape(label)}</span></div>'


def render_sources(sources: list[dict]) -> None:
    if not sources:
        return
    with st.expander(f"Sources ({len(sources)})", icon=":material/menu_book:"):
        cards = []
        for i, src in enumerate(sources, 1):
            cat = f" · {html.escape(src['category'])}" if src.get("category") else ""
            cards.append(
                f'<div class="source-card"><div class="source-head"><span class="source-idx">{i}</span>'
                f'<span class="source-name">{html.escape(src["title"])}</span>'
                f'<span class="source-file">{html.escape(src["file"])}{cat}</span></div>'
                f'<div class="source-text">{html.escape(src["text"])}</div></div>'
            )
        st.markdown("".join(cards), unsafe_allow_html=True)


def render_error(detail: str) -> None:
    st.markdown(
        '<div class="error-card"><b>Something went wrong.</b> I could not finish that answer. '
        "Check your <code>GROQ_API_KEY</code>, your internet connection, and that the document index exists, "
        f"then try again.<br><br><code>{html.escape(detail)}</code></div>",
        unsafe_allow_html=True,
    )


def render_message(msg: dict, show_sources: bool, show_time: bool) -> None:
    role = msg["role"]
    with st.chat_message(role):
        if msg.get("error"):
            render_error(msg["content"])
            return
        if role == "user":
            st.markdown(msg.get("display", msg["content"]))
            return
        st.markdown(format_answer(msg["content"]))
        if show_time and msg.get("elapsed") is not None:
            st.markdown(f'<div class="meta">{msg["elapsed"]:.1f}s</div>', unsafe_allow_html=True)
        if show_sources:
            render_sources(msg.get("sources") or [])


def scroll_to_bottom() -> None:
    components.html(
        """<script>
        const d = window.parent.document;
        const m = d.querySelector('[data-testid="stMain"]') || d.querySelector('section.main');
        if (m) m.scrollTo({top: m.scrollHeight, behavior: 'smooth'});
        </script>""",
        height=0,
    )


# ----------------------------------------------------------------------------
# Answer formatting: turn "Warning: ..." / "Note: ..." lines into callouts
# ----------------------------------------------------------------------------
_CALLOUT = re.compile(
    r"^\s*(?:[-*]\s+)?(?:⚠️|❗|💡)?\s*(?:\*\*|__)?(warning|caution|danger|important|note|tip)"
    r"(?::(?:\*\*|__)?|(?:\*\*|__):)\s*(.*)$",
    re.IGNORECASE,
)
_WARN_WORDS = {"warning", "caution", "danger", "important"}


def format_answer(text: str) -> str:
    """Convert warning/note lines to styled blockquotes. Safe on partial (streaming) text."""
    out: list[str] = []
    in_fence = False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue
        m = None if in_fence else _CALLOUT.match(line)
        if m:
            word = m.group(1).lower()
            if word in _WARN_WORDS:
                label = f":orange[⚠️ **{word.capitalize()}:**]"
            else:
                label = f":blue[💡 **{word.capitalize()}:**]"
            out.extend(["", f"> {label} {m.group(2)}", ""])
        else:
            out.append(line)
    return "\n".join(out)