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
  chapter?: string;
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
  language: "fr" | "en";
  media_logo_rectangle_id: string | null;
  editorial: { cover_line: string; headline: string;
    highlights: { fact_id: string; label: string; text: string }[] };
  month: string;
  limited_sources: number;
  google_news_countries_observed?: string[];
  sections: Record<"facts" | "site_changes" | "mentions", Fact[]>;
  sources: Source[];
};

const sections = ["facts", "site_changes", "mentions"] as const;
const chapters = [
  { id: "PRODUCT", fr: "Produits et partenariats", en: "Products and partnerships" },
  { id: "CUSTOMERS", fr: "Cas clients et déploiements", en: "Customer stories and deployments" },
  { id: "EXPERTISE", fr: "Expertise et réglementation", en: "Expertise and regulation" },
  { id: "EVENTS", fr: "Événements et prises de parole", en: "Events and speaking engagements" },
  { id: "COMPANY", fr: "Vie de l’entreprise", en: "Company updates" },
  { id: "OTHER", fr: "Autres signaux", en: "Other developments" },
  { id: "SITE_CHANGES", fr: "Évolutions du site", en: "Website changes" },
  { id: "MENTIONS", fr: "Mentions externes", en: "External coverage" },
] as const;
const sourceKinds: Record<string, [string, string]> = {
  LINKEDIN_CORPORATE: ["LinkedIn corporate", "Company LinkedIn"],
  LINKEDIN_EMPLOYEE: ["LinkedIn · veille salariés", "Employee LinkedIn watch"],
  SITE_PUBLICATION: ["Publication du site corporate", "Company website"],
  SITE_CHANGE: ["Page surveillée", "Monitored page"],
  MENTION: ["Mention externe", "External coverage"],
};
const dateKinds: Record<string, [string, string]> = {
  PUBLICATION: ["Publié", "Published"], OBSERVATION: ["Observé", "Observed"],
  COLLECTION: ["Collecté", "Collected"],
};
const styles = `
.sheet.cover h1{font-size:49px;line-height:1.05;color:#10283b}
.sheet.cover .cover-introduction{border-left:4px solid #007d71;background:transparent;padding:2mm 0 2mm 5mm}
.sheet.cover .cover-introduction p{font-size:20px;line-height:1.35}
.company-method{border-top:1px solid #cbd9dc;margin-top:5mm;padding-top:3mm;color:#10283b}
.company-method h2{font-size:15px;margin:0 0 2mm}
.company-method ul{margin:0;padding-left:4mm;display:grid;grid-template-columns:1fr 1fr;gap:2mm 7mm}
.company-method li,.company-method p{font-size:12px;line-height:1.35;margin:0}
.company-method p{margin-top:2mm}
.company-summary .touch-body>ul:not(.bibliography),
.company-detail .touch-body>ul:not(.bibliography){display:block}
.company-summary .touch-body>ul:not(.bibliography)>li,
.company-detail .touch-body>ul:not(.bibliography)>li{background:transparent;border-top:1px solid #cbd9dc;padding:4mm 0;margin:0}
.company-summary .touch-body>ul>li::first-line,.company-detail .touch-body>ul>li::first-line{font-weight:700}
.company-logo{max-width:30mm;max-height:9mm;width:auto;height:auto;object-fit:contain;vertical-align:middle}
`;

function safeUrl(value: string | null) {
  try {
    const url = new URL(value ?? "");
    return ["https:", "http:"].includes(url.protocol) ? url.href : undefined;
  } catch {
    return undefined;
  }
}

function makePresentation(report: Report): {
  html: string;
  filename: string;
  language: Report["language"];
  pageClasses: Record<string, string>;
  urls: { marker: string; url: string }[];
  method: { title: string; channels: string[]; limits: string };
} {
  const language = report.language === "en" ? "en" : "fr";
  const fr = language === "fr";
  const column = fr ? 0 : 1;
  const dates = new Intl.DateTimeFormat(language, { timeZone: "Europe/Paris" });
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
      const label = [source.title || (fr ? "Source originale" : "Original source"), sourceKinds[source.source_kind]?.[column],
        Number.isNaN(date.getTime()) ? null : `${dateKinds[source.date_kind]?.[column] ?? (fr ? "Daté" : "Dated")} le ${dates.format(date)}`]
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
      eyebrow: fr ? "Rapport mensuel de veille" : "Monthly company watch", paragraphs, bullets, source_ids: sourceIds,
      metrics: [], chart: null, takeaway: "", cautions: [],
    });
  }

  const [year, month] = report.month.split("-").map(Number);
  const start = `${report.month}-01`;
  const end = new Date(Date.UTC(year, month, 0)).toISOString().slice(0, 10);
  const title = `${report.company_name} · ${fr ? "Veille mensuelle" : "Monthly watch"}`;
  const pageClasses: Record<string, string> = {};
  const entries: { fact: Fact; key: string; pointer: string; chapter: string }[] = [];
  sections.forEach(section => report.sections[section].forEach((fact, index) => entries.push({
    fact, key: `${section}:${index}`, pointer: `/sections/${section}/${index}`,
    chapter: fact.chapter ?? (section === "facts" ? "OTHER" : section.toUpperCase()),
  })));
  const lookup = new Map(entries.map(entry => [entry.key, entry]));
  const citation = (ids: string[]) => ids.length ? ` [${ids.join(", ")}]` : "";
  addPage("COVER", title, [report.editorial.cover_line].filter(Boolean), [], []);
  if (report.editorial.highlights.length) {
    const summaryIds: string[] = [];
    const bullets = report.editorial.highlights.map((highlight, index) => {
      const entry = lookup.get(highlight.fact_id);
      if (!entry) throw new Error("Référence de synthèse introuvable.");
      const ids = refs([entry.fact.primary_id, ...entry.fact.support_ids, ...entry.fact.contribution_ids],
        `/editorial/highlights/${index}/text`, highlight.text);
      summaryIds.push(...ids);
      return `${highlight.label}
${highlight.text}${citation(ids)}`;
    });
    addPage("SUMMARY", report.editorial.headline, [], bullets, summaryIds);
    pages[pages.length - 1].eyebrow = fr ? "Le mois en bref" : "The month at a glance";
    pageClasses[String(pages.length)] = "company-summary";
  }

  const focusId = report.editorial.highlights[0]?.fact_id;
  for (const chapter of chapters) {
    const bullets: string[] = [];
    const pageRefs: string[] = [];
    const chapterEntries = entries.filter(entry => entry.chapter === chapter.id)
      .sort((a, b) => Number(b.key === focusId) - Number(a.key === focusId));
    chapterEntries.forEach(({ fact, pointer }) => {
      const primary = refs([fact.primary_id, ...fact.support_ids], `${pointer}/summary`, fact.summary);
      const contribution = refs(fact.contribution_ids, `${pointer}/contribution`, fact.contribution);
      const relays = refs(fact.relay_ids, `${pointer}/title`, fact.title);
      pageRefs.push(...primary, ...contribution, ...relays);
      bullets.push([
        fact.title,
        fact.summary + citation(primary),
        fact.contribution ? `${fr ? "Éclairage" : "Additional context"} — ${fact.contribution}${citation(contribution)}` : "",
        relays.length ? `${fr ? "Relais observés" : "Observed reshares"} · ${relays.length}${citation(relays)}` : "",
      ].filter(Boolean).join("\n"));
    });
    if (bullets.length) {
      addPage("ANALYSIS", chapter[language], [], bullets, pageRefs);
      pageClasses[String(pages.length)] = "company-detail";
    }
  }
  const count = (kind: string) => report.sources.filter(source => source.source_kind === kind).length;
  const markets = report.google_news_countries_observed?.length ?? 0;
  const marketNames = (report.google_news_countries_observed ?? []).join(", ");
  const google = markets
    ? fr ? `Marchés de recherche Google Actualités ayant remonté les mentions retenues : ${markets} (${marketNames}).`
      : `Google News market origins for retained results: ${markets} (${marketNames}).`
    : fr ? "Aucun pays de recherche Google documenté dans le corpus retenu."
      : "No Google search markets documented in the selected corpus.";
  const method = {
    title: fr ? "Objectif et méthode de veille" : "Watch scope and method",
    channels: fr ? [
      `LinkedIn : publications des pages officielles et d’une sélection de comptes salariés (${count("LINKEDIN_CORPORATE")} corporate, ${count("LINKEDIN_EMPLOYEE")} via les comptes salariés).`,
      `Site corporate : nouvelles publications et changements sur les pages surveillées (${count("SITE_PUBLICATION")} publications, ${count("SITE_CHANGE")} observations).`,
      `Mentions externes : recherches Google Actualités, puis sélection des résultats pertinents (${count("MENTION")} mentions retenues). ${google}`,
    ] : [
      `LinkedIn: official company pages and selected employee accounts (${count("LINKEDIN_CORPORATE")} company posts, ${count("LINKEDIN_EMPLOYEE")} via employee watch).`,
      `Company website: new publications and updates to monitored pages (${count("SITE_PUBLICATION")} publications, ${count("SITE_CHANGE")} observations).`,
      `External coverage: Google News searches followed by relevance screening (${count("MENTION")} mentions retained). ${google}`,
    ],
    limits: fr
      ? `Objectif : identifier les évolutions significatives du mois et les documenter par leurs sources. La veille couvre une sélection de sources publiques.${report.limited_sources ? ` ${report.limited_sources} source(s) analysée(s) à partir d’un extrait ou du titre.` : ""}`
      : `Objective: identify the month’s significant developments and link them to evidence. Coverage reflects a selection of public sources.${report.limited_sources ? ` ${report.limited_sources} source(s) analyzed from an excerpt or title.` : ""}`,
  };
  const document: RenderableDocument = {
    schema_version: "1.0", template: "GETCURATOR_AUTONOMOUS_V1", title,
    subtitle: `${start} – ${end}`, pages, sources, review_notes: [],
  };
  const filename = productionPdfFilename({ subject: title, language, periodStart: start, periodEnd: end })
    ?.replace(/_Report\.pdf$/i, "_Presentation.pdf") || `GetCurator_${report.month}_${language.toUpperCase()}_Presentation.pdf`;
  const html = buildTouchPresentationHtml(document, filename, language)
    .replace("</style>", styles + "</style>");
  return { html, filename, language, pageClasses, urls: Array.from(urls.values()), method };
}

export default function CompanyReportPresentation({ report }: { report: Report }) {
  const { html, filename, language, pageClasses, urls, method } = useMemo(() => makePresentation(report), [report]);
  const frame = useRef<HTMLIFrameElement>(null);
  const [checked, setChecked] = useState("");
  const [overflow, setOverflow] = useState<number[]>([]);
  const [citationError, setCitationError] = useState(false);

  async function checkLayout() {
    const doc = frame.current?.contentDocument;
    if (!doc) return;
    await doc.fonts.ready;
    if (frame.current?.contentDocument !== doc) return;
    const sheets = Array.from(doc.querySelectorAll<HTMLElement>(".sheet"));
    sheets.forEach((sheet, i) => {
      const pageClass = pageClasses[String(i + 1)];
      if (pageClass) sheet.classList.add(pageClass);
      const tagline = sheet.querySelector(".header .tagline");
      if (tagline) tagline.textContent = report.company_name;
    });
    const base = process.env.NEXT_PUBLIC_GCS_BASE_URL;
    if (base && report.media_logo_rectangle_id) {
      const logoUrl = safeUrl(`${base.replace(/\/$/, "")}/companies/${encodeURIComponent(report.media_logo_rectangle_id)}`);
      if (logoUrl) {
        const logo = doc.createElement("img");
        logo.src = logoUrl;
        logo.alt = report.company_name;
        logo.className = "company-logo";
        let timer: ReturnType<typeof setTimeout> | undefined;
        const loaded = await Promise.race([
          logo.decode().then(() => true).catch(() => false),
          new Promise<boolean>(resolve => { timer = setTimeout(() => resolve(false), 3000); }),
        ]);
        if (timer) clearTimeout(timer);
        if (frame.current?.contentDocument !== doc) return;
        if (loaded) sheets.forEach(sheet => sheet.querySelector(".header .tagline")?.replaceChildren(logo.cloneNode()));
      }
    }
    const cover = doc.querySelector(".sheet.cover");
    const footer = cover?.querySelector(".footer");
    if (cover && footer && !cover.querySelector(".company-method")) {
      const section = doc.createElement("section");
      section.className = "company-method";
      const heading = doc.createElement("h2");
      heading.textContent = method.title;
      const list = doc.createElement("ul");
      method.channels.forEach(channel => {
        const item = doc.createElement("li");
        item.textContent = channel;
        list.appendChild(item);
      });
      const limits = doc.createElement("p");
      limits.textContent = method.limits;
      section.append(heading, list, limits);
      cover.insertBefore(section, footer);
    }
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
      link.textContent = language === "fr" ? "Source originale" : "Original source";
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      entry.append(" · ", link);
    }
    setCitationError(missing);
    setOverflow(paginateTouchPresentation(doc, language).overflow);
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
      {language === "fr" ? "Imprimer / Enregistrer la présentation en PDF" : "Print / Save presentation as PDF"}
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
