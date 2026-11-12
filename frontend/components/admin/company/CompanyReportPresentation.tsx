"use client";

import { useMemo, useRef, useState } from "react";
import type { RenderableDocument } from "@/components/admin/production/ProductionDocumentPreview";
import { buildTouchPresentationHtml, paginateTouchPresentation } from "@/lib/touch-presentation-layout";
import { productionPdfFilename } from "@/lib/production-export";

type Source = {
  id: string;
  title: string | null;
  url: string | null;
  source_at: string;
  source_kind: string;
  date_kind: string;
};
type Fact = {
  title: string;
  summary: string;
  primary_id: string;
  support_ids: string[];
  relay_ids: string[];
  contribution: string;
  contribution_ids: string[];
};
type Report = {
  company_name: string;
  month: string;
  limited_sources: number;
  sections: Record<"facts" | "site_changes" | "mentions", Fact[]>;
  sources: Source[];
};

const blocks = [
  { id: "facts", title: "Faits du mois" },
  { id: "site_changes", title: "Évolutions observées sur le site" },
  { id: "mentions", title: "Mentions externes" },
] as const;
const sourceKinds: Record<string, string> = {
  LINKEDIN_CORPORATE: "LinkedIn corporate",
  LINKEDIN_EMPLOYEE: "LinkedIn · veille salariés",
  SITE_PUBLICATION: "Publication du site corporate",
  SITE_CHANGE: "Page surveillée",
  MENTION: "Mention externe",
};
const dateKinds: Record<string, string> = {
  PUBLICATION: "Publié", OBSERVATION: "Observé", COLLECTION: "Collecté",
};
const dates = new Intl.DateTimeFormat("fr-FR", { timeZone: "Europe/Paris" });

function safeUrl(value: string | null) {
  try {
    const url = new URL(value ?? "");
    return ["https:", "http:"].includes(url.protocol) ? url.href : undefined;
  } catch {
    return undefined;
  }
}

function makePresentation(report: Report) {
  const registry = new Map(report.sources.map(source => [source.id, source]));
  const urls = new Map<string, { marker: string; url: string }>();
  const sources: RenderableDocument["sources"] = [];
  const pages: RenderableDocument["pages"] = [];

  function refs(ids: string[], pointer: string, quote: string) {
    return Array.from(new Set(ids)).map(contentId => {
      const source = registry.get(contentId);
      if (!source) throw new Error(`Source du rapport introuvable : ${contentId}`);
      const id = `S${sources.length + 1}`;
      const date = new Date(source.source_at);
      const label = [source.title || "Source originale", sourceKinds[source.source_kind],
        Number.isNaN(date.getTime()) ? null : `${dateKinds[source.date_kind] || "Daté"} le ${dates.format(date)}`]
        .filter(Boolean).join(" · ");
      const url = safeUrl(source.url);
      if (url && !urls.has(contentId)) urls.set(contentId, { marker: `⟦GC-${id}⟧`, url });
      const marker = urls.get(contentId)?.marker;
      sources.push({ id, json_pointer: pointer, quote, content_id: contentId,
        label: marker ? `${label} ${marker}` : label });
      return id;
    });
  }

  function addPage(layout: RenderableDocument["pages"][number]["layout"], title: string,
    paragraphs: string[], bullets: string[], sourceIds: string[]) {
    pages.push({
      page_id: `company-report-${pages.length + 1}`, layout, title,
      eyebrow: "Rapport mensuel de veille", paragraphs, bullets, source_ids: sourceIds,
      metrics: [], chart: null, takeaway: "", cautions: [],
    });
  }

  const [year, month] = report.month.split("-").map(Number);
  const start = `${report.month}-01`;
  const end = new Date(Date.UTC(year, month, 0)).toISOString().slice(0, 10);
  const title = `${report.company_name} · Veille mensuelle`;
  addPage("COVER", title, [`${report.sources.length} sources dans le corpus.`], [], []);
  for (const { id, title: sectionTitle } of blocks) {
    const bullets: string[] = [];
    const pageRefs: string[] = [];
    const addBullet = (text: string, ids: string[], pointer: string, quote: string) => {
      const cited = refs(ids, pointer, quote);
      pageRefs.push(...cited);
      bullets.push(text + (cited.length ? ` [${cited.join(", ")}]` : ""));
    };
    report.sections[id].forEach((fact, index) => {
      const pointer = `/sections/${id}/${index}`;
      addBullet(`${fact.title}\n${fact.summary}`,
        [fact.primary_id, ...fact.support_ids], `${pointer}/summary`, fact.summary);
      if (fact.contribution && fact.contribution_ids.length) {
        addBullet(`Éclairage salarié — ${fact.contribution}`, fact.contribution_ids,
          `${pointer}/contribution`, fact.contribution);
      }
      if (fact.relay_ids.length) {
        addBullet(`Relais observés — ${fact.title}`, fact.relay_ids, `${pointer}/title`, fact.title);
      }
    });
    if (bullets.length) addPage("ANALYSIS", sectionTitle, [], bullets, pageRefs);
  }
  if (report.limited_sources) {
    addPage("ANALYSIS", "Périmètre et limites", [],
      [`${report.limited_sources} source(s) ont été analysées à partir d’un extrait ou du titre.`], []);
  }
  const document: RenderableDocument = {
    schema_version: "1.0", template: "GETCURATOR_AUTONOMOUS_V1", title,
    subtitle: `${start} – ${end}`, pages, sources, review_notes: [],
  };
  const filename = productionPdfFilename({ subject: title, language: "fr", periodStart: start, periodEnd: end })
    ?.replace(/_Report\.pdf$/i, "_Presentation.pdf") || `GetCurator_${report.month}_FR_Presentation.pdf`;
  return { html: buildTouchPresentationHtml(document, filename, "fr"), filename, urls: Array.from(urls.values()) };
}

export default function CompanyReportPresentation({ report }: { report: Report }) {
  const { html, filename, urls } = useMemo(() => makePresentation(report), [report]);
  const frame = useRef<HTMLIFrameElement>(null);
  const [checked, setChecked] = useState("");
  const [overflow, setOverflow] = useState<number[]>([]);
  const [citationError, setCitationError] = useState(false);

  async function checkLayout() {
    const doc = frame.current?.contentDocument;
    if (!doc) return;
    await doc.fonts.ready;
    if (frame.current?.contentDocument !== doc) return;
    let missing = false;
    for (const { marker, url } of urls) {
      const existing = Array.from(doc.querySelectorAll<HTMLAnchorElement>(".bibliography a[data-company-source]"))
        .some(link => link.dataset.companySource === marker);
      if (existing) continue;
      const entries = Array.from(doc.querySelectorAll(".bibliography li"))
        .filter(entry => entry.textContent?.includes(marker));
      if (entries.length !== 1) {
        missing = true;
        continue;
      }
      const entry = entries[0];
      const walker = doc.createTreeWalker(entry, 4);
      let node = walker.nextNode();
      while (node && !node.nodeValue?.includes(marker)) node = walker.nextNode();
      if (!node) {
        missing = true;
        continue;
      }
      node.nodeValue = node.nodeValue?.replace(marker, "") ?? "";
      const link = doc.createElement("a");
      link.dataset.companySource = marker;
      link.href = url;
      link.textContent = "Source originale";
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      entry.append(" · ", link);
    }
    setCitationError(missing);
    setOverflow(paginateTouchPresentation(doc, "fr").overflow);
    setChecked(html);
  }

  function print() {
    const child = frame.current?.contentWindow;
    if (!child || checked !== html || overflow.length || citationError) return;
    const previous = document.title;
    const restore = () => {
      document.title = previous;
      window.removeEventListener("afterprint", restore);
      child.removeEventListener("afterprint", restore);
    };
    document.title = filename.replace(/\.pdf$/i, "");
    window.addEventListener("afterprint", restore);
    child.addEventListener("afterprint", restore);
    try { child.focus(); child.print(); } catch (error) { restore(); throw error; }
  }

  return <section className="space-y-3 rounded border bg-white p-4">
    <button type="button" className="rounded border px-3 py-2 text-sm disabled:opacity-50"
      disabled={checked !== html || !!overflow.length || citationError} onClick={print}>
      Imprimer / Enregistrer la présentation en PDF
    </button>
    <p className="text-xs text-gray-600">{filename}</p>
    {citationError && <p role="alert" className="text-sm text-red-700">
      La bibliographie n’a pas pu être reliée aux sources. Export suspendu.
    </p>}
    {!!overflow.length && <p role="alert" className="text-sm text-red-700">
      Pages trop denses : {overflow.join(", ")}. Export suspendu.
    </p>}
    <iframe ref={frame} title="Présentation du rapport société" srcDoc={html}
      sandbox="allow-same-origin allow-modals" onLoad={checkLayout} className="h-[850px] w-full rounded border"/>
  </section>;
}
