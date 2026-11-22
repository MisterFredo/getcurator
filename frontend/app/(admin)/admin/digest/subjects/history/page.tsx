"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import SubjectDigestDocument, { type SubjectDigest } from "@/components/digest/SubjectDigestDocument";

type Entry = {
  id: string; name: string; company: string; email: string; audience: string;
  period_start: string; period_end: string; generated_at: string;
};
type Filters = { query: string; audience: string; date_from: string; date_to: string };
const emptyFilters: Filters = { query: "", audience: "", date_from: "", date_to: "" };
const pageSize = 50;

export default function DigestHistoryPage() {
  const [draft, setDraft] = useState(emptyFilters);
  const [filters, setFilters] = useState(emptyFilters);
  const [offset, setOffset] = useState(0);
  const [entries, setEntries] = useState<Entry[]>([]);
  const [total, setTotal] = useState(0);
  const [selected, setSelected] = useState("");
  const [digest, setDigest] = useState<SubjectDigest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [detailError, setDetailError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    setEntries([]);
    const params = new URLSearchParams({ limit: String(pageSize), offset: String(offset) });
    for (const [key, value] of Object.entries(filters)) if (value) params.set(key, value);
    api.get("/digest/admin/subject-digest-history?" + params.toString())
      .then(result => {
        if (active) { setEntries(result.digests); setTotal(result.total); }
      })
      .catch(failure => {
        if (active) { setError(failure instanceof Error ? failure.message : "Historique indisponible."); setTotal(0); }
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [filters, offset]);

  useEffect(() => {
    let active = true;
    setDigest(null);
    setDetailError("");
    if (selected) api.get("/digest/admin/subject-digests/" + encodeURIComponent(selected))
      .then(result => { if (active) setDigest(result.document); })
      .catch(failure => { if (active) setDetailError(failure instanceof Error ? failure.message : "Digest indisponible."); });
    return () => { active = false; };
  }, [selected]);

  function apply(next: Filters) {
    setFilters({ ...next, query: next.query.trim() });
    setOffset(0);
    setSelected("");
  }

  return (
    <div className="space-y-5">
      <Link href="/admin/digest" className="text-sm text-ratecard-blue underline">Produire un Digest</Link>
      <h1 className="text-3xl font-semibold">Historique des Digests</h1>
      <form className="space-y-4 rounded-xl border bg-white p-5" onSubmit={event => {
        event.preventDefault(); apply(draft);
      }}>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <label className="grid gap-1 text-sm">Destinataire, email ou société
            <input className="rounded border px-3 py-2" value={draft.query}
              onChange={event => setDraft({ ...draft, query: event.target.value })} />
          </label>
          <label className="grid gap-1 text-sm">Profils
            <select className="rounded border px-3 py-2" value={draft.audience}
              onChange={event => setDraft({ ...draft, audience: event.target.value })}>
              <option value="">Tous</option><option value="user">Utilisateurs</option><option value="expert">Experts</option>
            </select>
          </label>
          <label className="grid gap-1 text-sm">Période à partir du
            <input className="rounded border px-3 py-2" type="date" value={draft.date_from}
              max={draft.date_to || undefined} onChange={event => setDraft({ ...draft, date_from: event.target.value })} />
          </label>
          <label className="grid gap-1 text-sm">Période jusqu’au
            <input className="rounded border px-3 py-2" type="date" value={draft.date_to}
              min={draft.date_from || undefined} onChange={event => setDraft({ ...draft, date_to: event.target.value })} />
          </label>
        </div>
        <div className="flex gap-3">
          <button type="submit" className="rounded bg-ratecard-blue px-4 py-2 text-sm text-white">Rechercher</button>
          <button type="button" className="rounded border px-4 py-2 text-sm"
            onClick={() => { setDraft(emptyFilters); apply(emptyFilters); }}>Réinitialiser</button>
        </div>
        <p className="text-xs text-gray-500">Les résultats incluent les Digests dont la semaine recoupe la période choisie.</p>
      </form>
      {error && <p role="alert" className="text-red-700">{error}</p>}
      {loading ? <p role="status">Chargement…</p> : !error && <>
        <p className="text-sm text-gray-600">{total} Digest(s) · {total ? offset + 1 : 0}–{Math.min(offset + entries.length, total)}</p>
        <div className="overflow-x-auto rounded-lg border bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50"><tr>
              <th className="p-3">Destinataire</th><th className="p-3">Profil</th><th className="p-3">Période</th>
              <th className="p-3">Généré le</th><th className="p-3">Action</th>
            </tr></thead>
            <tbody>{entries.map(entry => <tr key={entry.id} className="border-t">
              <td className="p-3"><strong>{entry.name}</strong><div className="text-xs text-gray-500">{entry.company}</div><div className="text-xs text-gray-500">{entry.email}</div></td>
              <td className="p-3">{entry.audience === "expert" ? "Expert" : "Utilisateur"}</td>
              <td className="whitespace-nowrap p-3">{entry.period_start} → {entry.period_end}</td>
              <td className="p-3">{entry.generated_at.slice(0, 10)}</td>
              <td className="p-3"><button type="button" className="text-ratecard-blue underline" onClick={() => setSelected(entry.id)}>Ouvrir</button></td>
            </tr>)}</tbody>
          </table>
          {!entries.length && <p className="p-6 text-sm text-gray-500">Aucun Digest ne correspond à ces filtres.</p>}
        </div>
      </>}
      <nav className="flex gap-4 text-sm" aria-label="Pagination de l’historique">
        <button type="button" disabled={!offset || loading} onClick={() => { setSelected(""); setOffset(offset - pageSize); }} className="disabled:opacity-40">Précédent</button>
        <button type="button" disabled={offset + pageSize >= total || loading} onClick={() => { setSelected(""); setOffset(offset + pageSize); }} className="disabled:opacity-40">Suivant</button>
      </nav>
      {detailError && <p role="alert" className="text-red-700">{detailError}</p>}
      {selected && !digest && !detailError && <p role="status">Chargement du Digest…</p>}
      {digest && <SubjectDigestDocument key={digest.id} digest={digest} />}
    </div>
  );
}
