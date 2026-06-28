import os
from dotenv import load_dotenv
from openai import OpenAI
from langsmith.wrappers import wrap_openai
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Load environment configurations
load_dotenv()

# Initialize OpenAI Cloud Client — wrapped so LangSmith traces all GPT calls
openai_client = wrap_openai(OpenAI())

# Initialize Local Embedding Engine
print("[*] Loading local HuggingFace embedding engine for lookups...")
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'}
)

# Reference our local vector database storage folder
CHROMA_PERSIST_DIR = "chroma_db"
vector_db = Chroma(
    persist_directory=CHROMA_PERSIST_DIR,
    embedding_function=embedding_model
)

def rewrite_farmer_query(messy_query: str) -> str:
    """Transforms raw conversational input into an optimized search string."""
    system_instruction = (
        "You are an expert Agricultural Assistant specializing in Tamil Nadu government schemes.\n"
        "Your task is to take a raw, conversational, or structurally messy user query submitted by a local farmer "
        "and rewrite it into a clear, concise, objective keyword search phrase optimized for matching administrative data.\n"
        "Return ONLY the optimized search string. Do not include introductory text."
    )
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Rewrite this query: {messy_query}"}
            ],
            temperature=0.0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return messy_query


def retrieve_relevant_context(optimized_query: str, top_k: int = 3):
    """
    Uses standard similarity search to bypass aggressive relevance score 
    filtering, ensuring candidate text blocks reach the LLM context window.
    """
    try:
        # Standard similarity lookup gives us the raw documents directly
        return vector_db.similarity_search(optimized_query, k=top_k)
    except Exception as e:
        print(f"[!] Failure retrieving vectors: {str(e)}")
        return []


def _build_answer_messages(farmer_query: str, retrieved_chunks) -> list:
    """Assembles the system + user messages for the answer generation call."""
    context_str = ""
    for rank, doc in enumerate(retrieved_chunks, 1):
        scheme_name = doc.metadata.get("scheme_name", "Unknown Scheme")
        source_file = doc.metadata.get("source_file", "Unknown Source")
        context_str += f"--- CONTEXT BLOCK #{rank} ---\n"
        context_str += f"Source Scheme Document: {scheme_name} (File: {source_file})\n"
        context_str += f"Text Content: {doc.page_content}\n\n"

    system_prompt = (
        "You are the official Tamil Nadu Government Agricultural Scheme Digital Assistant.\n"
        "Your mission is to provide accurate, factual, and helpful guidance to local farmers based ONLY on the verified context blocks provided.\n\n"
        "CRITICAL GUARDRAILS:\n"
        "1. If the provided context does not contain the information to answer the question, state: "
        "'I am sorry, but I cannot find verified government records matching this request in our current database.'\n"
        "2. If the context discusses the topic (e.g., a scheme exists) but lacks specific field details (like a specific address layout), "
        "explain what the scheme provides and mention the department name found in the text.\n"
        "3. Every fact or department name you list MUST be accompanied by an inline citation referencing its source document (e.g., [Source: Scheme Name]).\n"
        "4. Structure your response cleanly using bullet points."
    )
    user_prompt = (
        f"VERIFIED BACKGROUND CONTEXT:\n{context_str}\n"
        f"FARMER USER QUESTION: {farmer_query}\n\n"
        f"Provide your factually grounded response with explicit citations:"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt},
    ]


def stream_grounded_answer(farmer_query: str, retrieved_chunks):
    """Yields text delta strings from GPT-4o-mini as they arrive (streaming)."""
    messages = _build_answer_messages(farmer_query, retrieved_chunks)
    try:
        stream = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.0,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except Exception as e:
        yield f"[!] Generation error occurred: {str(e)}"


def generate_grounded_answer(farmer_query: str, retrieved_chunks) -> str:
    """Non-streaming version — collects the full stream and returns a single string."""
    return "".join(stream_grounded_answer(farmer_query, retrieved_chunks))


def run_complete_rag_pipeline(user_input: str):
    print("\n" + "="*70)
    print(f"[INPUT] Farmer: '{user_input}'")
    
    optimized_query = rewrite_farmer_query(user_input)
    print(f"[REWRITE] Optimized Search: '{optimized_query}'")
    
    chunks = retrieve_relevant_context(optimized_query, top_k=3)
    print(f"[RETRIEVE] Pulled {len(chunks)} context blocks from local store.")
    
    final_response = generate_grounded_answer(user_input, chunks)
    
    print("\n" + "-"*30 + " FINAL GENERATED RESPONSE " + "-"*30)
    print(final_response)
    print("="*70)


if __name__ == "__main__":
    run_complete_rag_pipeline("where to go for polythene mulch demo?")
    run_complete_rag_pipeline("Can I get a subsidy for purchasing a drone to spray pesticide on coconuts?")