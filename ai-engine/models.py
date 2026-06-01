from pydantic import BaseModel
from typing import List 

class AnalysisRequest(BaseModel):
    raw_text: str

class AnalysisResponse(BaseModel):
    summary: str
    key_themes: List[str]

class SearchRequest(BaseModel):
    query: str

class SearchResultItem(BaseModel):
    id: int
    summary: str
    similarity_score: float

class SearchResponse(BaseModel):
    results: List[SearchResultItem]