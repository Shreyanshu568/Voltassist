import os
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(name="voltassist_docs")

data_folder = "data"
doc_id = 0

for filename in os.listdir(data_folder):
    filepath = os.path.join(data_folder, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    chunks = content.split("\n\n")

    for chunk in chunks:
        if chunk.strip():  
            collection.add(
                documents=[chunk],
                ids=[f"doc_{doc_id}"]
            )
            doc_id += 1

print(f"Done! {doc_id} chunks added to ChromaDB.")