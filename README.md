## Prerequisites

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) - Python package and environment manager
- OpenAI API key (for the chat client)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd cptracks
   ```

2. Create and activate a virtual environment using uv:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```

4. Set up your environment variables:
   Create a `.env` file in the root directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Database Connection

The MCP server uses SQLite with SQLAlchemy for database operations. The connection is configured in `mcp_server.py`:

```python
DATABASE_URL = "sqlite+aiosqlite:///./cpt_codes.db"
engine = create_async_engine(DATABASE_URL)
```

### Database Schema

The CPT codes are stored with the following schema:

```python
class CPTCode(Base):
    __tablename__ = "cpt_codes"
    code: Mapped[str] = mapped_column("Code", String, primary_key=True)
    state: Mapped[str] = mapped_column("State", String)
    description: Mapped[str] = mapped_column("Description", Text)
    ai_description: Mapped[str] = mapped_column("AI Description", Text)
```


## Using the Chat Client

An interactive chat client is provided to test the MCP server:

Run the chat client: (quit to exit)
   ```bash
   uv run server/client.py
   ```
