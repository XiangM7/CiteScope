"use client";

import { FormEvent, useState } from "react";

import { PageShell } from "@/components/page-shell";
import { askQuestion } from "@/lib/api";
import type { ChatResponse } from "@/lib/types";

export default function ChatPage() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<ChatResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!question.trim()) {
      return;
    }

    setBusy(true);
    setError(null);

    try {
      const response = await askQuestion(question.trim());
      setResult(response);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Question failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <PageShell
      eyebrow="Chat"
      title="Ask grounded questions against indexed sources"
      description="Answers are generated only from the retrieved context. You can inspect the citations and the supporting evidence snippets directly below the answer."
    >
      <section className="rounded-panel border border-white/60 bg-white/80 p-6 shadow-soft">
        <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
          <label className="text-sm font-semibold text-ink">Research question</label>
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="What does the uploaded material say about the study design?"
            rows={4}
            disabled={busy}
            className="rounded-3xl border border-ink/15 bg-white px-4 py-4 text-sm leading-6 outline-none transition focus:border-coral"
          />
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={busy || !question.trim()}
              className="rounded-full bg-ink px-5 py-3 text-sm font-semibold text-white disabled:opacity-60"
            >
              {busy ? "Searching and answering..." : "Ask CiteScope"}
            </button>
            {error && <p className="text-sm text-rose-700">{error}</p>}
          </div>
        </form>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <article className="rounded-panel border border-white/60 bg-white/80 p-6 shadow-soft">
          <h2 className="text-xl font-semibold text-ink">Answer</h2>
          <div className="mt-4 rounded-3xl border border-ink/10 bg-sand/60 p-5">
            <p className="whitespace-pre-wrap text-sm leading-7 text-ink/80">
              {result?.answer ?? "Ask a question after indexing sources to see a grounded answer here."}
            </p>
          </div>

          <div className="mt-6">
            <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-coral">Citations</h3>
            <div className="mt-3 space-y-3">
              {result?.citations.length ? (
                result.citations.map((citation) => (
                  <div key={citation.chunk_id} className="rounded-2xl border border-ink/10 bg-white p-4">
                    <p className="text-sm font-semibold text-ink">{citation.document_title}</p>
                    <p className="mt-1 text-sm text-ink/70">
                      Chunk #{citation.chunk_id}
                      {citation.page_number ? ` · Page ${citation.page_number}` : ""}
                    </p>
                    <p className="mt-1 break-all text-xs text-ink/55">{citation.source_path}</p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-ink/65">No citations yet. If evidence is insufficient, the answer will say so.</p>
              )}
            </div>
          </div>
        </article>

        <article className="rounded-panel border border-white/60 bg-white/80 p-6 shadow-soft">
          <h2 className="text-xl font-semibold text-ink">Retrieved evidence</h2>
          <div className="mt-4 space-y-4">
            {result?.retrieved_chunks.length ? (
              result.retrieved_chunks.map((chunk) => (
                <div key={chunk.chunk_id} className="rounded-3xl border border-ink/10 bg-mist/55 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-ink">{chunk.document_title}</p>
                    <p className="text-xs font-semibold uppercase tracking-[0.15em] text-ink/55">
                      Score {chunk.score.toFixed(3)}
                    </p>
                  </div>
                  <p className="mt-1 text-xs text-ink/60">
                    Chunk #{chunk.chunk_id}
                    {chunk.page_number ? ` · Page ${chunk.page_number}` : ""}
                    {chunk.section_title ? ` · ${chunk.section_title}` : ""}
                  </p>
                  <p className="mt-3 text-sm leading-6 text-ink/75">{chunk.chunk_text}</p>
                </div>
              ))
            ) : (
              <p className="text-sm text-ink/65">Retrieved chunks will appear here after the first successful question.</p>
            )}
          </div>
        </article>
      </section>
    </PageShell>
  );
}
