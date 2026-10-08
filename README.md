# Linux & Git Assistant

A beginner-friendly Gen AI course project that answers Linux and Git questions with
**RAG (retrieval-augmented generation)**. It searches local Markdown notes, sends the
most relevant excerpts to an LLM, and shows which notes informed the answer.

## How the pieces fit together

1. **Knowledge base:** Markdown files in `knowledge/` contain Linux and Git guidance.
2. **Chunking:** `assistant.py` splits the notes into overlapping sections.
3. **Retrieval:** TF-IDF turns the sections and question into vectors; cosine similarity
   selects the three closest sections.
4. **Generation:** The selected sections and question are sent to Groq or Gemini.
5. **User interface:** Streamlit displays the conversation and source filenames.

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

4. Install dependencies:

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

- TF-IDF is a simple lexical retrieval method. It does not understand meaning as well
  as embedding-based vector search.
- The bundled notes are a small teaching knowledge base, not a substitute for the
  official documentation or careful review of commands.
- A natural next course milestone is to replace TF-IDF with embeddings and a vector
  database such as Chroma, then compare retrieval quality.

## Provider documentation

- [Groq text generation](https://console.groq.com/docs/text-chat)
- [Gemini API](https://ai.google.dev/gemini-api/docs/generate-content)
- [Gemini model names](https://ai.google.dev/gemini-api/docs/models)
- [Groq supported models](https://console.groq.com/docs/models)
