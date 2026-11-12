"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api } from "@/lib/api";
import CompanyReportPresentation from "@/components/admin/company/CompanyReportPresentation";

const sections = [
  { id: "LINKEDIN_CORPORATE", label: "LinkedIn · Corporate" },
  { id: "LINKEDIN_EMPLOYEE", label: "LinkedIn · Salariés retenus" },
  { id: "SITE_PUBLICATION", label: "Publications du site corporate" },
  { id: "SITE_CHANGE", label: "Changements de pages surveillées" },
  { id: "MENTION", label: "Mentions externes" },
] as const;

type Company = { id_company: string; name: string };
type Candidate = {
  id: string;
  document_id: string | null;
  title: string | null;
  url: string | null;
  author: string | null;
  source_at: string;
  date_kind: "PUBLICATION" | "OBSERVATION" | "COLLECTION";
  source_kind: (typeof sections)[number]["id"];
  change_type: string | null;
};
type Corpus = {
  candidates: Candidate[];
  selected_ids: string[];
  revision: string;
  unavailable_count: number;
};

type Notebook = {
  revision: string;
  sources: { id: string; title: string | null; url: string | null; text_status: string;
    source_at: string; source_kind: string; date_kind: string }[];
  facts: {
    title: string; theme: string; summary: string; primary_id: string;
    support_ids: string[]; relay_ids: string[]; contribution_ids: string[]; contribution: string;
    reference_date?: string; date_kind?: Candidate["date_kind"];
  }[];
};

type CompanyReport = {
  company_name: string;
  month: string;
  revision: string;
  coverage: Partial<Record<Candidate["source_kind"], number>>;
  limited_sources: number;
  sections: Record<"facts" | "site_changes" | "mentions", Notebook["facts"]>;
  sources: Notebook["sources"];
};

const reportEndpoint = "/company/watch/library/company-report";

const notebookEndpoint = "/company/watch/library/report-notebook";

const endpoint = "/company/watch/library/report-corpus";
const button = "rounded border px-3 py-2 text-sm disabled:opacity-50";
const dateLabels = { PUBLICATION: "Publié", OBSERVATION: "Observé", COLLECTION: "Collecté" };
const formatter = new Intl.DateTimeFormat("fr-FR", { timeZone: "Europe/Paris" });

function previousMonth() {
  const parts = new Intl.DateTimeFormat("fr-FR", {
    timeZone: "Europe/Paris", year: "numeric", month: "numeric",
  }).formatToParts(new Date());
  const year = Number(parts.find(part => part.type === "year")?.value);
  const month = Number(parts.find(part => part.type === "month")?.value);
  return new Date(Date.UTC(year, month - 2, 1)).toISOString().slice(0, 7);
}

function safeUrl(value: string | null) {
  try {
    const url = new URL(value ?? "");
    if (url.protocol === "https:" || url.protocol === "http:") return url.href;
  } catch {
    return undefined;
  }
}

function NotebookView({ notebook, heading = "Notebook", showCoverage = true }: {
  notebook: Notebook; heading?: string; showCoverage?: boolean;
}) {
  const sources = new Map(notebook.sources.map(source => [source.id, source]));
  const limited = notebook.sources.filter(source => source.text_status !== "FULL").length;

  function sourceLinks(ids: string[]) {
    return ids.map(id => {
      const source = sources.get(id);
      const url = safeUrl(source?.url ?? null);
      return <li key={id}>{url
        ? <a className="underline" href={url} target="_blank" rel="noopener noreferrer">{source?.title || id}</a>
        : source?.title || id}</li>;
    });
  }

  return <section aria-label={heading} className="space-y-3">
    <h2 className="text-lg font-semibold">{heading} · {notebook.facts.length} fait(s)</h2>
    {showCoverage && limited > 0 && <p className="text-sm text-gray-600">
      {limited} source(s) ont été analysées à partir d’un extrait ou du titre.
    </p>}
    {notebook.facts.length === 0 && <p className="text-sm">Aucun fait dans cette rubrique.</p>}
    {notebook.facts.map((fact, index) => <article key={index} className="space-y-2 rounded border bg-white p-3">
      <p className="text-xs text-gray-600">{fact.theme}
        {fact.reference_date && fact.date_kind
          ? ` · ${dateLabels[fact.date_kind]} le ${formatter.format(new Date(fact.reference_date))}`
          : ""}
      </p>
      <h3 className="font-semibold">{fact.title}</h3>
      <p className="text-sm">{fact.summary}</p>
      <div className="text-sm">
        <p className="font-medium">Source principale</p><ul>{sourceLinks([fact.primary_id])}</ul>
      </div>
      {!!fact.support_ids.length && <details className="text-sm">
        <summary className="cursor-pointer">Sources complémentaires · {fact.support_ids.length}</summary>
        <ul>{sourceLinks(fact.support_ids)}</ul>
      </details>}
      {!!fact.relay_ids.length && <details className="text-sm">
        <summary className="cursor-pointer">Relais observés · {fact.relay_ids.length}</summary>
        <ul>{sourceLinks(fact.relay_ids)}</ul>
      </details>}
      {fact.contribution && <div className="text-sm">
        <p className="font-medium">Éclairage salarié</p>
        <p>{fact.contribution}</p>
        <ul>{sourceLinks(fact.contribution_ids)}</ul>
      </div>}
    </article>)}
  </section>;
}

function CompanyReportView({ report }: { report: CompanyReport }) {
  const [showPresentation, setShowPresentation] = useState(false);
  const blocks = [
    { id: "facts", title: "Faits du mois" },
    { id: "site_changes", title: "Évolutions observées sur le site" },
    { id: "mentions", title: "Mentions externes" },
  ] as const;

  function download() {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `rapport-societe-${report.month}.json`;
    link.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return <section className="space-y-4 rounded border bg-white p-4" aria-label="Rapport société">
    <header className="flex flex-wrap items-start justify-between gap-2">
      <div>
        <h2 className="text-xl font-semibold">{report.company_name} · {report.month}</h2>
        <p className="text-sm text-gray-600">{report.sources.length} sources dans le corpus</p>
      </div>
      <div className="flex flex-wrap gap-2">
        <button type="button" className={button} onClick={() => setShowPresentation(value => !value)}>
          {showPresentation ? "Masquer la présentation" : "Prévisualiser la présentation"}
        </button>
        <button type="button" className={button} onClick={download}>Télécharger le JSON</button>
      </div>
    </header>
    <ul className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-700">
      {sections.filter(item => report.coverage[item.id]).map(item =>
        <li key={item.id}>{item.label} · {report.coverage[item.id]}</li>
      )}
    </ul>
    {!!report.limited_sources && <p className="text-sm text-gray-600">
      {report.limited_sources} source(s) analysées à partir d’un extrait ou du titre.
    </p>}
    {showPresentation && <CompanyReportPresentation report={report}/>}
    {blocks.filter(block => block.id === "facts" || report.sections[block.id].length).map(block =>
      <NotebookView key={block.id} heading={block.title} showCoverage={false}
        notebook={{ revision: report.revision, facts: report.sections[block.id], sources: report.sources }}/>
    )}
  </section>;
}

export default function CompanyReportCorpusPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [company, setCompany] = useState("");
  const [month, setMonth] = useState(previousMonth);
  const [scope, setScope] = useState<{ company: string; month: string } | null>(null);
  const [corpus, setCorpus] = useState<Corpus | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [report, setReport] = useState<CompanyReport | null>(null);
  const [notebook, setNotebook] = useState<Notebook | null>(null);
  const [generating, setGenerating] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const dirty = !!corpus && (selected.length !== corpus.selected_ids.length ||
    selected.some(id => !corpus.selected_ids.includes(id)));

  useEffect(() => {
    let active = true;
    api.get("/company/watch/operations/companies")
      .then((result: { companies: Company[] }) => {
        if (active) setCompanies(result.companies);
      })
      .catch(() => { if (active) setError("Impossible de charger les sociétés suivies."); });
    return () => { active = false; };
  }, []);

  async function load(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || !company || !month) return;
    if (dirty && !window.confirm("Abandonner les modifications de sélection non enregistrées ?")) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const params = new URLSearchParams({ company_id: company, month });
      const next: Corpus = await api.get(`${endpoint}?${params}`);
      setReport(null);
      setNotebook(null);
      setCorpus(next);
      setSelected(next.selected_ids);
      setScope({ company, month });
      if (next.revision !== "0") {
        params.set("revision", next.revision);
        const result: { notebook: Notebook | null } = await api.get(`${notebookEndpoint}?${params}`);
        setNotebook(result.notebook);
        if (result.notebook) {
          const saved: { report: CompanyReport | null } = await api.get(`${reportEndpoint}?${params}`);
          setReport(saved.report);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de charger le corpus.");
    } finally {
      setBusy(false);
    }
  }

  async function save() {
    if (busy || !scope || !corpus) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result: { revision: string } = await api.put(endpoint, {
        company_id: scope.company, month: scope.month, selected_ids: selected, revision: corpus.revision,
      });
      setCorpus({ ...corpus, revision: result.revision, selected_ids: selected, unavailable_count: 0 });
      setReport(null);
      setNotebook(null);
      setNotice("Sélection enregistrée.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible d’enregistrer la sélection.");
    } finally {
      setBusy(false);
    }
  }

  async function generateNotebook() {
    if (busy || !scope || !corpus || dirty || corpus.revision === "0" || corpus.unavailable_count) return;
    setGenerating(true);
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result: { notebook: Notebook } = await api.post(notebookEndpoint, {
        company_id: scope.company, month: scope.month, revision: corpus.revision,
      });
      setNotebook(result.notebook);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de générer le Notebook.");
    } finally {
      setGenerating(false);
      setBusy(false);
    }
  }

  async function generateReport() {
    if (busy || !scope || !corpus || dirty || !notebook || notebook.revision !== corpus.revision ||
        corpus.unavailable_count) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result: { report: CompanyReport } = await api.post(reportEndpoint, {
        company_id: scope.company, month: scope.month, revision: corpus.revision,
      });
      setReport(result.report);
      setNotice("Rapport enregistré.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible d’enregistrer le rapport.");
    } finally {
      setBusy(false);
    }
  }

  return <main className="space-y-4">
    <header className="space-y-1">
      <Link className="text-sm underline" href="/admin/library/corpo">Library Corpo</Link>
      <h1 className="text-2xl font-semibold text-ratecard-blue">Corpus du rapport société</h1>
    </header>
    <form className="flex flex-wrap items-end gap-3 rounded border bg-white p-4" onSubmit={load}>
      <label className="text-sm">Société
        <select className="block rounded border px-3 py-2" required value={company} disabled={busy}
          onChange={event => setCompany(event.target.value)}>
          <option value="">Choisir une société</option>
          {companies.map(item => <option key={item.id_company} value={item.id_company}>{item.name}</option>)}
        </select>
      </label>
      <label className="text-sm">Mois
        <input className="block rounded border px-3 py-2" type="month" required value={month}
          disabled={busy} onChange={event => setMonth(event.target.value)}/>
      </label>
      <button className={button} disabled={busy || !company || !month}>Charger le corpus</button>
    </form>
    {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
    {notice && <p role="status" className="text-sm text-green-700">{notice}</p>}
    {corpus && scope && <>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="font-medium">
          {companies.find(item => item.id_company === scope.company)?.name ?? scope.company} · {scope.month}
          {" · "}{selected.length} / {corpus.candidates.length} sources sélectionnées
        </p>
        <button type="button" className={`${button} bg-ratecard-blue text-white`} onClick={save}
          disabled={busy || (!dirty && corpus.revision !== "0" && !corpus.unavailable_count)}>
          Enregistrer la sélection
        </button>
      </div>
      {corpus.unavailable_count > 0 && <p className="text-sm text-amber-800">
        {corpus.unavailable_count} source(s) du brouillon ne sont plus disponibles.
      </p>}
      {sections.map(section => {
        const items = corpus.candidates.filter(item => item.source_kind === section.id);
        const count = items.filter(item => selected.includes(item.id)).length;
        return <details key={`${scope.company}:${scope.month}:${section.id}`}
          open={section.id.startsWith("LINKEDIN") || undefined} className="rounded border bg-white p-3">
          <summary className="cursor-pointer text-sm font-medium">
            {section.label} · {count} / {items.length}
          </summary>
          {!items.length ? <p className="mt-2 text-sm text-gray-600">Aucune source pour ce mois.</p> :
            <ul className="mt-2 divide-y">
              {items.map(item => {
                const url = safeUrl(item.url);
                return <li key={item.id} className="flex flex-wrap items-start justify-between gap-2 py-2">
                  <label className="flex min-w-0 flex-1 items-start gap-2 text-sm">
                    <input className="mt-1" type="checkbox" disabled={busy} checked={selected.includes(item.id)}
                      onChange={event => {
                        const checked = event.target.checked;
                        setSelected(ids => checked ? [...ids, item.id] : ids.filter(id => id !== item.id));
                      }}/>
                    <span>
                      <span className="block font-medium">{item.title || "Source sans titre"}</span>
                      <span className="text-gray-600">{dateLabels[item.date_kind]} le {formatter.format(new Date(item.source_at))}
                        {item.author ? ` · ${item.author}` : ""}
                        {item.change_type ? (item.change_type === "NEW_PAGE" ? " · Première observation" : " · Modification") : ""}
                      </span>
                    </span>
                  </label>
                  {item.document_id && <Link className="text-sm underline" target="_blank" rel="noopener"
                    href={`/admin/library/corpo?document=${encodeURIComponent(item.document_id)}`}>Consulter</Link>}
                  {url && <a className="text-sm underline" href={url} target="_blank" rel="noopener noreferrer">Source</a>}
                </li>;
              })}
            </ul>}
        </details>;
      })}
      <div className="flex flex-wrap items-center gap-3">
        <button type="button" className={button} onClick={generateNotebook}
          disabled={busy || dirty || corpus.revision === "0" || !selected.length || !!corpus.unavailable_count || !!notebook}>
          {generating ? "Génération en cours…" : "Générer le Notebook"}
        </button>
        {(dirty || corpus.revision === "0") && <span className="text-sm text-gray-600">
          Enregistrez la sélection pour générer le Notebook.
        </span>}
      </div>
      {notebook && !dirty && <>
        {report ? <CompanyReportView report={report}/> : <>
          <NotebookView notebook={notebook}/>
          <button type="button" className={`${button} bg-ratecard-blue text-white`}
            disabled={busy || !!corpus.unavailable_count} onClick={generateReport}>
            Enregistrer le rapport société
          </button>
        </>}
      </>}
    </>}
  </main>;
}
