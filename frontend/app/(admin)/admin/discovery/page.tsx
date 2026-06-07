"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

import DiscoverySources from "@/components/admin/discovery/DiscoverySources";
import DiscoveryStats from "@/components/admin/discovery/DiscoveryStats";
import DiscoveryActions from "@/components/admin/discovery/DiscoveryActions";
import DiscoveryTable from "@/components/admin/discovery/DiscoveryTable";

type DiscoveryItem = {
  id_discovery: string;

  source_id: string;
  source_name?: string | null;

  url: string;
  title?: string | null;

  status: string;

  date_found?: string | null;
  created_at?: string | null;
};

type Source = {
  source_id: string;
  name: string;

  domain?: string | null;
  acquisition_mode?: string | null;
};

export default function DiscoveryPage() {

  const [items, setItems] = useState<DiscoveryItem[]>([]);
  const [sources, setSources] = useState<Source[]>([]);

  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const [statusFilter, setStatusFilter] = useState<
    "NEW" | "STORED" | "ALL"
  >("NEW");

  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);

  // =========================================================
  // LOAD
  // =========================================================

  async function loadData() {

    try {

      setLoading(true);

      const [discoveryRes, sourceRes] = await Promise.all([
        api.get("/discovery/list"),
        api.get("/source/list"),
      ]);

      setItems(
        discoveryRes.items || []
      );

      setSources(
        sourceRes.sources || []
      );

    } catch (e) {

      console.error(e);

      alert(
        "❌ Erreur chargement Discovery"
      );

    } finally {

      setLoading(false);

    }
  }

  // =========================================================
  // INIT
  // =========================================================

  useEffect(() => {

    loadData();

  }, []);

  // =========================================================
  // SCAN ALL
  // =========================================================

  async function scanAll() {

    try {

      setScanning(true);

      const res = await api.post(
        "/discovery/scan-all",
        {}
      );

      alert(
        `${res.discovered_urls || 0} URL(s) découverte(s)`
      );

      await loadData();

    } catch (e) {

      console.error(e);

      alert(
        "❌ Erreur scan"
      );

    } finally {

      setScanning(false);

    }
  }

  // =========================================================
  // SCAN SOURCE
  // =========================================================

  async function scanSource(
    sourceId: string,
    sourceName: string
  ) {

    try {

      const res = await api.post(
        `/discovery/scan/${sourceId}`,
        {}
      );

      alert(
        `${sourceName}\n${res.discovered_urls || 0} URL(s) découverte(s)`
      );

      await loadData();

    } catch (e) {

      console.error(e);

      alert(
        `❌ Erreur scan ${sourceName}`
      );
    }
  }

  // =========================================================
  // TOGGLE SELECTION
  // =========================================================

  function toggleSelection(
    idDiscovery: string
  ) {

    setSelectedIds((prev) =>

      prev.includes(idDiscovery)
        ? prev.filter(
            (x) => x !== idDiscovery
          )
        : [...prev, idDiscovery]

    );
  }

  function toggleAllSelections() {

    if (
      selectedIds.length === items.length
    ) {

      setSelectedIds([]);

      return;
    }

    setSelectedIds(
      items.map(
        (item) => item.id_discovery
      )
    );
  }

  // =========================================================
  // STORE SELECTED
  // =========================================================

  async function storeSelected() {

    if (
      selectedIds.length === 0
    ) {
      return;
    }

    try {

      const res = await api.post(
        "/discovery/store",
        {
          discovery_ids: selectedIds,
        }
      );

      alert(
        `${res.stored || 0} URL(s) stockée(s)`
      );

      setSelectedIds([]);

      await loadData();

    } catch (e) {

      console.error(e);

      alert(
        "❌ Erreur stockage"
      );
    }
  }

  // =========================================================
  // DISMISS SELECTED
  // =========================================================

  async function dismissSelected() {

    if (
      selectedIds.length === 0
    ) {
      return;
    }

    try {

      const res = await api.post(
        "/discovery/ignore",
        {
          discovery_ids: selectedIds,
        }
      );

      alert(
        `${res.ignored || 0} URL(s) dismiss`
      );

      setSelectedIds([]);

      await loadData();

    } catch (e) {

      console.error(e);

      alert(
        "❌ Erreur dismiss"
      );
    }
  }

  async function sendToStudio() {

    if (
      selectedIds.length === 0
    ) {
      return;
    }

    try {

      const res = await api.post(
        "/discovery/manual",
        {
          discovery_ids: selectedIds,
        }
      );

      alert(
        `${res.manual || 0} URL(s) envoyée(s) au Studio`
      );

      setSelectedIds([]);

      await loadData();

    } catch (e) {

      console.error(e);

      alert(
        "❌ Erreur Studio"
      );
    }
  }

  // =========================================================
  // FILTER
  // =========================================================

  const filteredItems = items.filter(
    (item) => {

      if (
        statusFilter === "ALL"
      ) {
        return true;
      }

      return (
        item.status === statusFilter
      );
    }
  );

  // =========================================================
  // UI
  // =========================================================

  return (

    <div className="space-y-8">

      {/* HEADER */}

      <div className="flex justify-between items-center">

        <div>

          <h1 className="text-3xl font-semibold text-ratecard-blue">
            Discovery
          </h1>

          <p className="text-gray-500 mt-1">
            Détection automatique des nouvelles URLs
          </p>

        </div>

        <button
          onClick={scanAll}
          disabled={scanning}
          className="bg-ratecard-green px-5 py-2 text-white rounded disabled:opacity-50"
        >
          {scanning
            ? "Scan en cours..."
            : "SCAN ALL SOURCES"}
        </button>

      </div>

      {/* SOURCES */}

      <DiscoverySources
        sources={sources}
        onScan={scanSource}
      />

      {/* STATS */}

      <DiscoveryStats
        total={items.length}
      />

      {/* ACTIONS */}

      <DiscoveryActions
        selectedCount={
          selectedIds.length
        }
        onStore={storeSelected}
        onManual={sendToStudio}
        onDismiss={dismissSelected}
      />

      {/* FILTERS */}

      <div className="flex gap-2">

        <button
          onClick={() =>
            setStatusFilter("NEW")
          }
          className={
            statusFilter === "NEW"
              ? "bg-ratecard-blue text-white px-3 py-1 rounded"
              : "bg-gray-100 px-3 py-1 rounded"
          }
        >
          NEW
        </button>

        <button
          onClick={() =>
            setStatusFilter("STORED")
          }
          className={
            statusFilter === "STORED"
              ? "bg-ratecard-blue text-white px-3 py-1 rounded"
              : "bg-gray-100 px-3 py-1 rounded"
          }
        >
          STORED
        </button>

        <button
          onClick={() =>
            setStatusFilter("ALL")
          }
          className={
            statusFilter === "ALL"
              ? "bg-ratecard-blue text-white px-3 py-1 rounded"
              : "bg-gray-100 px-3 py-1 rounded"
          }
        >
          ALL
        </button>

      </div>

      {/* TABLE */}

      {loading ? (

        <div className="text-gray-500">
          Chargement...
        </div>

      ) : filteredItems.length === 0 ? (

        <div className="bg-white border rounded p-8 text-center text-gray-500">
          Aucune URL découverte.
        </div>

      ) : (

        <DiscoveryTable
          items={items}
          selectedIds={selectedIds}
          onToggle={toggleSelection}
          onToggleAll={toggleAllSelections}
        />

      )}

    </div>

  );
}
