"use client";

import { useEffect, useState } from "react";

import { PageShell } from "@/components/page-shell";
import { listEvalCases, listEvalResults, runEvals } from "@/lib/api";
import type { EvalCase, EvalResult } from "@/lib/types";

function PassPill({ ok }: { ok: boolean }) {
  return (
    <span className={`rounded-full px-3 py-1 text-xs font-semibold ${ok ? "bg-emerald-100 text-emerald-900" : "bg-rose-100 text-rose-900"}`}>
      {ok ? "pass" : "fail"}
    </span>
  );
}

export default function EvalPage() {
  const [cases, setCases] = useState<EvalCase[]>([]);
  const [results, setResults] = useState<EvalResult[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refreshData() {
    try {
      const [casePayload, resultPayload] = await Promise.all([listEvalCases(), listEvalResults()]);
      setCases(casePayload);
      setResults(resultPayload);
    } catch (refreshError) {
      setError(refreshError instanceof Error ? refreshError.message : "Could not load eval data.");
    }
  }

  useEffect(() => {
    void refreshData();
  }, []);

  async function handleRunEvals() {
    setBusy(true);
    setError(null);
    try {
      const response = await runEvals();
      setResults(response.results);
      await refreshData();
    } catch (runError) {
      setError(runError instanceof Error ? runError.message : "Eval run failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <PageShell
      eyebrow="Eval"
      title="Run baseline retrieval and citation checks"
      description="Eval cases are auto-generated from indexed content so you can quickly inspect whether expected evidence is retrieved and cited in the answer output."
    >
      <section className="rounded-panel border border-white/60 bg-white/80 p-6 shadow-soft">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold text-ink">Predefined eval cases</h2>
            <p className="mt-1 text-sm text-ink/70">
              Each indexed document contributes a few lightweight regression cases tied to an expected document and page.
            </p>
          </div>
          <button
            type="button"
            onClick={() => void handleRunEvals()}
            disabled={busy || cases.length === 0}
            className="rounded-full bg-ink px-5 py-3 text-sm font-semibold text-white disabled:opacity-60"
          >
            {busy ? "Running evals..." : "Run all evals"}
          </button>
        </div>

        {error && <p className="mt-4 text-sm text-rose-700">{error}</p>}

        <div className="mt-5 space-y-4">
          {cases.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-ink/15 bg-sand/60 p-8 text-sm text-ink/70">
              No eval cases yet. Index at least one source on the Sources page first.
            </div>
          ) : (
            cases.map((evalCase) => (
              <article key={evalCase.id} className="rounded-3xl border border-ink/10 bg-white p-5">
                <p className="text-sm font-semibold text-ink">{evalCase.question}</p>
                <p className="mt-2 text-sm leading-6 text-ink/70">{evalCase.reference_answer}</p>
                <p className="mt-3 text-xs uppercase tracking-[0.18em] text-ink/50">
                  Expected doc {evalCase.expected_document_id ?? "n/a"}
                  {evalCase.expected_page_numbers.length ? ` · pages ${evalCase.expected_page_numbers.join(", ")}` : ""}
                </p>
              </article>
            ))
          )}
        </div>
      </section>

      <section className="rounded-panel border border-white/60 bg-white/80 p-6 shadow-soft">
        <h2 className="text-xl font-semibold text-ink">Latest results</h2>
        <div className="mt-5 overflow-x-auto">
          <table className="min-w-full border-separate border-spacing-y-3">
            <thead>
              <tr className="text-left text-xs uppercase tracking-[0.18em] text-ink/50">
                <th className="px-3">Eval</th>
                <th className="px-3">Retrieval</th>
                <th className="px-3">Citation</th>
                <th className="px-3">Answer score</th>
                <th className="px-3">Retrieved chunks</th>
              </tr>
            </thead>
            <tbody>
              {results.length === 0 ? (
                <tr>
                  <td className="rounded-3xl bg-sand/60 px-3 py-6 text-sm text-ink/70" colSpan={5}>
                    Run evals to populate result rows.
                  </td>
                </tr>
              ) : (
                results.map((result) => (
                  <tr key={result.id} className="rounded-3xl bg-mist/55 text-sm text-ink">
                    <td className="rounded-l-3xl px-3 py-4 align-top">
                      <p className="font-semibold">{result.question}</p>
                      <p className="mt-2 text-xs text-ink/60">{new Date(result.created_at).toLocaleString()}</p>
                    </td>
                    <td className="px-3 py-4 align-top">
                      <PassPill ok={result.retrieval_hit} />
                    </td>
                    <td className="px-3 py-4 align-top">
                      <PassPill ok={result.citation_correct} />
                    </td>
                    <td className="px-3 py-4 align-top">{result.answer_score.toFixed(3)}</td>
                    <td className="rounded-r-3xl px-3 py-4 align-top">{result.retrieved_chunk_ids.join(", ") || "none"}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </PageShell>
  );
}
