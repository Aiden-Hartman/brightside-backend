from collections import defaultdict
from typing import List, Dict, Any
import os
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from dotenv import load_dotenv

load_dotenv()

COLLECTION_NAME = "bright-side-supplements"
TOP_K = 30
TOP_PRODUCTS = 5

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

#print(f"Qdrant_url: {QDRANT_URL}")
#print(f"Qdrant_api_key: {QDRANT_API_KEY}")

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
embedding_model = SentenceTransformer("intfloat/e5-small-v2")

def clean_text(text: str) -> str:
    return text.strip().replace("\n", " ").replace("  ", " ")

def fetch_full_document_chunks(filename: str) -> List[str]:
    filter_by_filename = Filter(
        must=[FieldCondition(key="filename", match=MatchValue(value=filename))]
    )
    results = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=filter_by_filename,
        with_payload=True,
        limit=1000
    )
    return [clean_text(p.payload.get("text", "")) for p in results[0] if p.payload]

def query_top_products(query: str, top_n: int = TOP_PRODUCTS) -> List[Dict[str, Any]]:
    query_vector = embedding_model.encode(f"query: {query}", normalize_embeddings=True).tolist()

    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=TOP_K,
        with_payload=True
    )

    product_hits = {}

    for result in results:
        payload = result.payload or {}
        filename = payload.get("filename", "Unknown")
        product = payload.get("product", filename)
        score = result.score

        if product not in product_hits or score > product_hits[product]["match_score"]:
            product_hits[product] = {
                "product": product,
                "filename": filename,
                "source_type": payload.get("source_type", "unknown"),
                "match_score": score,
                "matched_chunk": clean_text(payload.get("text", "")),
                "full_document": ""
            }

    for hit in product_hits.values():
        chunks = fetch_full_document_chunks(hit["filename"])
        hit["full_document"] = "\n\n".join(chunks)

    return sorted(product_hits.values(), key=lambda x: x["match_score"], reverse=True)[:top_n]
