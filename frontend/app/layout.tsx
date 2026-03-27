import type { Metadata } from "next";
import type { ReactNode } from "react";

import { SiteNav } from "@/components/site-nav";

import "./globals.css";

export const metadata: Metadata = {
  title: "CiteScope",
  description: "Grounded research assistant for PDFs and web sources with citations and evaluations."
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body className="bg-sand text-ink antialiased">
        <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(159,211,199,0.32),_transparent_30%),radial-gradient(circle_at_top_right,_rgba(255,139,94,0.16),_transparent_25%),linear-gradient(180deg,_#fff9f2_0%,_#f2f7ff_100%)]">
          <SiteNav />
          {children}
        </div>
      </body>
    </html>
  );
}
