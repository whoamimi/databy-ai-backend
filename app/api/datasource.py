"""
app.api.datasource
"""

# app/api/datasource.py

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.agent.memory.gatekeeper import (
    search_hugging_dataset,
    search_kaggle_dataset,
    HUGGINGFACE_BROWSE_CONFIG,
)

router = APIRouter(prefix="/data", tags=["data-source"])

class HuggingFaceListResponse(BaseModel):
    dataset_ids: List[str]

class KaggleListItem(BaseModel):
    ref: str
    title: Optional[str]
    downloadCount: Optional[int]
    lastUpdated: Optional[str]

class KaggleListResponse(BaseModel):
    results: List[KaggleListItem]

@router.get("/huggingface/{domain}", response_model=HuggingFaceListResponse)
async def list_huggingface_datasets(
    domain: str,
    dataset_name: Optional[str] = Query(None, description="Exact dataset id or name to search"),
    limit: int = Query(5, gt=0, description="Maximum number of datasets to return"),
):
    if domain not in HUGGINGFACE_BROWSE_CONFIG:
        raise HTTPException(status_code=400, detail=f"Invalid domain: {domain}")
    try:
        ids = [ds_id for ds_id in search_hugging_dataset(domain=domain, dataset_name=dataset_name, limit=limit)]
        return HuggingFaceListResponse(dataset_ids=ids)
    except Exception as e:
        # Optionally log error
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/kaggle/{category}", response_model=KaggleListResponse)
async def list_kaggle_datasets(
    category: str,
    search_term: Optional[str] = Query(None, description="Keyword to search for in Kaggle datasets"),
    sort_by: str = Query("votes", description="How to sort results: votes|hottest|updated|active|published"),
    page: int = Query(1, gt=0, description="Page number of results"),
):
    # You might validate category if you have a set of allowed categories
    try:
        api_results = search_kaggle_dataset(search_meta=(search_term or category), sort_by=sort_by, page=page)
        items = []
        for ds in api_results:
            items.append(
                KaggleListItem(
                    ref=str(getattr(ds, "ref", getattr(ds, "id", ""))),
                    title=getattr(ds, "title", None),
                    downloadCount=getattr(ds, "downloadCount", None),
                    lastUpdated=str(getattr(ds, "lastUpdated", None)),
                )
            )
        return KaggleListResponse(results=items)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
