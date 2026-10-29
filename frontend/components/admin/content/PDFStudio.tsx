"use client";

import { useMemo, useState } from "react";

type Page = { page: number; char_count: number; image_count: number; needs_visual_review: boolean; preview: string };
type Inspection = { status: string; document_hash: string; filename: string; page_count: number; title: string | null; author: string | null; pages: Page[]; low_text_pages: number[]; visual_review_pages: number[] };
type Topic = { page_count: number; pages: { page: number; mentions: number }[] };
type Mapping = { status: string; document: { document_hash: string; filename: string; page_count: number; title: string | null; author: string | null }; quality: { low_text_pages: number[]; visual_review_pages: number[] }; sections: { page: number; heading_candidate: string }[]; topics: Record<string, Topic>; note: string };

const TOPIC_NAMES: Record<string, string> = {
  artificial_intelligence: "Intelligence artificielle",
  marketplaces: "Marketplaces",
  payments: "Paiements",
  logistics: "Logistique",
  regulation: "Réglementation",
  sustainability: "Développement durable",
  ecommerce_market: "Marché e-commerce",
};

// Vérifier cette variable avec la configuration existante de lib/api.ts.
// Le backend attend /api/discovery/pdf-studio/{inspect|map}.
const API_ROOT = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "");

async function uploadPDF(action: "inspect" | "map", file: File): Promise<Inspection | Mapping> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${API_ROOT}/api/discovery/pdf-studio/${action}`, {
    method: "POST",
    body: form,
    credentials: "include",
  });
  if (!response.ok) {
    let message = `Erreur HTTP ${response.status}`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") message = body.detail;
    } catch { /* Keep HTTP error. */ }
    throw new Error(message);
  }
  return response.json();
}

export default function PDFStudio() {
  const [file, setFile] = useState<File | null>(null);
  const [inspection, setInspection] = useState<Inspection | null>(null);
  const [mapping, setMapping] = useState<Mapping | null>(null);
  const [busy, setBusy] = useState<"inspect" | "map" | null>(null);
  const [error, setError] = useState("");
  const [expandedTopic, setExpandedTopic] = useState<string | null>(null);
  const [showPages, setShowPages] = useState(false);

  const topicEntries = useMemo(() => Object.entries(mapping?.topics || {}).sort((a, b) => b[1].page_count - a[1].page_count), [mapping]);

  function changeFile(next: File | null) {
    setFile(next);
    setInspection(null);
    setMapping(null);
    setError("");
    setExpandedTopic(null);
    setShowPages(false);
  }

  async function run(action: "inspect" | "map") {
    if (!file) { setError("Sélectionne un PDF."); return; }
    if (!file.name.toLowerCase().endsWith(".pdf")) { setError("Le fichier doit être un PDF."); return; }
    if (file.size > 30 * 1024 * 1024) { setError("Le PDF dépasse 30 Mo."); return; }
    setBusy(action);
    setError("");
    try {
      const result = await uploadPDF(action, file);
      if (action === "inspect") { setInspection(result as Inspection); setMapping(null); }
      else setMapping(result as Mapping);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur inattendue.");
    } finally { setBusy(null); }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold">PDF Studio</h1>
        <p className="mt-1 text-sm text-gray-500">V1 — inspection et cartographie, sans IA ni écriture dans BigQuery.</p>
      </div>

      <section className="rounded-xl border p-5 space-y-4">
        <label className="block text-sm font-medium" htmlFor="pdf-studio-file">Document PDF (30 Mo maximum, 300 pages maximum)</label>
        <input id="pdf-studio-file" type="file" accept=".pdf,application/pdf" className="block w-full text-sm" disabled={busy !== null} onChange={e => changeFile(e.target.files?.[0] || null)} />
        {file && <p className="text-sm text-gray-500">{file.name} — {(file.size / 1024 / 1024).toFixed(2)} Mo</p>}
        <div className="flex flex-wrap gap-3">
          <button type="button" onClick={() => void run("inspect")} disabled={!file || busy !== null} className="rounded-lg bg-black px-4 py-2 text-sm text-white disabled:opacity-40">{busy === "inspect" ? "Inspection…" : "1. Inspecter"}</button>
          <button type="button" onClick={() => void run("map")} disabled={!file || busy !== null} className="rounded-lg border px-4 py-2 text-sm disabled:opacity-40">{busy === "map" ? "Cartographie…" : "2. Cartographier"}</button>
        </div>
        {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
      </section>

      {inspection && (
        <section className="rounded-xl border p-5 space-y-3">
          <h2 className="text-lg font-semibold">Inspection</h2>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Metric label="Pages" value={inspection.page_count} />
            <Metric label="Pages avec peu de texte" value={inspection.low_text_pages.length} />
            <Metric label="Pages à revoir visuellement" value={inspection.visual_review_pages.length} />
            <Metric label="Images détectées" value={inspection.pages.reduce((sum, p) => sum + p.image_count, 0)} />
          </div>
          <p className="break-all text-xs text-gray-500">SHA-256 : {inspection.document_hash}</p>
          <button type="button" className="text-sm underline" onClick={() => setShowPages(!showPages)}>{showPages ? "Masquer" : "Afficher"} le détail des pages</button>
          {showPages && <div className="max-h-96 overflow-y-auto rounded-lg border divide-y">{inspection.pages.map(p => <div key={p.page} className="p-3 text-sm"><span className="font-semibold">Page {p.page}</span> · {p.char_count} caractères · {p.image_count} images {p.needs_visual_review && <span className="text-amber-700">· revue visuelle conseillée</span>}<p className="mt-1 whitespace-pre-wrap text-gray-500">{p.preview}</p></div>)}</div>}
        </section>
      )}

      {mapping && (
        <section className="rounded-xl border p-5 space-y-4">
          <h2 className="text-lg font-semibold">Cartographie — {mapping.document.filename}</h2>
          <p className="text-sm text-gray-500">{mapping.document.page_count} pages · {topicEntries.length} thèmes repérés · {mapping.sections.length} titres candidats</p>
          <p className="rounded-lg border p-3 text-sm">{mapping.note}</p>
          <div className="space-y-2">
            {topicEntries.map(([key, topic]) => <div key={key} className="rounded-lg border"><button type="button" className="flex w-full items-center justify-between gap-3 p-3 text-left text-sm" onClick={() => setExpandedTopic(expandedTopic === key ? null : key)}><span className="font-medium">{TOPIC_NAMES[key] || key}</span><span className="text-gray-500">{topic.page_count} pages {expandedTopic === key ? "−" : "+"}</span></button>{expandedTopic === key && <div className="border-t p-3 text-sm text-gray-600">Pages : {topic.pages.map(p => `${p.page} (${p.mentions})`).join(", ")}</div>}</div>)}
          </div>
          <details className="rounded-lg border p-3"><summary className="cursor-pointer text-sm font-medium">Titres de sections candidats ({mapping.sections.length})</summary><div className="mt-3 max-h-96 space-y-2 overflow-y-auto text-sm">{mapping.sections.map((s, index) => <div key={`${s.page}-${index}`}><span className="text-gray-500">p. {s.page}</span> — {s.heading_candidate}</div>)}</div></details>
          <p className="text-sm text-gray-500">Les thèmes sont des correspondances de mots-clés, pas encore des propositions d'articles.</p>
        </section>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return <div className="rounded-lg bg-gray-50 p-3"><div className="text-2xl font-semibold text-gray-900">{value}</div><div className="text-xs text-gray-600">{label}</div></div>;
}
