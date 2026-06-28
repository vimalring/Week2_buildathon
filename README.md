# 🌾 Tamil Nadu Agricultural Schemes AI Assistant (Two-Pipeline RAG)

A production-grade, zero-hallucination Retrieval-Augmented Generation (RAG) pipeline designed to help local farmers easily query and understand official government agricultural schemes. The system features a custom high-end forest green user interface built with Streamlit, real-time token streaming, and full telemetry observability via LangSmith.

---

## 🏛️ System Architecture

The application is built using a strict decoupled **Two-Pipeline RAG Architecture** to ensure low-latency performance and high grounding accuracy.

### 1. Offline Indexing Pipeline (Ingestion)
* **Intake:** Automated scraping framework using Playwright (to handle dynamic elements) and BeautifulSoup4 targeting the official TN Scheme List portal.
* **Normalization:** Custom regular expression filters to strip out administrative boilerplate, navigation bars, and formatting noise.
* **Smart Chunking:** Text is processed via a `RecursiveCharacterTextSplitter` configured to natural sentence boundaries (Chunk Size: 550, Overlap: 110) to preserve complete eligibility clauses.
* **Vector Vector Store:** Local CPU embedding execution using HuggingFace's `all-MiniLM-L6-v2` model, persisting structured payload data into a localized **ChromaDB** instance.

### 2. Online Retrieval & Generation Pipeline (Runtime)
* **Query Optimization:** Conversational, loose inputs are processed through `gpt-4o-mini` to rewrite them into optimized standalone administrative search queries.
* **Semantic Lookup:** Fetches the top 3 most relevant context blocks from the local ChromaDB database.
* **Grounded Streaming Generation:** Passes chunks into a hyper-strict system prompt matrix forcing deterministic facts with direct source citations, streaming tokens live to the user interface via Server-Sent Events (SSE).
* **Observability:** Completely hooked into LangSmith for tracing search modifications, database latency metrics, and prompt safety validation.

---

## ⚡ Tech Stack

* **Frontend UI:** Streamlit (Custom Premium CSS Theme Injection)
* **Orchestration Layer:** LangChain Ecosystem (`langchain-core`, `langchain-huggingface`)
* **Vector Database:** ChromaDB (Local Persistent Mode)
* **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (Local CPU Execution)
* **LLM Core Engine:** OpenAI `gpt-4o-mini` (Cloud Execution with Stream/SSE)
* **Data Extraction:** Playwright + BeautifulSoup4
* **Observability:** LangSmith Telemetry

---

## 🚀 Getting Started

### 1. Prerequisites
Make sure you have Python 3.11+ installed (successfully verified up to Python 3.14 on macOS).

### 2. Clone and Setup Environment
```bash
# Clone the repository
git clone [https://github.com/your-username/farmers_support.git](https://github.com/your-username/farmers_support.git)
cd farmers_support

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install all foundational dependencies
pip install playwright beautifulsoup4 requests chromadb sentence-transformers langchain-huggingface openai python-dotenv streamlit torchvision --no-deps
playwright install chromium