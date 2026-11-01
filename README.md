# Git & Linux Assistant

A retrieval-augmented generation (RAG) chatbot that answers Git and Linux questions from a
local knowledge base. It has a modern dark chat interface built with Streamlit, streams
answers as they are written, and includes a Troubleshoot mode for pasted terminal errors.

> The assistant only suggests commands. It never runs anything on your computer.

## Features

- **Grounded answers:** responses come from your own Linux and Git knowledge-base documents,
  not from the model's memory alone.
- **Chat interface:** welcome screen with suggested questions, streaming replies, loading
  indicator, syntax-highlighted code blocks with a copy button, and styled warning/note callouts.
- **Conversations:** a sidebar with titled chats, search, and delete. Follow-up questions
  are understood in context (the last 6 messages are used).
- **Troubleshoot mode:** paste a command and its error output and get a structured answer:
  Diagnosis, Likely cause, Fix, Verify.
- **Responsive layout:** works on desktop, tablet and mobile widths, with a collapsible sidebar.

## How it works

1. **Knowledge base:** `.txt` files in `docs/` are written as entries that start with a `###`
   heading, grouped under `##` categories.
2. **Chunking:** `ingestion_pipeline.py` creates one chunk per entry. Long entries are split
   (max 1200 characters) and each piece repeats its category and heading so it stays
   self-describing.
3. **Embeddings:** each chunk is embedded with `sentence-transformers/all-MiniLM-L6-v2`
   (runs locally on CPU) and stored in a local Chroma database (`db/chroma_db`, cosine similarity).
4. **Retrieval:** your question is rewritten into a standalone search query if it is a
   follow-up, then the top 6 chunks are retrieved.
5. **Generation:** the chunks, recent chat turns and your question go to an LLM on Groq
   (default model `openai/gpt-oss-120b`), which streams back the answer.
6. **Interface:** `app.py` and `ui.py` render everything with Streamlit.

```
Question -> rewrite (if follow-up) -> embed -> Chroma top-6 -> LLM (Groq) -> streamed answer
```

## Project structure

```
.
├── app.py                       # Streamlit app: state, sidebar, chat flow
├── ui.py                        # Theme CSS and reusable UI components
├── rag.py                       # RAG engine: rewrite, retrieve, stream answer
├── ingestion_pipeline.py        # Load docs, chunk, embed, store in Chroma
├── history_aware_generation.py  # Terminal chat version (same engine as the app)
├── retrieval_pipeline.py        # Standalone retrieval test script
├── answer_generation_1.py       # Earlier answer-generation experiment
├── check_index.py               # Diagnostic: chunk count and ranking checks
├── docs/                        # Knowledge-base .txt files
├── .streamlit/config.toml       # Dark theme settings
├── requirements.txt
└── .env.example
```

`db/` is created automatically and is not committed.

## Setup

**Requirements:** Python 3.10 or newer and a free [Groq API key](https://console.groq.com).

1. Create and activate a virtual environment:

   ```powershell
   # Windows PowerShell
   python -m venv venv
   venv\Scripts\Activate.ps1
   ```

   ```bash
   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and add your key:

   ```
   GROQ_API_KEY=your_key_here
   # optional: GROQ_MODEL=openai/gpt-oss-120b
   ```

   Keep `.env` private. It is ignored by Git.

4. Build the search index (first run downloads the embedding model):

   ```bash
   python ingestion_pipeline.py
   ```

5. Start the app:

   ```bash
   streamlit run app.py
   ```

If the index does not exist yet, `rag.py` builds it automatically on first start.

## Usage

- Ask a question in the chat box, or click a suggestion on the welcome screen.
- Press **Enter** to send and **Shift+Enter** for a new line.
- Switch on **Troubleshoot mode** in the sidebar, then paste a command with its error output.
- Use **New chat** to start over and the sidebar search to find earlier chats.

Example questions:

- What is Git?
- How do I undo my last commit?
- How do I find which process is using port 8080?
- Explain Linux file permissions.

## Updating the knowledge base

1. Add or edit `.txt` files in `docs/`. Start each entry with `### Title` and group entries
   under `## CATEGORY ...` headings.
2. Rebuild the index so the changes are picked up:

   ```bash
   python ingestion_pipeline.py --rebuild
   ```

   Without `--rebuild`, an existing index is reused and new documents are not indexed.

If a question gets "I don't have enough information...", the usual cause is a missing entry.
Add a short entry written the way people ask the question, then rebuild.

## Terminal version

```bash
python history_aware_generation.py
```

Prints the retrieved chunks for each question, which is useful for debugging retrieval.

## Configuration

| Setting | Where | Default |
|---|---|---|
| LLM provider key | `GROQ_API_KEY` in `.env` | none (required) |
| LLM model | `GROQ_MODEL` in `.env` | `openai/gpt-oss-120b` |
| Chunks retrieved | `DEFAULT_K` in `rag.py` | 6 |
| Max chunk size | `max_chars` in `ingestion_pipeline.py` | 1200 characters |
| Embedding model | `ingestion_pipeline.py` and `rag.py` | `all-MiniLM-L6-v2` |

## Limitations

- Answers are only as good as the documents. Topics missing from `docs/` get a refusal.
- Embedding search is weak on bare symbols and flags (for example, just "-m"). Entries that
  explain such flags in plain words help.
- Chats are kept in the browser session only and are lost on page refresh.
- Matching document excerpts are sent to Groq to generate each answer.
- The knowledge base is a learning resource. Check destructive commands (`rm -rf`,
  `git reset --hard`, `dd`) before running them.

## Tech stack

Python, Streamlit, LangChain, Chroma, Hugging Face sentence-transformers, Groq.