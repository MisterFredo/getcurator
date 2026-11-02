import { buildDocumentHtml } from "@/components/admin/production/ProductionDocumentPreview";
import type { RenderableDocument } from "@/components/admin/production/ProductionDocumentPreview";

const TOUCH_STYLES = `
.sheet{height:210mm;min-height:210mm;padding:11mm 15mm;display:flex;flex-direction:column;overflow:visible}
.header{flex:none;padding-bottom:4mm}.brand{font-size:20px}.tagline{font-size:11px}
.eyebrow{flex:none;margin-top:5mm;font-size:11px}
h1{flex:none;font-size:30px;line-height:1.14;margin:3mm 0 5mm;letter-spacing:-.5px;overflow-wrap:anywhere}
.touch-body{flex:1;min-height:0}.touch-body>ul:not(.bibliography){display:grid;grid-template-columns:1fr 1fr;align-content:start;gap:4mm;list-style:none;padding:0;margin:0}
.touch-body>ul:not(.bibliography)>li{font-size:18px;line-height:1.4;white-space:pre-line;margin:0;padding:4mm;background:#eef5f4;border-top:2px solid #008c80;overflow-wrap:anywhere;break-inside:avoid}
.touch-body>ul>li.touch-wide{grid-column:1/-1}
.touch-body>p{font-size:18px;line-height:1.45;white-space:pre-line}
.touch-body>.notes{font-size:11px;line-height:1.35;margin-top:3mm}
.footer{flex:none;margin-top:4mm;padding-top:3mm;font-size:10px}
.cover h1{font-size:44px;line-height:1.1;max-width:none;margin:6mm 0}
.cover .eyebrow{margin-top:10mm}.cover .subtitle{font-size:23px;margin-bottom:6mm}
.cover .cover-introduction{display:block;margin:0;padding:5mm 6mm}.cover .cover-introduction p{font-size:18px;line-height:1.5}
.cover .footer{margin-top:4mm}.touch-body .bibliography{display:grid;grid-template-columns:1fr 1fr;columns:auto;gap:4mm 7mm;margin:0}
.touch-body .bibliography li{font-size:12px;line-height:1.4;padding-bottom:3mm;border-bottom:1px solid #dfe8eb;margin:0;overflow-wrap:anywhere}
.touch-body .source-report{font-size:10px}
@media print{.sheet{height:210mm;margin:0;break-inside:avoid}.touch-body{min-height:0}}
`;

export function buildTouchPresentationHtml(document: RenderableDocument, filename: string, language: "fr" | "en") {
  // Bibliography labels refer to articles. Keep the full evidence registry on
  // the input document, but use one display number per article in the PDF.
  const referenceMap = new Map<string, string>();
  const articleIds = new Map<string, string>();
  const displaySources: RenderableDocument["sources"] = [];
  for (const source of document.sources) {
    const key = source.content_id || source.id;
    let id = articleIds.get(key);
    if (!id) { id = String(articleIds.size + 1); articleIds.set(key, id); displaySources.push({ ...source, id }); }
    referenceMap.set(source.id, id);
  }
  const refs = (ids: string[]) => Array.from(new Set(ids.map(id => referenceMap.get(id) || id)));
  const display = { ...document, sources: displaySources, pages: document.pages.map(page => ({ ...page,
    source_ids: refs(page.source_ids),
    bullets: page.bullets.map(text => text.replace(/\[(S\d+(?:, S\d+)*)\]/g,
      (_, ids: string) => `[${refs(ids.split(", ")).join(", ")}]`)),
  })) };
  return buildDocumentHtml(display, filename, language, true)
    .replace("</style>", TOUCH_STYLES + "</style>");
}

export type TouchLayoutResult = { count: number; overflow: number[] };

// Executed by the parent in the same-origin iframe, never as an iframe script.
export function paginateTouchPresentation(doc: Document, language: "fr" | "en"): TouchLayoutResult {
  const fr = language === "fr";
  const originals = Array.from(doc.querySelectorAll<HTMLElement>(".sheet"));
  const tolerance = 2;
  function wrap(sheet: HTMLElement) {
    const body = doc.createElement("div"); body.className = "touch-body";
    const footer = sheet.querySelector<HTMLElement>(".footer")!;
    for (const child of Array.from(sheet.children)) {
      if (!child.matches(".header,.eyebrow,h1,.subtitle,.footer")) body.appendChild(child);
    }
    sheet.insertBefore(body, footer);
    return body;
  }
  function fits(body: HTMLElement) {
    return body.scrollHeight <= body.clientHeight + tolerance && body.scrollWidth <= body.clientWidth + tolerance;
  }
  for (const original of originals) {
    if (original.querySelector(".touch-body")) continue; // idempotent
    const body = wrap(original);
    const heading = original.querySelector("h1")!;
    if (heading.getBoundingClientRect().height > 100) heading.style.fontSize = "25px";
    if (original.classList.contains("cover")) continue;
    const list = body.querySelector<HTMLUListElement>(":scope > ul");
    if (!list) continue;
    const items = Array.from(list.children) as HTMLElement[];
    const tail = Array.from(body.children).filter(child => child !== list);
    tail.forEach(child => child.remove());
    list.replaceChildren();
    let current: HTMLElement = original;
    let currentBody: HTMLElement = body;
    let currentList: HTMLUListElement = list;
    let continuation = 1;
    const baseTitle = heading.textContent || "";
    const next = () => {
      const sheet = original.cloneNode(true) as HTMLElement;
      const newBody = sheet.querySelector<HTMLElement>(".touch-body")!;
      newBody.replaceChildren();
      const newList = currentList.cloneNode(false) as HTMLUListElement; newBody.appendChild(newList);
      sheet.querySelector("h1")!.textContent = baseTitle;
      const eyebrow = sheet.querySelector(".eyebrow");
      if (eyebrow) eyebrow.textContent = `${fr ? "Suite" : "Continued"} · ${++continuation}`;
      current.after(sheet); current = sheet; currentBody = newBody; currentList = newList;
    };
    for (let item of items) {
      if ((item.textContent || "").length > 650) item.classList.add("touch-wide");
      currentList.appendChild(item);
      if (!fits(currentBody) && currentList.children.length > 1) { item.remove(); next(); currentList.appendChild(item); }
      // Very long notes are split at whitespace boundaries only when one note
      // cannot fit a whole page. Every word, number and qualifier is retained.
      if (!fits(currentBody) && currentList.children.length === 1) {
        const words: string[] = (item.textContent || "").match(/\S+\s*/g) || [];
        let remaining = words;
        while (remaining.length > 1 && !fits(currentBody)) {
          item.classList.add("touch-wide");
          let low = 1, high = remaining.length - 1, best = 0;
          while (low <= high) {
            const mid = Math.floor((low + high) / 2);
            item.textContent = remaining.slice(0, mid).join("");
            if (fits(currentBody)) { best = mid; low = mid + 1; } else high = mid - 1;
          }
          if (!best) { item.textContent = remaining.join(""); break; }
          item.textContent = remaining.slice(0, best).join("");
          remaining = remaining.slice(best);
          const rest = item.cloneNode(false) as HTMLElement;
          next(); currentList.appendChild(rest); item = rest; item.textContent = remaining.join("");
        }
      }
    }
    // Article references already appear alongside every bullet. Avoid a second
    // list of the same citations consuming space at the bottom of each page.
    for (const element of tail) if (!element.classList.contains("notes")) currentBody.appendChild(element);
  }
  const sheets = Array.from(doc.querySelectorAll<HTMLElement>(".sheet"));
  const overflow: number[] = [];
  sheets.forEach((sheet, index) => {
    sheet.dataset.page = String(index + 1);
    const footer = sheet.querySelector(".footer span:last-child");
    if (footer) footer.textContent = `${String(index + 1).padStart(2, "0")} / ${sheets.length}`;
    const body = sheet.querySelector<HTMLElement>(".touch-body");
    if (body && !fits(body)) overflow.push(index + 1);
    if (sheet.scrollWidth > sheet.clientWidth + tolerance || sheet.scrollHeight > sheet.clientHeight + tolerance)
      if (!overflow.includes(index + 1)) overflow.push(index + 1);
  });
  return { count: sheets.length, overflow };
}
