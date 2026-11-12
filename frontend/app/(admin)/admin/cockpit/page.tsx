"use client";

import { useState, useSyncExternalStore } from "react";
import { api } from "@/lib/api";
import type { QualityRow } from "@/types/cockpit";
import CockpitHeader from "@/components/admin/cockpit/CockpitHeader";
import MonitoringPanel from "@/components/admin/cockpit/MonitoringPanel";
import DiscoveryOperationsPanel from "@/components/admin/cockpit/DiscoveryOperationsPanel";
import OperationsPanel from "@/components/admin/cockpit/OperationsPanel";
import NumbersOperationsPanel from "@/components/admin/cockpit/NumbersOperationsPanel";
import QualityPanel from "@/components/admin/cockpit/QualityPanel";
import ResultsPanel from "@/components/admin/cockpit/ResultsPanel";
import TranslationBackfillOperation from "@/components/admin/cockpit/TranslationBackfillOperation";
import CompanyReportBatch from "@/components/admin/company/CompanyReportBatch";

const tabs = [
  { id: "ensemble", label: "Vue d’ensemble" },
  { id: "collecte", label: "Collecte & Library" },
  { id: "production", label: "Production" },
  { id: "qualite", label: "Qualité" },
  { id: "maintenance", label: "Maintenance" },
] as const;

function subscribe(callback: () => void) {
  window.addEventListener("hashchange", callback);
  return () => window.removeEventListener("hashchange", callback);
}

type CockpitTab = (typeof tabs)[number]["id"];

function getTab(): CockpitTab {
  return tabs.find(tab => "#" + tab.id === window.location.hash)?.id ?? "ensemble";
}

export default function CockpitPage() {
  const tab = useSyncExternalStore<CockpitTab>(subscribe, getTab, () => "ensemble");
  const [title, setTitle] = useState("");
  const [rows, setRows] = useState<QualityRow[]>([]);

  function results(nextTitle: string, nextRows: QualityRow[]) {
    setTitle(nextTitle);
    setRows(nextRows);
  }

  async function reloadDuplicates() {
    const response = await api.get("/cockpit/quality/duplicate-urls");
    if (response.status !== "ok" || !Array.isArray(response.results)) {
      throw new Error("Suppression effectuée, mais actualisation indisponible. Relancer le contrôle.");
    }
    results("Doublons par URL source", response.results);
  }

  return (
    <div className="space-y-6">
      <CockpitHeader />
      <nav aria-label="Rubriques du Cockpit" className="flex flex-wrap gap-2 border-b border-gray-200 pb-3">
        {tabs.map(item => (
          <a
            key={item.id}
            href={"#" + item.id}
            aria-current={item.id === tab ? "page" : undefined}
            className={`rounded-lg px-4 py-2 text-sm font-medium ${item.id === tab
              ? "bg-ratecard-blue text-white"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"}`}
          >
            {item.label}
          </a>
        ))}
      </nav>

      {tab === "ensemble" && (
        <div className="space-y-5">
          <DiscoveryOperationsPanel key="overview" overview />
          <MonitoringPanel />
        </div>
      )}
      {tab === "collecte" && <DiscoveryOperationsPanel key="collection" />}
      {tab === "production" && (
        <div className="space-y-5">
          <OperationsPanel section="production" />
          <NumbersOperationsPanel />
        </div>
      )}
      {tab === "qualite" && (
        <div className="space-y-5">
          <QualityPanel onResults={results} />
          <details className="rounded-xl border bg-white p-4">
            <summary className="cursor-pointer font-semibold">Diagnostics complémentaires</summary>
            <div className="mt-4"><QualityPanel bonus onResults={results} /></div>
          </details>
          <ResultsPanel
            key={title}
            title={title}
            rows={rows}
            onDelete={id => setRows(current => current.filter(row => String(row.ID_CONTENT) !== id))}
            onReload={title === "Doublons par URL source" ? reloadDuplicates : undefined}
          />
        </div>
      )}
      {tab === "maintenance" && (
        <div className="space-y-5">
          <OperationsPanel section="maintenance" />
          <details className="rounded-xl border bg-white p-4">
            <summary className="cursor-pointer font-semibold">Rattrapage historique des traductions</summary>
            <div className="mt-4"><TranslationBackfillOperation /></div>
          </details>
        </div>
      )}
    </div>
  );
}
