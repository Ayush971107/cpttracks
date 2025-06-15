# server/mcp_server.py
import os
from datetime import datetime, timezone

import dotenv
import openai
from pinecone import Pinecone, ServerlessSpec
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import String, Text, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, mapped_column

from enrichmcp import EnrichMCP
from enrichmcp.sqlalchemy import (
    EnrichSQLAlchemyMixin,
    include_sqlalchemy_models,
    sqlalchemy_lifespan,
)

dotenv.load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENVIRONMENT")
INDEX_NAME   = "insurance-codes"      
NAMESPACE    = "__default__"

if not OPENAI_KEY or not PINECONE_KEY or not PINECONE_ENV:
    raise RuntimeError(
        "Please set OPENAI_API_KEY, PINECONE_API_KEY and PINECONE_ENVIRONMENT"
    )

openai_client = openai.OpenAI(api_key=OPENAI_KEY)
pc = Pinecone(api_key=PINECONE_KEY, environment=PINECONE_ENV)
if INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=INDEX_NAME,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=PINECONE_ENV),
    )
pinecone_index = pc.Index(INDEX_NAME)

class Base(DeclarativeBase, EnrichSQLAlchemyMixin):
    pass

class BaseModel(Base):
    __abstract__ = True
    id                   = mapped_column(Integer, primary_key=True)
    code                 = mapped_column(String(32), unique=True, nullable=False)
    short_description    = mapped_column(Text, nullable=False)
    enhanced_description = mapped_column(Text, nullable=False)
    created_at           = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at           = mapped_column(
                              DateTime,
                              default=lambda: datetime.now(timezone.utc),
                              onupdate=lambda: datetime.now(timezone.utc),
                          )

class ICD10CMCode(BaseModel):   __tablename__ = "icd10cm_codes"
class ICD10PCSCode(BaseModel): __tablename__ = "icd10pcs_codes"
class CPTCode(BaseModel):      __tablename__ = "cpt_codes"
class HSPCSCode(BaseModel):    __tablename__ = "hspcs_codes"

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5437/sample_project"
engine = create_async_engine(DATABASE_URL, echo=False)

app = EnrichMCP(
    "Insurance Codes MCP Server",
    lifespan=sqlalchemy_lifespan(Base, engine),
    description="SQL + vector search over insurance codes"
)
include_sqlalchemy_models(app, Base)


@app.resource
def find_similar_codes(query: str, top_k: int = 5) -> list[str]:
    """
    Embed the natural-language `query` via OpenAI, query Pinecone,
    and return the top_k insurance codes from metadata.
    """
    # Get embedding
    emb_resp = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=query,
    )
    vector = emb_resp.data[0].embedding

    # Query Pinecone
    results = pinecone_index.query(
        vector=vector,
        top_k=top_k,
        namespace=NAMESPACE if NAMESPACE else None,
        include_metadata=True,
    )

    codes = []
    for match in results.matches:
        if ':' in match.id:
            code = match.id.split(':', 1)[1]
            codes.append(code)
    
    return codes

app.run()