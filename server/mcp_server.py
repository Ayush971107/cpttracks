from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import String, Text, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, mapped_column

from enrichmcp import EnrichMCP
from enrichmcp.sqlalchemy import (
    EnrichSQLAlchemyMixin,
    include_sqlalchemy_models,
    sqlalchemy_lifespan
)

class Base(DeclarativeBase, EnrichSQLAlchemyMixin):
    """Base class for all ORM models, with MCP mixin."""
    pass


class BaseModel(Base):
    __abstract__ = True

    id = mapped_column(Integer, primary_key=True)
    code = mapped_column(String(32), unique=True, nullable=False)
    short_description = mapped_column(Text, nullable=False)
    enhanced_description = mapped_column(Text, nullable=False)
    created_at = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = mapped_column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'short_description': self.short_description,
            'enhanced_description': self.enhanced_description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class ICD10CMCode(BaseModel):
    __tablename__ = 'icd10cm_codes'

class ICD10PCSCode(BaseModel):
    __tablename__ = 'icd10pcs_codes'

class CPTCode(BaseModel):
    __tablename__ = 'cpt_codes'

class HSPCSCode(BaseModel):
    __tablename__ = 'hspcs_codes'


DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5437/sample_project"

engine = create_async_engine(DATABASE_URL)

app = EnrichMCP(
    "CPT Code MCP Server",
    lifespan=sqlalchemy_lifespan(Base, engine),
    description="CPT Code MCP Server"
)

include_sqlalchemy_models(app, Base)

app.run()
