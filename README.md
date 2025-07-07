# CPTTracks

A high-performance Retrieval-Augmented Generation (RAG) system for medical billing code lookup and validation.  
Leverages OpenAI embeddings and Pinecone for sub-second, context-aware search over CPT, HCPCS, and ICD-10 datasets, with an EnrichMCP server providing real-time code reasoning and suggestions.

## Features

- **Fast, Context-Aware Search**  
  Uses OpenAI text embeddings + Pinecone vector DB to retrieve relevant insurance codes.
- **LLM-Driven Reasoning**  
  Top vector hits are fed into an LLM for additional context-aware analysis.
- **Modular MCP Server**  
  Async `find_similar_codes` endpoint built with EnrichMCP, SQLAlchemy, and Pinecone.
- **Easy Integration**  
  Provides validated code suggestions ready for revenue-cycle management workflows.

## Architecture

Client ──▶ MCP Server ──▶ OpenAI Embeddings
│
└─▶ Pinecone Vector DB ──▶ LLM Reasoner ──▶ Client


1. **Query Embedding**  
   User query → OpenAI embeddings.
2. **Vector Search**  
   Embedding → Pinecone → top-k code candidates.
3. **LLM Reasoning**  
   Candidates + context → GPT-style model → validated suggestions.

## Installation

```bash
git clone https://github.com/<your-username>/codecompass.git
cd codecompass
pip install -r requirements.txt
```

Create and populate your PostgreSQL database with CPT/HCPCS/ICD-10 tables.

Copy .env.example to .env and fill in OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_ENVIRONMENT, and DATABASE_URL.

Run the MCP server:

```bash
python server/mcp_server.py
```
