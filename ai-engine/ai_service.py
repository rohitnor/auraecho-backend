import os
import json
from groq import Groq
from pinecone import Pinecone
from database import get_db_connection # Only import the connection tool
from dotenv import load_dotenv
from langsmith import traceable

load_dotenv()

# Initialize cloud clients
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
pinecone_index = pc.Index("auraecho-index")
def transcribe_audio_with_groq(file_path: str) -> str:
    """Sends a local audio file to Groq Whisper for blazing-fast transcription."""
    with open(file_path, "rb") as file:
        transcription = groq_client.audio.transcriptions.create(
            file=(file_path, file.read()),
            model="whisper-large-v3",
            response_format="json"
        )
    return transcription.text

@traceable(name="Groq Insights Extraction")
def analyze_text_with_llm(text: str) -> dict:
    system_prompt = """
    # Context
    You are the core analytical extraction engine for Project AuraEcho. You process raw voice-note transcriptions.
    # Objective
    Distill the raw transcription into a clean summary and isolate exactly three overarching key themes.
    # Response Format
    Output strictly valid JSON matching this schema:
    {
      "summary": "string",
      "key_themes": ["theme1", "theme2", "theme3"]
    }
    """
    
    # 1. Generate the LLM Analysis
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        response_format={"type": "json_object"},
        temperature=0.2
    )
    
    analysis_result = json.loads(response.choices[0].message.content)
    
    # 2. Save structured results to PostgreSQL (Table is now guaranteed to exist!)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO notes (raw_text, summary, key_themes) VALUES (%s, %s, %s) RETURNING id;",
        (text, analysis_result["summary"], analysis_result["key_themes"])
    )
    inserted_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    # 3. Generate Vector Embedding using Pinecone Inference
    embedding_response = pc.inference.embed(
        model="multilingual-e5-large",
        inputs=[analysis_result["summary"]],
        parameters={"input_type": "passage"}
    )
    vector = embedding_response[0].values

    # 4. Store Vector inside Pinecone Index mapped to the Postgres ID
    pinecone_index.upsert(
        vectors=[
            {
                "id": str(inserted_id), 
                "values": vector, 
                "metadata": {"summary": analysis_result["summary"]}
            }
        ]
    )

    return analysis_result

def search_similar_notes(query: str, top_k: int = 3) -> list:
    # 1. Convert the user's search query into a mathematical vector
    query_embedding = pc.inference.embed(
        model="multilingual-e5-large",
        inputs=[query],
        parameters={"input_type": "query"} # Note: 'query' instead of 'passage'
    )
    vector = query_embedding[0].values

    # 2. Search Pinecone for the closest matching vectors
    search_results = pinecone_index.query(
        vector=vector,
        top_k=top_k,
        include_metadata=True
    )

    # 3. Format the results
    formatted_results = []
    for match in search_results['matches']:
        formatted_results.append({
            "id": int(match['id']),
            "summary": match['metadata']['summary'],
            "similarity_score": round(match['score'], 2)
        })
        
    return formatted_results