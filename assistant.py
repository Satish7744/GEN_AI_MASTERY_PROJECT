from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _load_chunks(knowledge_dir: Path, chunk_size: int = 850, overlap: int = 120) -> list[dict[str, str]]:
    """Load Markdown notes and split them into overlapping character chunks."""
    chunks: list[dict[str, str]] = []
    for path in sorted(knowledge_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            content = text[start:end].strip()
            if content:
                chunks.append({"source": path.name, "text": content})
            if end == len(text):
                break
            start = end - overlap
    return chunks


def retrieve_context(question: str, knowledge_dir: Path, top_k: int = 3) -> list[dict[str, str]]:
    """Retrieve the most relevant note chunks with TF-IDF and cosine similarity."""
    chunks = _load_chunks(knowledge_dir)
    if not chunks:
        return []
    documents = [chunk["text"] for chunk in chunks]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform([*documents, question])
    scores = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
    ranked = scores.argsort()[::-1][:top_k]
    return [chunks[index] for index in ranked if scores[index] > 0]


def _make_prompt(question: str, matches: list[dict[str, str]]) -> str:
    context = "\n\n".join(
        f"Source: {item['source']}\n{item['text']}" for item in matches
    ) or "No relevant local notes were found."
    return f"""You are a careful Linux and Git learning assistant for a beginner.
Use the reference notes below as your primary source. If they do not contain enough
information, say so and give a cautious general explanation. Never invent flags or
claim a command is risk-free. Explain what each suggested command does. For commands
that can delete, overwrite, expose, or permanently change data, explain the risk and
offer a safer inspection or backup step first. Do not execute commands.

Reference notes:
{context}

Question: {question}

Answer in clear steps. Use code blocks for commands and mention relevant source filenames."""


def answer_question(question: str, matches: list[dict[str, str]], provider: str) -> str:
    prompt = _make_prompt(question, matches)
    if provider == "Groq":
        return _ask_groq(prompt)
    if provider == "Gemini":
        return _ask_gemini(prompt)
    raise ValueError("Choose Groq or Gemini in the sidebar.")


def _ask_groq(prompt: str) -> str:
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing. Add it to your local .env file (see .env.example).")
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    response: Any = Groq(api_key=api_key).chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content or "The model returned an empty response."


def _ask_gemini(prompt: str) -> str:
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it to your local .env file (see .env.example).")
    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    # Keep the client alive for the full request. Creating it inline can let
    # Python close its underlying HTTP client before generate_content completes.
    with genai.Client(api_key=api_key) as client:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )
    return response.text or "The model returned an empty response."
