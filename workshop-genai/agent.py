import os
from dotenv import load_dotenv
load_dotenv()

from neo4j import GraphDatabase
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain_core.tools import tool
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.retrievers import VectorCypherRetriever, Text2CypherRetriever

# Initialize the chat model
model = init_chat_model("gpt-5.2", model_provider="openai")

# Connect to Neo4j database
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(
        os.getenv("NEO4J_USERNAME"),
        os.getenv("NEO4J_PASSWORD")
    )
)

# Create embedder for the retriever.
embedder = OpenAIEmbeddings(model="text-embedding-ada-002")

# Define retrieval query for Vector + Cypher context.
retrieval_query = """
MATCH (node)-[:FROM_DOCUMENT]->(d)-[:PDF_OF]->(lesson)
RETURN
    node.text as text, score,
    lesson.url as lesson_url,
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
    } as associated_entities
"""

# Create vector retriever against Chunk embeddings.
vector_retriever = VectorCypherRetriever(
    driver,
    neo4j_database=os.getenv("NEO4J_DATABASE"),
    index_name="chunkEmbedding",
    embedder=embedder,
    retrieval_query=retrieval_query,
)

# Create LLM for Text2CypherRetriever.
cypher_llm = OpenAILLM(model_name="gpt-5.2")

# Cypher examples as input/query pairs.
examples = [
    "USER INPUT: 'Find a node with the name $name?' QUERY: MATCH (node) WHERE toLower(node.name) CONTAINS toLower($name) RETURN node.name AS name, labels(node) AS labels",
]

# Build the text-to-cypher retriever.
text2cypher_retriever = Text2CypherRetriever(
    driver=driver,
    neo4j_database=os.getenv("NEO4J_DATABASE"),
    llm=cypher_llm,
    examples=examples,
)

# Define functions for each tool in the agent.

@tool("Get-graph-database-schema")
def get_schema():
    """Get the schema of the graph database."""
    results, summary, keys = driver.execute_query(
        "CALL db.schema.visualization()",
        database_=os.getenv("NEO4J_DATABASE")
    )
    return results

@tool("Search-lesson-content")
def search_lessons(query: str):
    """Search for lesson content related to the query."""
    result = vector_retriever.search(query_text=query, top_k=5)
    return [item.content for item in result.items]

@tool("Query-database")
def query_database(query: str):
    """A catchall tool to get answers to specific questions about lesson content."""
    result = text2cypher_retriever.get_search_results(query)
    return result

# Define a list of tools for the agent
tools = [get_schema, search_lessons, query_database]

# Create the agent with the model and tools
agent = create_agent(
    model,
    tools
)

# Run the application
query = os.getenv("AGENT_QUERY", "How many lessons are there?")

for step in agent.stream(
    {
        "messages": [{"role": "user", "content": query}]
    },
    stream_mode="values",
):
    step["messages"][-1].pretty_print()

