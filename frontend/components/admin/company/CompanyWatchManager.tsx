"use client";

import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import WatchCollectionPanel from "./WatchCollectionPanel";
import WatchDiscoveryWorkspace from "./WatchDiscoveryWorkspace";
import {
  createCompanyWatch, updateCompanyWatch,
} from "@/lib/companyWatch";
import type {
  WatchCompany, CompanyWatch, WatchPayload, WatchSourceType, WatchSourceRole, WatchMethod,
} from "@/lib/companyWatch";

import {listMonitoredWatches,listActiveWatchCompanies} from '@/lib/watchOperations';
import type {MonitoredWatch, WatchChannel, WatchKind} from '@/lib/watchOperations';
const dateText=(value?:string)=>value?new Date(value).toLocaleString('fr-FR',{timeZone:'Europe/Paris'}):'—';
const PAGE_SIZE = 50;
const control = "w-full border rounded px-3 py-2 bg-white disabled:opacity-50";
const button = "border rounded px-3 py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed";
const types: WatchSourceType[] = ["HTML", "LINKEDIN", "NEWSLETTER", "PDF"];
function message(error: unknown) {
  return error instanceof Error ? error.message : "Une erreur est survenue.";
}
function safeUrl(value: string): string | undefined {
  try {
    const url = new URL(value);
    return ["http:", "https:"].includes(url.protocol) ? url.href : undefined;
  } catch { return undefined; }
}
function emptyPayload(): WatchPayload {
  return { label: "", source_type: "HTML", source_url: "", source_role: "CORPORATE",
    author_name: null, collection_method: "MANUAL", collection_config: {}, is_active: true };
}

type Props = {
  // En mode fiche Company, le parent remonte le composant avec key=id_company.
  company?: WatchCompany;
};

export default function CompanyWatchManager({ company: fixedCompany }: Props) {
  const [companies, setCompanies] = useState<WatchCompany[]>(fixedCompany ? [fixedCompany] : []);
  const [companiesLoading, setCompaniesLoading] = useState(!fixedCompany);
  const [companiesError, setCompaniesError] = useState("");
  const [companyRetry, setCompanyRetry] = useState(0);
  const [selectedCompanyId, setCompanyId] = useState("");
  const companyId = fixedCompany?.id_company || selectedCompanyId;
  const [sourcesOpen,setSourcesOpen]=useState(!!fixedCompany);
  const [status, setStatus] = useState("all");
  const [channel,setChannel]=useState<WatchChannel>('ALL');
  const [kind,setKind]=useState<WatchKind>('ALL');
  const [offset, setOffset] = useState(0);
  const [rows, setRows] = useState<MonitoredWatch[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [actionError, setActionError] = useState("");
  const [notice, setNotice] = useState("");
  const [revision, setRevision] = useState(0);
  const [editor, setEditor] = useState<{ companyId: string; watchId?: string; companyName: string } | null>(null);
  const [draft, setDraft] = useState<WatchPayload>(emptyPayload);
  const [configText, setConfigText] = useState("{}");
  const [monitorMode, setMonitorMode] = useState<"LISTING" | "SINGLE_PAGE">("LISTING");
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(false);
  const [collectionRow, setCollectionRow] = useState<CompanyWatch | null>(null);
  const mutation = useRef(false);
  const mounted = useRef(true);

  useEffect(()=>{
    const refresh=()=>setRevision(value=>value+1);
    window.addEventListener('watch-scan-updated',refresh);window.addEventListener('contacts-updated',refresh);window.addEventListener('focus',refresh);
    return()=>{window.removeEventListener('watch-scan-updated',refresh);window.removeEventListener('contacts-updated',refresh);window.removeEventListener('focus',refresh);};
  },[]);
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);

  useEffect(() => {
    let cancelled = false;
    if (fixedCompany) {
      setCompanies([fixedCompany]);
      setCompaniesLoading(false);
      setCompaniesError("");
      return;
    }
    setCompaniesLoading(true);
    setCompaniesError("");
    listActiveWatchCompanies().then(data => {
      if (!cancelled) setCompanies([...data].sort((a, b) => a.name.localeCompare(b.name)));
    }).catch(error => {
      if (!cancelled) setCompaniesError(message(error));
    }).finally(() => { if (!cancelled) setCompaniesLoading(false); });
    return () => { cancelled = true; };
  }, [companyRetry, fixedCompany]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setLoadError("");
    setRows([]);
    setHasMore(false);
    listMonitoredWatches({ channel,kind,id_company: companyId || undefined,
      is_active: status === "all" ? undefined : status === "active", offset, limit: PAGE_SIZE,
    }).then(result => {
      if (cancelled) return;
      // Une suspension peut vider la dernière page du filtre « Actifs ».
      if (!result.watches.length && offset > 0) {
        setOffset(Math.max(0, offset - PAGE_SIZE));
        return;
      }
      setRows(result.watches);
      setHasMore(result.has_more);
    }).catch(error => {
      if (!cancelled) setLoadError(message(error));
    }).finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [companyId, status, channel,kind,offset, revision]);

  useEffect(() => {
    if (!dirty) return;
    function preventLoss(event: BeforeUnloadEvent) { event.preventDefault(); event.returnValue = ""; }
    window.addEventListener("beforeunload", preventLoss);
    return () => window.removeEventListener("beforeunload", preventLoss);
  }, [dirty]);

  function discardAllowed() {
    return !dirty || window.confirm("Abandonner les modifications non enregistrées ?");
  }
  function closeEditor() {
    if (busy || !discardAllowed()) return;
    setEditor(null); setDirty(false); setActionError("");
  }
  function startCreate() {
    const company = fixedCompany || companies.find(c => c.id_company === companyId);
    if (!company || !discardAllowed()) return;
    setEditor({ companyId: company.id_company, companyName: company.name });
    setDraft(emptyPayload()); setConfigText("{}"); setMonitorMode("LISTING"); setDirty(false); setNotice(""); setActionError("");
  }
  function startEdit(row: CompanyWatch) {
    if(row.id_contact){if(!discardAllowed())return;window.location.assign(`/admin/contact/edit/${encodeURIComponent(row.id_contact)}`);return;}

    if (!discardAllowed()) return;
    setEditor({ companyId: row.id_company, watchId: row.id_company_watch,
      companyName: row.company_name || row.id_company });
    setDraft({ label: row.label, source_type: row.source_type, source_url: row.source_url,
      source_role: row.source_role, author_name: row.author_name,
      collection_method: row.collection_method, collection_config: row.collection_config, is_active: row.is_active });
    setConfigText(JSON.stringify(row.collection_config || {}, null, 2));
    setMonitorMode(row.collection_config?.mode === "SINGLE_PAGE" || (!row.collection_config?.mode && row.source_url.includes("linkedin.com")) ? "SINGLE_PAGE" : "LISTING");
    setDirty(false); setNotice(""); setActionError("");
  }
  function change<K extends keyof WatchPayload>(key: K, value: WatchPayload[K]) {
    setDraft(previous => ({ ...previous, [key]: value })); setDirty(true);
  }
  function prefill(kind: "website" | "linkedin") {
    const company = fixedCompany || companies.find(c => c.id_company === editor?.companyId);
    const url = kind === "website" ? company?.website_url : company?.linkedin_url;
    if (!url) return;
    change("source_url", url);
    change("source_type", kind === "website" ? "HTML" : "LINKEDIN");
  }
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editor || mutation.current) return;
    setActionError(""); setNotice("");
    let config: Record<string, unknown>;
    try {
      const parsed: unknown = JSON.parse(configText);
      if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
        throw new Error("La configuration doit être un objet JSON.");
      }
      config = { ...(parsed as Record<string, unknown>), mode: monitorMode };
    } catch (error) { setActionError(message(error)); return; }
    const url = safeUrl(draft.source_url.trim());
    if (!url) { setActionError("Saisissez une URL HTTP(S) valide."); return; }
    if (!draft.label.trim()) { setActionError("Le libellé est obligatoire."); return; }
    const payload: WatchPayload = { ...draft, label: draft.label.trim(), source_url: draft.source_url.trim(),
      author_name: draft.author_name?.trim() || null, collection_config: config };
    mutation.current = true; setBusy(true);
    try {
      if (editor.watchId) await updateCompanyWatch(editor.companyId, editor.watchId, payload);
      else await createCompanyWatch(editor.companyId, payload);
      if (!mounted.current) return;
      setEditor(null); setDirty(false);
      setNotice(editor.watchId ? "Point de collecte mis à jour." : "Point de collecte créé.");
      setRevision(value => value + 1);
    } catch (error) { if (mounted.current) setActionError(message(error)); }
    finally { mutation.current = false; if (mounted.current) setBusy(false); }
  }
  async function toggle(row: CompanyWatch) {
    if (mutation.current) return;
    mutation.current = true; setBusy(true); setActionError(""); setNotice("");
    try {
      await updateCompanyWatch(row.id_company, row.id_company_watch, { is_active: !row.is_active });
      if (!mounted.current) return;
      setNotice(row.is_active ? "Suivi suspendu." : "Suivi activé.");
      setRevision(value => value + 1);
      if(row.id_contact)window.dispatchEvent(new Event('contacts-updated'));
    } catch (error) { if (mounted.current) setActionError(message(error)); }
    finally { mutation.current = false; if (mounted.current) setBusy(false); }
  }
  const editorCompany = fixedCompany || companies.find(c => c.id_company === editor?.companyId);
  return (
    <div className="space-y-6">
      <div className="text-sm"><a href="/admin/contact" className="underline">Gérer les contacts et leur suivi LinkedIn</a></div>
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          {fixedCompany ? (
            <h2 className="text-xl font-semibold text-ratecard-blue">Veille</h2>
          ) : (
            <>
              <p className="text-sm text-gray-500">Discovery / Veille</p>
              <h1 className="text-3xl font-semibold text-ratecard-blue">Veille</h1>
            </>
          )}
          <p className="text-gray-500 mt-1">{fixedCompany
            ? `Gérez les points de collecte de ${fixedCompany.name}.`
            : "Suivez les sites et comptes LinkedIn des sociétés et contacts, puis retrouvez les publications découvertes."}</p>
        </div>
        <button type="button" onClick={startCreate} disabled={!companyId || companiesLoading || busy || !!collectionRow}
          className="bg-ratecard-green text-white rounded px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed">
          Ajouter un point de collecte
        </button>
      </header>
      <div className="bg-white border rounded p-4 flex flex-wrap items-end gap-4">
        {!fixedCompany && <label className="flex-1 min-w-64 space-y-1">
          <span className="text-sm font-medium">Société</span>
          <select className={control} value={companyId} disabled={busy || !!editor || !!collectionRow || companiesLoading}
            onChange={event => { setCompanyId(event.target.value); setOffset(0); setNotice(""); setActionError(""); }}>
            <option value="">Toutes les sociétés actives suivies</option>
            {companies.map(company => <option key={company.id_company} value={company.id_company}>{company.name}</option>)}
          </select>
        </label>}
        <label className="space-y-1">
          <span className="text-sm font-medium">État</span>
          <select className={control} value={status} disabled={busy || !!editor || !!collectionRow}
            onChange={event => { setStatus(event.target.value); setOffset(0); }}>
            <option value="all">Tous</option><option value="active">Actifs</option><option value="inactive">Suspendus</option>
          </select>
        </label>
        <label className="space-y-1"><span className="text-sm font-medium">Canal</span>
          <select className={control} value={channel} onChange={e=>{setChannel(e.target.value as WatchChannel);setOffset(0);}}><option value="ALL">Sites et LinkedIn</option><option value="WEB">Sites</option><option value="LINKEDIN">LinkedIn</option></select></label>
        <label className="space-y-1"><span className="text-sm font-medium">Type de relevé</span>
          <select className={control} value={kind} onChange={e=>{setKind(e.target.value as WatchKind);setOffset(0);}}><option value="ALL">Tous les relevés</option><option value="PUBLICATIONS">Publications / URL</option><option value="SINGLE_PAGE">Pages uniques</option></select></label>
        <button type="button" className={button} disabled={loading || busy || !!editor || !!collectionRow}
          onClick={() => setRevision(value => value + 1)}>Actualiser</button>
      </div>
      {!companyId && <p className="text-sm text-gray-500">Sélectionnez une société pour ajouter un point de collecte.</p>}
      {companiesError && <div role="alert" className="text-red-700 bg-red-50 border rounded p-3">
        Chargement des sociétés : {companiesError} <button type="button" className="underline ml-2"
          onClick={() => setCompanyRetry(value => value + 1)}>Réessayer</button>
      </div>}
      {notice && <p role="status" className="bg-green-50 text-green-800 border rounded p-3">{notice}</p>}
      {actionError && <p role="alert" className="bg-red-50 text-red-700 border rounded p-3 whitespace-pre-wrap">{actionError}</p>}
      {editor && <section className="bg-white border rounded p-5 space-y-4" aria-labelledby="editor-title">
        <h2 id="editor-title" className="text-lg font-semibold text-ratecard-blue">
          {editor.watchId ? "Modifier" : "Ajouter"} un point de collecte — {editor.companyName}
        </h2>
        <form onSubmit={save} className="space-y-4">
          <fieldset disabled={busy} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <label className="space-y-1"><span className="text-sm">Libellé *</span>
              <input required maxLength={250} className={control} value={draft.label}
                onChange={event => change("label", event.target.value)} /></label>
            <label className="space-y-1"><span className="text-sm">Format *</span>
              <select className={control} value={draft.source_type}
                onChange={event => change("source_type", event.target.value as WatchSourceType)}>
                {types.map(type => <option key={type}>{type}</option>)}
              </select></label>
            <label className="space-y-1 md:col-span-2"><span className="text-sm">URL de la page ou du compte *</span>
              <input required type="url" maxLength={4096} className={control} value={draft.source_url}
                placeholder="https://…" onChange={event => change("source_url", event.target.value)} />
              <span className="block text-xs text-gray-500">Pour une newsletter : page d’inscription ou d’archives.</span>
            </label>
            <div className="md:col-span-2 flex flex-wrap gap-2">
              <button type="button" className={button} disabled={!editorCompany?.website_url} onClick={() => prefill("website")}>Reprendre le site de la société</button>
              <button type="button" className={button} disabled={!editorCompany?.linkedin_url} onClick={() => prefill("linkedin")}>Reprendre le LinkedIn de la société</button>
            </div>
            <label className="space-y-1"><span className="text-sm">Origine</span>
              <select className={control} value={draft.source_role}
                onChange={event => change("source_role", event.target.value as WatchSourceRole)}>
                <option value="CORPORATE">Corporate</option><option value="EMPLOYEE" disabled>Salarié — gérer via Contacts</option>
              </select></label>
            <label className="space-y-1"><span className="text-sm">Auteur / personne suivie</span>
              <input maxLength={250} className={control} value={draft.author_name || ""}
                onChange={event => change("author_name", event.target.value || null)} /></label>
            <label className="space-y-1"><span className="text-sm">Méthode de récupération</span>
              <select className={control} value={draft.collection_method}
                onChange={event => change("collection_method", event.target.value as WatchMethod)}>
                <option value="MANUAL">Manuel — publication collée</option><option value="STUDIO">Studio — texte collé</option><option value="HTML">HTML — récupération web</option><option value="BRIGHTDATA">Bright Data — posts LinkedIn</option>
              </select></label>
            <label className="flex items-center gap-2 self-end py-2">
              <input type="checkbox" checked={draft.is_active} onChange={event => change("is_active", event.target.checked)} />Suivi actif
            </label>
            <label className="space-y-1 md:col-span-2"><span className="text-sm">Comportement du scan HTML</span>
              <select className={control} value={monitorMode} onChange={event => { setMonitorMode(event.target.value as "LISTING" | "SINGLE_PAGE"); setDirty(true); }}>
                <option value="LISTING">Liste de publications — découvrir de nouvelles URL</option>
                <option value="SINGLE_PAGE">Page précise — détecter ses mises à jour</option>
              </select>
            </label>
            {draft.collection_method === "BRIGHTDATA" && <div className="md:col-span-2 border rounded p-3 space-y-2 bg-blue-50">
              <p className="text-sm">Posts LinkedIn de société ou de profil personnel. Le type est déduit de l’URL.</p>
              <p className="text-sm">Limite par scan : 100 publications par défaut. Pour l’ajuster, renseignez <code>limit_per_input</code> dans les paramètres avancés (entier, ou <code>null</code> pour demander sans plafond).</p>
              <p className="text-xs text-gray-600">La clé Bright Data est configurée uniquement dans le backend.</p>
            </div>}
            <details className="md:col-span-2">
              <summary className="cursor-pointer text-sm text-gray-600">Paramètres avancés</summary>
              <label className="block mt-3 space-y-1"><span className="text-sm">Configuration JSON</span>
                <textarea rows={5} className={`${control} font-mono text-sm`} value={configText}
                  onChange={event => { setConfigText(event.target.value); setDirty(true); }} /></label>
            </details>
          </fieldset>
          <div className="flex gap-2">
            <button type="submit" disabled={busy} className="bg-ratecard-blue text-white rounded px-4 py-2 disabled:opacity-50">
              {busy ? "Enregistrement…" : "Enregistrer"}</button>
            <button type="button" disabled={busy} className={button} onClick={closeEditor}>Annuler</button>
          </div>
        </form>
      </section>}
      {collectionRow && <WatchCollectionPanel key={collectionRow.id_company_watch}
        watch={collectionRow} onClose={() => setCollectionRow(null)} onBusyChange={setBusy} />}
      <button type="button" className={button} aria-expanded={sourcesOpen} aria-controls="corpo-source-list"
        onClick={()=>setSourcesOpen(value=>!value)}>
        {sourcesOpen ? "Masquer les points de collecte" : "Afficher les points de collecte"}
      </button>
      {sourcesOpen && <div id="corpo-source-list">
      <section className="bg-white border rounded overflow-hidden" aria-label="Points de collecte">
        {loading ? <p role="status" className="p-8 text-gray-500">Chargement…</p>
          : loadError ? <div role="alert" className="p-6 text-red-700 whitespace-pre-wrap">{loadError}
            <button type="button" className={`${button} ml-3`} onClick={() => setRevision(value => value + 1)}>Réessayer</button></div>
          : !rows.length ? <p className="p-8 text-center text-gray-500">Aucun point de collecte pour ces filtres.</p>
          : <div className="overflow-x-auto"><table className="w-full text-sm text-left">
            <thead className="bg-gray-50 text-gray-600"><tr>
              {['Société', 'Point de collecte', 'Format / origine', 'Récupération', 'État', 'Dernier relevé / diagnostics', 'Actions'].map(label =>
                <th scope="col" key={label} className="px-4 py-3 font-medium">{label}</th>)}
            </tr></thead>
            <tbody>{rows.map(row => <tr key={row.id_company_watch} className="border-t align-top">
              <td className="px-4 py-3">{row.company_name || row.id_company}</td>
              <td className="px-4 py-3"><div className="font-medium">{row.label}</div>
                {safeUrl(row.source_url) ? <a className="text-ratecard-blue underline break-all" href={safeUrl(row.source_url)}
                  target="_blank" rel="noopener noreferrer">{row.source_url}</a> : <span>{row.source_url}</span>}
                {row.author_name && <div className="text-gray-500">{row.author_name}</div>}</td>
              <td className="px-4 py-3">{row.source_type}<div className="text-gray-500">{row.source_role === 'EMPLOYEE' ? 'Salarié' : 'Corporate'}</div></td>
              <td className="px-4 py-3">{row.collection_method === 'BRIGHTDATA' ? 'Bright Data' : row.collection_method === 'HTML' ? 'HTML' : row.collection_method === 'STUDIO' ? 'Studio' : 'Manuel'}</td>
              <td className="px-4 py-3"><span className={`rounded px-2 py-1 text-xs ${row.is_active ? 'bg-green-50 text-green-800' : 'bg-gray-100 text-gray-600'}`}>
                {row.is_active ? 'Actif' : 'Suspendu'}</span></td>
              <td className="px-4 py-3 min-w-72"><p>{row.watch_channel==='LINKEDIN'?'LinkedIn':'Site'} · {row.watch_kind==='SINGLE_PAGE'?'Page unique':'Publications / URL'}</p>
                {row.diagnostic?<div className="mt-2 space-y-1 text-xs"><strong>{row.diagnostic.status==='FAILED'?'Échec':row.diagnostic.status==='RUNNING'?'En cours':row.diagnostic.warnings?.length?'Réussi avec avertissements':'Réussi'}</strong>
                  <p>Dernière tentative : {dateText(row.diagnostic.last_attempt_at)}</p><p>Dernier succès : {dateText(row.diagnostic.last_success_at)}</p>
                  {row.diagnostic.new!==undefined&&<p>Dernier succès : {row.diagnostic.new} nouveautés · {row.diagnostic.known||0} connues · {row.diagnostic.unchanged||0} inchangées</p>}
                  {row.diagnostic.error&&<p className="text-red-700 whitespace-pre-wrap">{row.diagnostic.error}</p>}
                  {!!row.diagnostic.warnings?.length&&<details><summary className="cursor-pointer text-amber-800">Remarques ({row.diagnostic.warnings.length})</summary>{row.diagnostic.warnings.map((w,i)=><p className="text-amber-800 mt-1" key={i}>{w}</p>)}</details>}
                </div>:<p className="mt-2 text-xs text-gray-500">Aucun relevé enregistré. Les anciens diagnostics HTML ne sont pas disponibles.</p>}
              </td>
              <td className="px-4 py-3"><div className="flex gap-2">
                <button type="button" className={button} disabled={busy || !!editor || !!collectionRow}
                  onClick={() => { setCollectionRow(row); setActionError(""); setNotice(""); }}>
                  Scan / URL
                </button>
                <button type="button" className={button} disabled={busy || !!collectionRow} onClick={() => startEdit(row)}>{row.id_contact?"Fiche contact":"Modifier"}</button>
                <button type="button" className={button} disabled={busy || !!editor || !!collectionRow} onClick={() => toggle(row)}>
                  {row.is_active ? 'Suspendre' : 'Activer'}</button>
              </div></td>
            </tr>)}</tbody>
          </table></div>}
        <div className="border-t px-4 py-3 flex items-center justify-between gap-3 text-sm">
          <span>{!loading && !loadError && rows.length ? `Lignes ${offset + 1}–${offset + rows.length}` : ' '}</span>
          <div className="flex gap-2">
            <button type="button" className={button} disabled={loading || busy || !!editor || !!collectionRow || offset === 0 || !!loadError}
              onClick={() => setOffset(value => Math.max(0, value - PAGE_SIZE))}>Précédent</button>
            <button type="button" className={button} disabled={loading || busy || !!editor || !!collectionRow || !hasMore || !!loadError}
              onClick={() => setOffset(value => value + PAGE_SIZE)}>Suivant</button>
          </div>
        </div>
      </section>
      </div>}
      {!collectionRow && <div className="pt-8 border-t">
        <WatchDiscoveryWorkspace key={companyId || "all"} companyId={companyId || undefined} channel={channel} kind={kind} onBusyChange={setBusy}/>
      </div>}
    </div>
  );
}
