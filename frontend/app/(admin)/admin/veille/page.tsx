"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import CompanyReportBatch, { companyReportHref } from "@/components/admin/company/CompanyReportBatch";

type Entry = { id_company: string; name: string; month: string; languages: string[]; has_notebook: boolean };

export default function WatchReportsPage() {
  const [entries, setEntries] = useState<Entry[] | null>(null);
  const [month, setMonth] = useState("");
  const [error, setError] = useState("");

  async function refresh() {
    try {
      setEntries((await api.get("/company/watch/reports/history")).reports);
      setError("");
    } catch {
      setError("Impossible de charger les rapports et brouillons.");
    }
  }

  useEffect(() => { void refresh(); }, []);

  const visible = entries?.filter(row => !month || row.month === month);
  return <main className="space-y-5">
    <header className="flex flex-wrap items-center justify-between gap-3">
      <div><h1 className="text-2xl font-semibold text-ratecard-blue">Veille</h1>
        <p className="text-sm text-gray-600">Rapports mensuels de veille par société</p></div>
      <Link href="/admin/veille/nouveau" className="rounded bg-ratecard-blue px-4 py-2 text-sm text-white">Générer un nouveau rapport</Link>
    </header>
    <CompanyReportBatch />
    <section className="space-y-3 rounded-xl border bg-white p-4">
      <h2 className="font-semibold">Rapports et brouillons</h2>
      <div className="flex flex-wrap gap-3 text-sm">
        <label>Mois <input className="rounded border p-2" type="month" value={month} onChange={event => setMonth(event.target.value)} /></label>
        <button className="rounded border px-3" onClick={refresh}>Actualiser</button>
      </div>
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      {!entries && !error && <p className="text-sm">Chargement…</p>}
      {visible?.length === 0 && <p className="text-sm">Aucun rapport ou brouillon pour ce filtre.</p>}
      {!!visible?.length && <table className="w-full text-left text-sm">
        <thead><tr><th>Société</th><th>Mois</th><th>État</th><th>Ouvrir</th></tr></thead>
        <tbody className="divide-y">{visible.map(row => <tr key={row.id_company + row.month}>
          <td className="py-2">{row.name}</td><td>{row.month}</td>
          <td>{row.languages.length ? "Rapport prêt" : row.has_notebook ? "Notebook prêt" : "Corpus enregistré"}</td>
          <td>{(row.languages.length ? row.languages : ["fr"]).map(lang =>
            <Link key={lang} className="mr-3 underline" href={companyReportHref(row.id_company, row.month, lang)}>
              {row.languages.length ? lang.toUpperCase() : "Reprendre"}
            </Link>)}</td>
        </tr>)}</tbody>
      </table>}
    </section>
  </main>;
}
