# Resume Knowledge Graph Report

## Overview

This report summarizes the end-to-end creation of a knowledge graph from the Kaggle Resume Dataset using `neo4j-graphrag` and Neo4j.

- Dataset: [Resume Dataset (Kaggle)](https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset)
- Main script: `workshop-genai/kg_resume_builder.py`
- Graph database: Neo4j sandbox instance (configured via `.env`)

## Objective

Build a combined graph that includes:

- **Lexical graph** (from unstructured resume text)
- **Domain graph** (from structured fields such as resume ID and category)

This enables both semantic exploration (skills, roles, tools) and structured filtering (candidate/category).

## Data Source

The dataset was downloaded and extracted to:

- `workshop-genai/data/resume-dataset/Resume/Resume.csv`

Relevant CSV fields used:

- `ID`
- `Resume_str`
- `Category`

## Pipeline Design

The script configures `SimpleKGPipeline` with:

- LLM: `gpt-5-nano` (`reasoning_effort=minimal`)
- Embeddings: `text-embedding-ada-002`
- Text splitter: `FixedSizeSplitter(chunk_size=1200, chunk_overlap=150)`
- Input mode: `from_pdf=False` and `run_async(text=..., document_metadata=...)`

### Schema Constraints

Node types:

- `Skill`, `Role`, `Tool`, `Domain`, `Education`, `Certification`, `Achievement`

Relationship types:

- `HAS_SKILL`, `WORKED_AS`, `USED_TOOL`, `IN_DOMAIN`, `STUDIED`, `EARNED`, `ACHIEVED`, `RELATED_TO`

Patterns:

- `(Role)-[:HAS_SKILL]->(Skill)`
- `(Role)-[:USED_TOOL]->(Tool)`
- `(Role)-[:IN_DOMAIN]->(Domain)`
- `(Education)-[:RELATED_TO]->(Domain)`
- `(Certification)-[:RELATED_TO]->(Skill)`
- `(Achievement)-[:RELATED_TO]->(Role)`
- `(Skill)-[:RELATED_TO]->(Skill)`

## Structured Enrichment

After each resume ingestion, the following structured model is merged:

- `(:Candidate {resume_id})`
- `(:Category {name})`
- `(:Candidate)-[:HAS_RESUME]->(:Document)`
- `(:Document)-[:IN_CATEGORY]->(:Category)`

This is implemented with Cypher in `LINK_STRUCTURED_CYPHER` inside `kg_resume_builder.py`.

## Execution

Sample run command used:

```bash
RESUME_MAX_ROWS=10 RESUME_SLEEP_SECONDS=0.2 .venv/bin/python workshop-genai/kg_resume_builder.py
```

Environment controls supported by script:

- `RESUME_MAX_ROWS` (default `25`)
- `RESUME_SLEEP_SECONDS` (default `0.5`)
- `RESUME_CLEAR_GRAPH_FIRST` (default `true`)

## Results (Sample Run: 10 resumes)

Final graph counts:

- `documents: 10`
- `chunks: 65`
- `entities: 316`
- `candidates: 10`
- `categories: 1`

Processing summary:

- Processed: `10`
- Skipped: `0`

## Example Insights

From exploration queries on the built graph:

- Top skills included: `Recruitment`, `HR`, `filing`, `administrative`, `ADP`, `customer service`
- Top roles included: `HR Manager`, `HR Specialist`, `HR Director`, `HR Administrator`
- Candidate lookup by skill is possible (example: searching for `customer service`)

## Example Cypher Queries

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

Find candidates by skill:

```cypher
MATCH (cand:Candidate)-[:HAS_RESUME]->(:Document)<-[:FROM_DOCUMENT]-(c:Chunk)<-[:FROM_CHUNK]-(skill:Skill)
WHERE toLower(skill.name) CONTAINS "customer service"
RETURN DISTINCT cand.resume_id, cand.category, skill.name
LIMIT 20
```

## Observations and Next Improvements

- The graph creation workflow is stable on sampled data.
- Entity quality can be improved by refining schema descriptions and adding post-processing for noisy values.
- Recommended next step: ingest more rows gradually (for example `100`, then `500`) to monitor API rate limits and quality.
- Add deduplication/normalization rules for skill and role names (case, aliases, spelling variants).

