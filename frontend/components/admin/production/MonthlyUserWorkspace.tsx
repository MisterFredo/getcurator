"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import ProductionDocumentPreview from "./ProductionDocumentPreview";
import type { ProductionSourceMetadata } from "./ProductionDocumentPreview";
import type { ProductionDocument } from "@/types/production-document";
import type { PdfExportContext } from "@/lib/production-export";

type Recipient = { id: string; name: string; company?: string | null };
type Coverage = { complete: boolean; covered_days: number; expected_days: number;
  missing_days: string[]; digest_ids: string[]; period_start: string; period_end: string };
type CoverageResult = { current: Coverage; previous: Coverage; provisional: boolean; calendar_end: string };
type MonthlyRow = { production_id: string; name: string; user_id: string; month: string;
  language: string; status: string; provisional: boolean; created_at: string };
type Artifact = { artifact_id: string; stage: string; status: string; version_number: number;
  response_id?: string | null; request?: unknown; result?: unknown };
type Monthly = {
  production_id: string; title: string; status: string; language: string;
  monthly: { user_id: string; name: string; month: string; provisional: boolean;
    period_start: string; period_end: string; previous_month: string;
    comparison_mode: "MONTHLY_REPORT" | "DIGESTS" | "NONE";
    reference_production_id: string | null; current_coverage: Coverage; previous_coverage: Coverage };
  document: ProductionDocument | null; document_artifact_id: string | null;
  history: Artifact[]; latest_artifact: Artifact | null; document_attempts: number;
  error: { message?: string; issues?: { code: string; location: string; message: string }[] } | null;
  export_context: PdfExportContext; source_metadata: ProductionSourceMetadata;
  queue?: { queued: boolean; running: boolean; max_reports: number };
  last_activity?: string | null;
  simple_review?: { phase: string; review_completed?: boolean; repair_attempted?: boolean; repair_applied?: boolean;
    warnings: { location: string; message: string }[]; notes: string[];
    blockers: { location: string; message: string }[] } | null;
};

const LABELS: Record<string, string> = {
  prepared: "Prêt à démarrer", starting: "Démarrage", planning: "Préparation du plan",
  preparing_document: "Préparation de la rédaction", writing: "Rédaction", reviewing: "Relecture globale",
  correcting: "Corrections ciblées", completed: "Disponible", failed: "Intervention nécessaire",
  revalidating: "Revalidation technique du document sauvegardé",
  submission_unknown: "Acceptation à vérifier", needs_attention: "À vérifier",
};
const RUNNING = ["prepared", "starting", "planning", "preparing_document", "writing", "reviewing", "correcting", "revalidating"];
const INPUT = "w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm";
const BUTTON = "rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm disabled:opacity-50";
const PRIMARY = "rounded-lg bg-emerald-700 px-4 py-2 text-sm text-white disabled:opacity-50";
const PANEL = "space-y-4 rounded-xl border border-slate-200 bg-white p-5";
const message = (e: unknown) => e instanceof Error ? e.message : "Une erreur est survenue.";
function previousMonth() {
  const now = new Date();
  return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() - 1, 1)).toISOString().slice(0, 7);
}

function downloadDiagnostic(value: Monthly) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: "application/json" }));
  const link = document.createElement("a"); link.href = url;
  link.download = `monthly-${value.monthly.month}-diagnostic.json`; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function MonthlyUserWorkspace() {
  const [recipients, setRecipients] = useState<Recipient[]>([]);
  const [search, setSearch] = useState("");
  const [userId, setUserId] = useState("");
  const [month, setMonth] = useState(previousMonth);
  const [language, setLanguage] = useState<"fr" | "en">("en");
  const [allowIncomplete, setAllowIncomplete] = useState(false);
  const [newVersion, setNewVersion] = useState(false);
  const [coverage, setCoverage] = useState<CoverageResult | null>(null);
  const [coverageLoading, setCoverageLoading] = useState(false);
  const [coverageError, setCoverageError] = useState("");
  const [filterUser, setFilterUser] = useState("");
  const [filterMonth, setFilterMonth] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [offset, setOffset] = useState(0);
  const [rows, setRows] = useState<MonthlyRow[]>([]);
  const [more, setMore] = useState(false);
  const [listLoading, setListLoading] = useState(false);
  const [reload, setReload] = useState(0);
  const [selected, setSelected] = useState<Monthly | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [pollError, setPollError] = useState("");
  const [responseId, setResponseId] = useState("");
  const [viewGeneration, setViewGeneration] = useState(0);
  const controlsBusy = busy;
  const openSequence = useRef(0);
  const actionLock = useRef(false);
  const shouldPoll = Boolean(selected && RUNNING.includes(selected.status));

  useEffect(() => {
    let active = true;
    api.get("/production/monthly-users/recipients").then(res => {
      if (active) setRecipients(res.recipients ?? []);
    }).catch(e => { if (active) setError(message(e)); });
    const id = new URLSearchParams(window.location.search).get("monthly");
    if (id) void openMonthly(id);
    return () => { active = false; openSequence.current += 1; };
    // Initial source list and optional saved Monthly.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    let active = true;
    setCoverage(null); setCoverageError(""); setAllowIncomplete(false);
    setCoverageLoading(false);
    if (!userId || !month) return;
    setCoverageLoading(true);
    api.get(`/production/monthly-users/coverage?user_id=${encodeURIComponent(userId)}&month=${encodeURIComponent(month)}`)
      .then(res => { if (active) setCoverage(res); })
      .catch(e => { if (active) setCoverageError(message(e)); })
      .finally(() => { if (active) setCoverageLoading(false); });
    return () => { active = false; };
  }, [userId, month]);

  useEffect(() => {
    let active = true;
    setListLoading(true);
    const params = new URLSearchParams({ user_id: filterUser, month: filterMonth,
      status: filterStatus, limit: "50", offset: String(offset) });
    api.get(`/production/monthly-users?${params.toString()}`).then(res => {
      if (!active) return;
      const items: MonthlyRow[] = res.monthlies ?? [];
      setRows(items); setMore(items.length === 50);
    }).catch(e => { if (active) setError(message(e)); })
      .finally(() => { if (active) setListLoading(false); });
    return () => { active = false; };
  }, [filterUser, filterMonth, filterStatus, offset, reload]);

  async function openMonthly(id: string) {
    const token = ++openSequence.current;
    setBusy(true); setError(""); setPollError("");
    try {
      const res = await api.get(`/production/monthly-users/${encodeURIComponent(id)}`);
      if (token !== openSequence.current) return;
      setSelected(res.monthly); setResponseId("");
      const url = new URL(window.location.href); url.searchParams.set("monthly", id);
      window.history.replaceState(null, "", url.toString());
    } catch (e) { if (token === openSequence.current) setError(message(e)); }
    finally { if (token === openSequence.current) { setBusy(false); setViewGeneration(value => value + 1); } }
  }

  useEffect(() => {
    if (!selected || !shouldPoll) return;
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const id = selected.production_id;
    const token = openSequence.current;
    async function poll() {
      try {
        const res = await api.get(`/production/monthly-users/${encodeURIComponent(id)}`);
        if (!active || token !== openSequence.current) return;
        setSelected(res.monthly); setPollError("");
        if (RUNNING.includes(res.monthly.status)) {
          // Reading does not write BQ or enqueue duplicate background workers.
          // Resume explicitly only when no worker survives a process restart.
          if (res.monthly.queue && !res.monthly.queue.running && !res.monthly.queue.queued) {
            await api.post(`/production/monthly-users/${encodeURIComponent(id)}/refresh`, {});
          }
          if (active) timer = setTimeout(() => void poll(), 4000);
        }
        else setReload(value => value + 1);
      } catch (e) {
        if (active) setPollError(`${message(e)} Le suivi est suspendu. Utilisez Actualiser / reprendre.`);
      }
    }
    timer = setTimeout(() => void poll(), 1500);
    return () => { active = false; clearTimeout(timer); };
    // Run one polling loop per opened Monthly; updates do not restart the timer.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected?.production_id, shouldPoll, viewGeneration]);

  async function start() {
    if (actionLock.current || !userId || !month) return;
    actionLock.current = true; setBusy(true); setError("");
    const key = `getcurator-monthly:${userId}:${month}:${language}:${newVersion ? "revision" : "initial"}`;
    let requestId: string = crypto.randomUUID();
    try {
      try {
        const old = localStorage.getItem(key);
        if (old && /^[0-9a-f-]{36}$/i.test(old)) requestId = old;
        localStorage.setItem(key, requestId);
      } catch { /* Durable server IDs remain authoritative. */ }
      const res = await api.post("/production/monthly-users", {
        request_id: requestId, user_id: userId, month, language,
        allow_incomplete: allowIncomplete, new_version: newVersion,
      });
      try { localStorage.removeItem(key); } catch { /* Optional local cache. */ }
      setSelected(null);
      await openMonthly(res.monthly.production_id);
      setReload(value => value + 1); setNewVersion(false);
    } catch (e) { setError(message(e)); }
    finally { setBusy(false); actionLock.current = false; }
  }

  async function refresh() {
    if (!selected || actionLock.current) return;
    actionLock.current = true; setBusy(true); setError("");
    try {
      await api.post(`/production/monthly-users/${selected.production_id}/refresh`,
        responseId.trim() ? { response_id: responseId.trim() } : {});
      // Remount the polling loop after a manual resume.
      const id = selected.production_id;
      setSelected(null); await openMonthly(id); setReload(value => value + 1);
    } catch (e) { setError(message(e)); }
    finally { setBusy(false); actionLock.current = false; }
  }

  const recipientOptions = recipients.filter(r => `${r.name} ${r.company || ""}`.toLowerCase().includes(search.toLowerCase()));
  const canStart = Boolean(userId && month && coverage && coverage.current.digest_ids.length
    && (coverage.current.complete || allowIncomplete) && !coverageLoading && !controlsBusy);

  return <div className="mx-auto max-w-[1600px] space-y-6">
    <header className="flex flex-wrap items-start justify-between gap-3">
      <div><h1 className="text-3xl font-semibold">Monthly Users</h1>
        <p className="mt-2 text-slate-500">Le bilan personnalisé du mois, avec évolution par rapport au mois précédent.</p></div>
      <Link className={BUTTON} href="/admin/production">Autres productions</Link>
    </header>
    {error && <p role="alert" className="rounded-lg bg-red-50 p-4 text-red-800">{error}</p>}
    <section className={PANEL}>
      <h2 className="text-xl font-semibold">Générer un Monthly</h2>
      <div className="grid gap-4 md:grid-cols-4">
        <label className="text-sm md:col-span-2">Utilisateur
          <input className={`${INPUT} mb-2`} value={search} placeholder="Rechercher par nom ou société" onChange={e => setSearch(e.target.value)} />
          <select className={INPUT} value={userId} onChange={e => setUserId(e.target.value)} disabled={controlsBusy}>
            <option value="">Choisir un utilisateur</option>
            {recipients.filter(r => r.id === userId || recipientOptions.some(o => o.id === r.id)).map(r =>
              <option key={r.id} value={r.id}>{r.name}{r.company ? ` · ${r.company}` : ""}</option>)}
          </select>
        </label>
        <label className="text-sm">Mois<input type="month" className={INPUT} value={month} disabled={controlsBusy} onChange={e => setMonth(e.target.value)} /></label>
        <label className="text-sm">Langue<select className={INPUT} value={language} disabled={controlsBusy} onChange={e => setLanguage(e.target.value as "fr" | "en")}><option value="en">English</option><option value="fr">Français</option></select></label>
      </div>
      {coverageLoading && <p className="text-sm text-slate-500">Vérification des éditions disponibles…</p>}
      {coverageError && <p role="alert" className="text-sm text-red-800">{coverageError}</p>}
      {coverage && <div className="rounded-lg bg-slate-50 p-4 text-sm space-y-2">
        <p><strong>{coverage.current.period_start} → {coverage.current.period_end}</strong> · {coverage.current.digest_ids.length} Digests · {coverage.current.covered_days}/{coverage.current.expected_days} jours couverts par leurs périodes.</p>
        <p>Mois précédent : {coverage.previous.digest_ids.length} Digests · {coverage.previous.covered_days}/{coverage.previous.expected_days} jours couverts. Le dernier Monthly disponible sera utilisé en priorité s’il existe.</p>
        {coverage.provisional && <p>Le mois est en cours : la période s’arrête à la dernière journée terminée et le rapport sera provisoire.</p>}
        {!coverage.current.complete && <>
          <p className="text-amber-800">Des périodes ne sont pas couvertes. <Link href="/admin/digest" className="underline">Compléter les Digests</Link></p>
          <label className="flex gap-2"><input type="checkbox" checked={allowIncomplete} onChange={e => setAllowIncomplete(e.target.checked)} />Générer une version provisoire en conservant cette limite visible.</label>
          <details><summary className="cursor-pointer">Jours non couverts</summary><p>{coverage.current.missing_days.join(", ")}</p></details>
        </>}
        <p className="text-xs text-slate-500">Dates de publication en Europe/Paris. La couverture des périodes de Digests ne certifie pas l’exhaustivité de la collecte amont.</p>
      </div>}
      <div className="flex flex-wrap items-center gap-4">
        <button type="button" className={PRIMARY} disabled={!canStart} onClick={() => void start()}>{busy ? "Traitement…" : "Générer / ouvrir le Monthly"}</button>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={newVersion} disabled={controlsBusy} onChange={e => setNewVersion(e.target.checked)} />Créer une nouvelle version, en conservant les précédentes.</label>
      </div>
      <p className="text-xs text-slate-500">Une présentation, une relecture globale et, si nécessaire, une passe de corrections ciblées. Les réserves restent visibles sans bloquer l’export. Sans nouvelle version, le document existant est repris.</p>
    </section>

    <section className={PANEL}>
      <div className="flex flex-wrap items-center justify-between gap-3"><h2 className="text-xl font-semibold">Historique des Monthly Users</h2>
        <button className={BUTTON} disabled={listLoading} onClick={() => setReload(v => v + 1)}>Actualiser la liste</button></div>
      <div className="flex flex-wrap gap-3">
        <select aria-label="Filtrer par utilisateur" className={INPUT + " md:!w-auto"} value={filterUser} onChange={e => { setFilterUser(e.target.value); setOffset(0); }}>
          <option value="">Tous les utilisateurs</option>{recipients.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
        </select>
        <input type="month" aria-label="Filtrer par mois" className={INPUT + " md:!w-auto"} value={filterMonth} onChange={e => { setFilterMonth(e.target.value); setOffset(0); }} />
        <select aria-label="Filtrer par statut" className={INPUT + " md:!w-auto"} value={filterStatus} onChange={e => { setFilterStatus(e.target.value); setOffset(0); }}>
          <option value="">Tous les statuts</option><option value="completed">Disponibles</option><option value="planning">Plan</option><option value="writing">Rédaction</option><option value="reviewing">Contrôle qualité</option><option value="needs_attention">À vérifier</option><option value="submission_unknown">Acceptation à vérifier</option>
        </select>
      </div>
      {listLoading && <p className="text-sm text-slate-500">Chargement…</p>}
      {!listLoading && !rows.length && <p className="text-sm text-slate-500">Aucun Monthly pour ces filtres.</p>}
      <div className="overflow-x-auto"><table className="w-full text-sm"><thead><tr className="border-b text-left text-slate-500">
        <th className="p-3">Utilisateur</th><th className="p-3">Mois</th><th className="p-3">Langue</th><th className="p-3">Statut</th><th className="p-3">Créé le</th><th className="p-3" />
      </tr></thead><tbody>{rows.map(row => <tr key={row.production_id} className="border-b">
        <td className="p-3 font-medium">{row.name}</td><td className="p-3">{row.month}{row.provisional ? " · provisoire" : ""}</td>
        <td className="p-3">{row.language.toUpperCase()}</td><td className="p-3">{LABELS[row.status] || row.status}</td>
        <td className="p-3">{new Date(row.created_at).toLocaleDateString("fr-FR")}</td>
        <td className="p-3"><button className={BUTTON} disabled={controlsBusy} onClick={() => void openMonthly(row.production_id)}>Ouvrir</button></td>
      </tr>)}</tbody></table></div>
      <div className="flex gap-3"><button className={BUTTON} disabled={!offset || listLoading} onClick={() => setOffset(v => Math.max(0, v - 50))}>Précédent</button><button className={BUTTON} disabled={!more || listLoading} onClick={() => setOffset(v => v + 50)}>Suivant</button></div>
    </section>

    {selected && <section className="space-y-5">
      <div className={PANEL}>
        <div className="flex flex-wrap items-center justify-between gap-3"><h2 className="text-xl font-semibold">{selected.monthly.name} · {selected.monthly.month}{selected.monthly.provisional ? " · Provisoire" : ""}</h2>
          <button className={BUTTON} disabled={controlsBusy} onClick={() => void refresh()}>Actualiser / reprendre</button></div>
        <p role="status" className="font-medium text-emerald-800">{selected.queue?.queued ? "En attente d’un créneau de production" : (selected.status === "completed" && (selected.simple_review?.warnings.length || selected.simple_review?.notes.length) ? "Disponible avec réserves" : LABELS[selected.status] || selected.status)}</p>
        {selected.queue?.queued && <p className="text-sm text-slate-500">La demande est enregistrée ; elle démarrera dès qu’un créneau sera disponible.</p>}
        {selected.simple_review && <div className="rounded-lg bg-slate-50 p-3 text-sm space-y-2">
          <p>Une relecture globale · Une passe de corrections au maximum · Aucune boucle de réécriture.</p>
          {selected.simple_review.phase === "review" && <p>Relecture du document enregistré…</p>}
          {selected.simple_review.phase === "repair" && <p>Correction des passages signalés…</p>}
          {selected.simple_review.phase === "released" && <p>{selected.simple_review.repair_applied ? "Corrections ciblées enregistrées." : selected.simple_review.repair_attempted ? "Le document antérieur est conservé." : selected.simple_review.review_completed ? "Aucune passe de correction nécessaire." : "La relecture n’a pas abouti."} Le document est disponible.</p>}
          {selected.simple_review.notes.map((note, i) => <p key={i} className="text-amber-900">{note}</p>)}
          {!!selected.simple_review.warnings.length && <div className="text-amber-900"><p className="font-medium">Réserves de relecture</p>{selected.simple_review.warnings.map((item, i) => <p key={i}>{item.location} · {item.message}</p>)}</div>}
        </div>}
        <p className="text-sm">Période : {selected.monthly.period_start} → {selected.monthly.period_end} · {selected.language.toUpperCase()} · {selected.document_attempts} versions du document.</p>
        <p className="text-sm">Référence : {selected.monthly.comparison_mode === "MONTHLY_REPORT" ? `Monthly de ${selected.monthly.previous_month}`
          : selected.monthly.comparison_mode === "DIGESTS" ? `Digests de ${selected.monthly.previous_month} (pas de Monthly précédent)` : "Premier point de référence, aucune matière comparative disponible"}.</p>
        {selected.monthly.reference_production_id && <button className="text-sm underline" disabled={controlsBusy} onClick={() => void openMonthly(selected.monthly.reference_production_id!)}>Ouvrir le Monthly de référence</button>}
        {RUNNING.includes(selected.status) && <p className="text-sm text-slate-500">Le traitement avance en arrière-plan. Vous pouvez fermer cette page. Les étapes sont enregistrées ; après une interruption du serveur, Actualiser / reprendre relance le suivi sans recommencer les étapes acquises.</p>}
        {pollError && <p role="alert" className="text-red-800">{pollError}</p>}
        {selected.error && <div className="rounded-lg bg-amber-50 p-3 text-sm text-amber-900"><p>{selected.error.message}</p>
          {selected.error.issues?.map((issue, index) => <p key={index}>{issue.location} · {issue.message}</p>)}
        </div>}
        {selected.status === "failed" && <p className="text-sm">Le document et le diagnostic sont conservés. Une erreur factuelle majeure non résolue ou une invalidité technique empêche sa mise à disposition. Consultez le diagnostic avant de déclencher une nouvelle production.</p>}
        {(selected.status === "submission_unknown" || (selected.status === "starting" && !selected.latest_artifact?.response_id)) && <label className="block text-sm">Rattacher une réponse retrouvée dans les logs
          <input className={INPUT} placeholder="resp_…" value={responseId} onChange={e => setResponseId(e.target.value)} />
          <span className="text-xs text-slate-500">Actualiser / reprendre vérifie son rattachement. Ne créez pas une nouvelle version pour contourner une acceptation inconnue.</span>
        </label>}
        <details><summary className="cursor-pointer text-sm">Étapes et diagnostic</summary>
          <ol className="mt-3 space-y-2 text-sm">{selected.history.map(item => <li key={item.artifact_id}>V{item.version_number} · {item.stage === "REVIEW_BATCH" ? "Contrôles parallèles" : item.stage === "CORRECTION_PROPOSAL" ? "Proposition de corrections" : item.stage === "CORRECTION_CHECK" ? "Vérification des corrections" : item.stage} · {item.status}</li>)}</ol>
          <button className={`${BUTTON} mt-3`} onClick={() => downloadDiagnostic(selected)}>Télécharger le diagnostic</button>
          <Link className="ml-3 text-sm underline" href={`/admin/production/reports?production=${selected.production_id}`}>Ouvrir le détail technique Production</Link>
        </details>
      </div>
      {selected.status === "completed" && selected.document && <ProductionDocumentPreview
        key={selected.document_artifact_id || selected.production_id} document={selected.document}
        exportContext={selected.export_context} sourceMetadata={selected.source_metadata} lockExportContext />}
    </section>}
  </div>;
}
