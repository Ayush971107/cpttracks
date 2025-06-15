import asyncio
import uvicorn

from mcp_server import engine, Base, app
from sqlalchemy.ext.asyncio import async_sessionmaker
from mcp_server import CPTCode

AsyncSession = async_sessionmaker(engine, expire_on_commit=False)

async def init_db_and_seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    samples = [
        CPTCode(
            code=f"{10000+i}",
            state="CA" if i % 2 == 0 else "TX",
            description=f"Procedure example {i}",
            ai_description=f"AI-desc for {10000+i}"
        )
        for i in range(50)
    ]
    async with AsyncSession() as session:
        session.add_all(samples)
        await session.commit()

async def main():
    await init_db_and_seed()
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db_and_seed())
    import uvicorn
    uvicorn.run("mcp_server:app", host="127.0.0.1", port=8000, log_level="info")