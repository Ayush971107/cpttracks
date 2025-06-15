from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from enrichmcp import EnrichMCP
from enrichmcp.sqlalchemy import EnrichSQLAlchemyMixin, include_sqlalchemy_models, sqlalchemy_lifespan

# 1. Define the SQLAlchemy declarative base with the EnrichMCP mixin
class Base(DeclarativeBase, EnrichSQLAlchemyMixin):
    """Base class for all ORM models, with MCP mixin."""
    pass

class CPTCode(Base):
    __tablename__ = "cpt_codes"
    code: Mapped[str] = mapped_column("Code", String, primary_key=True)
    state: Mapped[str] = mapped_column("State", String)
    description: Mapped[str] = mapped_column("Description", Text)
    ai_description: Mapped[str] = mapped_column("AI Description", Text)

DATABASE_URL = "sqlite+aiosqlite:///./cpt_codes.db"
engine = create_async_engine(DATABASE_URL, echo=True)

app = EnrichMCP(
    "CPT Code MCP Server",
    lifespan=sqlalchemy_lifespan(Base, engine),
    description="CPT Code MCP Server"
)

include_sqlalchemy_models(app, Base)

if __name__ == "__main__":
    app.run()
