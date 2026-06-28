# 🌾 TN AgriScheme AI – Farmer Support RAG Chatbot

An AI-powered **Retrieval-Augmented Generation (RAG)** application that helps farmers discover and understand **Tamil Nadu Government Agricultural Schemes** using verified government documents. The application provides **source-cited, context-aware answers** powered by **LangChain**, **OpenAI GPT**, and a **Vector Database**.

---

# 🚀 Features

* 📄 Upload and index Government PDF documents
* 🤖 AI-powered Question & Answer chatbot
* 🔍 Semantic Search using Vector Embeddings
* 📚 Retrieval-Augmented Generation (RAG)
* 📖 Source-Cited Answers
* 🛡️ Hallucination Reduction using Grounded Context
* 💬 Natural Language Queries
* 🌱 Agriculture Scheme Knowledge Base
* ⚡ Fast Semantic Retrieval
* 🎨 Modern Streamlit UI

---

# 🏗️ Architecture

The application follows a **Two-Pipeline RAG Architecture**.

### Offline Indexing Pipeline

```
Government PDF Documents
        │
        ▼
Document Loader
        │
        ▼
Text Cleaning & Normalization
        │
        ▼
Metadata Extraction
        │
        ▼
Semantic Chunking
        │
        ▼
Embedding Generation
        │
        ▼
Vector Database
```

---

### Online Retrieval Pipeline

```
User Question
      │
      ▼
Query Embedding
      │
      ▼
Vector Similarity Search
      │
      ▼
Relevant Chunks
      │
      ▼
Prompt Assembly
      │
      ▼
OpenAI GPT
      │
      ▼
Context-Aware Answer
      │
      ▼
Source Citations
```

---

# 🛠️ Technology Stack

| Technology             | Purpose                 |
| ---------------------- | ----------------------- |
| Python                 | Backend                 |
| Streamlit              | User Interface          |
| LangChain              | RAG Framework           |
| OpenAI GPT             | Large Language Model    |
| OpenAI Embeddings      | Text Embeddings         |
| ChromaDB / Qdrant      | Vector Database         |
| PyPDF                  | PDF Parsing             |
| FAISS *(Optional)*     | Vector Search           |
| LangSmith *(Optional)* | Observability & Tracing |

---

# 📁 Project Structure

```
TN-AgriScheme-AI/

│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env
│
├── data/
│     ├── Government_PDFs/
│
├── db/
│     ├── Vector Database
│
├── assets/
│     ├── Logo
│     ├── Images
│
├── uploads/
│
└── venv/
```

---

# ⚙️ Installation

## 1. Clone Repository

```bash
git clone https://github.com/yourusername/TN-AgriScheme-AI.git
```

---

## 2. Navigate to Project

```bash
cd TN-AgriScheme-AI
```

---

## 3. Create Virtual Environment

```bash
python3 -m venv venv
```

---

## 4. Activate Virtual Environment

### macOS / Linux

```bash
source venv/bin/activate
```

### Windows

```cmd
venv\Scripts\activate
```

---

## 5. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 Environment Variables

Create a `.env` file.

```text
OPENAI_API_KEY=your_openai_api_key
```

---

# ▶️ Run the Application

```bash
streamlit run app.py
```

The application will be available at:

```
http://localhost:8501
```

---

# 💡 Example Questions

* What subsidy is available for maize cultivation?
* Can I get financial assistance for a pesticide drone?
* Is there a subsidy for drip irrigation?
* What documents are required for PM-KISAN?
* How do I apply for an agricultural machinery subsidy?
* What support is available for organic farming?
* Which department provides seed subsidies?

---

# 🔍 How the RAG Pipeline Works

1. Government PDF documents are loaded.
2. Documents are cleaned and normalized.
3. Text is split into semantic chunks.
4. Embeddings are generated.
5. Chunks are stored in the Vector Database.
6. User submits a question.
7. The question is converted into an embedding.
8. Similar chunks are retrieved.
9. Retrieved context is sent to the OpenAI model.
10. The AI generates a grounded answer with citations.

---

# 🎯 Key Features

* Semantic Search
* Source-Based Answers
* Metadata Filtering
* AI-Powered Retrieval
* Government Knowledge Base
* Context-Aware Responses
* Modern Responsive UI
* Easy Document Expansion

---

# 🌱 Future Enhancements

* 🎤 Voice Input (Tamil & English)
* 🌐 Multi-language Support
* 📷 Plant Disease Detection
* ☁️ Weather Integration
* 📍 Location-Based Scheme Recommendations
* 📄 Government Circular Updates
* 📊 Farmer Dashboard
* ❤️ Feedback Collection
* 🔔 Scheme Notifications
* 📱 Mobile Responsive UI

---

# 📸 Screenshots

Add application screenshots here.

```
assets/screenshots/
```

---

# 📈 Future Architecture

* Hybrid Search (Vector + BM25)
* Query Rewriting
* Re-ranking
* Metadata Filtering
* Conversation Memory
* LangSmith Monitoring
* Qdrant Vector Database
* GPT-5 Integration

---

# 🤝 Contributing

Contributions are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Push your branch.
5. Open a Pull Request.

---

# 📄 License

This project is licensed under the **MIT License**.

---

# 👨‍💻 Author

**Vimal**



## ⭐ If you found this project helpful, please consider giving it a Star on GitHub!
