"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Job = {
  status: "IDLE" | "RUNNING" | "PARTIAL" | "COMPLETE";
  remaining: number;
  written?: number;
  skipped?: number;
  failed?: number;
  error?: string;
};

const endpoint = "/cockpit/operations/library-post-requalification";
const labels = {
  IDLE: "Prêt",
  RUNNING: "En cours",
  PARTIAL: "À reprendre",
  COMPLETE: "Terminé",
};

export default function LibraryPostRequalification() {
  const [job, setJob] = useState<Job | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (starting) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function refresh() {
      try {
        const current: Job = await api.get(endpoint + "/status");
        if (cancelled) return;
        setJob(current);
        setError("");
        if (current.status === "RUNNING") timer = setTimeout(refresh, 10000);
      } catch {
        if (cancelled) return;
        setError("Suivi de la requalification indisponible.");
        timer = setTimeout(refresh, 10000);
      }
    }

    void refresh();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [starting]);

  async function start() {
    setStarting(true);
    setError("");
    try {
      setJob(await api.post(endpoint + "/start", {}));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Requalification indisponible.");
    } finally {
      setStarting(false);
    }
  }

  return (
    <section className="space-y-2 border-t pt-4" aria-label="Requalification des posts salariés">
      <h3 className="font-semibold">Requalification des posts salariés</h3>
      <p className="text-sm text-gray-600">
        Applique les règles actuelles aux posts encore éligibles. Vous pouvez quitter le Cockpit pendant le traitement.
      </p>
      <button
        type="button"
        className="rounded border px-4 py-2 disabled:opacity-50"
        disabled={starting || !job || job.status === "RUNNING" || job.remaining === 0}
        onClick={() => void start()}
      >
        {job?.status === "PARTIAL" ? "Reprendre la requalification" : "Requalifier les posts à vérifier"}
      </button>
      {job && (
        <p role="status" className="text-sm">
          {labels[job.status]} · {job.remaining} encore éligibles · {job.written ?? 0} verdicts
          enregistrés · {job.skipped ?? 0} passés · {job.failed ?? 0} échecs sur ce passage
        </p>
      )}
      {(error || job?.error) && <p role="alert" className="text-sm text-red-700">{error || job?.error}</p>}
    </section>
  );
}
