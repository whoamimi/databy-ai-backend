"""
app.api.mongodb
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, constr
from typing import List, Any, Optional

mongo = APIRouter(prefix="/mongo", tags=["mongo"])

class MongoCredentials(BaseModel):
    uri: constr(min_length=10)       # MongoDB connection string / URI
    database: constr(min_length=1)   # Name of the database to access


def get_db_client(creds: MongoCredentials):
    """Establishes MongoDB client connection using PyMongo."""
    try:
        client = MongoClient(creds.uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")  # Simple connectivity test
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not connect to MongoDB: {e}"
        )
    return client, creds.database


@mongo.post("/collections", response_model=List[str])
def list_collections(creds: MongoCredentials) -> List[str]:
    """
    Given MongoDB URI & database name, return list of collection names.
    """
    client, db_name = get_db_client(creds)
    db = client[db_name]
    try:
        names = db.list_collection_names()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing collections: {e}"
        )
    return names


class CollectionQuery(BaseModel):
    creds: MongoCredentials
    collection_name: constr(min_length=1)
    filter: Optional[dict] = Field(default_factory=dict)
    limit: int = Field(default=10, ge=1, le=1000)


@mongo.post("/collection/documents", response_model=List[Any])
def get_collection_documents(query: CollectionQuery) -> List[Any]:
    """
    Fetch documents from a specified collection in the user's database.
    """
    client, db_name = get_db_client(query.creds)
    db = client[db_name]
    coll = db[query.collection_name]
    try:
        cursor = coll.find(query.filter).limit(query.limit)
        docs = list(cursor)
        for doc in docs:
            doc["_id"] = str(doc["_id"])  # Convert ObjectId for JSON serialization
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching documents: {e}"
        )
    return docs