import os
import re
import shutil
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

# Set to True to delete and rebuild the vector store on every run.
# Set to False after a successful ingestion so later runs reuse the store.
REBUILD = True


def load_documents(docs_path="docs"):
    print(f"Loading documents from {docs_path}...")
    if not os.path.exists(docs_path):
        raise FileNotFoundError(f"The directory {docs_path} does not exist. Please create it and add your files.")
    loader = DirectoryLoader(
        path=docs_path,
        glob="*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True
    )
    documents = loader.load()
    if len(documents) == 0:
        raise FileNotFoundError(f"No .txt files found in {docs_path}. Please add your documents.")

    for i, doc in enumerate(documents[:2]):
        print(f"\nDocument {i+1}:")
        print(f" Source: {doc.metadata['source']}")
        print(f" Content length: {len(doc.page_content)} characters")
        print(f" Content preview: {doc.page_content[:100]}...")
        print(f" Metadata: {doc.metadata}")

    return documents


def split_documents(documents, max_chars=1200):
    """One chunk per '### ' entry. Long entries are split into pieces of at most
    max_chars, and every piece repeats the category and heading so it stays
    self-describing (all-MiniLM-L6-v2 only embeds roughly the first 256 tokens)."""
    print("Splitting documents into entry-based chunks...")
    chunks = []
    for doc in documents:
        source = doc.metadata.get("source", "")
        category = ""
        for part in re.split(r"(?m)^(?=### )", doc.page_content):
            cats = re.findall(r"(?m)^## (.+)$", part)
            clean = re.sub(r"(?m)^## .+$", "", part)
            clean = re.sub(r"(?m)^---\s*$", "", clean).strip()

            if clean.startswith("###"):
                heading, _, body = clean.partition("\n")
                title = heading.lstrip("# ").strip()
                prefix = f"[{category}]\n{heading}\n"
                meta = {"source": source, "category": category, "title": title}

                buf = ""
                for line in body.split("\n"):
                    if buf and len(buf) + len(line) > max_chars:
                        chunks.append(Document(page_content=prefix + buf.strip(),
                                               metadata=dict(meta)))
                        buf = ""
                    buf += line + "\n"
                if buf.strip():
                    chunks.append(Document(page_content=prefix + buf.strip(),
                                           metadata=dict(meta)))

            # the category line sits at the end of the previous part
            if cats:
                category = cats[-1].strip()

    print(f"Created {len(chunks)} chunks")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n--- Chunk {i+1} ---")
        print(f"Source: {chunk.metadata['source']}")
        print(f"Length: {len(chunk.page_content)} characters")
        print(chunk.page_content[:300])
        print("-" * 50)

    return chunks


def create_vector_store(chunks, persist_directory="db/chroma_db"):
    """Create and persist ChromaDB vector store"""
    print("Creating embeddings and storing in ChromaDB...")

    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    print("--- Creating vector store ---")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=persist_directory,
        collection_metadata={"hnsw:space": "cosine"}
    )
    print("--- Finished creating vector store ---")

    print(f"Vector store created and saved to {persist_directory}")
    return vectorstore


def main():
    """Main ingestion pipeline"""
    print("=== RAG Document Ingestion Pipeline ===\n")

    docs_path = "docs"
    persistent_directory = "db/chroma_db"

    # Optionally wipe the old store so new documents are re-indexed
    if REBUILD and os.path.exists(persistent_directory):
        shutil.rmtree(persistent_directory)
        print("Old vector store deleted.")

    # Reuse the existing vector store if it is still there
    if os.path.exists(persistent_directory):
        print("✅ Vector store already exists. No need to re-process documents.")

        embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        vectorstore = Chroma(
            persist_directory=persistent_directory,
            embedding_function=embedding_model,
            collection_metadata={"hnsw:space": "cosine"}
        )
        print(f"Loaded existing vector store with {vectorstore._collection.count()} documents")
        return vectorstore

    print("Persistent directory does not exist. Initializing vector store...\n")

    # 1. Loading the files
    documents = load_documents(docs_path=docs_path)

    # 2. Chunking the files
    chunks = split_documents(documents)

    # 3. Embedding and storing in the vector DB
    vectorstore = create_vector_store(chunks, persistent_directory)

    print("\n✅ Ingestion complete! Your documents are now ready for RAG queries.")
    return vectorstore


if __name__ == "__main__":
    main()