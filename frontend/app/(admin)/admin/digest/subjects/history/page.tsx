"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import SubjectDigestDocument, { type SubjectDigest } from "@/components/digest/SubjectDigestDocument";

type Entry = { id: string; name: string; period_start: string; period_end: string; generated_at: string };
const endpoint = "/digest/admin/subject-digests";
const pageSize = 50;

export default function SubjectDigestHistoryPage() {
  const [week, setWeek] = useState("");
  const [offset, setOffset] = useState(0);
  const [entries, setEntries] = useState<Entry[]>([]);
  const [selected, setSelected] = useState("");
  const [digest, setDigest] = useState<SubjectDigest | null>(null);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState("");
  const [detailError, setDetailError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setListError("");
    const params = new URLSearchParams({ limit: String(pageSize), offset: String(offset) });
    if (week) params.set("period_start", week);
    api.get(endpoint + "?" + params.toString())
      .then(result => { if (active) setEntries(result.digests); })
      .catch(error => {
        if (active) {
          setEntries([]);
          setListError(error instanceof Error ? error.message : "Historique indisponible.");
        }
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [week, offset]);

  useEffect(() => {
    setDigest(null);
    setDetailError("");
    if (!selected) return;
    let active = true;
    api.get(endpoint + "/" + encodeURIComponent(selected))
      .then(result => { if (active) setDigest(result.document); })
      .catch(error => { if (active) setDetailError(error instanceof Error ? error.message : "Digest indisponible."); });
    return () => { active = false; };
  }, [selected]);

  return (
    <div className="space-y-5">
      <Link href="/admin/digest" className="text-sm text-ratecard-blue underline">Produire un Digest</Link>
      <h1 className="text-3xl font-semibold">Historique des Digests</h1>
      <label className="flex items-center gap-3 text-sm">
        Début de semaine
        <input type="date" value={week} className="rounded border px-3 py-2" onChange={event => {
          setWeek(event.target.value);
          setOffset(0);
          setSelected("");
        }} />
      </label>
      {listError && <p role="alert" className="text-red-700">{listError}</p>}
      {loading ? <p role="status">Chargement…</p> : entries.length ? (
        <ul className="divide-y rounded border bg-white">
          {entries.map(entry => (
            <li key={entry.id}>
              <button type="button" aria-pressed={selected === entry.id} onClick={() => setSelected(entry.id)}
                className="flex w-full flex-wrap justify-between gap-3 px-4 py-3 text-left text-sm hover:bg-slate-50">
                <span className="font-medium text-ratecard-blue">{entry.name}</span>
                <span>{entry.period_start} → {entry.period_end}</span>
                <span>{entry.generated_at.slice(0, 10)}</span>
              </button>
            </li>
          ))}
        </ul>
      ) : !listError && <p>Aucun Digest enregistré.</p>}
      <nav className="flex gap-4 text-sm" aria-label="Pagination de l’historique">
        <button type="button" disabled={!offset || loading} onClick={() => setOffset(offset - pageSize)} className="disabled:opacity-40">Précédent</button>
        <button type="button" disabled={entries.length < pageSize || loading} onClick={() => setOffset(offset + pageSize)} className="disabled:opacity-40">Suivant</button>
      </nav>
      {detailError && <p role="alert" className="text-red-700">{detailError}</p>}
      {selected && !digest && !detailError && <p role="status">Chargement du Digest…</p>}
      {digest && <SubjectDigestDocument key={digest.id} digest={digest} />}
    </div>
  );
}
