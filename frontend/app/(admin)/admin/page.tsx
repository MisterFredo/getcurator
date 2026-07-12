"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

/* ================= TYPES ================= */

type RawStats = {
  total: number;
  total_stored: number;
  total_processing: number;
  total_error: number;
};

type ContentStats = {
  total: number;
  total_draft: number;
  total_ready: number;
  total_published: number;
  total_scheduled: number;
  total_published_this_year: number;
  total_published_this_month: number;
};

/* ================= COMPONENT ================= */

export default function AdminHome() {

  const [rawStats, setRawStats] = useState<RawStats | null>(null);
  const [contentStats, setContentStats] = useState<ContentStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStats() {
      try {

        const [
          rawRes,
          contentRes,
        ] = await Promise.all([
          api.get("/content/raw/admin/stats"),
          api.get("/content/admin/stats"),
        ]);

        setRawStats(rawRes.stats);
        setContentStats(contentRes.stats);

      } catch (e) {
        console.error("Erreur dashboard admin", e);
      }

      setLoading(false);
    }

    loadStats();
  }, []);

    if (loading) return <div>Chargement dashboard…</div>;

  return (
    <div className="space-y-12">

      <h1 className="text-3xl font-semibold text-ratecard-blue">
        Dashboard Admin
      </h1>

      {/* ================= RAW ================= */}

      {rawStats && (
        <Section title="RAW Pipeline">
          <StatGrid>
            <StatCard label="Total RAW" value={rawStats.total} />
            <StatCard label="En stock" value={rawStats.total_stored} yellow />
            <StatCard label="En cours" value={rawStats.total_processing} />
            <StatCard label="Erreurs" value={rawStats.total_error} red />
          </StatGrid>
        </Section>
      )}

      {/* ================= CONTENT ================= */}

      {contentStats && (
        <Section title="Content (Analyses)">
          <StatGrid>
            <StatCard label="Total" value={contentStats.total} />
            <StatCard label="Draft" value={contentStats.total_draft} yellow />
            <StatCard label="Ready" value={contentStats.total_ready} />
            <StatCard label="Published" value={contentStats.total_published} green />
            <StatCard label="Scheduled" value={contentStats.total_scheduled} />
            <StatCard label="Publié cette année" value={contentStats.total_published_this_year} />
            <StatCard label="Publié ce mois" value={contentStats.total_published_this_month} />
          </StatGrid>
        </Section>
      )}

    </div>
  );
}

/* ================= UI HELPERS ================= */

function Section({ title, children }: any) {
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">{title}</h2>
      {children}
    </div>
  );
}

function StatGrid({ children }: any) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
      {children}
    </div>
  );
}

function StatCard({
  label,
  value,
  yellow,
  red,
  green,
}: {
  label: string;
  value: number;
  yellow?: boolean;
  red?: boolean;
  green?: boolean;
}) {

  let bg = "bg-white";
  let text = "text-gray-800";

  if (yellow) {
    bg = "bg-yellow-50";
    text = "text-yellow-700";
  }

  if (red) {
    bg = "bg-red-50";
    text = "text-red-700";
  }

  if (green) {
    bg = "bg-green-50";
    text = "text-green-700";
  }

  return (
    <div className={`${bg} rounded-lg p-4 border`}>
      <div className="text-xs text-gray-500">{label}</div>
      <div className={`text-2xl font-semibold ${text}`}>
        {value ?? 0}
      </div>
    </div>
  );
}
