"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "@/lib/api";

type Source = { source_id: string; name: string };
type Evidence = {
  id: string;
  page: number;
  fact: string;
  quote: string;
  kind?: string;
  geography?: string | null;
  period?: string | null;
  status: "VERIFIED" | "NEEDS_REVIEW" | "REJECTED";
  reason?: string;
  match_score?: number;
};
type Batch = {
  start_page: number;
  end_page: number;
  page_count: number;
  next_page: number | null;
  units: Omit<Evidence, "id">[];
  counts?: Record<string, number>;
};
type Topic = {
  id: string;
  title: string;
  angle: string;
  editorial_rationale: string;
  unit_ids: string[];
  pages: number[];
  evidence_count: number;
  review_count: number;
  evidence: Evidence[];
};
type TopicsResult = {
  version: string;
  proposals: Topic[];
  summary: {
    eligible_units: number;
    covered_units: number;
    uncovered_units: number;
    coverage_percent: number;
    topic_proposals: number;
    analysis_batches: number;
  };
  uncovered_evidence: Evidence[];
};

const button = "rounded-md border px-3 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-40";
const primary = `${button} border-ratecard-blue bg-ratecard-blue text-white`;
const field = "mt-1 w-full rounded-md border p-2 text-sm";
const errText = (error: unknown) => error instanceof Error ? error.message : String(error);
const normalize = (value: string) => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toLowerCase();

function downloadJson(filename: string, value: unknown) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: "application/json" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function PDFStudio() {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [sources, setSources] = useState<Source[]>([]);
  const [sourceId, setSourceId] = useState("");
  const [newSource, setNewSource] = useState(false);
  const [sourceName, setSourceName] = useState("");
  const [sourceDomain, setSourceDomain] = useState("");
  const [sourceUniverse, setSourceUniverse] = useState("");
  const [units, setUnits] = useState<Evidence[]>([]);
  const [nextPage, setNextPage] = useState<number | null>(1);
  const [pageCount, setPageCount] = useState<number | null>(null);
  const [topics, setTopics] = useState<TopicsResult | null>(null);
  const [approvedIds, setApprovedIds] = useState<string[]>([]);
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const [showEvidence, setShowEvidence] = useState(false);
  const [busy, setBusy] = useState<"" | "source" | "extract" | "topics">("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const abortRef = useRef(false);

  useEffect(() => {
    let mounted = true;
    api.get("/source/list")
      .then((result: { sources?: Source[] }) => {
        if (mounted) setSources(result.sources || []);
      })
      .catch((e: unknown) => {
        if (mounted) setError(`Impossible de charger les sources : ${errText(e)}`);
      });
    return () => { mounted = false; abortRef.current = true; };
  }, []);

  const completed = nextPage === null;
  const acceptedUnits = useMemo(() => units.filter(unit => unit.status !== "REJECTED"), [units]);
  const rejectedCount = units.length - acceptedUnits.length;
  const duplicateSource = sources.find(source => normalize(source.name) === normalize(sourceName));
  const activeTopic = topics?.proposals.find(topic => topic.id === selectedTopic);

  function reset(next: File | null) {
    if (busy) return;
    setFile(next);
    setTitle(next?.name.replace(/\.pdf$/i, "").replace(/[_-]+/g, " ") || "");
    setUnits([]);
    setNextPage(1);
    setPageCount(null);
    setTopics(null);
    setApprovedIds([]);
    setSelectedTopic(null);
    setShowEvidence(false);
    setError("");
    setNotice("");
  }

  async function createSource() {
    if (!sourceName.trim() || duplicateSource || busy) return;
    setBusy("source"); setError("");
    try {
      const result = await api.post("/source/create", {
        name: sourceName.trim(),
        type_source: "PUBLISHER",
        domain: sourceDomain.trim() || null,
        universe_id: sourceUniverse.trim() || null,
        acquisition_mode: "PDF_MANUAL",
      }) as { source_id: string };
      if (!result.source_id) throw new Error("La source créée ne possède pas d'identifiant.");
      setSources(previous => [...previous, { source_id: result.source_id, name: sourceName.trim() }]
        .sort((a, b) => a.name.localeCompare(b.name)));
      setSourceId(result.source_id);
      setNewSource(false);
    } catch (e) { setError(errText(e)); }
    finally { setBusy(""); }
  }

  async function extractAll() {
    if (!file || busy || completed) return;
    if (!file.name.toLowerCase().endsWith(".pdf") || file.size > 30 * 1024 * 1024) {
      setError("Fichier PDF requis (30 Mo maximum)."); return;
    }
    abortRef.current = false;
    setBusy("extract"); setError(""); setNotice("");
    let cursor: number | null = nextPage;
    let collected = [...units];
    let total = pageCount;
    try {
      while (cursor !== null && !abortRef.current) {
        const form = new FormData();
        form.append("file", file);
        form.append("start_page", String(cursor));
        const batch = await api.postForm("/discovery/pdf-studio/v8/extract", form) as Batch;
        if (batch.start_page !== cursor || !Array.isArray(batch.units) ||
            (batch.next_page !== null && batch.next_page <= cursor)) {
          throw new Error("Réponse d'extraction incohérente.");
        }
        const offset = collected.length;
        const incoming: Evidence[] = batch.units.map((unit, index) => ({
          ...unit,
          id: `U${String(offset + index + 1).padStart(5, "0")}`,
          status: unit.status || "NEEDS_REVIEW",
        }));
        collected = [...collected, ...incoming];
        total = batch.page_count;
        cursor = batch.next_page;
        setUnits(collected);
        setPageCount(total);
        setNextPage(cursor);
      }
      if (cursor === null) setNotice(`Extraction terminée : ${total} pages parcourues, ${collected.length} informations relevées.`);
    } catch (e) {
      setError(`${errText(e)} — les lots déjà extraits sont conservés. Tu peux reprendre.`);
    } finally { setBusy(""); }
  }

  function updateUnit(id: string, status: Evidence["status"]) {
    setUnits(previous => previous.map(unit => unit.id === id ? { ...unit, status } : unit));
    setTopics(null); setApprovedIds([]); setSelectedTopic(null);
  }

  async function identifyTopics() {
    if (!completed || !acceptedUnits.length || !title.trim() || busy) return;
    setBusy("topics"); setError(""); setNotice("");
    try {
      const result = await api.post("/discovery/pdf-studio/v8/topics", {
        document_title: title.trim(),
        source_id: sourceId || null,
        units,
      }) as TopicsResult;
      if (result.version !== "8.0" || !Array.isArray(result.proposals)) {
        throw new Error("Réponse d'identification des sujets invalide.");
      }
      setTopics(result);
      setApprovedIds([]);
      setSelectedTopic(result.proposals[0]?.id || null);
      setNotice(`${result.proposals.length} sujets proposés. Vérifie les angles et leurs preuves.`);
    } catch (e) { setError(errText(e)); }
    finally { setBusy(""); }
  }

  const exportData = {
    version: "8.0",
    document_title: title.trim(),
    filename: file?.name,
    source_id: sourceId || null,
    extraction_complete: completed,
    page_count: pageCount,
    units,
    topics,
    approved_topic_ids: approvedIds,
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">PDF Studio</h1>
        <p className="text-sm text-gray-600">Un document, des informations sourcées, puis des sujets éditoriaux pour GetCurator.</p>
      </header>

      {error && <div role="alert" className="rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-800">{error}</div>}
      {notice && <div role="status" className="rounded-lg border bg-gray-50 p-3 text-sm">{notice}</div>}

      <section className="space-y-4 rounded-xl border p-5">
        <h2 className="font-semibold">1. Document</h2>
        <input type="file" accept=".pdf,application/pdf" disabled={Boolean(busy)}
          onChange={event => reset(event.target.files?.[0] || null)} className="block w-full text-sm" />
        {file && <p className="text-xs text-gray-500">{file.name} · {(file.size / 1048576).toFixed(2)} Mo</p>}
        <label className="block text-sm">Titre du document
          <input className={field} value={title} disabled={Boolean(busy) || Boolean(topics)}
            onChange={event => setTitle(event.target.value)} />
        </label>
        <div className="flex gap-4 text-sm">
          <label className="flex items-center gap-2"><input type="radio" checked={!newSource} disabled={Boolean(busy)} onChange={() => setNewSource(false)} /> Source existante</label>
          <label className="flex items-center gap-2"><input type="radio" checked={newSource} disabled={Boolean(busy)} onChange={() => setNewSource(true)} /> Nouvelle source</label>
        </div>
        {!newSource ? (
          <label className="block text-sm">Éditeur
            <select className={field} value={sourceId} disabled={Boolean(busy)} onChange={event => setSourceId(event.target.value)}>
              <option value="">Sélectionner une source</option>
              {sources.map(source => <option key={source.source_id} value={source.source_id}>{source.name}</option>)}
            </select>
          </label>
        ) : (
          <div className="grid gap-3 md:grid-cols-2">
            <label className="text-sm">Nom<input className={field} value={sourceName} onChange={event => setSourceName(event.target.value)} /></label>
            <label className="text-sm">Domaine<input className={field} value={sourceDomain} onChange={event => setSourceDomain(event.target.value)} /></label>
            <label className="text-sm">ID univers (facultatif)<input className={field} value={sourceUniverse} onChange={event => setSourceUniverse(event.target.value)} /></label>
            <div className="flex items-end"><button type="button" className={button} disabled={Boolean(busy) || !sourceName.trim() || Boolean(duplicateSource)} onClick={() => void createSource()}>Créer la source</button></div>
            {duplicateSource && <p className="text-sm text-amber-700">Cette source existe déjà : {duplicateSource.name}</p>}
          </div>
        )}
      </section>

      <section className="space-y-4 rounded-xl border p-5">
        <div>
          <h2 className="font-semibold">2. Extraction des informations</h2>
          <p className="mt-1 text-sm text-gray-600">Toutes les pages sont traitées automatiquement. En cas d'erreur, le traitement peut reprendre au dernier lot.</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <button type="button" className={primary} disabled={!file || Boolean(busy) || completed} onClick={() => void extractAll()}>
            {busy === "extract" ? "Extraction en cours…" : completed ? "Extraction terminée" : units.length ? "Reprendre l'extraction" : "Extraire le document"}
          </button>
          <span className="text-sm text-gray-600">
            {completed ? `${pageCount ?? 0} / ${pageCount ?? 0}` : `${Math.max(0, (nextPage ?? 1) - 1)} / ${pageCount ?? "?"}`} pages · {units.length} informations · {rejectedCount} écartées
          </span>
        </div>
        {pageCount !== null && <div className="h-2 overflow-hidden rounded-full bg-gray-100"><div className="h-full bg-ratecard-blue transition-all" style={{ width: `${Math.min(100, Math.round(100 * (completed ? pageCount : (nextPage ?? 1) - 1) / Math.max(1, pageCount)))}%` }} /></div>}
        {!!units.length && <>
          <button type="button" className={`${button} text-xs`} onClick={() => setShowEvidence(value => !value)}>
            {showEvidence ? "Masquer" : "Vérifier"} les informations extraites
          </button>
          {showEvidence && <div className="max-h-[480px] space-y-3 overflow-y-auto rounded-lg border p-3">
            {units.map(unit => <div key={unit.id} className="space-y-1 border-b pb-3 text-sm">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-medium">{unit.id} · page {unit.page}</span>
                <select aria-label={`Statut de ${unit.id}`} className="rounded border p-1 text-xs" value={unit.status} disabled={Boolean(busy)}
                  onChange={event => updateUnit(unit.id, event.target.value as Evidence["status"])}>
                  <option value="VERIFIED">Citation correspondante</option>
                  <option value="NEEDS_REVIEW">À vérifier</option>
                  <option value="REJECTED">Écarter</option>
                </select>
              </div>
              <p>{unit.fact}</p>
              <p className="text-xs text-gray-500">Citation source : {unit.quote || "Absente"}</p>
            </div>)}
          </div>}
          <p className="text-xs text-amber-700">La correspondance textuelle d'une citation ne garantit pas l'exactitude de l'interprétation. Vérifier les chiffres et tableaux dans le PDF original.</p>
        </>}
      </section>

      <section className="space-y-4 rounded-xl border p-5">
        <div>
          <h2 className="font-semibold">3. Sujets éditoriaux</h2>
          <p className="mt-1 text-sm text-gray-600">Sol propose des angles autonomes à partir de toutes les informations disponibles, sans découpage imposé par les pages ou les pays.</p>
        </div>
        <button type="button" className={primary} disabled={Boolean(busy) || !completed || !acceptedUnits.length || !title.trim()}
          onClick={() => void identifyTopics()}>
          {busy === "topics" ? "Identification en cours…" : topics ? "Relancer l'identification" : "Identifier les sujets"}
        </button>
        {topics && <>
          <p className="text-sm font-medium">{topics.proposals.length} sujets proposés · {topics.summary.coverage_percent}% de couverture ({topics.summary.covered_units}/{topics.summary.eligible_units} informations)</p>
          <div className="grid gap-4 lg:grid-cols-[minmax(220px,1fr)_minmax(0,2fr)]">
            <div className="max-h-[520px] space-y-2 overflow-y-auto">
              {topics.proposals.map(topic => <button type="button" key={topic.id} onClick={() => setSelectedTopic(topic.id)}
                className={`w-full rounded-lg border p-3 text-left text-sm ${selectedTopic === topic.id ? "border-blue-500 bg-blue-50" : "hover:bg-gray-50"}`}>
                <span className="block font-medium">{topic.title}</span>
                <span className="mt-1 block text-xs text-gray-500">{topic.evidence_count} preuves · {approvedIds.includes(topic.id) ? "Validé" : "À examiner"}</span>
              </button>)}
            </div>
            {activeTopic && <div className="space-y-3 rounded-lg border p-4 text-sm">
              <h3 className="font-semibold">{activeTopic.title}</h3>
              <p><strong>Angle :</strong> {activeTopic.angle}</p>
              <p><strong>Pourquoi ce sujet :</strong> {activeTopic.editorial_rationale}</p>
              <p className="text-xs text-gray-500">Pages : {activeTopic.pages.join(", ")} · {activeTopic.review_count} preuves à revoir</p>
              <div className="max-h-72 space-y-2 overflow-y-auto border-t pt-3">
                {activeTopic.evidence.map(evidence => <div key={evidence.id} className="border-b pb-2">
                  <p className="font-medium">p. {evidence.page} · {evidence.fact}</p>
                  <p className="mt-1 text-xs text-gray-500">{evidence.quote}</p>
                </div>)}
              </div>
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={approvedIds.includes(activeTopic.id)}
                  onChange={event => setApprovedIds(previous => event.target.checked
                    ? [...previous.filter(id => id !== activeTopic.id), activeTopic.id]
                    : previous.filter(id => id !== activeTopic.id))} />
                Valider ce sujet
              </label>
            </div>}
          </div>
          {!!topics.uncovered_evidence.length && <details className="rounded-lg border p-3 text-sm">
            <summary className="cursor-pointer">{topics.uncovered_evidence.length} informations non couvertes</summary>
            <div className="mt-3 max-h-64 space-y-2 overflow-y-auto">{topics.uncovered_evidence.map(unit => <p key={unit.id}>{unit.id} · p. {unit.page} — {unit.fact}</p>)}</div>
          </details>}
        </>}
      </section>

      <section className="space-y-3 rounded-xl border p-5">
        <h2 className="font-semibold">4. Préparer les contenus GetCurator</h2>
        <p className="text-sm text-gray-600">{approvedIds.length} sujet(s) validé(s). La génération des articles et leur import RAW ne sont pas encore disponibles dans le backend V8.</p>
        <button type="button" className={button} disabled={!units.length || Boolean(busy)}
          onClick={() => downloadJson(`pdf-studio-${file?.name.replace(/\.pdf$/i, "") || "document"}.json`, exportData)}>
          Exporter le travail (preuves, sujets et validations)
        </button>
        <p className="text-xs text-gray-500">Cet export permet de conserver le travail. Il ne crée aucun contenu dans GetCurator.</p>
      </section>
    </div>
  );
}
