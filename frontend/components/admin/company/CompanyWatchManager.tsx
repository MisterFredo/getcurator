"use client";

import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import WatchCollectionPanel from "./WatchCollectionPanel";
import {
  listWatchCompanies, listCompanyWatches, createCompanyWatch, updateCompanyWatch,
} from "@/lib/companyWatch";
import type {
  WatchCompany, CompanyWatch, WatchPayload, WatchSourceType, WatchSourceRole, WatchMethod,
} from "@/lib/companyWatch";

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
  const [status, setStatus] = useState("all");
  const [offset, setOffset] = useState(0);
  const [rows, setRows] = useState<CompanyWatch[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [actionError, setActionError] = useState("");
  const [notice, setNotice] = useState("");
  const [revision, setRevision] = useState(0);
  const [editor, setEditor] = useState<{ companyId: string; watchId?: string; companyName: string } | null>(null);
  const [draft, setDraft] = useState<WatchPayload>(emptyPayload);
  const [configText, setConfigText] = useState("{}");
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(false);
  const [collectionRow, setCollectionRow] = useState<CompanyWatch | null>(null);
  const mutation = useRef(false);
  const mounted = useRef(true);

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
    listWatchCompanies().then(data => {
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
    listCompanyWatches({ id_company: companyId || undefined,
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
  }, [companyId, status, offset, revision]);

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
    setDraft(emptyPayload()); setConfigText("{}"); setDirty(false); setNotice(""); setActionError("");
  }
  function startEdit(row: CompanyWatch) {
    if (!discardAllowed()) return;
    setEditor({ companyId: row.id_company, watchId: row.id_company_watch,
      companyName: row.company_name || row.id_company });
    setDraft({ label: row.label, source_type: row.source_type, source_url: row.source_url,
      source_role: row.source_role, author_name: row.author_name,
      collection_method: row.collection_method, collection_config: row.collection_config, is_active: row.is_active });
    setConfigText(JSON.stringify(row.collection_config || {}, null, 2));
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
      config = parsed as Record<string, unknown>;
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
    } catch (error) { if (mounted.current) setActionError(message(error)); }
    finally { mutation.current = false; if (mounted.current) setBusy(false); }
  }
  const editorCompany = fixedCompany || companies.find(c => c.id_company === editor?.companyId);
  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          {fixedCompany ? (
            <h2 className="text-xl font-semibold text-ratecard-blue">Veille Corpo</h2>
          ) : (
            <>
              <p className="text-sm text-gray-500">Discovery / Corpo</p>
              <h1 className="text-3xl font-semibold text-ratecard-blue">Veille sociétés</h1>
            </>
          )}
          <p className="text-gray-500 mt-1">{fixedCompany
            ? `Gérez les points de collecte de ${fixedCompany.name}.`
            : "Configurez les pages, comptes et newsletters à suivre pour chaque société."}</p>
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
            <option value="">Toutes les sociétés</option>
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
                <option value="CORPORATE">Corporate</option><option value="EMPLOYEE">Salarié</option>
              </select></label>
            <label className="space-y-1"><span className="text-sm">Auteur / personne suivie</span>
              <input maxLength={250} className={control} value={draft.author_name || ""}
                onChange={event => change("author_name", event.target.value || null)} /></label>
            <label className="space-y-1"><span className="text-sm">Méthode de récupération</span>
              <select className={control} value={draft.collection_method}
                onChange={event => change("collection_method", event.target.value as WatchMethod)}>
                <option value="MANUAL">Manuel — publication collée</option><option value="STUDIO">Studio — texte collé</option><option value="HTML">HTML — récupération web</option>
              </select></label>
            <label className="flex items-center gap-2 self-end py-2">
              <input type="checkbox" checked={draft.is_active} onChange={event => change("is_active", event.target.checked)} />Suivi actif
            </label>
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
      <section className="bg-white border rounded overflow-hidden" aria-label="Points de collecte">
        {loading ? <p role="status" className="p-8 text-gray-500">Chargement…</p>
          : loadError ? <div role="alert" className="p-6 text-red-700 whitespace-pre-wrap">{loadError}
            <button type="button" className={`${button} ml-3`} onClick={() => setRevision(value => value + 1)}>Réessayer</button></div>
          : !rows.length ? <p className="p-8 text-center text-gray-500">Aucun point de collecte pour ces filtres.</p>
          : <div className="overflow-x-auto"><table className="w-full text-sm text-left">
            <thead className="bg-gray-50 text-gray-600"><tr>
              {['Société', 'Point de collecte', 'Format / origine', 'Récupération', 'État', 'Actions'].map(label =>
                <th scope="col" key={label} className="px-4 py-3 font-medium">{label}</th>)}
            </tr></thead>
            <tbody>{rows.map(row => <tr key={row.id_company_watch} className="border-t align-top">
              <td className="px-4 py-3">{row.company_name || row.id_company}</td>
              <td className="px-4 py-3"><div className="font-medium">{row.label}</div>
                {safeUrl(row.source_url) ? <a className="text-ratecard-blue underline break-all" href={safeUrl(row.source_url)}
                  target="_blank" rel="noopener noreferrer">{row.source_url}</a> : <span>{row.source_url}</span>}
                {row.author_name && <div className="text-gray-500">{row.author_name}</div>}</td>
              <td className="px-4 py-3">{row.source_type}<div className="text-gray-500">{row.source_role === 'EMPLOYEE' ? 'Salarié' : 'Corporate'}</div></td>
              <td className="px-4 py-3">{row.collection_method === 'HTML' ? 'HTML' : row.collection_method === 'STUDIO' ? 'Studio' : 'Manuel'}</td>
              <td className="px-4 py-3"><span className={`rounded px-2 py-1 text-xs ${row.is_active ? 'bg-green-50 text-green-800' : 'bg-gray-100 text-gray-600'}`}>
                {row.is_active ? 'Actif' : 'Suspendu'}</span></td>
              <td className="px-4 py-3"><div className="flex gap-2">
                <button type="button" className={button} disabled={busy || !!editor || !!collectionRow}
                  onClick={() => { setCollectionRow(row); setActionError(""); setNotice(""); }}>
                  Collecte / publications
                </button>
                <button type="button" className={button} disabled={busy || !!collectionRow} onClick={() => startEdit(row)}>Modifier</button>
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
    </div>
  );
}

