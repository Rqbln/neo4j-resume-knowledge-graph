"use client"

import Image from "next/image"
import { useEffect, useRef } from "react"
import {
  Bot,
  BrainCircuit,
  Database,
  Plus,
  Radar,
} from "lucide-react"

import { renderCanvas } from "@/components/ui/canvas"

/** Verified ingest: `kg_resume_builder.py`, RESUME_MAX_ROWS=25 — update after re-run. */
const STATS = {
  resumes: 25,
  chunks: 164,
  entities: 601,
  embeddingModel: "text-embedding-ada-002",
  embeddingDims: 1536,
} as const

const PILLARS = [
  {
    step: "01",
    title: "Agent with Neo4j, Python & LangChain",
    icon: Bot,
    body:
      "A small LangChain agent orchestrates tools against the graph: schema introspection, semantic chunk search, and Text2Cypher for structured questions — all driven from Python and the Neo4j driver.",
    tags: ["LangChain", "Python", "Tool calling"],
  },
  {
    step: "02",
    title: "GraphRAG for better LLM answers",
    icon: BrainCircuit,
    body:
      "GraphRAG combines retrieval from the knowledge graph with generation: entities, relationships, and chunk text give the model grounded context so answers stay closer to your data and less generic.",
    tags: ["Context quality", "Grounding", "neo4j-graphrag"],
  },
  {
    step: "03",
    title: "Vectors in Neo4j for similarity search",
    icon: Radar,
    body:
      "Chunk embeddings live in Neo4j; a vector index powers nearest-neighbour search. Vector + Cypher retrievers merge similarity scores with graph patterns (e.g. document → category → entities).",
    tags: ["Vector index", "Cosine", "VectorCypherRetriever"],
  },
] as const

export function ResumeHero() {
  const cleanupRef = useRef<(() => void) | null>(null)

  useEffect(() => {
    cleanupRef.current = renderCanvas("canvas")
    return () => {
      cleanupRef.current?.()
    }
  }, [])

  return (
    <section
      id="resume-kg-hero"
      className="relative min-h-screen overflow-hidden bg-gradient-to-b from-emerald-50 via-white to-teal-50/60 text-zinc-900"
    >
      <div className="pointer-events-none absolute inset-0 opacity-[0.22]">
        <Image
          src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=2000&q=80"
          alt=""
          fill
          className="object-cover"
          priority
          sizes="100vw"
        />
      </div>
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_90%_60%_at_50%_-10%,rgba(16,185,129,0.35),transparent_55%)]" />
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-white/75 via-white/88 to-emerald-50/90" />

      <div className="animate-fade-in relative z-10 mx-auto max-w-6xl px-4 pb-24 pt-16 md:pt-20">
        <div className="flex justify-center">
          <span className="inline-flex items-center gap-2 rounded-full border border-emerald-300/80 bg-white/90 px-4 py-1.5 text-xs font-medium text-emerald-900 shadow-sm shadow-emerald-900/5 backdrop-blur-sm">
            <Database className="size-3.5 text-emerald-600" aria-hidden />
            Neo4j · Python · LangChain · GraphRAG
          </span>
        </div>

        <h1 className="mx-auto mt-10 max-w-4xl text-center text-4xl font-semibold leading-[1.1] tracking-tight text-zinc-900 md:text-6xl md:leading-[1.08]">
          <span className="bg-gradient-to-br from-emerald-700 via-emerald-600 to-teal-600 bg-clip-text text-transparent">
            Resume knowledge graph
          </span>
          <br />
          <span className="text-2xl font-normal text-zinc-600 md:text-3xl">
            three ideas from the build
          </span>
        </h1>

        <p className="mx-auto mt-5 max-w-2xl text-center text-sm leading-relaxed text-zinc-600 md:text-base">
          Hands-on track: ingest résumés into Neo4j, then apply the same GraphRAG ideas as in the workshop — agent orchestration, grounded generation, and vector search over{" "}
          <code className="rounded border border-emerald-200 bg-emerald-50 px-1.5 py-0.5 text-emerald-900">
            Chunk
          </code>{" "}
          nodes. <span className="font-medium text-emerald-800">Move the pointer</span> to see the trail effect.
        </p>

        <div className="relative mx-auto mt-14">
          <div className="absolute -inset-px rounded-2xl bg-gradient-to-b from-emerald-400/35 via-emerald-300/15 to-teal-300/25 blur-md" />
          <div className="relative rounded-2xl border border-emerald-200/90 bg-white/85 p-6 shadow-xl shadow-emerald-900/10 backdrop-blur-md md:p-10">
            <Plus
              strokeWidth={2.5}
              className="pointer-events-none absolute -left-1 -top-1 size-6 text-emerald-500 md:size-7"
              aria-hidden
            />
            <Plus
              strokeWidth={2.5}
              className="pointer-events-none absolute -bottom-1 -left-1 size-6 text-emerald-500 md:size-7"
              aria-hidden
            />
            <Plus
              strokeWidth={2.5}
              className="pointer-events-none absolute -right-1 -top-1 size-6 text-emerald-500 md:size-7"
              aria-hidden
            />
            <Plus
              strokeWidth={2.5}
              className="pointer-events-none absolute -bottom-1 -right-1 size-6 text-emerald-500 md:size-7"
              aria-hidden
            />

            <p className="text-center text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700/90">
              Main axes
            </p>

            <div className="mt-8 grid gap-5 md:grid-cols-3 md:gap-6">
              {PILLARS.map((pillar) => {
                const Icon = pillar.icon
                return (
                  <article
                    key={pillar.step}
                    className="group relative flex flex-col rounded-xl border border-emerald-100 bg-gradient-to-b from-white to-emerald-50/40 p-5 shadow-sm transition-shadow hover:border-emerald-300/80 hover:shadow-md"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <span className="font-mono text-[10px] font-medium tabular-nums text-emerald-700/70">
                        {pillar.step}
                      </span>
                      <div className="flex size-11 shrink-0 items-center justify-center rounded-lg border border-emerald-200 bg-emerald-100/80 text-emerald-700 shadow-inner transition-transform group-hover:scale-105">
                        <Icon className="size-5" strokeWidth={1.75} aria-hidden />
                      </div>
                    </div>
                    <h2 className="mt-4 text-left text-base font-semibold leading-snug text-zinc-900 md:text-lg">
                      {pillar.title}
                    </h2>
                    <p className="mt-3 flex-1 text-left text-sm leading-relaxed text-zinc-600">
                      {pillar.body}
                    </p>
                    <ul className="mt-4 flex flex-wrap gap-1.5">
                      {pillar.tags.map((tag) => (
                        <li
                          key={tag}
                          className="rounded-md border border-emerald-100 bg-white/90 px-2 py-0.5 text-[10px] font-medium text-emerald-900/80"
                        >
                          {tag}
                        </li>
                      ))}
                    </ul>
                  </article>
                )
              })}
            </div>

            <div className="mt-10 flex flex-wrap items-center justify-center gap-x-10 gap-y-3 border-t border-emerald-100 pt-8 text-center">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
                  Résumés
                </p>
                <p className="mt-0.5 text-2xl font-semibold tabular-nums text-emerald-600">
                  {STATS.resumes}
                </p>
              </div>
              <div className="hidden h-10 w-px bg-emerald-200 sm:block" aria-hidden />
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
                  Chunks
                </p>
                <p className="mt-0.5 text-2xl font-semibold tabular-nums text-emerald-600">
                  {STATS.chunks}
                </p>
              </div>
              <div className="hidden h-10 w-px bg-emerald-200 sm:block" aria-hidden />
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
                  Entities resolved
                </p>
                <p className="mt-0.5 text-2xl font-semibold tabular-nums text-emerald-600">
                  {STATS.entities}
                </p>
              </div>
              <div className="hidden h-10 w-px bg-emerald-200 sm:block" aria-hidden />
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
                  Embeddings
                </p>
                <p className="mt-0.5 text-sm font-semibold text-emerald-700">
                  {STATS.embeddingDims}d · {STATS.embeddingModel.replace("text-embedding-", "")}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* On top so strokes are visible; clicks pass through */}
      <canvas
        className="pointer-events-none absolute inset-0 z-20 mx-auto h-full w-full max-w-none"
        id="canvas"
        aria-hidden
      />
    </section>
  )
}
