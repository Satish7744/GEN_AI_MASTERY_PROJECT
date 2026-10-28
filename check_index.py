from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

emb = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)
db = Chroma(persist_directory="db/chroma_db", embedding_function=emb,
            collection_metadata={"hnsw:space": "cosine"})

print("Total chunks in DB:", db._collection.count())

# 1. Is the new entry in the database at all?
hits = db.get(where_document={"$contains": "What does -m mean in Git"})
print("New -m entry present:", len(hits["ids"]) > 0)

# 2. Does it rank in the top 6 for the question?
for q in ["What is -m in git?", "What does -m mean in git commit?"]:
    print(f"\nQuery: {q}")
    for doc, score in db.similarity_search_with_score(q, k=6):
        title = doc.metadata.get("title", doc.page_content[:50])
        print(f"  {score:.3f}  {title}")