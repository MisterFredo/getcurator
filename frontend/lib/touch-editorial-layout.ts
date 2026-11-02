import { buildDocumentHtml } from "@/components/admin/production/ProductionDocumentPreview";
import type { ProductionDocument } from "@/types/production-document";
const STYLES = `
.sheet{height:210mm;min-height:210mm;display:flex;flex-direction:column;padding:11mm 15mm;overflow:visible}
.header,.eyebrow,h1,.subtitle,.footer{flex:none}.header{padding-bottom:4mm}
.eyebrow{margin-top:4mm;font-size:11px}h1{font-size:30px;line-height:1.15;margin:3mm 0 5mm;overflow-wrap:anywhere}
.editorial-body{flex:1;min-height:0}.editorial-body p,.editorial-body li{font-size:17px;line-height:1.45;overflow-wrap:anywhere}
.editorial-body>p{margin-bottom:4mm}.editorial-body ul{margin-bottom:4mm}.editorial-body .bullets{gap:4mm}
.editorial-body .bullets li{padding:4mm}.editorial-body .takeaway{font-size:17px;margin-top:4mm}
.editorial-body .chart .context,.editorial-body .chart .chart-note{font-size:11px;line-height:1.4}.editorial-body .chart h3{font-size:14px;line-height:1.3}
.editorial-body .notes{font-size:11px;line-height:1.35;margin-bottom:2mm}.footer{margin-top:4mm;font-size:10px;padding-top:3mm}
.cover h1{font-size:42px}.cover .eyebrow{margin-top:8mm}.cover .subtitle{font-size:21px}.cover .cover-introduction p{font-size:17px}
.cover .footer{margin-top:4mm}.editorial-body .bibliography{columns:2}.editorial-body .bibliography li{font-size:12px;line-height:1.4}
.sheet.compact .editorial-body p,.sheet.compact .editorial-body li{font-size:15px;line-height:1.35}
.sheet.compact h1{font-size:27px}.sheet.compact .editorial-body .chart .context,.editorial-body .chart .chart-note{font-size:11px;line-height:1.4}.editorial-body .chart h3{font-size:14px;line-height:1.3}
.editorial-body .notes{font-size:10px}
@media print{.sheet{height:210mm;break-inside:avoid;margin:0}.editorial-body{min-height:0}}
`;
export function buildTouchEditorialHtml(document: ProductionDocument, filename: string, language: "fr" | "en") {
  return buildDocumentHtml(document,filename,language,true).replace("</style>",STYLES+"</style>");
}
export function checkTouchEditorialLayout(doc: Document) {
  const fr = doc.documentElement.lang !== "en";
  const originals = Array.from(doc.querySelectorAll<HTMLElement>(".sheet"));
  const wrap = (sheet: HTMLElement): HTMLElement => {
    const existing = sheet.querySelector<HTMLElement>(".editorial-body");
    if (existing) return existing;
    const body = doc.createElement("div");
    body.className = "editorial-body";
    const footer = sheet.querySelector<HTMLElement>(".footer")!;
    for (const child of Array.from(sheet.children)) {
      if (!child.matches(".header,.eyebrow,h1,.subtitle,.footer")) body.appendChild(child);
    }
    sheet.insertBefore(body, footer);
    return body;
  };
  const fits = (sheet: HTMLElement, body: HTMLElement) =>
    body.scrollHeight <= body.clientHeight + 2
    && body.scrollWidth <= body.clientWidth + 2
    && sheet.scrollHeight <= sheet.clientHeight + 2
    && sheet.scrollWidth <= sheet.clientWidth + 2;
  const compactIfNeeded = (sheet: HTMLElement, body: HTMLElement) => {
    sheet.classList.remove("compact");
    if (!fits(sheet, body)) sheet.classList.add("compact");
  };

  for (const sheet of originals) {
    const body = wrap(sheet);
    compactIfNeeded(sheet, body);
    const chart = body.querySelector<HTMLElement>(":scope > .chart");
    // Split only an overflowing chart composition, once. No text is rewritten,
    // no source data changes, and the chart keeps its comparability note.
    if (!fits(sheet, body) && chart && !sheet.dataset.chartContinuation) {
      const content = Array.from(body.children);
      const introduction = content.find(child => child.tagName === "P"
        && !child.classList.contains("notes") && !child.classList.contains("takeaway"));
      const details = content.filter(child => child !== chart && child !== introduction);
      if (details.length) {
        const continuation = sheet.cloneNode(true) as HTMLElement;
        const continuationBody = continuation.querySelector<HTMLElement>(".editorial-body")!;
        continuationBody.replaceChildren();
        for (const child of details) continuationBody.appendChild(child);
        // Repeat only the citation line so each printed page is traceable.
        const references = details.find(child => child.classList.contains("notes")
          && (child.textContent || "").startsWith("Sources :"));
        if (references) body.appendChild(references.cloneNode(true));
        sheet.dataset.chartContinuation = "chart";
        continuation.dataset.chartContinuation = "details";
        continuation.classList.remove("has-visual", "has-mixed");
        const firstEyebrow = sheet.querySelector(".eyebrow");
        const nextEyebrow = continuation.querySelector(".eyebrow");
        if (firstEyebrow) firstEyebrow.textContent = fr ? "Graphique et contexte · 1/2" : "Chart and context · 1/2";
        if (nextEyebrow) nextEyebrow.textContent = fr ? "Analyse et limites · 2/2" : "Analysis and limitations · 2/2";
        sheet.after(continuation);
        compactIfNeeded(sheet, body);
        compactIfNeeded(continuation, continuationBody);
      }
    }
  }
  const sheets = Array.from(doc.querySelectorAll<HTMLElement>(".sheet"));
  const overflow: number[] = [];
  sheets.forEach((sheet, index) => {
    if (!fits(sheet, wrap(sheet))) overflow.push(index + 1);
    sheet.dataset.page = String(index + 1);
    const label = sheet.querySelector(".footer span:last-child");
    if (label) label.textContent = `${index + 1} / ${sheets.length}`;
  });
  return { count: sheets.length, overflow };
}
