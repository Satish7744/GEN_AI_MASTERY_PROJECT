import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

PERSIST_DIR = "db/chroma_db"
DEFAULT_K = 6
MODEL_NAME = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)

# Build the index automatically on first run
if not os.path.exists(PERSIST_DIR):
    from ingestion_pipeline import main as build_index
    build_index()

db = Chroma(
    persist_directory=PERSIST_DIR,
    embedding_function=embeddings,
    collection_metadata={"hnsw:space": "cosine"},
)

model = ChatGroq(model=MODEL_NAME, temperature=0)

NO_ANSWER = "I don't have enough information to answer that question based on the provided documents."


def rewrite_question(user_question, chat_history):
    """Make a follow-up question standalone, keeping commands and flags intact."""
    if not chat_history:
        return user_question
    messages = [
        SystemMessage(content=(
            "Given the chat history, rewrite the new question to be standalone and searchable. "
            "Keep exact command names, flags (like -m), and error messages from the question "
            "unchanged. Return only the rewritten question."
        )),
    ] + chat_history + [HumanMessage(content=f"New question: {user_question}")]
    return model.invoke(messages).content.strip()


def retrieve(search_question, k=DEFAULT_K):
    """Return the k most relevant chunks."""
    return db.as_retriever(search_kwargs={"k": k}).invoke(search_question)


def stream_answer(user_question, docs, chat_history):
    """Yield the answer piece by piece, grounded in the retrieved docs."""
    context = "\n\n".join(f"[{i}] {doc.page_content}" for i, doc in enumerate(docs, 1))

    prompt = f"""Answer the question using the documents below. You may combine information
from several documents (for example, to list commands). Put commands in code blocks and
warn about destructive ones. If the documents do not contain the answer, reply exactly:
"{NO_ANSWER}"

Question: {user_question}

Documents:
{context}
"""
    messages = [
        SystemMessage(content="You are a Git and Linux command assistant. Answer only from the provided documents. Only suggest commands; never claim to run them."),
    ] + chat_history + [HumanMessage(content=prompt)]

    for chunk in model.stream(messages):
        if chunk.content:
            yield chunk.content