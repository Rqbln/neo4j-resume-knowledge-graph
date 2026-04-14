"""
LangChain agent for the resume knowledge graph built with `kg_resume_builder.py`.

Prerequisites:
- Load the resume graph (run `kg_resume_builder.py` with your desired `RESUME_MAX_ROWS`).
- Ensure `OPENAI_API_KEY` and Neo4j credentials are set in `.env`.

Environment:
- RESUME_AGENT_QUERY: default user message (optional).
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.retrievers import Text2CypherRetriever, VectorCypherRetriever

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
load_dotenv()

_READ_START = re.compile(
    r"^\s*(MATCH|OPTIONAL\s+MATCH|CALL|WITH|RETURN|SHOW|UNWIND)\b",
    re.IGNORECASE | re.DOTALL,
)
_BLOCKED = re.compile(
    r"\b(CREATE|MERGE|DELETE|DETACH\s+DELETE|SET|REMOVE|DROP|FOREACH)\b",
    re.IGNORECASE,
)


def _validate_read_only_cypher(cypher: str) -> str | None:
    """Return an error message if the statement is not allowed, else None."""
    text = cypher.strip()
    if not text:
        return "Empty Cypher string."
    if not _READ_START.search(text):
        return "Query must start with MATCH, OPTIONAL MATCH, CALL, WITH, RETURN, SHOW, or UNWIND."
    if _BLOCKED.search(text):
        return "Mutating Cypher is not allowed (no CREATE, MERGE, DELETE, SET, etc.)."
    return None


model = init_chat_model("gpt-5.2", model_provider="openai")

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),
)

# Vector index for Chunk embeddings (same model/dimensions as the KG builder).
driver.execute_query(
    """
    CREATE VECTOR INDEX chunkEmbedding IF NOT EXISTS
    FOR (n:Chunk)
    ON n.embedding
    OPTIONS {indexConfig: {
        `vector.dimensions`: 1536,
        `vector.similarity_function`: 'cosine'
    }}
    """,
    database_=os.getenv("NEO4J_DATABASE"),
)

embedder = OpenAIEmbeddings(model="text-embedding-ada-002")

# Resume graph: lexical chunks + domain nodes (Candidate, Category). No Lesson/PDF_OF.
resume_vector_retrieval_query = """
MATCH (node)-[:FROM_DOCUMENT]->(d:Document)
OPTIONAL MATCH (d)-[:IN_CATEGORY]->(cat:Category)
OPTIONAL MATCH (cand:Candidate)-[:HAS_RESUME]->(d)
RETURN
    node.text AS text,
    score,
    d.resume_id AS resume_id,
    cat.name AS category,
    collect {
        MATCH (node)<-[:FROM_CHUNK]-(entity)-[r]->(other)-[:FROM_CHUNK]->()
        WITH toStringList([
            head([label IN labels(entity) WHERE NOT label IN ['__Entity__', '__KGBuilder__']]),
            entity.name,
            properties(entity)['type'],
            properties(entity)['description'],
            type(r),
            head([label IN labels(other) WHERE NOT label IN ['__Entity__', '__KGBuilder__']]),
            other.name,
            properties(other)['type'],
            properties(other)['description']
        ]) AS values
        RETURN reduce(acc = "", item IN values | acc || coalesce(item || ' ', ''))
    } AS associated_entities
"""

resume_vector_retriever = VectorCypherRetriever(
    driver,
    neo4j_database=os.getenv("NEO4J_DATABASE"),
    index_name="chunkEmbedding",
    embedder=embedder,
    retrieval_query=resume_vector_retrieval_query,
)

cypher_llm = OpenAILLM(model_name="gpt-5.2")

resume_text2cypher_examples = [
    (
        "USER INPUT: 'How many resume documents are in the graph?' "
        "QUERY: MATCH (d:Document) RETURN count(d) AS document_count"
    ),
    (
        "USER INPUT: 'How many candidates are there per job category?' "
        "QUERY: MATCH (c:Candidate) RETURN c.category AS category, count(c) AS candidates "
        "ORDER BY candidates DESC"
    ),
    (
        "USER INPUT: 'List skills that appear in resumes for the HR category.' "
        "QUERY: MATCH (cat:Category {name: 'HR'})<-[:IN_CATEGORY]-(d:Document)"
        "<-[:FROM_DOCUMENT]-(ch:Chunk)<-[:FROM_CHUNK]-(s:Skill) "
        "RETURN DISTINCT s.name AS skill ORDER BY skill LIMIT 50"
    ),
    (
        "USER INPUT: 'Find roles mentioned together with Python skills.' "
        "QUERY: MATCH (r:Role)-[:HAS_SKILL]->(s:Skill) "
        "WHERE toLower(s.name) CONTAINS 'python' "
        "RETURN DISTINCT r.name AS role, s.name AS skill LIMIT 30"
    ),
    (
        "USER INPUT: 'Which tools are linked to data engineering roles?' "
        "QUERY: MATCH (r:Role)-[:USED_TOOL]->(t:Tool) "
        "WHERE toLower(r.name) CONTAINS 'data engineer' "
        "RETURN DISTINCT t.name AS tool LIMIT 40"
    ),
    (
        "USER INPUT: 'Sample five resume IDs and their categories.' "
        "QUERY: MATCH (d:Document)-[:IN_CATEGORY]->(cat:Category) "
        "RETURN d.resume_id AS resume_id, cat.name AS category LIMIT 5"
    ),
]

text2cypher_retriever = Text2CypherRetriever(
    driver=driver,
    neo4j_database=os.getenv("NEO4J_DATABASE"),
    llm=cypher_llm,
    examples=resume_text2cypher_examples,
)


@tool("Get-resume-graph-schema")
def get_resume_schema() -> Any:
    """Return nodes and relationships in the Neo4j graph (labels and patterns). Use for questions about graph structure."""
    results, _, _ = driver.execute_query(
        "CALL db.schema.visualization()",
        database_=os.getenv("NEO4J_DATABASE"),
    )
    return results


@tool("Search-resume-content")
def search_resume_content(query: str) -> list[Any]:
    """Semantic search over resume text chunks and linked entities (skills, roles, tools, etc.). Use for open-ended questions about experience and qualifications."""
    result = resume_vector_retriever.search(query_text=query, top_k=5)
    return [item.content for item in result.items]


@tool("Ask-resume-graph")
def ask_resume_graph(natural_language_question: str) -> Any:
    """Convert a question to Cypher and return database results. Use for counts, filters, aggregations, and structured lookups over candidates, categories, and extracted entities."""
    return text2cypher_retriever.get_search_results(natural_language_question)


@tool("Run-read-only-cypher")
def run_read_only_cypher(cypher: str) -> Any:
    """Execute a read-only Cypher query and return rows. Use when you already have a precise MATCH/RETURN (no writes)."""
    err = _validate_read_only_cypher(cypher)
    if err:
        return {"error": err}
    records, _, _ = driver.execute_query(
        cypher,
        database_=os.getenv("NEO4J_DATABASE"),
    )
    return [r.data() for r in records]


tools = [
    get_resume_schema,
    search_resume_content,
    ask_resume_graph,
    run_read_only_cypher,
]

agent = create_agent(model, tools)

if __name__ == "__main__":
    query = os.getenv(
        "RESUME_AGENT_QUERY",
        "How many distinct job categories appear in the resume graph?",
    )
    for step in agent.stream(
        {"messages": [{"role": "user", "content": query}]},
        stream_mode="values",
    ):
        step["messages"][-1].pretty_print()
