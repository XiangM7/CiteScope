import { ReactNode } from "react";

type PageShellProps = {
  title: string;
  eyebrow: string;
  description: string;
  children: ReactNode;
};

export function PageShell({ title, eyebrow, description, children }: PageShellProps) {
  return (
    <main className="mx-auto flex max-w-6xl flex-col gap-8 px-6 py-10">
      <section className="rounded-panel border border-white/60 bg-white/80 p-8 shadow-soft backdrop-blur">
        <p className="text-sm font-semibold uppercase tracking-[0.22em] text-coral">{eyebrow}</p>
        <div className="mt-4 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div className="max-w-3xl">
            <h1 className="font-serif text-4xl text-ink">{title}</h1>
            <p className="mt-3 text-base leading-7 text-ink/75">{description}</p>
          </div>
        </div>
      </section>
      {children}
    </main>
  );
}
