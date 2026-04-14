# Neo4j Resume Knowledge Graph

Ce dépôt présente le travail réalisé lors du **GraphSummit Paris** (journée *« Graphes + IA : redonnez du sens à vos données »*), dans le cadre du **deuxième atelier pratique de l’après-midi** — *Créer des applications GenAI plus pertinentes grâce aux graphes de connaissances & GraphRAG* (14h30–17h00).

> **À copier dans le champ « About » du dépôt GitHub :**  
> *GraphSummit Paris — Atelier GraphRAG & graphes de connaissances. Hybrid KG (résumés) avec Neo4j, Python et LangChain. « Graphes + IA : redonnez du sens à vos données ».*

---

## À propos — GraphSummit Paris

### Graphes + IA : redonnez du sens à vos données

Une journée pour apprendre, s’inspirer et voir le concret. À GraphSummit Paris, découvrez comment les graphes donnent du sens à des données complexes et les transforment en connaissances exploitables pour des systèmes d’IA plus intelligents.

### Pourquoi participer ?

- Prenez de meilleures décisions grâce aux informations issues des graphes clés de votre entreprise.
- Faites passer l’IA du stade expérimental à celui de la production en créant une base de données prête pour l’IA.
- Déployez une IA explicable grâce aux applications optimisées par GraphRAG.

### Les temps forts

- Découvrez comment la plateforme d’intelligence de graphes de Neo4j accélère la réinvention des systèmes data et IA.
- Comprenez comment les leaders du secteur déploient des solutions de graphes et d’IA pour obtenir des résultats concrets.
- Participez à des ateliers animés par des experts Neo4j.
- Bénéficiez d’un aperçu exclusif de la roadmap produit Neo4j, des nouvelles fonctionnalités d’IA aux innovations cloud.
- Rencontrez des pairs confrontés à des défis similaires en matière de données, ainsi que des ingénieurs et partenaires Neo4j.

### Programme (extrait)

*L’agenda peut évoluer ; repères indicatifs de la journée type.*

| Horaire | Sujet |
|--------|--------|
| 9:00 – 9:30 | Accueil & café |
| 9:30 – 9:35 | Mot de bienvenue — Eva Delier, Neo4j |
| 9:35 – 10:20 | Keynote *Graphes + IA : redonnez du sens à vos données* — Jesús Barrasa, Neo4j |
| 10:20 – 10:45 | L’Oréal — *Beauty Genius* et graphes de connaissances — Baptiste Dupré |
| 10:45 – 11:00 | Capgemini — Knowledge Graph en entreprise — Guillaume Gérard |
| 11:00 – 11:30 | Pause |
| 11:30 – 11:55 | Oneytrust — détection de réseaux de fraude — Laure Littler & Hélène Cherel |
| 11:55 – 12:40 | Vision et roadmap produit Neo4j — Ivan Zoratti *(en anglais)* |
| 12:40 – 13:10 | Panel / Q&A matinée |
| 13:10 – 14:30 | Déjeuner |
| **14:30 – 17:00** | **Ateliers** (deux parcours en parallèle) |
| 17:00 – 18:00 | Networking |

**Ateliers de l’après-midi (14h30 – 17h00)**

1. **Passer de zéro à la mise en production avec Neo4j, Aura et les agents IA** — bases des graphes, modélisation, chargement, visualisation, agent IA sur Aura.
2. **Créer des applications GenAI plus pertinentes grâce aux graphes de connaissances & GraphRAG** — limites de la GenAI, combinaison recherche vectorielle / KG / data science, exemples de code, compétences réutilisables sur vos projets.

*Ce dépôt illustre le parcours GraphRAG / graphes de connaissances (atelier 2) : pipeline Python, Neo4j, embeddings, retrieval et agent.*

---

## Project highlights

- Build a **knowledge graph from unstructured resume text** with `SimpleKGPipeline`
- Enrich the graph with **structured metadata** (`Candidate`, `Category`)
- Use a **custom schema** to extract domain entities (`Skill`, `Role`, `Tool`, `Domain`, etc.)
- **Query** the graph for practical insights (top skills, roles, candidate discovery by skill)
- Extend with **vector search** and a **LangChain agent** (`resume_agent.py`, course `agent.py`)

## Tech stack

- Python 3
- Neo4j
- `neo4j-graphrag`
- OpenAI (LLM + embeddings)
- LangChain (agent tooling)
- Kaggle dataset integration
- Optional showcase: `linkedin-onepager/` (Next.js one-pager)

## Dataset

- Source: [Kaggle Resume Dataset](https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset)
- Expected local file: `workshop-genai/data/resume-dataset/Resume/Resume.csv`

## Main files

- `workshop-genai/kg_resume_builder.py`: end-to-end resume graph builder
- `workshop-genai/resume_agent.py`: LangChain agent for the resume graph (vector + Text2Cypher)
- `workshop-genai/RESUME_KG_REPORT.md`: detailed report (methodology, results, roadmap)
- `workshop-genai/kg_builder.py`: baseline KG pipeline from PDF
- `workshop-genai/kg_builder_schema.py`: schema-constrained KG extraction
- `workshop-genai/kg_structured_builder.py`: structured + unstructured lesson graph
- `workshop-genai/agent.py` / `vector_cypher_rag.py`: course GraphRAG and agent examples

## Quick start

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

3. Run the resume graph pipeline:

```bash
RESUME_MAX_ROWS=25 RESUME_SLEEP_SECONDS=0.5 .venv/bin/python workshop-genai/kg_resume_builder.py
```

## Example queries

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

## Deliverable

- Full write-up: [Resume Knowledge Graph Report](workshop-genai/RESUME_KG_REPORT.md) (scope, architecture, schema, runs, queries, next steps)

## Complément — GraphAcademy

Les exercices de base s’appuient également sur le cours en ligne [Neo4j and Generative AI Workshop](https://graphacademy.neo4j.com/courses/workshop-genai) ([GraphAcademy](https://graphacademy.neo4j.com)).
