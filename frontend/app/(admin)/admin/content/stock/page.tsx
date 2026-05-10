"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

import StockImportPanel from "@/components/admin/stock/StockImportPanel";
import StockFilters from "@/components/admin/stock/StockFilters";
import StockTable from "@/components/admin/stock/StockTable";
import RawDrawer from "@/components/admin/stock/RawDrawer";
import SourceMonitoringTable from "@/components/admin/stock/SourceMonitoringTable";

const PAGE_SIZE = 50;

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
  const [processing, setProcessing] = useState(false);

  const [filters, setFilters] = useState({
    status: "",
    source_id: "",
    import_type: "",
    content_type: "", // 🔥 NEW
  });

  // =========================
  // LOAD RAW DATA
  // =========================

  async function load() {
    try {
      const offset = (page - 1) * PAGE_SIZE;

      const queryParams = new URLSearchParams();

      if (filters.status) queryParams.append("status", filters.status);
      if (filters.source_id) queryParams.append("source_id", filters.source_id);
      if (filters.import_type) queryParams.append("import_type", filters.import_type);

      // 🔥 NEW
      if (filters.content_type) {
        queryParams.append("content_type", filters.content_type);
      }

      queryParams.append("limit", PAGE_SIZE.toString());
      queryParams.append("offset", offset.toString());

      const [listRes, statsRes] = await Promise.all([
        api.get(`/content/raw/stock?${queryParams.toString()}`),
        api.get("/content/raw/admin/stats"),
      ]);

      setRaws(listRes.rows || []);
      setTotal(listRes.total || 0);
      setStats(statsRes.stats || null);

    } catch (e) {
      console.error("Erreur chargement stock", e);
      alert("Erreur chargement stock");
    }
  }

  // =========================
  // LOAD SOURCE MONITORING
  // =========================

  async function loadSourcesMonitoring() {
    try {
      const res = await api.get("/content/source/monitoring");
      setSourcesMonitoring(res.sources || []);
    } catch (e) {
      console.error("Erreur monitoring sources", e);
    }
  }

  // =========================
  // EFFECTS
  // =========================

  useEffect(() => {
    if (view === "raw") {
      load();
    } else {
      loadSourcesMonitoring();
    }
  }, [view, filters, page]);

  // reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [filters]);

  useEffect(() => {
    async function loadSources() {
      try {
        const res = await api.get("/content/source/list");
        setSources(res.sources || []);
      } catch (e) {
        console.error("Erreur chargement sources", e);
      }
    }
    loadSources();
  }, []);

  useEffect(() => {
    async function loadCompanies() {
      try {
        const res = await api.get("/company/list");
        setCompanies(res.items || []);
      } catch (e) {
        console.error("Erreur chargement companies", e);
      }
    }

    loadCompanies();
  }, []);

  // =========================
  // ACTIONS
  // =========================

  async function handleDestock(id?: string) {
    if (!confirm("Confirmer la génération ?")) return;

    setProcessing(true);

    try {
      await api.post(
        "/content/raw/destock",
        id ? { id_raw: id } : { limit: 50 }
      );

      await load();
    } catch (e) {
      console.error("Erreur destock", e);
      alert("Erreur destock");
    }

    setProcessing(false);
  }

  async function handleRetry(id: string) {
    if (!confirm("Relancer cette entrée ?")) return;

    try {
      await api.post(`/content/raw/retry/${id}`, {});
      await load();
    } catch (e) {
      console.error("Erreur retry", e);
      alert("Erreur retry");
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Supprimer cette entrée ?")) return;

    try {
      await api.delete(`/content/raw/delete/${id}`);
      await load();
    } catch (e) {
      console.error("Erreur suppression", e);
      alert("Erreur suppression");
    }
  }

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="space-y-8 p-6">

      {/* HEADER */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-ratecard-blue">
          Stock RAW
        </h1>

        <button
          onClick={() => handleDestock()}
          disabled={processing}
          className="bg-ratecard-green text-white px-3 py-2 rounded text-sm"
        >
          {processing ? "Traitement..." : "Déstocker"}
        </button>
      </div>

      {/* TOGGLE */}
      <div className="flex gap-2">
        <button
          onClick={() => setView("raw")}
          className={`px-3 py-1 rounded ${
            view === "raw" ? "bg-black text-white" : "border"
          }`}
        >
          RAW
        </button>

        <button
          onClick={() => setView("sources")}
          className={`px-3 py-1 rounded ${
            view === "sources" ? "bg-black text-white" : "border"
          }`}
        >
          SOURCES
        </button>
      </div>

      {/* IMPORT (only RAW view) */}
      {view === "raw" && (
        <div className="border rounded-lg p-6 bg-white shadow-sm">
          <StockImportPanel
            sources={sources}
            companies={companies}
            onImported={load}
          />
        </div>
      )}

      {/* STATS + FILTERS (only RAW view) */}
      {view === "raw" && (
        <div className="flex flex-wrap justify-between items-center gap-6">

          {stats && (
            <div className="flex gap-6 text-sm">
              <span>Total: <strong>{stats.total}</strong></span>
              <span>Stock: <strong>{stats.total_stored}</strong></span>
              <span>Processing: <strong>{stats.total_processing}</strong></span>
              <span>OK: <strong>{stats.total_processed}</strong></span>
              <span className="text-red-600">
                Error: <strong>{stats.total_error}</strong>
              </span>
            </div>
          )}

          <StockFilters
            sources={sources}
            status={filters.status}
            sourceId={filters.source_id}
            importType={filters.import_type}
            contentType={filters.content_type} // 🔥 NEW
            total={total}
            onStatusChange={(v) =>
              setFilters((prev) => ({ ...prev, status: v }))
            }
            onSourceChange={(v) =>
              setFilters((prev) => ({ ...prev, source_id: v }))
            }
            onImportTypeChange={(v) =>
              setFilters((prev) => ({ ...prev, import_type: v }))
            }

            // 🔥 NEW
            onContentTypeChange={(v) =>
              setFilters((prev) => ({
                ...prev,
                content_type: v,
              }))
            }
          />
        </div>
      )}

      {/* TABLE */}
      <div className="border rounded-lg overflow-hidden">
        {view === "raw" ? (
          <StockTable
            raws={raws}
            onDestock={handleDestock}
            onRetry={handleRetry}
            onDelete={handleDelete}
            onOpen={(raw) => setSelectedRaw(raw)}
          />
        ) : (
          <SourceMonitoringTable sources={sourcesMonitoring} />
        )}
      </div>

      {/* PAGINATION (only RAW) */}
      {view === "raw" && totalPages > 1 && (
        <div className="flex justify-center gap-4 text-sm">
          <button
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
            className="px-3 py-1 border rounded disabled:opacity-40"
          >
            Précédent
          </button>

          <span>
            Page {page} / {totalPages}
          </span>

          <button
            disabled={page === totalPages}
            onClick={() => setPage((p) => p + 1)}
            className="px-3 py-1 border rounded disabled:opacity-40"
          >
            Suivant
          </button>
        </div>
      )}

      {/* DRAWER */}
      {view === "raw" && (
        <RawDrawer
          raw={selectedRaw}
          onClose={() => setSelectedRaw(null)}
          onSaved={load}
        />
      )}

    </div>
  );
}
