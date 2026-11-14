"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { refreshDailyJob, startDailyBulk } from "@/lib/editorial";
import type { BulkDay } from "@/lib/editorial";

const storageKey = "editorial-bulk-results";
const button = "rounded border border-slate-300 px-3 py-2 text-sm disabled:opacity-50";

function rowKey(row: BulkDay) {
  return `${row.date}:${row.job?.job_id ?? "summary"}`;
}

export default function EditorialBulk({ dates = [], onUpdate }: {
  dates?: string[];
  onUpdate?: () => void;
}) {
  const [results, setResults] = useState<BulkDay[]>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const request = useRef<{ key: string; id: string } | undefined>(undefined);
  const lock = useRef(false);
  const update = useRef(onUpdate);
  useEffect(() => { update.current = onUpdate; }, [onUpdate]);
  useEffect(() => {
    try {
      const saved = sessionStorage.getItem(storageKey);
      if (saved) setResults(JSON.parse(saved));
    } catch { /* Optional browser storage. */ }
  }, []);
  useEffect(() => {
    if (!results) return;
    try { sessionStorage.setItem(storageKey, JSON.stringify(results)); } catch { /* Optional browser storage. */ }
    const pending = results.filter(row => row.job?.status === "in_progress");
    if (busy || !pending.length) return;
    let stopped = false;
    const timer = setTimeout(async () => {
      try {
        const next = await Promise.all(pending.slice(0, 3).map(async row => ({
          ...row, job: await refreshDailyJob(row.job!.job_id),
        })));
        if (stopped) return;
        setResults(results.map(row => next.find(item => rowKey(item) === rowKey(row)) ?? row));
        if (next.some(row => row.job.status !== "in_progress")) update.current?.();
      } catch {
        if (!stopped) setError("Suivi interrompu. Actualisez le lot pour reprendre.");
      }
    }, 8000);
    return () => { stopped = true; clearTimeout(timer); };
  }, [results, busy]);

  async function launch(mode: "selected_dates" | "current_month") {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    const selection = mode === "selected_dates" ? dates.slice().sort() : [];
    const key = JSON.stringify([mode, selection]);
    try {
      if (request.current?.key !== key) request.current = { key, id: crypto.randomUUID() };
      const rows = await startDailyBulk(mode, selection, request.current.id);
      if (!rows.some(row => row.error)) request.current = undefined;
      setResults(previous => {
        const rowsByKey = new Map(rows.map(row => [rowKey(row), row]));
        const ongoing = (previous ?? []).filter(row =>
          row.job?.status === "in_progress" || row.job?.status === "submission_unknown"
        );
        for (const row of ongoing) {
          if (!rowsByKey.has(rowKey(row))) rowsByKey.set(rowKey(row), row);
        }
        if (!rows.length) return previous ?? rows;
        return Array.from(rowsByKey.values()).sort((a, b) => a.date.localeCompare(b.date));
      });
      update.current?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Le lancement du lot a échoué.");
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }

  const active = results?.some(row => row.job?.status === "in_progress");
  return (
    <section className="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap gap-2">
        <button className={button} disabled={busy} onClick={() => void launch("current_month")}>
          Compléter le mois en cours
        </button>
        {onUpdate && <button className={button} disabled={busy || !dates.length || dates.length > 31}
          onClick={() => void launch("selected_dates")}>Compléter les dates sélectionnées ({dates.length})</button>}
        {active && <button className={button} disabled={busy} onClick={() => {
          setError("");
          setResults(rows => rows?.slice());
        }}>Actualiser le lot</button>}
      </div>
      {busy && <p role="status">Réservation des éditions…</p>}
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      {results && <div className="text-sm">
        {results.length === 0 && <p>Aucune journée terminée ce mois-ci.</p>}
        <ul className="space-y-1">
          {results.map(row => <li key={rowKey(row)}>
            <span className="font-medium">{row.date}</span>
            {row.error ? ` · ${row.error}` : row.no_content ? " · Sans contenu" : <>
              {row.job && <> · <Link className="underline" href={`/admin/editorial?job=${encodeURIComponent(row.job.job_id)}`}>
                {row.job.universes.length} éditions lancées</Link> · {row.job.status}</>}
              {!!row.already_done && ` · ${row.already_done} déjà faites`}
              {!!row.in_progress && ` · ${row.in_progress} déjà en cours`}
            </>}
          </li>)}
        </ul>
      </div>}
    </section>
  );
}
