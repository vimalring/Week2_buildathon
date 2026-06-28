import os
import re
import shutil
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Directory Layout
BASE_DATA_DIR = "tn_agri_data"
TEXT_DIR = os.path.join(BASE_DATA_DIR, "text")
CHROMA_PERSIST_DIR = "chroma_db"

def clean_government_text(text: str) -> str:
    """Strips raw system formatting lines and extra whitespace."""
    text = re.sub(r"Source Link Matrix: .*", "", text)
    text = re.sub(r"Official Scheme Name: .*", "", text)
    text = re.sub(r"-{10,}", "", text)
    text = re.sub(r"(Skip to main content|Tamil Nadu Government Portal|Department of Agriculture)", "", text, flags=re.IGNORECASE)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    return text.strip()

def process_and_vectorize_documents():
    print("[*] Initializing raw text document loaders...")
    if not os.path.exists(TEXT_DIR) or not os.listdir(TEXT_DIR):
        print(f"[!] Error: '{TEXT_DIR}' is empty. Run your scraper first.")
        return

    loader = DirectoryLoader(TEXT_DIR, glob="**/*.txt", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"})
    raw_documents = loader.load()
    print(f"[✓] Loaded {len(raw_documents)} raw text documents.")

    processed_chunks = []
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=550, chunk_overlap=110, separators=["\n\n", "\n", ".", " ", ""])

    print("[*] Resegmenting text blocks with localized metadata tracking...")
    for doc in raw_documents:
        filename = os.path.basename(doc.metadata.get("source", "unknown_scheme"))
        scheme_title = filename.replace(".txt", "").replace("_", " ")
        cleaned_content = clean_government_text(doc.page_content)
        
        if not cleaned_content:
            continue
            
        doc.page_content = cleaned_content
        doc_chunks = text_splitter.split_documents([doc])
        
        for index, chunk in enumerate(doc_chunks):
            chunk.metadata = {
                "source_file": filename,
                "scheme_name": scheme_title,
                "chunk_index": index,
                "data_type": "text_portal"
            }
            processed_chunks.append(chunk)

    print(f"[✓] Created {len(processed_chunks)} normalized text chunks.")

    # Clear old database files if they exist to prevent cross-contamination during testing
    if os.path.exists(CHROMA_PERSIST_DIR):
        print("[*] Clearing old vector database files...")
        shutil.rmtree(CHROMA_PERSIST_DIR)

    print("[*] Initializing local HuggingFace Embedding engine (`all-MiniLM-L6-v2`)...")
    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )

    print("[*] Generating embeddings and building local ChromaDB database. Please wait...")
    vector_db = Chroma.from_documents(
        documents=processed_chunks,
        embedding=embedding_model,
        persist_directory=CHROMA_PERSIST_DIR
    )
    
    print(f"[✓][✓] Success! Local vector store initialized at: '{CHROMA_PERSIST_DIR}'")
    return vector_db

if __name__ == "__main__":
    process_and_vectorize_documents()