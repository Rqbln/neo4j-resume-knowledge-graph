import asyncio
import csv
import os
import time

from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import (
    FixedSizeSplitter,
)
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.llm import OpenAILLM

load_dotenv()


DATASET_CSV = "./workshop-genai/data/resume-dataset/Resume/Resume.csv"
MAX_RESUMES = int(os.getenv("RESUME_MAX_ROWS", "25"))
SLEEP_SECONDS = float(os.getenv("RESUME_SLEEP_SECONDS", "0.5"))
CLEAR_GRAPH_FIRST = os.getenv("RESUME_CLEAR_GRAPH_FIRST", "true").lower() == "true"

NODE_TYPES = [
    "Skill",
    "Role",
    "Tool",
    "Domain",
    "Education",
    "Certification",
    "Achievement",
]

RELATIONSHIP_TYPES = [
    "HAS_SKILL",
    "WORKED_AS",
    "USED_TOOL",
    "IN_DOMAIN",
    "STUDIED",
    "EARNED",
    "ACHIEVED",
    "RELATED_TO",
]

PATTERNS = [
    ("Role", "HAS_SKILL", "Skill"),
    ("Role", "USED_TOOL", "Tool"),
    ("Role", "IN_DOMAIN", "Domain"),
    ("Education", "RELATED_TO", "Domain"),
    ("Certification", "RELATED_TO", "Skill"),
    ("Achievement", "RELATED_TO", "Role"),
    ("Skill", "RELATED_TO", "Skill"),
]

LINK_STRUCTURED_CYPHER = """
MATCH (d:Document {resume_id: $resume_id})
MERGE (candidate:Candidate {resume_id: $resume_id})
SET candidate.category = $category
MERGE (category:Category {name: $category})
MERGE (candidate)-[:HAS_RESUME]->(d)
MERGE (d)-[:IN_CATEGORY]->(category)
"""


def main() -> None:
    neo4j_driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),
    )
    neo4j_driver.verify_connectivity()

    llm = OpenAILLM(
        model_name="gpt-5-nano",
        model_params={"reasoning_effort": "minimal"},
    )

    embedder = OpenAIEmbeddings(model="text-embedding-ada-002")
    text_splitter = FixedSizeSplitter(chunk_size=1200, chunk_overlap=150)

    kg_builder = SimpleKGPipeline(
        llm=llm,
        driver=neo4j_driver,
        neo4j_database=os.getenv("NEO4J_DATABASE"),
        embedder=embedder,
        from_pdf=False,
        text_splitter=text_splitter,
        schema={
            "node_types": NODE_TYPES,
            "relationship_types": RELATIONSHIP_TYPES,
            "patterns": PATTERNS,
        },
    )

    if CLEAR_GRAPH_FIRST:
        neo4j_driver.execute_query(
            "MATCH (n) DETACH DELETE n",
            database_=os.getenv("NEO4J_DATABASE"),
        )
        print("Cleared existing graph.")

    processed = 0
    skipped = 0

    with open(DATASET_CSV, encoding="utf8", newline="") as fh:
        for row in csv.DictReader(fh):
            if processed >= MAX_RESUMES:
                break

            resume_id = row["ID"].strip()
            category = row["Category"].strip()
            resume_text = row["Resume_str"].strip()

            if not resume_text:
                skipped += 1
                continue

            metadata = {
                "resume_id": resume_id,
                "category": category,
                "source": "kaggle-resume-dataset",
                "document_type": "resume",
            }

            try:
                result = asyncio.run(
                    kg_builder.run_async(text=resume_text, document_metadata=metadata)
                )

                _, summary, _ = neo4j_driver.execute_query(
                    LINK_STRUCTURED_CYPHER,
                    parameters_={"resume_id": resume_id, "category": category},
                    database_=os.getenv("NEO4J_DATABASE"),
                )

                processed += 1
                print(
                    f"[{processed}/{MAX_RESUMES}] resume_id={resume_id} "
                    f"category={category} result={result.result} "
                    f"structured_updates={summary.counters.contains_updates}"
                )
            except Exception as exc:
                skipped += 1
                print(f"Skipped resume_id={resume_id} due to error: {exc}")

            if SLEEP_SECONDS > 0:
                time.sleep(SLEEP_SECONDS)

    records, _, _ = neo4j_driver.execute_query(
        """
        RETURN
            count{ (:Document) } AS documents,
            count{ (:Chunk) } AS chunks,
            count{ (:__Entity__) } AS entities,
            count{ (:Candidate) } AS candidates,
            count{ (:Category) } AS categories
        """,
        database_=os.getenv("NEO4J_DATABASE"),
    )
    print("Final counts:", records[0].data())
    print(f"Processed resumes: {processed}; Skipped: {skipped}")

    neo4j_driver.close()


if __name__ == "__main__":
    main()
