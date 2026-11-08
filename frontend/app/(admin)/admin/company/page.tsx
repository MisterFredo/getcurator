"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Pencil, Trash2 } from "lucide-react";

const GCS_BASE_URL = process.env.NEXT_PUBLIC_GCS_BASE_URL!;
const COMPANY_MEDIA_PATH = "companies";

type CompanyRow = {
  id_company: string;
  name: string;
  type?: string | null;
  description?: string | null;
  media_logo_rectangle_id?: string | null;
  is_partner?: boolean | null;
  universes?: string[];
  mention_watch_enabled?: boolean;
};
type MentionFilter = "all" | "enabled" | "disabled";
const errorText = (e: unknown) => e instanceof Error ? e.message : "Erreur de sauvegarde";

export default function CompanyList() {
  const [companies, setCompanies] = useState<CompanyRow[]>([]);
  const [contactCounts,setContactCounts]=useState<Record<string,number>|null>(null);
  const [countsError,setCountsError]=useState("");
  const [countsRevision,setCountsRevision]=useState(0);
  const [search, setSearch] = useState("");
  const [mentionFilter, setMentionFilter] = useState<MentionFilter>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState<Record<string, boolean>>({});
  const pending = useRef<Record<string, boolean>>({});
  const alive = useRef(true);

  useEffect(() => {
    alive.current = true;
    const filter = new URLSearchParams(window.location.search).get("mention_watch");
    if (filter === "enabled" || filter === "disabled") setMentionFilter(filter);
    async function load() {
      try {
        const res = await api.get("/company/list");
        if (alive.current) setCompanies(res.companies || []);
      } catch (e) {
        console.error(e);
        if (alive.current) setError(`Erreur chargement sociétés : ${errorText(e)}`);
      } finally {
        if (alive.current) setLoading(false);
      }
    }
    load();
    return () => { alive.current = false; };
  }, []);

  useEffect(()=>{
    let stopped=false;setCountsError("");
    void api.get("/contact/company-counts").then((res:{counts:Record<string,number>})=>{
      if(!stopped)setContactCounts(res.counts);
    }).catch((e:unknown)=>{if(!stopped){setContactCounts(null);setCountsError(`Compteurs contacts indisponibles : ${errorText(e)}`);}});
    return()=>{stopped=true;};
  },[countsRevision]);

  useEffect(()=>{
    const refresh=()=>setCountsRevision(v=>v+1);
    window.addEventListener("focus",refresh);window.addEventListener("contacts-updated",refresh);
    return()=>{window.removeEventListener("focus",refresh);window.removeEventListener("contacts-updated",refresh);};
  },[]);

  async function toggleMentionWatch(company: CompanyRow) {
    if (pending.current[company.id_company]) return;
    const next = !company.mention_watch_enabled;
    pending.current[company.id_company] = true;
    setSaving(v => ({...v, [company.id_company]: true}));
    setError("");
    try {
      const res = await api.put(`/company/${encodeURIComponent(company.id_company)}/mention-watch`, {is_enabled: next});
      if (typeof res.is_enabled !== "boolean") throw new Error("Réponse de sauvegarde invalide");
      if (alive.current) setCompanies(rows => rows.map(row => row.id_company === company.id_company
        ? {...row, mention_watch_enabled: res.is_enabled} : row));
    } catch (e) {
      console.error(e);
      if (alive.current) setError(`Veille Mentions de ${company.name} : ${errorText(e)}`);
    } finally {
      delete pending.current[company.id_company];
      if (alive.current) setSaving(v => ({...v, [company.id_company]: false}));
    }
  }

  async function deleteCompany(id: string, name: string) {
    if (pending.current[id] || !confirm(`Supprimer "${name}" ?`)) return;
    pending.current[id] = true;
    setSaving(v => ({...v, [id]: true}));
    setError("");
    try {
      await api.delete(`/company/${encodeURIComponent(id)}`);
      if (alive.current) setCompanies(rows => rows.filter(c => c.id_company !== id));
    } catch (e) {
      console.error(e);
      if (alive.current) setError(`Erreur suppression : ${errorText(e)}`);
    } finally {
      delete pending.current[id];
      if (alive.current) setSaving(v => ({...v, [id]: false}));
    }
  }

  const enabledCount = companies.filter(c => c.mention_watch_enabled === true).length;
  const filtered = companies.filter(c => {
    const q = search.trim().toLowerCase();
    const matches = c.name.toLowerCase().includes(q) || (c.type || "").toLowerCase().includes(q);
    const enabled = c.mention_watch_enabled === true;
    return matches && (mentionFilter === "all" || (mentionFilter === "enabled" ? enabled : !enabled));
  });

  return <div className="space-y-8">
    <div className="flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 className="text-3xl font-semibold text-ratecard-blue">Companies</h1>
        <div className="text-sm text-gray-500 mt-1">{companies.length} companies · {enabledCount} avec veille Mentions activée</div>
      </div>
      <Link href="/admin/company/create" className="bg-ratecard-green text-white px-4 py-2 rounded">+ New Company</Link>
    </div>

    <div className="flex flex-wrap gap-4 items-end">
      <label className="block w-full max-w-md"><span className="block text-sm mb-1">Rechercher</span>
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search..." className="border rounded px-3 py-2 w-full"/>
      </label>
      <label><span className="block text-sm mb-1">Veille Mentions</span>
        <select value={mentionFilter} onChange={e => setMentionFilter(e.target.value as MentionFilter)} className="border rounded px-3 py-2 bg-white">
          <option value="all">Toutes les sociétés</option><option value="enabled">Activée</option><option value="disabled">Désactivée</option>
        </select>
      </label>
      <button type="button" onClick={()=>setCountsRevision(v=>v+1)} className="underline py-2">Actualiser les compteurs contacts</button>
      <Link href="/admin/discovery/corpo/mentions" className="underline py-2">Ouvrir Discovery / Mentions</Link>
    </div>
    <p className="text-sm text-gray-500">L’activation rend la société éligible aux collectes de mentions Google Actualités. Elle ne déclenche pas encore de collecte automatique.</p>
    {countsError && <p role="alert" className="text-amber-700">{countsError}</p>}
    {error && <p role="alert" className="text-red-700">{error}</p>}

    {loading ? <div>Loading...</div> : filtered.length === 0 ? <div className="text-gray-500 italic">No company found.</div> :
      <div className="overflow-x-auto"><table className="w-full text-sm border-collapse">
        <thead><tr className="bg-gray-100 border-b">
          <th className="p-2 w-[90px]">Logo</th><th className="p-2 text-left">Name</th><th className="p-2 text-center">Description</th>
          <th className="p-2 text-left">Type</th><th className="p-2 text-left">Universes</th><th className="p-2 text-center">Partner</th>
          <th className="p-2 text-center">Contacts</th><th className="p-2 text-left">Veille Mentions</th><th className="p-2 text-right">Actions</th>
        </tr></thead>
        <tbody>{filtered.map(c => {
          const logoUrl = c.media_logo_rectangle_id ? `${GCS_BASE_URL}/${COMPANY_MEDIA_PATH}/${c.media_logo_rectangle_id}` : null;
          const enabled = c.mention_watch_enabled === true;
          return <tr key={c.id_company} className="border-b hover:bg-gray-50">
            <td className="p-2">{logoUrl ? <img src={logoUrl} alt={c.name} className="h-10 max-w-[110px] object-contain"/> : <span className="text-gray-400">—</span>}</td>
            <td className="p-2 font-medium">{c.name}</td><td className="p-2 text-center">{c.description?.trim() ? "Oui" : "Non"}</td>
            <td className="p-2">{c.type || "—"}</td>
            <td className="p-2"><div className="flex flex-wrap gap-1">{(c.universes || []).map(u => <span key={u} className="px-2 py-0.5 rounded text-xs bg-blue-100 text-blue-700">{u}</span>)}</div></td>
            <td className="text-center">{c.is_partner ? "✓" : "—"}</td>
            <td className="p-2 text-center">{contactCounts===null?<span className="text-gray-400">{countsError?"—":"…"}</span>:<Link className="underline font-medium" href={`/admin/contact?id_company=${encodeURIComponent(c.id_company)}`} aria-label={`Voir les ${contactCounts[c.id_company]||0} contacts de ${c.name}`}>{contactCounts[c.id_company]||0}</Link>}</td>
            <td className="p-2"><div className="flex flex-col items-start gap-1">
              <span className={enabled ? "text-green-700 font-medium" : "text-gray-500"}>{enabled ? "Activée" : "Désactivée"}</span>
              <button type="button" onClick={() => toggleMentionWatch(c)} disabled={!!saving[c.id_company]} aria-pressed={enabled}
                aria-label={`${enabled ? "Suspendre" : "Activer"} la veille Mentions de ${c.name}`} className="border rounded px-2 py-1 disabled:opacity-40">
                {saving[c.id_company] ? "Enregistrement…" : enabled ? "Suspendre" : "Activer"}
              </button>
              {enabled && <Link className="text-xs underline" href={`/admin/discovery/corpo/mentions?id_company=${encodeURIComponent(c.id_company)}`}>Collecter</Link>}
            </div></td>
            <td className="p-2 text-right"><div className="flex justify-end gap-3">
              <Link href={`/admin/company/edit/${c.id_company}`} aria-label={`Modifier ${c.name}`} className="text-blue-600 hover:text-blue-800"><Pencil size={16}/></Link>
              <button type="button" disabled={!!saving[c.id_company]} onClick={() => deleteCompany(c.id_company, c.name)} aria-label={`Supprimer ${c.name}`} className="text-red-600 hover:text-red-800 disabled:opacity-40"><Trash2 size={16}/></button>
            </div></td>
          </tr>;
        })}</tbody>
      </table></div>}
  </div>;
}
