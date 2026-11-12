"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

const endpoint = "/company/watch/reports/batch";
const button = "rounded border px-3 py-2 text-sm disabled:opacity-50";

type Company = { id_company: string; name: string };
type Status = "PENDING" | "READY" | "EXISTING" | "EMPTY" | "REVIEW" | "FAILED";
type Job = {
  status: "RUNNING" | "COMPLETE";
  month: string;
  language: "fr" | "en";
  updated_at: string;
  companies: (Company & { status: Status; message?: string })[];
};

const labels: Record<Status, string> = {
  PENDING: "À traiter", READY: "Prêt", EXISTING: "Déjà disponible",
  EMPTY: "Sans corpus", REVIEW: "Corpus à vérifier", FAILED: "Échec",
};

export function companyReportHref(id: string, month: string, language = "fr") {
  return "/admin/veille/nouveau?" + new URLSearchParams({ company: id, month, language });
}

export default function CompanyReportBatch() {
  const [options, setOptions] = useState<{ month: string; companies: Company[] } | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [language, setLanguage] = useState("fr");
  const [job, setJob] = useState<Job | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function loadOptions() {
    try {
      const result = await api.get(endpoint + "/options");
      setOptions(result);
      setSelected(result.companies.map((company: Company) => company.id_company));
      setError("");
    } catch {
      setError("Impossible de charger les sociétés suivies.");
    }
  }

  useEffect(() => { void loadOptions(); }, []);

  useEffect(() => {
    let active = true;
    let timer: number | undefined;
    async function poll() {
      try {
        const result = await api.get(endpoint);
        if (active) setJob(result.job);
      } catch {
        // Keep the last observed server state and retry on the next poll.
      } finally {
        if (active) timer = window.setTimeout(poll, 6000);
      }
    }
    void poll();
    return () => { active = false; window.clearTimeout(timer); };
  }, []);

  async function launch(resume: boolean) {
    if (busy || !options) return;
    setBusy(true);
    setError("");
    try {
      await api.post(endpoint + (resume ? "/resume" : ""), resume ? {} : {
        month: options.month, company_ids: selected, language,
      });
      setJob((await api.get(endpoint)).job);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de lancer le lot.");
    } finally {
      setBusy(false);
    }
  }

  const running = job?.status === "RUNNING";
  return <details className="rounded-xl border bg-white p-4">
    <summary className="cursor-pointer font-semibold">Générer les rapports du dernier mois</summary>
    <div className="mt-4 space-y-4">
      <p className="text-sm text-gray-600">Le lot reprend le corpus enregistré ou la présélection du mois. Vous pouvez quitter la page après le lancement.</p>
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      {!options && <button className={button} onClick={loadOptions}>Charger les sociétés suivies</button>}
      {options && <fieldset className="space-y-3" disabled={busy || running}>
        <legend className="font-medium">{options.month} · {selected.length} / {options.companies.length} sociétés</legend>
        <div className="flex flex-wrap items-center gap-3">
          <button type="button" className={button} onClick={() => setSelected(options.companies.map(row => row.id_company))}>Tout cocher</button>
          <button type="button" className={button} onClick={() => setSelected([])}>Tout décocher</button>
          <label className="text-sm">Langue <select className="rounded border p-2" value={language} onChange={event => setLanguage(event.target.value)}>
            <option value="fr">Français</option><option value="en">English</option>
          </select></label>
        </div>
        <div className="grid max-h-56 gap-2 overflow-auto rounded border p-3 sm:grid-cols-2 lg:grid-cols-3">
          {options.companies.map(company => <label key={company.id_company} className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={selected.includes(company.id_company)} onChange={event => {
              const checked = event.target.checked;
              setSelected(ids => checked ? [...ids, company.id_company] : ids.filter(id => id !== company.id_company));
            }}/>{company.name}
          </label>)}
          {!options.companies.length && <p className="text-sm">Aucune société suivie.</p>}
        </div>
        <button type="button" className={button + " bg-ratecard-blue text-white"} disabled={!selected.length}
          onClick={() => void launch(false)}>Lancer la génération</button>
      </fieldset>}
      {job && <div className="space-y-2 border-t pt-3 text-sm">
        <p role="status" className="font-semibold">{job.month} · {job.language.toUpperCase()} · {running ? "En cours" : "Terminé"}
          {" · "}{job.companies.filter(row => row.status !== "PENDING").length} / {job.companies.length} traitées</p>
        {running && <p>Dernière progression à {new Date(job.updated_at).toLocaleString("fr-FR")}</p>}
        {(running || job.companies.some(row => row.status === "FAILED")) &&
          <button type="button" className={button} disabled={busy || !options} onClick={() => void launch(true)}>
            {running ? "Reprendre après interruption" : "Réessayer les échecs"}
          </button>}
        <details>
          <summary className="cursor-pointer">Résultats par société</summary>
          <ul className="divide-y">
            {job.companies.map(row => <li className="py-2" key={row.id_company}>
              <Link className="underline" href={companyReportHref(row.id_company, job.month, job.language)}>{row.name}</Link>
              {" · "}{labels[row.status]}{row.message && ` · ${row.message}`}
            </li>)}
          </ul>
        </details>
      </div>}
    </div>
  </details>;
}
