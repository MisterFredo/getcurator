"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import StockImportPanel from "@/components/admin/stock/StockImportPanel";
import StockFilters from "@/components/admin/stock/StockFilters";
import StockTable from "@/components/admin/stock/StockTable";
import RawDrawer from "@/components/admin/stock/RawDrawer";
import SourceMonitoringTable from "@/components/admin/stock/SourceMonitoringTable";

const PAGE_SIZE = 50;
type JobStatus = "IDLE" | "RUNNING" | "COMPLETED" | "ERROR";
type DestockJob = {
  status: JobStatus;
  job_id: string | null;
  started_at: string | null;
  finished_at: string | null;
  processed: number | null;
  errors: number | null;
  error: string | null;
  result?: unknown;
};

export default function ContentStockPage() {
  const [view, setView] = useState<"raw" | "sources">("raw");
  const [raws, setRaws] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [companies, setCompanies] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [sources, setSources] = useState<any[]>([]);
  const [sourcesMonitoring, setSourcesMonitoring] = useState<any[]>([]);
  const [selectedRaw, setSelectedRaw] = useState<any>(null);
  const [job, setJob] = useState<DestockJob | null>(null);
  const [starting, setStarting] = useState(false);
  const startingRef = useRef(false);
  const previousStatus = useRef<JobStatus | null>(null);
  const [filters, setFilters] = useState({
    status: "", source_id: "", import_type: "", id_primary_company: "",
  });

  const load = useCallback(async () => {
    try {
      const queryParams = new URLSearchParams();
      if (filters.status) queryParams.append("status", filters.status);
      if (filters.source_id) queryParams.append("source_id", filters.source_id);
      if (filters.import_type) queryParams.append("import_type", filters.import_type);
      if (filters.id_primary_company) queryParams.append("id_primary_company", filters.id_primary_company);
      queryParams.append("limit", String(PAGE_SIZE));
      queryParams.append("offset", String((page - 1) * PAGE_SIZE));
      const [listRes, statsRes] = await Promise.all([
        api.get(`/acquisition/raw/stock?${queryParams.toString()}`),
        api.get("/acquisition/raw/admin/stats"),
      ]);
      setRaws(listRes.rows || []);
      setTotal(listRes.total || 0);
      setStats(statsRes.stats || null);
    } catch (e) {
      console.error("Erreur chargement stock", e);
    }
  }, [filters, page]);

  const loadSourcesMonitoring = useCallback(async () => {
    try {
      const res = await api.get("/content/source/monitoring");
      setSourcesMonitoring(res.sources || []);
    } catch (e) {
      console.error("Erreur monitoring sources", e);
    }
  }, []);

  const refreshJob = useCallback(async () => {
    try {
      const next = (await api.get("/acquisition/raw/destock/status")) as DestockJob;
      setJob(next);
      if (previousStatus.current === "RUNNING" && next.status !== "RUNNING") {
        void load();
      }
      previousStatus.current = next.status;
    } catch (e) {
      console.error("Impossible de récupérer le statut du déstockage", e);
      // Fail closed: don't allow another launch when status cannot be verified.
      setJob(null);
    }
  }, [load]);

  useEffect(() => {
    if (view === "raw") void load();
    else void loadSourcesMonitoring();
  }, [view, load, loadSourcesMonitoring]);

  useEffect(() => { setPage(1); }, [filters]);

  useEffect(() => {
    void api.get("/source/list").then((res: any) => setSources(res.sources || []))
      .catch((e: unknown) => console.error("Erreur chargement sources", e));
    void api.get("/company/list").then((res: any) => setCompanies(res.companies || []))
      .catch((e: unknown) => console.error("Erreur chargement companies", e));
  }, []);

  useEffect(() => {
    void refreshJob();
    const timer = window.setInterval(() => { void refreshJob(); }, 4000);
    const onFocus = () => { void refreshJob(); };
    window.addEventListener("focus", onFocus);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("focus", onFocus);
    };
  }, [refreshJob]);

  const busy = starting || job === null || job.status === "RUNNING";

  async function handleDestock(id?: string) {
    if (busy || startingRef.current) return;
    if (!confirm(id ? "Confirmer la génération de ce RAW ?" : "Confirmer le déstockage complet ?")) return;
    startingRef.current = true;
    setStarting(true);
    try {
      const response = (await api.post(
        "/acquisition/raw/destock",
        id ? { id_raw: id } : { limit: 50 },
      )) as DestockJob;
      setJob(response);
      previousStatus.current = response.status;
    } catch (e) {
      console.error("Erreur démarrage déstockage", e);
      // A timeout/409 doesn't mean the job is stopped. Re-query the server.
      await refreshJob();
      alert("Lancement non confirmé. Vérifiez le statut affiché avant de réessayer.");
    } finally {
      startingRef.current = false;
      setStarting(false);
    }
  }

  async function handleRetry(id: string) {
    if (busy) return;
    if (!confirm("Relancer cette entrée ?")) return;
    try {
      await api.post(`/acquisition/raw/retry/${id}`, {});
      await load();
    } catch (e) { console.error("Erreur retry", e); alert("Erreur retry"); }
  }

  async function handleDelete(id: string) {
    if (busy) return;
    if (!confirm("Supprimer cette entrée ?")) return;
    try {
      await api.delete(`/acquisition/raw/delete/${id}`);
      await load();
    } catch (e) { console.error("Erreur suppression", e); alert("Erreur suppression"); }
  }

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="space-y-8 p-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-ratecard-blue">Stock RAW</h1>
        <button
          onClick={() => void handleDestock()}
          disabled={busy}
          className="bg-ratecard-green text-white px-3 py-2 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {starting ? "Démarrage..." : job === null ? "Vérification..." : job.status === "RUNNING" ? "Déstockage en cours..." : "Déstocker"}
        </button>
      </div>

      <div role="status" aria-live="polite" className="border rounded-lg bg-white px-4 py-3 text-sm">
        {job === null && "Vérification du statut serveur… Déstockage indisponible tant que le statut est inconnu."}
        {job?.status === "IDLE" && "Aucun déstockage en cours."}
        {job?.status === "RUNNING" && (
          <span>Déstockage en cours depuis {job.started_at ? new Date(job.started_at).toLocaleString("fr-FR") : "quelques instants"}. Vous pouvez quitter cette page ; le traitement continue côté serveur.</span>
        )}
        {job?.status === "COMPLETED" && (
          <span>Dernier déstockage terminé{job.processed !== null ? ` — ${job.processed} traités` : ""}{job.errors !== null ? `, ${job.errors} erreurs` : ""}. Actualisez le stock si nécessaire.</span>
        )}
        {job?.status === "ERROR" && <span className="text-red-600">Échec du dernier déstockage : {job.error || "erreur inconnue"}</span>}
      </div>

      <div className="flex gap-2">
        <button onClick={() => setView("raw")} className={`px-3 py-1 rounded ${view === "raw" ? "bg-black text-white" : "border"}`}>RAW</button>
        <button onClick={() => setView("sources")} className={`px-3 py-1 rounded ${view === "sources" ? "bg-black text-white" : "border"}`}>SOURCES</button>
      </div>

      {view === "raw" && (
        <div className="border rounded-lg p-6 bg-white shadow-sm">
          <StockImportPanel sources={sources} onImported={load} />
        </div>
      )}

      {view === "raw" && (
        <div className="flex flex-wrap justify-between items-center gap-6">
          {stats && (
            <div className="flex gap-6 text-sm">
              <span>Total: <strong>{stats.total}</strong></span>
              <span>Stock: <strong>{stats.total_stored}</strong></span>
              <span>Processing: <strong>{stats.total_processing}</strong></span>
              <span>OK: <strong>{stats.total_processed}</strong></span>
              <span className="text-red-600">Error: <strong>{stats.total_error}</strong></span>
            </div>
          )}
          <StockFilters
            sources={sources} companies={companies}
            status={filters.status} sourceId={filters.source_id}
            importType={filters.import_type} primaryCompanyId={filters.id_primary_company}
            total={total}
            onStatusChange={(v) => setFilters((prev) => ({ ...prev, status: v }))}
            onSourceChange={(v) => setFilters((prev) => ({ ...prev, source_id: v }))}
            onImportTypeChange={(v) => setFilters((prev) => ({ ...prev, import_type: v }))}
            onPrimaryCompanyChange={(v) => setFilters((prev) => ({ ...prev, id_primary_company: v }))}
          />
        </div>
      )}

      <div className="border rounded-lg overflow-hidden">
        {view === "raw" ? (
          <StockTable
            raws={raws}
            onDestock={(id) => { if (!busy) void handleDestock(id); }}
            onRetry={(id) => { if (!busy) void handleRetry(id); }}
            onDelete={(id) => { if (!busy) void handleDelete(id); }}
            onOpen={(raw) => setSelectedRaw(raw)}
          />
        ) : <SourceMonitoringTable sources={sourcesMonitoring} />}
      </div>

      {view === "raw" && totalPages > 1 && (
        <div className="flex justify-center gap-4 text-sm">
          <button disabled={page === 1} onClick={() => setPage((p) => p - 1)} className="px-3 py-1 border rounded disabled:opacity-40">Précédent</button>
          <span>Page {page} / {totalPages}</span>
          <button disabled={page === totalPages} onClick={() => setPage((p) => p + 1)} className="px-3 py-1 border rounded disabled:opacity-40">Suivant</button>
        </div>
      )}
      {view === "raw" && <RawDrawer raw={selectedRaw} onClose={() => setSelectedRaw(null)} onSaved={load} />}
    </div>
  );
}
