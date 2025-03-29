from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models import QueryInput
from app.recommender import query_top_products
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

API_KEY = os.getenv("API_KEY")
print(f"Loaded api_key: {API_KEY}")

from fastapi import FastAPI, Security
from fastapi.security.api_key import APIKeyHeader

API_KEY_NAME = "x-api-key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        print(f"Received api_key: {api_key}")
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key

# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/recommend")
def recommend_products(
    data: QueryInput,
    api_key: str = Security(get_api_key)
):
    return query_top_products(data.question)

