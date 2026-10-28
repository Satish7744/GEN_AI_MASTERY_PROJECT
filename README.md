# Linux & Git Assistant

A beginner-friendly Gen AI course project that answers Linux and Git questions with
**RAG (retrieval-augmented generation)**. It searches local Markdown notes, sends the
most relevant excerpts to an LLM, and shows which notes informed the answer.

## How the pieces fit together

1. **Knowledge base:** Markdown files in `knowledge/` contain Linux and Git guidance.
   Add your own `.txt`, `.md`, or text-based `.pdf` notes with the sidebar uploader;
   uploaded notes are stored locally under `knowledge/uploads/`.
2. **Chunking:** `assistant.py` splits the notes into overlapping sections.
3. **Embeddings:** Chroma's local default embedding model turns each section and the
   question into vectors. It downloads its model files the first time the app indexes
   the notes.
4. **Retrieval:** Chroma stores those vectors locally and selects the three closest
   sections by cosine similarity.
5. **Generation:** The selected sections, recent chat turns, and question are sent to
   Groq or Gemini.
6. **Citations:** PDF results include the source filename and page number.
7. **Troubleshooting:** Paste a Linux or Git error, choose the OS/shell, and get a
   guided diagnosis that starts with inspection steps and explains any suggested fix.
8. **User interface:** Streamlit displays the conversation and sources.

Use the **Search in** selector in the sidebar to search all notes or limit retrieval to
one document. For a question about a project PDF, select that PDF so unrelated Linux
and Git notes cannot be included in the retrieved context.

Choose **Troubleshoot an error** in the sidebar and paste the terminal output. The
assistant infers the command and shell where possible, then leads with a likely fix and
copy-ready command. Remove API keys, passwords, and private data before submitting.
The assistant suggests commands for review; it never runs them on your computer.

This keeps the RAG steps visible for learning rather than hiding them behind a framework.
The app only suggests commands; it never runs them.

## Run locally

1. Install Python 3.10 or newer.
2. Open a terminal in this folder and create a virtual environment:

   ```bash
   python -m venv .venv
   ```

3. Activate it:

   ```bash
   # Linux/macOS
   source .venv/bin/activate

   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   ```

4. Install dependencies (Chroma's first installation adds a few packages):

   ```bash
   python -m pip install -r requirements.txt
   ```

5. Copy `.env.example` to `.env`. Add a key for **one** provider:

   ```dotenv
   GROQ_API_KEY=your_groq_key_here
   ```

   Or use `GEMINI_API_KEY` instead. Keep `.env` private; it is ignored by Git. Model
   names can be changed with `GROQ_MODEL` or `GEMINI_MODEL` if your provider account
   does not have access to the defaults.

6. Start the app:

   ```bash
   streamlit run app.py
   ```

## Example questions

- What does `git restore --staged` do?
- How can I see hidden files in Linux?
- What should I inspect before using `git reset --hard`?

## Limitations and next steps

- The local embedding model improves meaning-based search, but can still retrieve
  imperfect matches. Review the Sources shown with each answer.
- Uploaded notes and the Chroma index stay on your computer. Matching text excerpts
  are sent to the selected Groq or Gemini provider when the app answers a question.
- Chroma stores its local index in `chroma_db/`; this folder is ignored by Git and can
  be rebuilt from the Markdown files in `knowledge/`.
- The bundled notes are a small teaching knowledge base, not a substitute for the
  official documentation or careful review of commands.
- The uploader accepts UTF-8 text, Markdown, and text-based PDFs up to 5 MB each.
  Scanned PDFs need OCR, which this version does not include.
- Chat context includes only the six most recent conversation turns and lasts for the
  current browser session.

## Provider documentation

- [Groq text generation](https://console.groq.com/docs/text-chat)
- [Gemini API](https://ai.google.dev/gemini-api/docs/generate-content)
- [Gemini model names](https://ai.google.dev/gemini-api/docs/models)
- [Groq supported models](https://console.groq.com/docs/models)
