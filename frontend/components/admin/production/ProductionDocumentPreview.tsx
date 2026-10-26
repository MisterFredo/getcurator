"use client";

import { useMemo, useRef, useState } from "react";
import type { DocumentChart, DocumentPage, ProductionDocument } from "@/types/production-document";
import { productionPdfFilename } from "@/lib/production-export";
import type { PdfExportContext } from "@/lib/production-export";

const escape = (value: string) => value.replace(/[&<>"']/g, c => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
}[c] || c));
const number = (value: number) => value.toLocaleString("fr-FR", { maximumSignificantDigits: 6 });

function chartHtml(chart: DocumentChart): string {
  const points = chart.points;
  const values = points.map(p => p.value);
  const low = Math.min(0, ...values);
  const high = Math.max(0, ...values);
  const span = high - low || 1;
  let drawing = "";
  if (chart.kind === "COMPARISON") {
    const x = (value: number) => 300 + (value - low) / span * 350;
    const zero = x(0);
    drawing = `<line x1="${zero}" y1="0" x2="${zero}" y2="${points.length * 35}" stroke="#a9bcc4"/>`;
    points.forEach((point, index) => {
      const y = index * 35 + 5;
      const end = x(point.value);
      drawing += `<text x="2" y="${y + 17}" font-size="12" fill="#142333">${escape(point.label)}</text><rect x="${Math.min(zero, end)}" y="${y}" width="${Math.abs(end - zero)}" height="24" rx="2" fill="${point.value >= 0 ? "#008c80" : "#718592"}"/><text x="${point.value < 0 ? end - 7 : end + 7}" y="${y + 17}" text-anchor="${point.value < 0 ? "end" : "start"}" font-size="12" fill="#142333">${escape(number(point.value))}</text>`;
    });
    drawing += `<text x="${zero}" y="${points.length * 35 + 14}" text-anchor="middle" font-size="10" fill="#60727e">0</text>`;
  } else {
    const bottom = 128;
    const x = (index: number) => 65 + index / (points.length - 1) * 600;
    const y = (value: number) => bottom - (value - low) / span * 90;
    drawing = `<line x1="65" y1="${bottom}" x2="665" y2="${bottom}" stroke="#a9bcc4"/><polyline fill="none" stroke="#008c80" stroke-width="3" points="${points.map((p, i) => `${x(i)},${y(p.value)}`).join(" ")}"/>`;
    points.forEach((point, index) => {
      drawing += `<circle cx="${x(index)}" cy="${y(point.value)}" r="4" fill="#008c80"/><text x="${x(index)}" y="${y(point.value) - 10}" text-anchor="middle" font-size="12">${escape(number(point.value))}</text><text x="${x(index)}" y="150" text-anchor="middle" font-size="11">${escape(point.label)}</text>`;
    });
  }
  const height = chart.kind === "COMPARISON" ? points.length * 35 + 25 : 165;
  return `<div class="chart"><h3>${escape(chart.title)}</h3><p class="context">${escape(chart.measure)} · ${escape(chart.unit)} · ${escape(chart.scope)}</p><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 ${height}" style="height:${Math.min(190, height)}px" role="img" aria-label="${escape(chart.title)}">${drawing}</svg><p class="chart-note">${escape(chart.comparability_note)} · ${escape(Array.from(new Set(points.map(p => p.source_id))).join(", "))}</p></div>`;
}

const STYLES = `
:root{--ink:#142333;--teal:#008c80;--muted:#60727e;--line:#dfe8eb}*{box-sizing:border-box}html,body{margin:0;background:#e8edef;color:var(--ink);font-family:Arial,Helvetica,sans-serif}
.sheet{width:297mm;min-height:210mm;padding:12mm 17mm;margin:20px auto;background:#fbfcfc;box-shadow:0 8px 30px #14233314}
.header{display:flex;justify-content:space-between;align-items:center;padding-bottom:5mm;border-bottom:1px solid var(--line)}.brand{font-size:19px;font-weight:700}.brand span{color:var(--teal);margin-right:8px}.tagline{font-size:10px;color:var(--muted)}
.eyebrow{margin-top:6mm;color:var(--teal);font-size:10px;letter-spacing:1px;text-transform:uppercase;font-weight:700}h1{font-size:31px;line-height:1.14;letter-spacing:-.7px;margin:4mm 0 6mm}h3{font-size:12px;margin:0 0 2mm}
p,li{font-size:13px;line-height:1.55}p{margin:0 0 3mm}ul{padding-left:5mm;margin:0 0 4mm}li{margin-bottom:2mm}.bullets{display:grid;grid-template-columns:1fr 1fr;gap:4mm;list-style:none;padding:0}.bullets li{padding:4mm;background:#eef6f4;border-top:2px solid var(--teal)}
.metrics{display:flex;gap:4mm;margin-bottom:5mm;break-inside:avoid}.metric{flex:1;min-width:0;background:#eef6f4;padding:3mm;border-top:2px solid var(--teal)}.value{overflow-wrap:anywhere;font-size:29px;font-weight:700;color:var(--teal);line-height:1.15;margin-bottom:2mm}.label{overflow-wrap:anywhere;font-size:12px;line-height:1.4}.context{overflow-wrap:anywhere;font-size:10px;color:var(--muted);line-height:1.4;margin-top:2mm}.chart{margin-bottom:4mm;break-inside:avoid}.chart svg{display:block;width:100%;margin:2mm 0}.chart-note{font-size:9px;color:var(--muted)}
.takeaway{color:#142333;background:#eaf5f2;border-left:3px solid var(--teal);padding:3mm 4mm;break-inside:avoid}.notes{font-size:10px;color:var(--muted);line-height:1.4;margin-bottom:2mm}.footer{display:flex;justify-content:space-between;border-top:1px solid var(--line);padding-top:3mm;margin-top:5mm;font-size:9px;color:var(--muted)}
.cover{background:var(--ink);color:white}.cover h1{font-size:43px;margin-top:15mm;max-width:235mm}.cover .eyebrow{margin-top:24mm;color:#8ddbd0}.cover .subtitle{font-size:19px;color:#c1e5df}.cover .header,.cover .footer{border-color:#ffffff30}.cover .tagline,.cover .notes,.cover .footer{color:#c1d3d8}.cover .takeaway{background:#eaf5f2;color:#142333;border-left-color:#008c80}
.has-visual p,.has-visual li{font-size:12px}.has-visual .notes,.has-visual .context{font-size:9px}.has-visual .value{font-size:28px}.has-visual .chart-note{font-size:9px}
.bibliography{columns:2;column-gap:8mm;list-style:none;padding:0}.bibliography li{font-size:10px;line-height:1.4;break-inside:avoid;margin-bottom:3mm}.source-label{font-weight:700}.source-report{color:var(--muted)}
.sources-page .bibliography{columns:3;column-gap:6mm}.sources-page .bibliography li{margin-bottom:2mm}.sources-page p,.sources-page li{font-size:11px;line-height:1.4}.sources-page h1{margin-bottom:4mm}
.compact{padding:9mm 15mm}.compact .header{padding-bottom:3mm}.compact .eyebrow{margin-top:4mm}.compact h1{font-size:28px;margin:3mm 0 4mm}.compact p{margin-bottom:2mm}.compact .footer{margin-top:3mm;padding-top:2mm}.compact .chart svg{max-height:110px}.compact .metrics{margin-bottom:2mm}.compact .notes{margin-bottom:1mm}.compact .takeaway{padding:2mm 3mm}
.complement-label{font-size:10px!important;color:var(--muted);margin-bottom:2mm}.has-mixed .chart{margin-bottom:2mm}.has-mixed .chart svg{max-height:135px}.has-mixed .metrics{margin-bottom:3mm}.has-mixed .metric{padding:2mm 3mm}.has-mixed .value{font-size:24px}.has-mixed .context{margin-top:1mm}
@page{size:A4 landscape;margin:0}@media print{html,body{background:white}.sheet{margin:0;box-shadow:none;break-after:page;page-break-after:always}.sheet:last-child{break-after:auto;page-break-after:auto}*{-webkit-print-color-adjust:exact;print-color-adjust:exact}p{orphans:3;widows:3}h1,h3{break-after:avoid}}
`;

export function buildDocumentHtml(document: ProductionDocument, filename?: string | null, language: "fr" | "en" = "fr"): string {
  const known = new Map(document.sources.map(source => [source.id, source]));
  const used = new Set(document.pages.flatMap(page => page.source_ids));
  const groups = new Map<string, { ids: string[]; label: string; version: number }>();
  for (const source of document.sources.filter(item => used.has(item.id))) {
    const key = `${source.report_id}:${source.report_version}:${source.content_id || "report"}`;
    const existing = groups.get(key);
    if (existing) existing.ids.push(source.id);
    else groups.set(key, { ids: [source.id], label: source.label, version: source.report_version });
  }
  const bibliographyEntries = Array.from(groups.values());
  // Bibliography is an appendix, never stacked below the full method page.
  // Bounded groups keep long titles and many citations readable at print size.
  const chunks: typeof bibliographyEntries[] = [];
  let chunk: typeof bibliographyEntries = [];
  let weight = 0;
  for (const entry of bibliographyEntries) {
    const size = entry.label.length + entry.ids.join(" ").length + 70;
    if (chunk.length && (chunk.length >= 15 || weight + size > 2200)) {
      chunks.push(chunk); chunk = []; weight = 0;
    }
    chunk.push(entry); weight += size;
  }
  if (chunk.length) chunks.push(chunk);
  const composed: { page: DocumentPage; entries: typeof bibliographyEntries }[] =
    document.pages.map(page => ({ page, entries: [] }));
  chunks.forEach((entries, index) => composed.push({
    page: {
      page_id: `bibliography-${index + 1}`, layout: "SOURCES",
      title: "Références documentaires", eyebrow: `Bibliographie · ${index + 1}/${chunks.length}`,
      paragraphs: [], bullets: [], metrics: [], chart: null, takeaway: "",
      cautions: [], source_ids: [],
    }, entries,
  }));
  return `<!doctype html><html lang="${language}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escape(filename ? filename.replace(/\.pdf$/i, "") : document.title)}</title><style>${STYLES}</style></head><body>${composed.map(({ page, entries }, index: number) => {
    const cover = page.layout === "COVER";
    const sources = page.layout === "SOURCES";
    const chart = page.chart ? chartHtml(page.chart) : "";
    const metrics = page.metrics.length ? `${page.chart ? '<p class="complement-label">Indicateurs complémentaires — hors série graphique</p>' : ""}<div class="metrics">${page.metrics.map(metric => `<div class="metric"><div class="value">${escape(metric.display_value)}</div><div class="label">${escape(metric.label)}</div><div class="context">${escape(metric.context)} [${escape(metric.source_id)}]</div></div>`).join("")}</div>` : "";
    const visual = chart + metrics;
    const paragraphs = page.paragraphs.map(text => `<p>${escape(text)}</p>`).join("");
    const bullets = page.bullets.length ? `<ul class="${page.layout === "SUMMARY" || page.layout === "IMPLICATIONS" ? "bullets" : ""}">${page.bullets.map(text => `<li>${escape(text)}</li>`).join("")}</ul>` : "";
    const bibliography = entries.length ? `<ul class="bibliography">${entries.map(source => `<li><span class="source-label">${source.ids.map(id => `[${escape(id)}]`).join(" ")} ${escape(source.label)}</span><br><span class="source-report">Rapport sauvegardé · version ${source.version}</span></li>`).join("")}</ul>` : "";
    const citations = page.source_ids.filter(id => known.has(id)).map(id => `[${escape(id)}]`).join(" ");
    return `<section class="sheet ${cover ? "cover" : ""} ${sources ? "sources-page" : ""} ${visual ? "has-visual" : ""} ${page.chart && page.metrics.length ? "has-mixed" : ""}" data-page="${index + 1}"><div class="header"><div class="brand"><span>✦</span>GetCurator</div><div class="tagline">Bringing clarity to complexity</div></div><div class="eyebrow">${escape(page.eyebrow || (cover ? "Rapport autonome" : "Analyse & perspectives"))}</div><h1>${escape(cover ? document.title : page.title)}</h1>${cover ? `<p class="subtitle">${escape(document.subtitle)}</p>` : ""}${visual}${paragraphs}${bullets}${page.takeaway ? `<p class="takeaway" style="color:#142333;background-color:#eaf5f2">${escape(page.takeaway)}</p>` : ""}${bibliography}${citations && !sources ? `<p class="notes">Sources : ${citations}</p>` : ""}${page.cautions.map(caution => `<p class="notes">${escape(caution)}</p>`).join("")}<div class="footer"><span>GETCURATOR · RAPPORT AUTONOME</span><span>${String(index + 1).padStart(2, "0")}</span></div></section>`;
  }).join("")}</body></html>`;
}

export default function ProductionDocumentPreview({ document, exportContext }: { document: ProductionDocument; exportContext?: PdfExportContext }) {
  const [naming, setNaming] = useState<PdfExportContext>(() => exportContext || {
    subject: document.title, language: "fr", periodStart: "", periodEnd: "",
  });
  const filename = productionPdfFilename(naming);
  const frame = useRef<HTMLIFrameElement>(null);
  const [overflow, setOverflow] = useState<number[]>([]);
  const [checkedHtml, setCheckedHtml] = useState("");
  const [printedPages, setPrintedPages] = useState(document.pages.length);
  const html = useMemo(() => buildDocumentHtml(document, filename, naming.language), [document, filename, naming.language]);
  const printable = checkedHtml === html && Boolean(filename);

  function checkLayout() {
    const sheets = frame.current?.contentDocument?.querySelectorAll<HTMLElement>(".sheet");
    if (!sheets) return;
    setPrintedPages(sheets.length);
    const exceeds = (sheet: HTMLElement) => {
      const box = sheet.getBoundingClientRect();
      return box.height > box.width * 210 / 297 + 3 || sheet.scrollWidth > sheet.clientWidth + 2;
    };
    // Try a defined, readable compact composition before showing a warning.
    // No clipping, hidden content, or arbitrary scaling is used.
    Array.from(sheets).forEach(sheet => {
      sheet.classList.remove("compact");
      if (exceeds(sheet)) sheet.classList.add("compact");
    });
    const exceeded = Array.from(sheets).filter(exceeds).map(sheet => Number(sheet.dataset.page));
    setOverflow(exceeded);
    setCheckedHtml(html);
  }

  function printDocument() {
    const child = frame.current?.contentWindow;
    if (!child || !filename || !printable) return;
    const previousTitle = window.document.title;
    const printTitle = filename.replace(/\.pdf$/i, "");
    const restore = () => {
      window.document.title = previousTitle;
      window.removeEventListener("afterprint", restore);
      child.removeEventListener("afterprint", restore);
    };
    window.document.title = printTitle;
    child.document.title = printTitle;
    window.addEventListener("afterprint", restore);
    child.addEventListener("afterprint", restore);
    try { child.focus(); child.print(); } catch (error) { restore(); throw error; }
  }

  return <section className="rounded-xl border bg-white p-6 space-y-4">
    <h2 className="text-lg font-semibold">Rapport GetCurator — compositions génériques</h2>
    <p className="text-sm text-gray-600">{document.pages.length} pages éditoriales{checkedHtml === html && printedPages > document.pages.length ? ` + ${printedPages - document.pages.length} page(s) de bibliographie` : ""} · A4 paysage · modèle {document.template}. Les contrôles de structure et de provenance ne remplacent pas la relecture des interprétations.</p>
    {overflow.length > 0 && <p role="alert" className="rounded bg-amber-50 p-3 text-amber-900">Débordement sur les pages {overflow.join(", ")}. Export autorisé : vérifiez le résultat dans l’aperçu d’impression.</p>}
    <fieldset className="grid gap-3 rounded-lg border p-4 sm:grid-cols-2">
      <legend className="px-1 text-sm font-medium">Nom du fichier PDF</legend>
      <label className="text-sm">Sujet<input className="mt-1 w-full rounded border px-3 py-2" value={naming.subject} maxLength={250} onChange={e => setNaming(current => ({ ...current, subject: e.target.value }))} /></label>
      <label className="text-sm">Langue<select className="mt-1 w-full rounded border px-3 py-2" value={naming.language} onChange={e => setNaming(current => ({ ...current, language: e.target.value as "fr" | "en" }))}><option value="fr">FR</option><option value="en">EN</option></select></label>
      <label className="text-sm">Début de période<input type="date" className="mt-1 w-full rounded border px-3 py-2" value={naming.periodStart} onChange={e => setNaming(current => ({ ...current, periodStart: e.target.value }))} /></label>
      <label className="text-sm">Fin de période<input type="date" className="mt-1 w-full rounded border px-3 py-2" value={naming.periodEnd} onChange={e => setNaming(current => ({ ...current, periodEnd: e.target.value }))} /></label>
      <p className="break-all text-xs text-slate-600 sm:col-span-2">{filename || "Renseignez un sujet et une période valide pour nommer le PDF."}</p>
    </fieldset>
    <button type="button" disabled={!printable} className="rounded bg-ratecard-blue px-4 py-2 text-white disabled:opacity-50" onClick={printDocument}>Imprimer / Enregistrer en PDF</button>
    <p className="text-xs text-gray-500">Choisir A4 paysage, arrière-plans activés et en-têtes/pieds de page du navigateur désactivés. Vérifier l’aperçu d’impression.</p>
    <iframe ref={frame} title="Document GetCurator" srcDoc={html} onLoad={checkLayout} sandbox="allow-same-origin allow-modals" className="h-[800px] w-full rounded border" />
    <details><summary className="cursor-pointer">Contrôle éditorial et traçabilité — hors impression</summary>
      <ul className="mt-3 list-disc pl-5 text-sm">{document.review_notes.map((note, i) => <li key={i}>{note}</li>)}</ul>
      <pre className="mt-3 whitespace-pre-wrap break-words text-xs">{JSON.stringify(document.sources, null, 2)}</pre>
    </details>
  </section>;
}
