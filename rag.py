# rag.py
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

# Load environment variables (GROQ_API_KEY from .env)
load_dotenv()

# Connect to your document database
persistent_directory = "db/chroma_db"
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)
db = Chroma(persist_directory=persistent_directory, embedding_function=embeddings)

# Set up AI model
model = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)


def rewrite_question(user_question, chat_history):
    """Make the question standalone using the conversation history."""
    if not chat_history:
        return user_question

    messages = [
        SystemMessage(content="Given the chat history, rewrite the new question to be standalone and searchable. Just return the rewritten question."),
    ] + chat_history + [
        HumanMessage(content=f"New question: {user_question}")
    ]
    return model.invoke(messages).content.strip()


def retrieve(search_question, k=3):
    """Find the k most relevant document chunks."""
    retriever = db.as_retriever(search_kwargs={"k": k})
    return retriever.invoke(search_question)


def stream_answer(user_question, docs, chat_history):
    """Ask the LLM using the retrieved docs, and yield the answer piece by piece."""
    formatted_docs = "\n".join([f"- {doc.page_content}" for doc in docs])

    combined_input = f"""Based on the following documents, please answer this question: {user_question}

    Documents:
    {formatted_docs}

    Please provide a clear, helpful answer using only the information from these documents. If you can't find the answer in the documents, say "I don't have enough information to answer that question based on the provided documents."
    """

    messages = [
        SystemMessage(content="You are a helpful assistant that answers questions based on provided documents and conversation history."),
    ] + chat_history + [
        HumanMessage(content=combined_input)
    ]

    for chunk in model.stream(messages):
        if chunk.content:
            yield chunk.content