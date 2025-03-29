from fastapi import FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from app.models import QueryInput
from app.recommender import query_top_products
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI()

# Load and clean API key
API_KEY = (os.getenv("API_KEY") or "").strip()
if not API_KEY:
    print("⚠️ WARNING: API_KEY not loaded from environment!")
else:
    #print(f"✅ Loaded API_KEY: {repr(API_KEY)}")

# Setup API key header extraction
API_KEY_NAME = "x-api-key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in prod
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security dependency to check the API key
async def get_api_key(request: Request, api_key: str = Security(api_key_header)):
    received_key = (api_key or "").strip()
    #print(f"🛂 Received API key: {repr(received_key)}")
    #print(f"📬 Request headers: {dict(request.headers)}")

    if received_key != API_KEY:
        print("❌ API key mismatch!")
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    print("✅ API key validated successfully.")
    return received_key

# Recommend endpoint with key protection
@app.post("/recommend")
def recommend_products(
    data: QueryInput,
    api_key: str = Security(get_api_key)
):
    print(f"📩 Received question: {data.question}")
    return query_top_products(data.question)
