# Neo4j Resume Knowledge Graph

Professional project demonstrating how to build a hybrid knowledge graph (lexical + structured) from resume data using Neo4j and GraphRAG for Python.

## Project Highlights

- Build a **knowledge graph from unstructured resume text** with `SimpleKGPipeline`
- Enrich graph with **structured metadata** (`Candidate`, `Category`)
- Use a custom schema to extract domain entities (`Skill`, `Role`, `Tool`, `Domain`, etc.)
- Query graph for practical insights (top skills, top roles, candidate discovery by skill)

## Tech Stack

- Python 3
- Neo4j
- `neo4j-graphrag`
- OpenAI (LLM + embeddings)
- Kaggle dataset integration

## Dataset

- Source: [Kaggle Resume Dataset](https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset)
- Expected local file: `workshop-genai/data/resume-dataset/Resume/Resume.csv`

## Main Files

- `workshop-genai/kg_resume_builder.py`: end-to-end resume graph builder
- `workshop-genai/RESUME_KG_REPORT.md`: final workshop report (methodology, implementation, and outcomes)
- `workshop-genai/kg_builder.py`: baseline KG pipeline from PDF
- `workshop-genai/kg_builder_schema.py`: schema-constrained KG extraction
- `workshop-genai/kg_structured_builder.py`: structured + unstructured lesson graph

## Quick Start

1. Install dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

2. Configure environment in `.env`:

```env
OPENAI_API_KEY="sk-..."
NEO4J_URI="bolt://..."
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="..."
NEO4J_DATABASE="neo4j"
```

3. Run resume graph pipeline:

```bash
RESUME_MAX_ROWS=25 RESUME_SLEEP_SECONDS=0.5 .venv/bin/python workshop-genai/kg_resume_builder.py
```

## Example Queries

Count graph objects:

```cypher
RETURN
  count{ (:Document) } AS documents,
  count{ (:Chunk) } AS chunks,
  count{ (:__Entity__) } AS entities,
  count{ (:Candidate) } AS candidates,
  count{ (:Category) } AS categories
```

Top skills by category:

```cypher
MATCH (cat:Category)<-[:IN_CATEGORY]-(:Document)<-[:FROM_DOCUMENT]-(c:Chunk)<-[:FROM_CHUNK]-(skill:Skill)
WHERE skill.name IS NOT NULL AND trim(skill.name) <> ""
RETURN cat.name AS category, skill.name AS skill, count(*) AS mentions
ORDER BY mentions DESC
LIMIT 20
```

## Final Workshop Deliverable

This repository includes my final workshop report completed at the end of the practical session.

- Full report: [Resume Knowledge Graph Report](workshop-genai/RESUME_KG_REPORT.md)
- Coverage: project scope, architecture choices, schema design, execution results, queries, and improvement roadmap

## Workshop origin

This repo extends exercises from the [Neo4j and Generative AI Workshop](https://graphacademy.neo4j.com/courses/workshop-genai) on [GraphAcademy](https://graphacademy.neo4j.com).
