import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="mx-auto flex max-w-6xl flex-col gap-10 px-6 py-10">
      <section className="grid gap-8 rounded-panel border border-white/70 bg-white/80 p-8 shadow-soft backdrop-blur lg:grid-cols-[1.3fr_0.7fr]">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-coral">Local-First Research MVP</p>
          <h1 className="mt-4 max-w-3xl font-serif text-5xl leading-tight text-ink">
            Ground your answers in uploaded PDFs and saved web pages, with citations you can inspect.
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-ink/75">
            CiteScope ingests source material, preserves page metadata, retrieves evidence, answers only from that
            evidence, and runs simple evals to show whether retrieval and citations are landing in the right place.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/sources"
              className="rounded-full bg-ink px-6 py-3 text-sm font-semibold text-white transition hover:translate-y-[-1px]"
            >
              Start with sources
            </Link>
            <Link
              href="/chat"
              className="rounded-full border border-ink/15 bg-white px-6 py-3 text-sm font-semibold text-ink transition hover:bg-mist"
            >
              Go to chat
            </Link>
          </div>
        </div>

        <div className="grid gap-4">
          {[
            {
              title: "Ingestion",
              text: "Upload PDFs or add URLs. CiteScope stores the source, parses it, chunks it, and indexes it locally."
            },
            {
              title: "Grounded answers",
              text: "Each response includes citation objects and the retrieved evidence snippets used to answer."
            },
            {
              title: "Simple evals",
              text: "Auto-generated eval cases let you quickly measure retrieval hit rate, citation correctness, and answer overlap."
            }
          ].map((item) => (
            <article key={item.title} className="rounded-3xl border border-ink/10 bg-mist/70 p-5">
              <h2 className="text-lg font-semibold text-ink">{item.title}</h2>
              <p className="mt-2 text-sm leading-6 text-ink/70">{item.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="grid gap-6 md:grid-cols-3">
        {[
          {
            step: "1",
            title: "Add sources",
            text: "Save PDFs and web pages, then trigger indexing to populate local chunks and vector embeddings."
          },
          {
            step: "2",
            title: "Ask questions",
            text: "Use the chat page to query only the indexed corpus and inspect the exact evidence used."
          },
          {
            step: "3",
            title: "Run evals",
            text: "Baseline evals help verify that retrieval and citation behavior stay grounded as the app evolves."
          }
        ].map((card) => (
          <article key={card.step} className="rounded-panel border border-white/60 bg-white/75 p-6 shadow-soft">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-coral">Step {card.step}</p>
            <h2 className="mt-3 text-2xl font-semibold text-ink">{card.title}</h2>
            <p className="mt-3 text-sm leading-7 text-ink/75">{card.text}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
