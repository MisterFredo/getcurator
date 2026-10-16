"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import ProductionDocumentPreview from "@/components/admin/production/ProductionDocumentPreview";
import type { ProductionDocument } from "@/types/production-document";
import {
  browseProductions, readProduction, browseArtifacts, readArtifact,
  startPlan, saveReviewedPlan, startDocument, importDocument, refreshArtifact,
} from "@/lib/production-workflow";
import {
  blocksSubmission, isRunning, stageLabel, statusLabel,
} from "@/types/production-workflow";
import type {
  ProductionListItem, ProductionWorkspace, WorkflowArtifact, WorkflowArtifactSummary,
} from "@/types/production-workflow";

type SourceReport = {
  report_id: string; subject: string; output_language: string;
  period_start?: string | null; period_end?: string | null;
};
type LegacyPlanSummary = { plan_version: number; plan_id: string };
type LegacyPlan = { title: string; editorial_angle: string; pages: {
  title: string; layout: string; key_message: string; explanation_outline: string[];
  visual_intent: string; cautions: string[];
}[] };
const INPUT = "w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm";
const BUTTON = "rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm disabled:opacity-50";
const PRIMARY = "rounded-lg bg-emerald-700 px-4 py-2 text-sm text-white disabled:opacity-50";
const PANEL = "space-y-4 rounded-xl border border-slate-200 bg-white p-5";
const message = (err: unknown) => err instanceof Error ? err.message : "Une erreur est survenue.";
const date = (value?: string | null) => value ? new Date(value).toLocaleString("fr-FR") : "";
function download(name: string, value: string, type = "application/json") {
  const url = URL.createObjectURL(new Blob([value], { type }));
  const anchor = window.document.createElement("a");
  anchor.href = url; anchor.download = name; anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
// Keep only an idempotency key locally, never the authoritative result.
// A lost POST response can then be retried as the same operation.
async function generationRequest(key: string, submit: (id: string) => Promise<WorkflowArtifact>) {
  const storageKey = `getcurator-production-pending:${key}`;
  let id: string = crypto.randomUUID();
  try {
    const previous = localStorage.getItem(storageKey);
    if (previous && /^[0-9a-f-]{36}$/i.test(previous)) id = previous;
    localStorage.setItem(storageKey, id);
  } catch { /* BigQuery remains authoritative when browser storage is unavailable. */ }
  const item = await submit(id);
  try { localStorage.removeItem(storageKey); } catch { /* Optional browser cache. */ }
  return item;
}

function legacyText(plan: LegacyPlan) {
  return `# ${plan.title}\n\n${plan.editorial_angle}\n\n` + plan.pages.map((page, i) =>
    `## Page ${i + 1} — ${page.title}\nComposition : ${page.layout}\n\n${page.key_message}\n\n` +
    page.explanation_outline.map(line => `- ${line}`).join("\n") +
    `\n\nVisuel : ${page.visual_intent}\n` + page.cautions.map(line => `Limite : ${line}`).join("\n")
  ).join("\n\n");
}

export default function ProductionWorkspace({ mode }: { mode: "create" | "list" }) {
  const [productions, setProductions] = useState<ProductionListItem[]>([]);
  const [productionOffset, setProductionOffset] = useState(0);
  const [moreProductions, setMoreProductions] = useState(false);
  const [reports, setReports] = useState<SourceReport[]>([]);
  const [reportOffset, setReportOffset] = useState(0);
  const [moreReports, setMoreReports] = useState(false);
  const [reportSearch, setReportSearch] = useState("");
  const [productionSearch, setProductionSearch] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [title, setTitle] = useState("");
  const [objective, setObjective] = useState("");
  const [audience, setAudience] = useState("Décideurs médias et marketing");
  const [language, setLanguage] = useState<"fr" | "en">("fr");
  const [pages, setPages] = useState<number | null>(null);
  const [production, setProduction] = useState<ProductionWorkspace | null>(null);
  const [history, setHistory] = useState<WorkflowArtifactSummary[]>([]);
  const [historyOffset, setHistoryOffset] = useState(0);
  const [moreHistory, setMoreHistory] = useState(false);
  const [artifact, setArtifact] = useState<WorkflowArtifact | null>(null);
  const [editor, setEditor] = useState("");
  const [original, setOriginal] = useState("");
  const [editing, setEditing] = useState(false);
  const [editorParent, setEditorParent] = useState<string | null>(null);
  const [responseId, setResponseId] = useState("");
  const [legacy, setLegacy] = useState<LegacyPlanSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const selection = useRef(0);
  const actionLock = useRef(false);
  const selectedArtifact = useRef<string | null>(null);
  const editorDirty = useRef(false);
  editorDirty.current = editing && editor !== original;
  const activeRun = history.find(item => isRunning(item.status));
  const blocked = history.some(item => blocksSubmission(item.status));

  function installArtifact(item: WorkflowArtifact) {
    selectedArtifact.current = item.artifact_id;
    setArtifact(item);
    setResponseId("");
    const plan = ["PLAN", "APPROVED_PLAN"].includes(item.stage) && item.status === "completed";
    setEditing(plan);
    const text = plan ? item.result?.text || "" : "";
    setEditor(text); setOriginal(text);
    setEditorParent(plan ? item.artifact_id : null);
  }
  function mergeArtifact(item: WorkflowArtifact) {
    setHistory(current => [item, ...current.filter(row => row.artifact_id !== item.artifact_id)]
      .sort((a, b) => b.version_number - a.version_number));
  }
  async function refreshList() {
    const items = await browseProductions();
    setProductions(items); setProductionOffset(items.length); setMoreProductions(items.length === 100);
  }
  async function openProduction(id: string) {
    if (editorDirty.current && !window.confirm("Quitter le plan sans enregistrer ces modifications ?")) return;
    const token = ++selection.current;
    setBusy(true); setError(""); setNotice("");
    setProduction(null); setHistory([]); setArtifact(null); setLegacy([]);
    setEditing(false); setEditor(""); setOriginal(""); selectedArtifact.current = null;
    try {
      const [saved, items] = await Promise.all([readProduction(id), browseArtifacts(id)]);
      if (token !== selection.current) return;
      setProduction(saved); setHistory(items); setHistoryOffset(items.length); setMoreHistory(items.length === 100);
      const url = new URL(window.location.href); url.searchParams.set("production", id);
      window.history.replaceState(null, "", url.toString());
      const first = items.find(row => blocksSubmission(row.status)) || items[0];
      if (first) {
        const detail = await readArtifact(id, first.artifact_id);
        if (token === selection.current) installArtifact(detail);
      }
    } catch (err) { if (token === selection.current) setError(message(err)); }
    finally { if (token === selection.current) setBusy(false); }
  }

  useEffect(() => {
    let alive = true;
    async function init() {
      const results = await Promise.allSettled([
        mode === "create" ? api.get("/touch/reports?archive=active&limit=100&offset=0") : Promise.resolve({ reports: [] }),
        mode === "list" ? browseProductions() : Promise.resolve([]),
      ]);
      if (!alive) return;
      if (results[0].status === "fulfilled") {
        const rows: SourceReport[] = results[0].value.reports;
        setReports(rows); setReportOffset(rows.length); setMoreReports(rows.length === 100);
      }
      if (results[1].status === "fulfilled") {
        const rows = results[1].value;
        setProductions(rows); setProductionOffset(rows.length); setMoreProductions(rows.length === 100);
      }
      const failures = results.filter((r): r is PromiseRejectedResult => r.status === "rejected");
      if (failures.length) setError(failures.map(r => message(r.reason)).join(" · "));
      setLoading(false);
      const id = new URLSearchParams(window.location.search).get("production");
      if (id && mode === "list") await openProduction(id);
      if (id && mode === "create") window.location.replace(`/admin/production/reports?production=${encodeURIComponent(id)}`);
    }
    void init();
    return () => { alive = false; selection.current += 1; };
    // Initial load only; further opens are explicit.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!production || !activeRun?.response_id) return;
    const prodId = production.production_id;
    const runId = activeRun.artifact_id;
    const token = selection.current;
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        const updated = await refreshArtifact(prodId, runId);
        if (stopped || token !== selection.current) return;
        mergeArtifact(updated);
        if (selectedArtifact.current === runId) {
          if (updated.status === "completed" && updated.stage === "PLAN" && !editorDirty.current) installArtifact(updated);
          else setArtifact(updated);
        }
        if (isRunning(updated.status)) timer = setTimeout(() => void poll(), 8000);
        else { setNotice("Le résultat et son diagnostic sont enregistrés dans la production."); void refreshList().catch(err => setError(message(err))); }
      } catch (err) {
        if (!stopped) setError(`${message(err)} Le suivi automatique est suspendu. Utilisez « Actualiser le suivi ».`);
      }
    }
    timer = setTimeout(() => void poll(), 1500);
    return () => { stopped = true; clearTimeout(timer); };
    // Stable run ID: polling updates the status without restarting its timer.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [production?.production_id, activeRun?.artifact_id, activeRun?.response_id]);

  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => {
      if (editorDirty.current) { event.preventDefault(); event.returnValue = ""; }
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, []);

  async function act(action: () => Promise<void>) {
    if (actionLock.current) return;
    actionLock.current = true; setBusy(true); setError(""); setNotice("");
    try { await action(); }
    catch (err) { setError(message(err)); }
    finally { actionLock.current = false; setBusy(false); }
  }
  async function create() {
    const res = await api.post("/production/", {
      title: title.trim(), report_ids: selected, objective: objective.trim(),
      target_audience: audience.trim(), output_language: language,
      output_format: "AUTONOMOUS_REPORT", target_page_count: pages,
    });
    window.location.assign(`/admin/production/reports?production=${encodeURIComponent(res.production.production_id)}`);
  }
  async function chooseArtifact(id: string) {
    if (!production) return;
    if (editorDirty.current && !window.confirm("Quitter le plan sans enregistrer ces modifications ?")) return;
    const token = selection.current;
    const detail = await readArtifact(production.production_id, id);
    if (token === selection.current) installArtifact(detail);
  }
  async function savePlan() {
    if (!production) return;
    const item = await saveReviewedPlan(production.production_id, crypto.randomUUID(), editor, editorParent);
    mergeArtifact(item); installArtifact(item); await refreshList();
    setNotice("Plan validé et enregistré. Vous pouvez maintenant générer le rapport depuis cette version.");
  }
  async function submitDocument() {
    if (!production || !artifact) return;
    const item = await generationRequest(`${production.production_id}:document:${artifact.artifact_id}`,
      id => startDocument(production.production_id, id, artifact.artifact_id));
    mergeArtifact(item); installArtifact(item); await refreshList();
  }
  async function submitPlan() {
    if (!production) return;
    if (editorDirty.current && !window.confirm("Quitter le plan sans enregistrer ces modifications ?")) return;
    const item = await generationRequest(`${production.production_id}:plan`,
      id => startPlan(production.production_id, id));
    mergeArtifact(item); installArtifact(item); await refreshList();
  }
  async function refreshSelected() {
    if (!production || !artifact) return;
    const item = await refreshArtifact(production.production_id, artifact.artifact_id, responseId.trim());
    mergeArtifact(item);
    if (!editorDirty.current) installArtifact(item); else setArtifact(item);
    await refreshList();
  }
  async function uploadDocument(file: File) {
    if (!production) return;
    if (file.size > 5 * 1024 * 1024) throw new Error("Le fichier JSON dépasse 5 Mo.");
    const value = JSON.parse(await file.text()) as ProductionDocument;
    const item = await importDocument(production.production_id, crypto.randomUUID(), value,
      artifact?.stage === "APPROVED_PLAN" ? artifact.artifact_id : null);
    mergeArtifact(item); installArtifact(item); await refreshList();
    setNotice("Document importé, contrôlé contre le socle et enregistré, sans appel LLM.");
  }
  async function loadLegacy(version?: number) {
    if (!production) return;
    if (!version) {
      const res = await api.get(`/production/${encodeURIComponent(production.production_id)}/plans?limit=100&offset=0`);
      setLegacy(res.plans); if (!res.plans.length) setNotice("Aucun plan de l'ancien moteur.");
    } else {
      if (editorDirty.current && !window.confirm("Remplacer le plan non enregistré ?")) return;
      const res = await api.get(`/production/${encodeURIComponent(production.production_id)}/plan?version=${version}`);
      const text = legacyText(res.plan.snapshot.plan);
      setArtifact(null); selectedArtifact.current = null;
      setEditing(true); setEditor(text); setOriginal(""); setEditorParent(null);
      setNotice("Ancien plan chargé comme brouillon. Relisez-le avant de le valider dans le nouveau parcours.");
    }
  }

  const approved = artifact?.stage === "APPROVED_PLAN" && artifact.status === "completed";
  const unchangedApproved = approved && editor === original;
  const document = artifact?.status === "completed" ? artifact.result?.document : null;

  return <div className="mx-auto max-w-[1600px] space-y-6">
    <header className="flex flex-wrap items-start justify-between gap-3">
      <div><h1 className="text-2xl font-semibold">{mode === "create" ? "Nouvelle production" : "Productions enregistrées"}</h1>
        <p className="mt-2 text-sm text-slate-500">Rapports Touch sauvegardés → plan relu → rapport autonome.</p></div>
      <div className="flex flex-wrap gap-2">
        <Link className={BUTTON} onClick={event => {
          if (editorDirty.current && !window.confirm("Quitter le plan sans enregistrer ces modifications ?")) event.preventDefault();
        }} href={mode === "create" ? "/admin/production/reports" : "/admin/production"}>{mode === "create" ? "Voir les productions" : "Nouvelle production"}</Link>
        {mode === "list" && <button className={BUTTON} disabled={busy} onClick={() => void act(refreshList)}>Actualiser la liste</button>}
      </div>
    </header>
    {error && <p role="alert" className="rounded-lg bg-red-50 p-4 text-sm text-red-800">{error}</p>}
    {notice && <p role="status" className="rounded-lg bg-emerald-50 p-4 text-sm text-emerald-900">{notice}</p>}
    {loading ? <p>Chargement…</p> : <div className={mode === "create" ? "max-w-3xl" : "grid items-start gap-6 xl:grid-cols-[330px_minmax(0,1fr)]"}>
      <aside className="min-w-0 space-y-5">
        {mode === "create" && <details className={PANEL} open>
          <summary className="cursor-pointer font-semibold">Nouvelle production</summary>
          <label className="block text-sm">Titre<input className={INPUT} value={title} maxLength={250} onChange={e => setTitle(e.target.value)} /></label>
          <label className="block text-sm">Objectif<textarea className={INPUT} rows={3} value={objective} maxLength={5000} onChange={e => setObjective(e.target.value)} /></label>
          <label className="block text-sm">Public<input className={INPUT} value={audience} maxLength={2000} onChange={e => setAudience(e.target.value)} /></label>
          <div className="grid grid-cols-2 gap-3">
            <label className="text-sm">Langue<select className={INPUT} value={language} onChange={e => setLanguage(e.target.value as "fr" | "en")}><option value="fr">Français</option><option value="en">Anglais</option></select></label>
            <label className="text-sm">Pages<select className={INPUT} value={pages ?? "auto"} onChange={e => setPages(e.target.value === "auto" ? null : Number(e.target.value))}>
              <option value="auto">Automatique</option>{Array.from({ length: 37 }, (_, i) => i + 4).map(n => <option key={n} value={n}>{n}</option>)}
            </select></label>
          </div>
          <p className="text-xs text-slate-500">Format disponible : rapport autonome GetCurator. Le format avec speaker sera intégré ultérieurement.</p>
          <div className="border-t pt-3"><h3 className="mb-2 text-sm font-medium">Rapports Touch · {selected.length}/20</h3>
            <input className={INPUT} placeholder="Filtrer les rapports chargés" value={reportSearch} onChange={e => setReportSearch(e.target.value)} />
            <div className="mt-3 max-h-80 space-y-2 overflow-y-auto">
              {reports.filter(r => (r.subject || "").toLocaleLowerCase().includes(reportSearch.toLocaleLowerCase())).map(r => <label key={r.report_id} className="flex gap-2 rounded border p-3 text-sm">
                <input type="checkbox" checked={selected.includes(r.report_id)} disabled={busy || (!selected.includes(r.report_id) && selected.length >= 20)}
                  onChange={() => setSelected(values => values.includes(r.report_id) ? values.filter(v => v !== r.report_id) : [...values, r.report_id])} />
                <span>{r.subject}<span className="mt-1 block text-xs text-slate-500">{r.output_language?.toUpperCase()} · {r.period_start} / {r.period_end}</span></span>
              </label>)}
            </div>
            {moreReports && <button className={`${BUTTON} mt-3`} disabled={busy} onClick={() => void act(async () => {
              const res = await api.get(`/touch/reports?archive=active&limit=100&offset=${reportOffset}`);
              const rows: SourceReport[] = res.reports;
              setReports(current => [...current, ...rows.filter(r => !current.some(c => c.report_id === r.report_id))]);
              setReportOffset(reportOffset + rows.length); setMoreReports(rows.length === 100);
            })}>Charger plus de rapports</button>}
          </div>
          <button className={`${PRIMARY} w-full`} disabled={busy || !title.trim() || !selected.length} onClick={() => void act(create)}>Créer la production</button>
        </details>}
        {mode === "list" && <section className={PANEL}>
          <h2 className="font-semibold">Productions enregistrées</h2>
          <input className={INPUT} value={productionSearch} onChange={e => setProductionSearch(e.target.value)} placeholder="Filtrer les productions chargées" />
          {!productions.length && <p className="text-sm text-slate-500">Aucune production enregistrée.</p>}
          {productions.filter(p => p.title.toLocaleLowerCase().includes(productionSearch.toLocaleLowerCase())).map(p => <button key={p.production_id} disabled={busy}
            onClick={() => void openProduction(p.production_id)} className={`w-full rounded-lg border p-3 text-left ${production?.production_id === p.production_id ? "border-emerald-500 bg-emerald-50" : "bg-white"}`}>
            <span className="block text-sm font-medium">{p.title}</span>
            <span className="mt-1 block text-xs text-slate-500">{p.workflow?.latest ? `${stageLabel(p.workflow.latest.STAGE)} · ${statusLabel(p.workflow.latest.STATUS)}` : "Socle préparé"}</span>
            <span className="mt-1 block text-xs text-slate-500">{p.workflow?.document_count || 0} rapport(s) · {date(p.workflow?.updated_at || p.updated_at)}</span>
          </button>)}
          {moreProductions && <button className={BUTTON} disabled={busy} onClick={() => void act(async () => {
            const rows = await browseProductions(productionOffset);
            setProductions(current => [...current, ...rows.filter(r => !current.some(c => c.production_id === r.production_id))]);
            setProductionOffset(productionOffset + rows.length); setMoreProductions(rows.length === 100);
          })}>Charger plus de productions</button>}
        </section>}
      </aside>
      {mode === "list" && <main className="min-w-0 space-y-5">
        {!production ? <div className={PANEL}>Créez une production ou ouvrez une production enregistrée.</div> : <>
          <section className={PANEL}>
            <h2 className="text-xl font-semibold">{production.title}</h2>
            <p className="text-sm text-slate-600">{production.corpus.request.objective || "Aucun objectif complémentaire."}</p>
            <p className="text-xs text-slate-500">{production.output_language.toUpperCase()} · Rapport autonome · {production.target_page_count ? `${production.target_page_count} pages souhaitées` : "Longueur automatique"}</p>
            <details><summary className="cursor-pointer text-sm">{production.corpus.reports.length} rapports sources · socle conservé</summary>
              <ul className="mt-2 space-y-2 text-sm">{production.corpus.reports.map(r => <li key={r.report_id}>{r.payload.subject || r.report_id} · v{r.version_number}</li>)}</ul>
            </details>
            {production.output_format !== "AUTONOMOUS_REPORT" && <p className="text-sm text-amber-800">Cette ancienne production utilise le format speaker, non pris en charge par le moteur intégré. Créez un rapport autonome depuis les mêmes sources.</p>}
            <div className="flex flex-wrap gap-2">
              <button className={PRIMARY} disabled={busy || blocked || production.output_format !== "AUTONOMOUS_REPORT"} onClick={() => void act(submitPlan)}>Générer un nouveau plan</button>
              <button className={BUTTON} disabled={busy || blocked} onClick={() => {
                if (editorDirty.current && !window.confirm("Remplacer le plan non enregistré ?")) return;
                setArtifact(null); selectedArtifact.current = null; setEditing(true); setEditor(""); setOriginal(""); setEditorParent(null);
              }}>Coller un plan déjà relu</button>
              <label className={`${BUTTON} cursor-pointer ${busy || blocked ? "opacity-50" : ""}`}>Importer un document JSON
                <input type="file" accept="application/json,.json" className="sr-only" disabled={busy || blocked} onChange={e => {
                  const file = e.target.files?.[0]; e.target.value = "";
                  if (file) void act(() => uploadDocument(file));
                }} />
              </label>
            </div>
            <p className="text-xs text-slate-500">Les générations sont payantes. Sauvegarder, importer et actualiser une réponse existante ne déclenche aucune nouvelle génération.</p>
          </section>
          <section className={PANEL}>
            <h3 className="font-semibold">Historique des plans et rapports</h3>
            {!history.length && <p className="text-sm text-slate-500">Aucune version dans le nouveau parcours.</p>}
            <div className="flex max-h-64 flex-col gap-2 overflow-y-auto">{history.map(item => <button key={item.artifact_id} className={`${BUTTON} text-left ${artifact?.artifact_id === item.artifact_id ? "border-emerald-500 bg-emerald-50" : ""}`}
              disabled={busy} onClick={() => void act(() => chooseArtifact(item.artifact_id))}>
              V{item.version_number} · {stageLabel(item.stage)} · {statusLabel(item.status)}<span className="ml-2 text-xs text-slate-500">{date(item.created_at)}</span>
            </button>)}</div>
            {moreHistory && <button className={BUTTON} disabled={busy} onClick={() => void act(async () => {
              const rows = await browseArtifacts(production.production_id, historyOffset);
              setHistory(current => [...current, ...rows.filter(r => !current.some(c => c.artifact_id === r.artifact_id))]);
              setHistoryOffset(historyOffset + rows.length); setMoreHistory(rows.length === 100);
            })}>Charger plus de versions</button>}
            <details><summary className="cursor-pointer text-xs text-slate-500">Historique de l’ancien moteur</summary>
              <button className={`${BUTTON} mt-2`} disabled={busy} onClick={() => void act(() => loadLegacy())}>Charger les anciens plans</button>
              {legacy.map(p => <button key={p.plan_id} className={`${BUTTON} ml-2 mt-2`} disabled={busy} onClick={() => void act(() => loadLegacy(p.plan_version))}>Reprendre le plan v{p.plan_version}</button>)}
            </details>
          </section>
          {artifact && <section className={PANEL}>
            <div className="flex flex-wrap items-center justify-between gap-3"><h3 className="font-semibold">V{artifact.version_number} · {stageLabel(artifact.stage)} · {statusLabel(artifact.status)}</h3>
              <button className={BUTTON} onClick={() => download(`production-v${artifact.version_number}-diagnostic.json`, JSON.stringify(artifact, null, 2))}>Télécharger le diagnostic</button></div>
            {artifact.model && <p className="text-xs text-slate-500">Modèle : {artifact.model}</p>}
            {isRunning(artifact.status) && <p className="text-sm">Le traitement continue en arrière-plan. Vous pouvez fermer cette page puis rouvrir la production.</p>}
            {artifact.result?.error && <p className="rounded bg-amber-50 p-3 text-sm text-amber-900">{artifact.result.error.message || JSON.stringify(artifact.result.error)}</p>}
            {artifact.status !== "completed" && artifact.stage !== "APPROVED_PLAN" && <div className="space-y-3">
              {!artifact.response_id && <label className="block text-sm">Rattacher un identifiant de réponse retrouvé dans les logs
                <input className={INPUT} value={responseId} placeholder="resp_…" onChange={e => setResponseId(e.target.value)} /></label>}
              <button className={BUTTON} disabled={busy || (!artifact.response_id && !responseId.startsWith("resp_"))} onClick={() => void act(refreshSelected)}>Actualiser le suivi / revérifier sans régénérer</button>
            </div>}
            {artifact.result?.text && !editing && !document && <details><summary className="cursor-pointer text-sm">Texte reçu — peut être partiel</summary><pre className="mt-3 whitespace-pre-wrap break-words text-xs">{artifact.result.text}</pre></details>}
          </section>}
          {editing && <section className={PANEL}>
            <h3 className="font-semibold">{approved ? "Plan validé" : "Plan à relire"}</h3>
            <p className="text-sm text-slate-500">Relisez les constats, les chiffres et leurs périodes. Toute validation enregistre une nouvelle version du plan.</p>
            <textarea className={`${INPUT} min-h-[420px] font-mono`} value={editor} maxLength={150000} onChange={e => setEditor(e.target.value)} />
            <div className="flex flex-wrap gap-2">
              <button className={PRIMARY} disabled={busy || blocked || !editor.trim() || unchangedApproved} onClick={() => void act(savePlan)}>{approved ? "Enregistrer et valider les modifications" : "Valider et enregistrer le plan"}</button>
              <button className={PRIMARY} disabled={busy || blocked || !unchangedApproved || production.output_format !== "AUTONOMOUS_REPORT"} onClick={() => void act(submitDocument)}>Générer le rapport depuis ce plan validé</button>
              <button className={BUTTON} disabled={!editor.trim()} onClick={() => download("plan-getcurator.md", editor, "text/markdown;charset=utf-8")}>Télécharger le plan</button>
            </div>
            {editor !== original && <p className="text-xs text-amber-800">Modifications non enregistrées.</p>}
          </section>}
          {document && <>
            <div className="flex flex-wrap gap-3"><button className={BUTTON} onClick={() => download("document-getcurator.json", JSON.stringify(document, null, 2))}>Télécharger le document JSON</button>
              {artifact?.parent_artifact_id && <button className={BUTTON} disabled={busy} onClick={() => void act(() => chooseArtifact(artifact.parent_artifact_id!))}>Ouvrir le plan source</button>}</div>
            <ProductionDocumentPreview document={document} />
          </>}
        </>}
      </main>}
    </div>}
  </div>;
}
