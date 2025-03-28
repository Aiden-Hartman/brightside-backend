from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models import QueryInput
from app.recommender import query_top_products

app = FastAPI()

# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/recommend")
def recommend_products(data: QueryInput):
    return query_top_products(data.question)
