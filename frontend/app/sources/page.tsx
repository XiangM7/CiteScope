"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";

import { PageShell } from "@/components/page-shell";
import { StatusBadge } from "@/components/status-badge";
import { addWebDocument, indexDocument, listDocuments, uploadDocument } from "@/lib/api";
import type { DocumentItem } from "@/lib/types";

export default function SourcesPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refreshDocuments() {
    try {
      const items = await listDocuments();
      setDocuments(items);
    } catch (refreshError) {
      setError(refreshError instanceof Error ? refreshError.message : "Failed to load sources.");
    }
  }

  useEffect(() => {
    void refreshDocuments();
  }, []);

  async function handleFiles(event: ChangeEvent<HTMLInputElement>) {
    const files = event.target.files;
    if (!files?.length) {
      return;
    }

    setBusy(true);
    setError(null);
    setMessage(`Uploading and indexing ${files.length} PDF file${files.length > 1 ? "s" : ""}...`);

    try {
      for (const file of Array.from(files)) {
        const document = await uploadDocument(file);
        await indexDocument(document.id);
      }
      setMessage("Sources uploaded and indexed.");
      await refreshDocuments();
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "Upload failed.");
      setMessage(null);
    } finally {
      event.target.value = "";
      setBusy(false);
    }
  }

  async function handleUrlSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!url.trim()) {
      return;
    }

    setBusy(true);
    setError(null);
    setMessage("Fetching, parsing, and indexing the web source...");

    try {
      const document = await addWebDocument(url.trim());
      await indexDocument(document.id);
      setUrl("");
      setMessage("Web source indexed.");
      await refreshDocuments();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Could not add the web source.");
      setMessage(null);
    } finally {
      setBusy(false);
    }
  }

  async function handleReindex(documentId: number) {
    setBusy(true);
    setError(null);
    setMessage("Re-indexing source...");
    try {
      await indexDocument(documentId);
      setMessage("Source re-indexed.");
      await refreshDocuments();
    } catch (reindexError) {
      setError(reindexError instanceof Error ? reindexError.message : "Re-index failed.");
      setMessage(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <PageShell
      eyebrow="Sources"
      title="Ingest PDFs and web pages"
      description="Each source is stored locally, parsed explicitly, chunked with metadata, and indexed into a persistent Chroma collection."
    >
      <section className="grid gap-6 lg:grid-cols-2">
        <article className="rounded-panel border border-white/60 bg-white/80 p-6 shadow-soft">
          <h2 className="text-xl font-semibold text-ink">Upload PDFs</h2>
          <p className="mt-2 text-sm leading-6 text-ink/70">
            Page numbers are preserved per chunk so PDF citations can point back to the originating page.
          </p>
          <label className="mt-5 flex cursor-pointer flex-col items-center justify-center rounded-3xl border border-dashed border-ink/20 bg-mist/60 p-8 text-center">
            <span className="text-sm font-semibold text-ink">Choose one or more PDF files</span>
            <span className="mt-2 text-sm text-ink/65">Files are uploaded, saved locally, then indexed automatically.</span>
            <input type="file" accept="application/pdf" multiple className="hidden" onChange={handleFiles} disabled={busy} />
          </label>
        </article>

        <article className="rounded-panel border border-white/60 bg-white/80 p-6 shadow-soft">
          <h2 className="text-xl font-semibold text-ink">Add a web page</h2>
          <p className="mt-2 text-sm leading-6 text-ink/70">
            CiteScope fetches the page, extracts the readable body text, stores the title and URL, and indexes it like any other source.
          </p>
          <form className="mt-5 flex flex-col gap-3" onSubmit={handleUrlSubmit}>
            <input
              type="url"
              placeholder="https://example.com/article"
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              disabled={busy}
              className="rounded-2xl border border-ink/15 bg-white px-4 py-3 text-sm outline-none ring-0 transition focus:border-coral"
            />
            <button
              type="submit"
              disabled={busy || !url.trim()}
              className="rounded-full bg-ink px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
            >
              Save and index URL
            </button>
          </form>
        </article>
      </section>

      {(message || error) && (
        <section className={`rounded-panel border p-4 ${error ? "border-rose-200 bg-rose-50" : "border-emerald-200 bg-emerald-50"}`}>
          <p className="text-sm font-medium text-ink">{error ?? message}</p>
        </section>
      )}

      <section className="rounded-panel border border-white/60 bg-white/80 p-6 shadow-soft">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold text-ink">Indexed source inventory</h2>
            <p className="mt-1 text-sm text-ink/70">Statuses update as each source moves from upload to parsing to indexing.</p>
          </div>
          <button
            type="button"
            onClick={() => void refreshDocuments()}
            className="rounded-full border border-ink/15 bg-white px-4 py-2 text-sm font-semibold text-ink"
          >
            Refresh
          </button>
        </div>

        <div className="mt-6 space-y-4">
          {documents.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-ink/15 bg-sand/60 p-8 text-sm text-ink/70">
              No sources yet. Upload a PDF or add a URL to start building the local research corpus.
            </div>
          ) : (
            documents.map((document) => (
              <article key={document.id} className="rounded-3xl border border-ink/10 bg-white p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="max-w-3xl">
                    <div className="flex flex-wrap items-center gap-3">
                      <h3 className="text-lg font-semibold text-ink">{document.title}</h3>
                      <StatusBadge status={document.status} />
                    </div>
                    <p className="mt-2 text-sm text-ink/65">
                      {document.source_type.toUpperCase()} · {document.chunk_count} chunk{document.chunk_count === 1 ? "" : "s"}
                    </p>
                    <p className="mt-2 break-all text-sm leading-6 text-ink/70">{document.source_path}</p>
                  </div>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void handleReindex(document.id)}
                    className="rounded-full border border-ink/15 bg-mist px-4 py-2 text-sm font-semibold text-ink disabled:opacity-50"
                  >
                    Re-index
                  </button>
                </div>
              </article>
            ))
          )}
        </div>
      </section>
    </PageShell>
  );
}
