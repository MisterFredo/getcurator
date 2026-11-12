"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import LibraryPostRequalification from "./LibraryPostRequalification";

type Job = {
  status: "IDLE" | "RUNNING" | "PARTIAL" | "COMPLETE";
  phase?: "LIBRARY" | "QUALIFICATION";
  registered?: number;
  withdrawn?: number;
  corporate_requalified?: number;
  qualified?: number;
  registration_failed?: number;
  qualification_failed?: number;
  error?: string;
};

const endpoint = "/cockpit/operations/library-post-backlog";
const labels = {
  IDLE: "À lancer",
  RUNNING: "En cours",
  PARTIAL: "À reprendre",
  COMPLETE: "Terminé",
};

export default function LibraryPostBacklog() {
  const [job, setJob] = useState<Job | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function poll() {
      try {
        const result = await api.get(endpoint + "/status");
        if (!cancelled) {
          setJob(result);
          if (result.status === "RUNNING") timer = setTimeout(poll, 10000);
        }
      } catch {
        if (!cancelled) {
          timer = setTimeout(poll, 10000);
        }
      }
    }

    void poll();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [job?.status]);

  async function start() {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      setJob(await api.post(endpoint + "/start", {}));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Rattrapage indisponible");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <section className="border-t pt-4 space-y-2">
        <h3 className="font-semibold">Rattrapage des posts LinkedIn</h3>
        <p className="text-sm text-gray-600">
          Importe et qualifie les posts LinkedIn corporate et salariés. Reprend les anciens « Autre » corporate.
        </p>
        <button className="border rounded px-4 py-2 disabled:opacity-50" disabled={busy} onClick={() => void start()}>
          {job?.status === "RUNNING" || job?.status === "PARTIAL" ? "Reprendre le rattrapage" : "Lancer le rattrapage"}
        </button>
        {job && job.status !== "IDLE" && (
          <p role="status" className="text-sm">
            {labels[job.status]} · {job.phase === "LIBRARY" ? "Import Library" : "Qualification"} ·{" "}
            {job.registered ?? 0} importés · {job.qualified ?? 0} qualifiés
            {" "}dont {job.corporate_requalified ?? 0} corporate requalifiés ·{" "}
            {job.withdrawn ?? 0} déjà retirés ·{" "}
            {(job.registration_failed ?? 0) + (job.qualification_failed ?? 0)} échecs sur ce passage
          </p>
        )}
        {(error || job?.error) && <p role="alert" className="text-sm text-red-700">{error || job?.error}</p>}
      </section>
      <LibraryPostRequalification />
    </>
  );
}
