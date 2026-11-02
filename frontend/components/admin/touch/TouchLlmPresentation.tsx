"use client";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { TouchCorpusNotebook } from "@/types/touch";
import type { TouchPresentationOptions } from "@/lib/touch-presentation";
import { listTouchPresentations, readTouchPresentation, startTouchPresentation,
  refreshTouchPresentation, activePresentation } from "@/lib/touch-presentation-workflow";
import type { TouchPresentationJob } from "@/lib/touch-presentation-workflow";
import TouchPresentationPreview from "@/components/admin/touch/TouchPresentationPreview";
const BUTTON = "rounded-lg border px-4 py-2 text-sm disabled:opacity-50";
const errorText = (e: unknown) => e instanceof Error ? e.message : "Opération impossible.";
// Compare content, not property order; canonical Numbers are not presentation inputs.
function canonical(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object") return `{${Object.keys(value).filter(k => !["validated_numbers", "quarantined_numbers"].includes(k)).sort()
    .map(k => `${JSON.stringify(k)}:${canonical((value as Record<string, unknown>)[k])}`).join(",")}}`;
  return JSON.stringify(value) ?? "null";
}
export default function TouchLlmPresentation(props: TouchPresentationOptions & { reportId: string | null }) {
  const { reportId, notebook } = props;
  const [jobs, setJobs] = useState<TouchPresentationJob[]>([]);
  const [selected, setSelected] = useState<TouchPresentationJob | null>(null);
  const [version, setVersion] = useState<number | null>(null);
  const [matches, setMatches] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [responseId, setResponseId] = useState("");
  const [offset, setOffset] = useState(0);
  const [more, setMore] = useState(false);
  const [ready, setReady] = useState(false);
  const action = useRef(false), epoch = useRef(0), chosen = useRef<string | null>(null);
  const pendingKey = useRef<string | null>(null);
  const running = jobs.find(item => activePresentation(item.status));
  function merge(item: TouchPresentationJob) {
    setJobs(current => [item, ...current.filter(j => j.artifact_id !== item.artifact_id)]
      .sort((a,b) => b.version_number - a.version_number));
  }
  function install(item: TouchPresentationJob) {
    chosen.current = item.artifact_id; setSelected(item); setResponseId("");
  }
  useEffect(() => {
    const token = ++epoch.current;
    setReady(false); setJobs([]); setSelected(null); setVersion(null); setMatches(false); setError("");
    chosen.current = null; pendingKey.current = null;
    if (!reportId) return;
    const id = reportId;
    async function init() {
      try {
        const [saved, history] = await Promise.all([api.get(`/touch/reports/${encodeURIComponent(id)}`), listTouchPresentations(id)]);
        if (epoch.current !== token) return;
        const report = saved.report as { version_number: number; notebook: TouchCorpusNotebook };
        setVersion(report.version_number); setMatches(canonical(report.notebook) === canonical(notebook));
        setJobs(history); setOffset(history.length); setMore(history.length === 30);
        const first = history.find(j => activePresentation(j.status)) || history[0];
        if (first) {
          const detail = await readTouchPresentation(id, first.artifact_id);
          if (epoch.current === token) install(detail);
        }
        if (epoch.current === token) setReady(true);
      } catch (e) { if (epoch.current === token) setError(errorText(e)); }
    }
    void init();
    return () => { epoch.current++; };
  }, [reportId, notebook]);
  useEffect(() => {
    if (!reportId || !running?.response_id || !["queued", "in_progress"].includes(running.status)) return;
    const id = reportId, artifact = running.artifact_id, token = epoch.current;
    let stop = false;
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        const item = await refreshTouchPresentation(id, artifact);
        if (stop || token !== epoch.current) return;
        merge(item); if (chosen.current === artifact) setSelected(item);
        if (["queued", "in_progress"].includes(item.status)) timer = setTimeout(() => void poll(), 8000);
      } catch (e) { if (!stop && token === epoch.current) setError(`${errorText(e)} Suivi suspendu : utilisez Actualiser.`); }
    }
    timer = setTimeout(() => void poll(), 1500);
    return () => { stop = true; clearTimeout(timer); };
  }, [reportId, running?.artifact_id, running?.response_id]);
  async function act(run: () => Promise<void>) {
    if (action.current) return;
    action.current = true; setBusy(true); setError("");
    try { await run(); } catch (e) { setError(errorText(e)); }
    finally { action.current = false; setBusy(false); }
  }
  async function generate() {
    if (!reportId || !version || !ready || !matches || running) return;
    const id = reportId, token = epoch.current;
    const key = `getcurator-touch-presentation:${id}:${version}`;
    if (!pendingKey.current) {
      try { pendingKey.current = localStorage.getItem(key); } catch { /* optional storage */ }
    }
    const artifact = pendingKey.current || crypto.randomUUID();
    pendingKey.current = artifact;
    try { localStorage.setItem(key, artifact); } catch { /* ref still prevents an accidental duplicate */ }
    const item = await startTouchPresentation(id, artifact, version);
    try { localStorage.removeItem(key); } catch { /* optional storage */ }
    pendingKey.current = null;
    if (epoch.current !== token) return;
    merge(item); install(item);
  }
  const doc = selected?.status === "completed" ? selected.result?.document : null;
  if (!reportId) return <p className="rounded border bg-amber-50 p-4 text-sm">Enregistrez le rapport pour générer sa présentation éditorialisée.</p>;
  return <section className="space-y-4 rounded-xl border bg-white p-5">
    <h3 className="text-lg font-semibold">Présentation éditorialisée</h3>
    <p className="text-sm text-slate-600">Le LLM regroupe et hiérarchise le rapport enregistré, sans nouvel angle ni information extérieure. Les générations sont payantes ; la lecture et l’actualisation ne régénèrent rien.</p>
    {error && <p role="alert" className="rounded bg-red-50 p-3 text-sm text-red-800">{error}</p>}
    {ready && !matches && <p className="rounded bg-amber-50 p-3 text-sm">Le Notebook affiché diffère du rapport enregistré. Enregistrez-le ou rouvrez le rapport avant de générer.</p>}
    <div className="flex flex-wrap gap-3">
      <button type="button" className={BUTTON} disabled={busy || !ready || !matches || !!running}
        onClick={() => void act(generate)}>{busy ? "Traitement…" : jobs.length ? "Générer une nouvelle version" : "Générer la présentation"}</button>
      <button type="button" className={BUTTON} disabled={busy} onClick={() => void act(async () => {
        const token = epoch.current;
        const history = await listTouchPresentations(reportId);
        if (token !== epoch.current) return;
        setJobs(history); setOffset(history.length); setMore(history.length === 30);
        if (!ready) {
          const saved = await api.get(`/touch/reports/${encodeURIComponent(reportId)}`);
          if (token !== epoch.current) return;
          setVersion(saved.report.version_number); setMatches(canonical(saved.report.notebook) === canonical(notebook)); setReady(true);
        }
      })}>Actualiser l’historique</button>
    </div>
    {jobs.length > 0 && <div className="flex max-h-60 flex-col gap-2 overflow-auto">{jobs.map(job => <button type="button" key={job.artifact_id}
      disabled={busy} className={`${BUTTON} text-left ${selected?.artifact_id === job.artifact_id ? "bg-blue-50" : ""}`}
      onClick={() => void act(async () => { const token = epoch.current; const detail = await readTouchPresentation(reportId,job.artifact_id);
        if (token === epoch.current) install(detail); })}>Présentation V{job.version_number} · Rapport V{job.report_version} · {job.status}</button>)}</div>}
    {more && <button type="button" className={BUTTON} disabled={busy} onClick={() => void act(async () => {
      const token = epoch.current; const rows = await listTouchPresentations(reportId, offset);
      if (token !== epoch.current) return;
      setJobs(current => [...current,...rows.filter(r=>!current.some(c=>c.artifact_id===r.artifact_id))]);
      setOffset(offset + rows.length); setMore(rows.length===30);
    })}>Charger les versions précédentes</button>}
    {selected && <div className="space-y-3">
      {version !== selected.report_version && <p className="rounded bg-amber-50 p-3 text-sm">Cette présentation correspond à une ancienne version du rapport.</p>}
      {selected.result?.error?.message && <p role="alert" className="rounded bg-amber-50 p-3 text-sm">{selected.result.error.message}</p>}
      {activePresentation(selected.status) && <p className="text-sm">Traitement enregistré. Vous pouvez quitter cette page puis revenir pour consulter le suivi.</p>}
      {selected.status !== "completed" && <div className="space-y-2">
        {!selected.response_id && <input className="w-full rounded border px-3 py-2 text-sm" placeholder="Rattacher le resp_ retrouvé dans les logs"
          aria-label="Identifiant de réponse" value={responseId} onChange={e=>setResponseId(e.target.value)} />}
        <button type="button" className={BUTTON} disabled={busy || (!selected.response_id && !responseId.startsWith("resp_"))}
          onClick={() => void act(async () => { const token = epoch.current;
            const item=await refreshTouchPresentation(reportId,selected.artifact_id,responseId.trim());
            if (token !== epoch.current) return; merge(item); install(item);
          })}>Actualiser le suivi / revérifier sans régénérer</button>
      </div>}
      {selected.result?.text && !doc && <details><summary className="cursor-pointer text-sm">Texte reçu et diagnostic</summary><pre className="whitespace-pre-wrap break-words text-xs">{JSON.stringify(selected.result,null,2)}</pre></details>}
      {doc && <>
        <TouchPresentationPreview {...props} documentOverride={doc} key={selected.artifact_id}
          outputLanguage={selected.result?.export_context?.output_language || props.outputLanguage}
          periodStart={selected.result?.export_context ? selected.result.export_context.period_start : props.periodStart}
          periodEnd={selected.result?.export_context ? selected.result.export_context.period_end : props.periodEnd} />
        <details><summary className="cursor-pointer text-sm">Couverture des chapitres et contrôles</summary>
          <pre className="whitespace-pre-wrap break-words text-xs">{JSON.stringify({ coverage:selected.result?.section_coverage, notes:selected.result?.validation_notes },null,2)}</pre>
        </details>
      </>}
    </div>}
  </section>;
}
