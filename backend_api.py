from collections import defaultdict
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- Config ---
COLLECTION_NAME = "bright-side-supplements"
TOP_K = 30
TOP_PRODUCTS = 5
QDRANT_URL = "https://911142df-1d84-498b-95f7-e2963c1f4078.us-east4-0.gcp.cloud.qdrant.io"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.8Vqf0hlLpHQuEKqV4m018NqCi4yq7tKSa8llXhHkl7o"

# --- Clients ---
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

embedding_model = SentenceTransformer("intfloat/e5-small-v2")


# --- Helpers ---
def clean_text(text: str) -> str:
    return text.strip().replace("\n", " ").replace("  ", " ")


def fetch_full_document_chunks(filename: str) -> List[str]:
    """Fetch all chunks that belong to the same document (by filename)"""
    filter_by_filename = Filter(
        must=[
            FieldCondition(key="filename", match=MatchValue(value=filename))
        ]
    )
    results = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=filter_by_filename,
        with_payload=True,
        limit=1000  # adjust if your documents are very large
    )
    chunks = []
    for point in results[0]:
        payload = point.payload or {}
        text = payload.get("text", "")
        if text:
            chunks.append(clean_text(text))
    return chunks


# --- Main Query Function ---
def query_top_products(query: str, top_n: int = TOP_PRODUCTS) -> List[Dict[str, Any]]:
    query_vector = embedding_model.encode(f"query: {query}", normalize_embeddings=True).tolist()

    search_results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=TOP_K,
        with_payload=True
    )

    product_hits = {}

    for result in search_results:
        payload = result.payload or {}
        text = payload.get("text", "")
        filename = payload.get("filename", "Unknown")
        product = payload.get("product", filename)
        source_type = payload.get("source_type", "unknown")
        score = result.score

        if product not in product_hits or score > product_hits[product]["match_score"]:
            product_hits[product] = {
                "product": product,
                "filename": filename,
                "source_type": source_type,
                "match_score": score,
                "matched_chunk": clean_text(text),
                "full_document": ""  # will populate later
            }

    # Now fetch full chunks for each top product
    for product in product_hits:
        filename = product_hits[product]["filename"]
        full_chunks = fetch_full_document_chunks(filename)
        full_text = "\n\n".join(full_chunks)
        product_hits[product]["full_document"] = full_text

    sorted_hits = sorted(product_hits.values(), key=lambda x: x["match_score"], reverse=True)
    return sorted_hits[:top_n]


app = FastAPI()

# Allow frontend to connect (for now we allow all origins for simplicity)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryInput(BaseModel):
    question: str

@app.post("/recommend")
def recommend_products(data: QueryInput):
    results = query_top_products(data.question)
    return results
