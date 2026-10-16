"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { AUDIO_VISUAL_STYLES, REVIEWED_AUDIO_SHA256, audioPageVisual } from "./AudioReportVisuals";

/* Self-contained preview. No raw model HTML is executed. */
type Props = {
  markdown: string;
  completed: boolean;
};

type ReportPage = { number: number; title: string; body: string };

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[char] || char));
}

function inline(value: string): string {
  // Only explicitly supported Markdown constructs are rendered.
  // Raw HTML, images and scripts are always escaped.
  const pattern = /(\*\*([^*\n]+)\*\*|`([^`\n]+)`|\[([^\]\n]+)\]\((https?:\/\/[^\s)]+)\)|\*([^*\n]+)\*)/g;
  let output = "";
  let cursor = 0;
  for (const match of value.matchAll(pattern)) {
    const index = match.index ?? 0;
    output += escapeHtml(value.slice(cursor, index));
    if (match[2]) output += `<strong>${escapeHtml(match[2])}</strong>`;
    else if (match[3]) output += `<code>${escapeHtml(match[3])}</code>`;
    else if (match[6]) output += `<em>${escapeHtml(match[6])}</em>`;
    else output += `<a href="${escapeHtml(match[5])}" target="_blank" rel="noopener noreferrer">${escapeHtml(match[4])}</a>`;
    cursor = index + match[0].length;
  }
  return output + escapeHtml(value.slice(cursor));
}

function blocks(value: string, compactSources = false): string {
  if (compactSources) {
    const months: Record<string, string> = { July: "Juillet", August: "Août", September: "Septembre" };
    value = value.replace(
      /— Rapport mensuel : \*\*Developments in Audio & Podcast during (July|August|September) (\d{4})\*\*/g,
      (_, month: string, year: string) => `— **${months[month]} ${year}**`,
    ).replace(/— Source disponible : (https?:\/\/[^\s]+)/g, "— [Consulter la source]($1)");
  }
  return value.replace(/\n(?=\*\*(?:Sources?|Limites|Périmètre|Lecture recommandée|Implication)\s*:)/g, "\n\n").trim().split(/\n\s*\n/).filter(Boolean).map(block => {
    const lines = block.trim().split("\n");
    if (lines.every(line => /^\s*[-*] /.test(line))) {
      return `<ul>${lines.map(line => `<li>${inline(line.replace(/^\s*[-*] /, ""))}</li>`).join("")}</ul>`;
    }
    if (/^#{1,6}\s/.test(block)) {
      return `<h3>${inline(block.replace(/^#{1,6}\s+/, ""))}</h3>`;
    }
    const isImplication = /^\*\*Implication\s*:/i.test(block);
    const isNote = /^\*\*(Sources?|Limites|Périmètre|Lecture recommandée)\s*:/i.test(block);
    return `<p class="${isImplication ? "implication" : isNote ? "note" : ""}">${inline(lines.join(" "))}</p>`;
  }).join("\n");
}

function parseReport(markdown: string) {
  const normalized = markdown.replace(/\r\n/g, "\n");
  const registerAt = normalized.search(/^#\s+Registre de contrôle\b/m);
  const published = (registerAt >= 0 ? normalized.slice(0, registerAt) : normalized)
    .replace(/^FIN_DU_RAPPORT\s*$/gm, "").trim();
  const register = registerAt >= 0
    ? normalized.slice(registerAt).replace(/^FIN_DU_RAPPORT\s*$/gm, "").trim()
    : "";
  const title = published.match(/^#\s+(.+)$/m)?.[1] || "Rapport GetCurator";
  const headers = Array.from(published.matchAll(/^##\s+Page\s+(\d+)\s*[—–-]\s*(.+)$/gm));
  const pages: ReportPage[] = headers.map((header, index) => ({
    number: Number(header[1]),
    title: header[2].trim(),
    body: published.slice(
      (header.index ?? 0) + header[0].length,
      headers[index + 1]?.index ?? published.length,
    ).replace(/(?:\n\s*---\s*)+$/g, "").trim(),
  }));
  const contiguous = pages.every((page, index) => page.number === index + 1);
  return { title, pages, register, contiguous };
}

const PRINT_STYLES = `
:root{--ink:#142333;--teal:#008c80;--line:#dfe8eb;--muted:#60727e}
*{box-sizing:border-box}html,body{margin:0;background:#e8edef;color:var(--ink);font-family:Arial,Helvetica,sans-serif}
.sheet{width:297mm;min-height:210mm;margin:20px auto;background:#fbfcfc;padding:13mm 17mm 12mm;position:relative;box-shadow:0 8px 30px #14233314}
.brand{font-size:19px;font-weight:700;letter-spacing:-.6px;display:flex;align-items:center;gap:9px}.mark{color:var(--teal);font-size:25px;font-weight:400}
.header{display:flex;justify-content:space-between;align-items:center;padding-bottom:6mm;border-bottom:1px solid var(--line)}
.tagline{font-size:10px;color:var(--muted)}.eyebrow{font-size:10px;font-weight:700;letter-spacing:1.4px;color:var(--teal);text-transform:uppercase;margin-top:8mm}
h1{font-size:34px;line-height:1.12;letter-spacing:-1px;margin:5mm 0 7mm;max-width:245mm}h3{font-size:14px;line-height:1.3;margin:5mm 0 3mm}
.copy{font-size:14px;line-height:1.58;max-width:250mm}.copy p{margin:0 0 4mm}.copy strong{font-weight:700}.copy ul{padding-left:5mm;margin:0 0 4mm}.copy li{margin-bottom:2mm}
.implication{border-left:3px solid var(--teal);background:#eaf5f2;padding:4mm 5mm;font-size:14px;break-inside:avoid}
.copy .note{font-size:10.5px;line-height:1.45;color:var(--muted);margin-bottom:2mm}
a{color:var(--teal);overflow-wrap:anywhere}code{font-size:.9em;overflow-wrap:anywhere}
.footer{display:flex;justify-content:space-between;margin-top:7mm;padding-top:3mm;border-top:1px solid var(--line);font-size:9px;color:var(--muted);letter-spacing:.6px}
.cover{background:var(--ink);color:white;min-height:210mm;display:flex;flex-direction:column}.cover .header{border-color:#ffffff25}.cover .brand{color:white}.cover .tagline{color:#c5d9dc}
.cover .eyebrow{margin-top:25mm;color:#8ddbd0}.cover h1{font-size:43px;max-width:235mm;margin:7mm 0 10mm}.cover .copy{max-width:225mm;color:#dfebed;font-size:15px}.cover .note{color:#b7ccd0}.cover .footer{margin-top:auto;padding-top:5mm;border-color:#ffffff25;color:#b7ccd0}
.sources .copy{font-size:10px;line-height:1.4}.sources .copy li{break-inside:avoid;margin-bottom:3mm}.sources h1{font-size:29px}.sources .copy ul{columns:2;column-gap:10mm;list-style:none;padding:0}
@page{size:A4 landscape;margin:0}
@media print{html,body{background:white}.sheet{margin:0;box-shadow:none;break-after:page;page-break-after:always;min-height:210mm}.sheet:last-child{break-after:auto;page-break-after:auto}*{-webkit-print-color-adjust:exact;print-color-adjust:exact}.sources{min-height:210mm}.copy p{orphans:3;widows:3}h1,h3{break-after:avoid}}
`;

function buildHtml(title: string, pages: ReportPage[], audioVisuals = false): string {
  return `<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escapeHtml(title)}</title><style>${PRINT_STYLES}${AUDIO_VISUAL_STYLES}</style></head><body>${pages.map((page, index) => {
    const cover = index === 0;
    const sources = index === pages.length - 1 && (/sources|méthode|périmètre/i.test(page.title) || /Références utilisées|\*\*\[S\d+\]\*\*/.test(page.body));
    const visual = audioVisuals ? audioPageVisual(page.number) : "";
    return `<section class="sheet ${visual ? "has-visual" : ""} ${cover ? "cover" : sources ? "sources" : ""}"><div class="header"><div class="brand"><span class="mark">✦</span>GetCurator</div><span class="tagline">Bringing clarity to complexity</span></div><div class="eyebrow">${cover ? "Rapport autonome" : "Analyse & perspectives"}</div><h1>${inline(cover ? title : page.title)}</h1>${visual}<div class="copy">${blocks(page.body, sources)}</div><div class="footer"><span>GETCURATOR · RAPPORT</span><span>${String(page.number).padStart(2, "0")}</span></div></section>`;
  }).join("\n")}</body></html>`;
}

export default function ProductionReportPreview({ markdown, completed }: Props) {
  const frame = useRef<HTMLIFrameElement>(null);
  const [verifiedMarkdown, setVerifiedMarkdown] = useState("");
  useEffect(() => {
    let cancelled = false;
    const normalized = markdown.replace(/\r\n/g, "\n").trim();
    if (!window.crypto?.subtle) return;
    void window.crypto.subtle.digest("SHA-256", new TextEncoder().encode(normalized))
      .then(buffer => {
        const hash = Array.from(new Uint8Array(buffer)).map(value => value.toString(16).padStart(2, "0")).join("");
        if (!cancelled) setVerifiedMarkdown(hash === REVIEWED_AUDIO_SHA256 ? markdown : "");
      }).catch(() => { if (!cancelled) setVerifiedMarkdown(""); });
    return () => { cancelled = true; };
  }, [markdown]);
  const audioVisuals = verifiedMarkdown === markdown && markdown.length > 0;
  const report = useMemo(() => parseReport(markdown), [markdown]);
  const html = useMemo(() => buildHtml(report.title, report.pages, audioVisuals), [report, audioVisuals]);
  const completeMarker = /^FIN_DU_RAPPORT\s*$/m.test(markdown);
  const exportable = completed && completeMarker && report.contiguous && report.pages.length > 0;

  function saveHtml() {
    const url = URL.createObjectURL(new Blob([html], { type: "text/html;charset=utf-8" }));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "rapport-getcurator.html";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  if (!report.pages.length) return <p role="alert">Aucune page reconnue. Le rapport doit contenir des titres « ## Page 1 — … ».</p>;

  return (
    <section className="space-y-4 rounded-xl border bg-white p-6">
      <h2 className="text-lg font-semibold">Aperçu du rapport GetCurator</h2>
      <p className="text-sm text-gray-600">{report.pages.length} pages éditoriales · A4 paysage. Le registre de contrôle est séparé du document imprimé. La pagination physique dépend de la longueur du contenu.</p>
      <p className="text-sm text-gray-600">{audioVisuals ? "Visuels du pilote Audio activés : cette version exacte du rapport a une configuration éditoriale dédiée." : "Aperçu typographique : aucune configuration de chiffres vérifiée pour cette version du texte."}</p>
      {!exportable && <p role="alert" className="rounded bg-amber-50 p-3 text-sm text-amber-800">Export désactivé : vérifier que la génération est terminée, que la ligne FIN_DU_RAPPORT est présente et que les numéros de page se suivent depuis 1.</p>}
      <div className="flex flex-wrap gap-3">
        <button type="button" disabled={!exportable} className="rounded bg-ratecard-blue px-4 py-2 text-white disabled:opacity-50" onClick={() => { frame.current?.contentWindow?.focus(); frame.current?.contentWindow?.print(); }}>Imprimer / Enregistrer en PDF</button>
        <button type="button" disabled={!exportable} className="rounded border px-4 py-2 disabled:opacity-50" onClick={saveHtml}>Télécharger la version HTML</button>
      </div>
      <p className="text-xs text-gray-500">Dans la fenêtre d’impression : choisir « Enregistrer au format PDF », A4 paysage, activer les arrière-plans et désactiver les en-têtes/pieds de page du navigateur. Vérifie l’aperçu avant d’enregistrer.</p>
      <iframe ref={frame} title="Rapport GetCurator" srcDoc={html} sandbox="allow-same-origin allow-modals allow-popups" className="h-[800px] w-full rounded border bg-gray-100" />
      {report.register && <details><summary className="cursor-pointer font-medium">Registre de contrôle — non imprimé</summary><pre className="mt-3 whitespace-pre-wrap break-words text-xs leading-6">{report.register}</pre></details>}
    </section>
  );
}
