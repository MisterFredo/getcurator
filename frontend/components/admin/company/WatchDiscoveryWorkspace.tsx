"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { changeCorpoDiscoveryStatus,
  getCorpoStoredContent, attachCorpoSnapshot, importCorpoLibraryStep } from "@/lib/companyWatch";
import type { CompanyWatch, CorpoDiscovery } from "@/lib/companyWatch";

import WatchScanControls from './WatchScanControls';
import {listWatchItems} from '@/lib/watchOperations';
import type {WatchChannel,WatchKind,WatchRole} from '@/lib/watchOperations';
const button = "border rounded px-3 py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed";
const labels = { NEW_URL: "Nouvelle URL", NEW_PAGE: "Nouvelle page", UPDATED_PAGE: "Mise à jour" };
const errorText = (error: unknown) => error instanceof Error ? error.message : "Erreur de traitement";
function safeUrl(value: string) {
  try { const u = new URL(value); return ["http:", "https:"].includes(u.protocol) ? u.href : undefined; }
  catch { return undefined; }
}

export default function WatchDiscoveryWorkspace({ companyId, watch, role="ALL", channel="ALL", kind="ALL", onBusyChange }: {
  companyId?: string; watch?: CompanyWatch;role?:WatchRole; channel?:WatchChannel;kind?:WatchKind;onBusyChange?: (busy: boolean) => void;
}) {
  const [items, setItems] = useState<CorpoDiscovery[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [status, setStatus] = useState("NEW");
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState("");
  const [errors, setErrors] = useState<string[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [content, setContent] = useState<Awaited<ReturnType<typeof getCorpoStoredContent>> | null>(null);
  const [snapshotId, setSnapshotId] = useState("");
  const [contentLoading, setContentLoading] = useState(false);
  const mounted = useRef(true);
  const working = useRef(false);
  const stop = useRef(false);
  const sequence = useRef(0);
  const contentSequence = useRef(0);
  const scopeCompany = watch?.id_company || companyId;
  const scopeWatch = watch?.id_company_watch;

  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; stop.current = true; onBusyChange?.(false); };
  }, [onBusyChange]);

  const reload = useCallback(async () => {
    const request = ++sequence.current;
    setLoading(true); setLoadError("");
    try {
      const response = await listWatchItems({ companyId: scopeCompany, watchId: scopeWatch, status, role,channel,kind,offset });
      if (!mounted.current || sequence.current !== request) return;
      if (!response.items.length && offset > 0) { setOffset(value => Math.max(0, value - 50)); return; }
      setItems(response.items); setHasMore(response.has_more);
    } catch (error) {
      if (mounted.current && sequence.current === request) setLoadError(errorText(error));
    } finally {
      if (mounted.current && sequence.current === request) setLoading(false);
    }
  }, [scopeCompany, scopeWatch, status, role,channel,kind,offset]);
  useEffect(() => { setItems([]); void reload(); }, [reload]);
  useEffect(() => { setSelected([]); setContent(null); setOffset(0); }, [scopeCompany, scopeWatch, status,role,channel,kind]);
  useEffect(() => {
    if (!running) return;
    const prevent = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ""; };
    window.addEventListener("beforeunload", prevent);
    return () => window.removeEventListener("beforeunload", prevent);
  }, [running]);

  function begin() {
    if (working.current) return false;
    working.current = true; stop.current = false; setRunning(true); onBusyChange?.(true);
    setErrors([]); setWarnings([]); setContent(null); contentSequence.current += 1; setContentLoading(false);
    return true;
  }
  async function finish() {
    working.current = false;
    if (!mounted.current) return;
    setRunning(false); onBusyChange?.(false);
    if (stop.current) setProgress("Arrêt après l’étape en cours. Les captures et segments extraits sont conservés ; reprenez les imports dans le filtre En cours. Une collecte Bright Data déjà lancée continue.");
    await reload();
  }
  async function importSelected() {
    if (!selected.length || !begin()) return;
    const ids = [...selected]; let imported = 0;
    try {
      for (let index=0; index<ids.length && mounted.current && !stop.current; index++) {
        try {
          let complete = false;
          while (!complete && mounted.current && !stop.current) {
            setProgress(`Library ${index+1}/${ids.length} — enregistrement / extraction…`);
            const response = await importCorpoLibraryStep(ids[index]);
            if (!mounted.current) break;
            complete = response.library_status === "IMPORTED";
            setProgress(`Library ${index+1}/${ids.length} — ${response.next_chunk}/${response.chunk_count} segment(s) traité(s).`);
            if (complete) {
              imported++;
              setSelected(previous => previous.filter(id => id !== ids[index]));
            }
            await reload();
          }
        } catch (error) {
          if (mounted.current) setErrors(previous => [...previous,`Import Library : ${errorText(error)}. Reprise disponible dans le filtre Erreurs / En cours.`]);
        }
      }
      if (mounted.current && !stop.current) setProgress(`${imported}/${ids.length} publication(s) importée(s) dans la Library, avec extraction terminée.`);
    } finally { await finish(); }
  }
  async function changeSelected(action: "dismiss" | "restore") {
    if (!selected.length || !begin()) return;
    const ids = [...selected];
    let updated = 0, skipped = 0;
    try {
      for (let index = 0; index < ids.length && mounted.current && !stop.current; index += 500) {
        const batch = ids.slice(index, index + 500);
        setProgress(action === "dismiss" ? "Ignorer la sélection…" : "Restaurer la sélection…");
        const response = await changeCorpoDiscoveryStatus(batch, action);
        if (!mounted.current) break;
        updated += response.updated; skipped += response.skipped;
        setSelected(previous => previous.filter(id => !batch.includes(id)));
        await reload();
      }
      if (mounted.current && !stop.current) {
        setProgress(`${updated} URL/version(s) ${action === "dismiss" ? "ignorée(s)" : "restaurée(s)"}.${skipped ? ` ${skipped} ligne(s) déjà traitée(s) ou indisponible(s).` : ""}`);
      }
    } catch (error) {
      if (mounted.current) setErrors(previous => [...previous, errorText(error)]);
    } finally { await finish(); }
  }
  async function view(row: CorpoDiscovery) {
    const request = ++contentSequence.current;
    setContentLoading(true);
    try {
      const response = await getCorpoStoredContent(row.id_discovery);
      if (mounted.current && request === contentSequence.current) setContent(response);
    } catch (error) { if (mounted.current) setErrors(previous => [...previous,errorText(error)]); }
    finally { if (mounted.current && request === contentSequence.current) setContentLoading(false); }
  }
  
  const eligible = items.filter(row => status === "DISMISSED" ? row.status === "DISMISSED" :
    row.status !== "DISMISSED" && row.library_status !== "IMPORTED" && row.watch_active !== false);
  const allPageSelected = eligible.length > 0 && eligible.every(row => selected.includes(row.id_discovery));
  function togglePage() {
    const ids = eligible.map(row => row.id_discovery);
    setSelected(previous => allPageSelected ? previous.filter(id => !ids.includes(id)) : Array.from(new Set([...previous,...ids])));
  }
  const heading = watch?.label ?? {
    EMPLOYEE: "Publications découvertes — Salariés",
    CORPORATE: "Publications découvertes — Corporate",
    ALL: "Publications découvertes — Toutes les sources",
  }[role];
  return <section className="space-y-4" aria-label={heading}>
    <div className="flex flex-wrap justify-between gap-3 items-center">
      <div><a className="underline text-sm text-ratecard-blue" href="/admin/library/corpo">Ouvrir la Library →</a><h2 className="text-xl font-semibold text-ratecard-blue">{heading}</h2>
        <p className="text-sm text-gray-500">Scanner → sélectionner → envoyer vers la Library.</p></div>
    </div>
    <WatchScanControls companyId={scopeCompany} watch={watch} role={role} channel={channel} kind={kind} onComplete={()=>void reload()}/>
    {watch && !["HTML", "BRIGHTDATA"].includes(watch.collection_method) && <p className="text-sm text-gray-500">Le scan est disponible pour les points configurés en HTML ou Bright Data. L’entrée Manuel / Studio sera raccordée séparément.</p>}
    {watch?.collection_method === "BRIGHTDATA" && <div className="border rounded p-3 space-y-3 bg-blue-50">
      <p className="text-sm">Le suivi côté serveur récupère les collectes déjà lancées. Un lancement incertain doit être rattaché avec son identifiant avant toute nouvelle demande.</p>
      <details><summary className="text-sm cursor-pointer">Rattacher un lancement incertain</summary>
        <p className="text-sm mt-2">Uniquement si le lancement a été interrompu avant réception de son identifiant : recopiez le snapshot ID depuis Bright Data.</p>
        <input className="border rounded px-3 py-2 mt-2" value={snapshotId} placeholder="sd_…" onChange={event => setSnapshotId(event.target.value)} disabled={running}/>
        <button type="button" className={`${button} ml-2`} disabled={running || !snapshotId.trim()} onClick={async () => {
          if (!begin()) return;
          try { await attachCorpoSnapshot(watch, snapshotId.trim()); setProgress("Collecte rattachée. Cliquez sur Récupérer le dernier scan LinkedIn."); }
          catch (error) { if (mounted.current) setErrors([errorText(error)]); }
          finally { await finish(); }
        }}>Rattacher</button>
      </details>
    </div>}
    <div className="flex flex-wrap gap-3 items-center">
      <label className="text-sm">Afficher <select className="border rounded px-3 py-2" value={status} disabled={running}
        onChange={event => setStatus(event.target.value)}>
        <option value="NEW">À importer</option><option value="IMPORTING">En cours</option><option value="ERROR">Erreurs</option><option value="IMPORTED">Importés dans la Library</option><option value="DISMISSED">Ignorés</option><option value="ALL">Tous</option>
      </select></label>
      <button type="button" className={button} disabled={running || loading} onClick={() => void reload()}>Actualiser</button>
      <button type="button" className={button} disabled={running || !eligible.length} onClick={togglePage}>
        {allPageSelected ? "Désélectionner cette page" : "Tout sélectionner sur cette page"}</button>
      {status === "DISMISSED" ? (
        <button type="button" className={button} disabled={running || !selected.length}
          onClick={() => void changeSelected("restore")}>Restaurer la sélection ({selected.length})</button>
      ) : (<>
        <button type="button" className={button} disabled={running || !selected.length || items.some(row => selected.includes(row.id_discovery) && (row.status !== "NEW" || row.library_status !== "PENDING"))}
          onClick={() => void changeSelected("dismiss")}>Ignorer la sélection ({selected.length})</button>
        <button type="button" className="bg-ratecard-blue text-white rounded px-4 py-2 disabled:opacity-50"
          disabled={running || !selected.length} onClick={() => void importSelected()}>Envoyer vers la Library ({selected.length})</button>
      </>)}
    </div>
    {progress && <p role="status" className="bg-blue-50 p-3 rounded">{progress}</p>}
    {running && <button type="button" className={button} onClick={() => {stop.current=true;setProgress("Arrêt demandé après la requête en cours…");}}>Arrêter après l’étape en cours</button>}
    {!!warnings.length && <details><summary className="cursor-pointer text-amber-800">Couverture et avertissements ({warnings.length})</summary>
      <ul className="list-disc pl-5 text-sm text-amber-800">{warnings.map((w,i)=><li key={i}>{w}</li>)}</ul></details>}
    {!!errors.length && <div role="alert" className="bg-red-50 text-red-700 p-3 rounded">{errors.map((error,i)=><p className="break-words" key={i}>{error}</p>)}</div>}
    {loading ? <p role="status">Chargement des URL…</p> : loadError ? <p role="alert" className="text-red-700">{loadError}</p>
      : !items.length ? <div className="border rounded bg-white p-8 text-center text-gray-500">Aucune publication pour ce filtre. Lancez un scan ou consultez les publications importées.</div>
      : <div className="border rounded bg-white overflow-x-auto"><table className="w-full text-sm text-left"><thead className="bg-gray-50"><tr>
        <th className="p-3"><input type="checkbox" aria-label="Sélectionner cette page" checked={allPageSelected} disabled={running || !eligible.length} onChange={togglePage}/></th>
        <th className="p-3">Société / point</th><th className="p-3">URL / titre</th><th className="p-3">Découverte</th><th className="p-3" title="Date de publication du post ; elle peut différer de la date d’un relais.">Parution</th><th className="p-3">Détecté le</th><th className="p-3">État</th><th className="p-3">Consultation</th>
      </tr></thead><tbody>{items.map(row=><tr key={row.id_discovery} className="border-t align-top">
        <td className="p-3"><input type="checkbox" aria-label={`Sélectionner ${row.title || row.url}`} checked={selected.includes(row.id_discovery)}
          disabled={running || !eligible.some(item => item.id_discovery === row.id_discovery)}
          onChange={()=>setSelected(previous=>previous.includes(row.id_discovery)?previous.filter(id=>id!==row.id_discovery):[...previous,row.id_discovery])}/></td>
        <td className="p-3">{row.company_name}<div className="text-gray-500">{row.watch_label}</div><div className="text-xs text-gray-500">{(()=>{try{return new URL(row.url).hostname.endsWith("linkedin.com")?"LinkedIn":"Site";}catch{return "Site";}})()} · {row.change_type==="NEW_URL"?"Publication / URL":"Page unique"}</div></td>
        <td className="p-3 max-w-xl"><p className="font-medium">{row.title || row.url}</p>
          <a href={safeUrl(row.url)} target="_blank" rel="noopener noreferrer" className="underline text-ratecard-blue break-all">{row.url}</a>
          {row.error && <p className="text-red-700 break-words">{row.error}</p>}</td>
        <td className="p-3">{labels[row.change_type]}</td>
        <td className="p-3 whitespace-nowrap" title={row.publication_date_note || "Date de publication"}>
          {row.published_at ? new Date(row.published_at).toLocaleString("fr-FR", {
            timeZone: "Europe/Paris", dateStyle: "short", timeStyle: "short",
          }) : "—"}
        </td>
        <td className="p-3">{row.date_found ? new Date(row.date_found).toLocaleString("fr-FR", {timeZone:"Europe/Paris"}) : "—"}</td>
        <td className="p-3">{row.status === "DISMISSED" ? "Ignoré" : row.library_status === "IMPORTED" ? "Importé dans la Library" : row.library_status === "IMPORTING" ? "En cours" : row.library_status === "ERROR" ? "Erreur — à reprendre" : "À importer"}</td>
        <td className="p-3">{row.id_document && <a className="underline text-ratecard-blue block mb-2" href={`/admin/library/corpo?document=${encodeURIComponent(row.id_document)}`}>Voir dans la Library</a>}{row.status === "STORED" && <button type="button" className={button} disabled={running || contentLoading} onClick={()=>void view(row)}>Voir le texte</button>}</td>
      </tr>)}</tbody></table></div>}
    <div className="flex justify-end gap-2">
      <button type="button" className={button} disabled={running || loading || !!loadError || offset===0} onClick={()=>setOffset(value=>Math.max(0,value-50))}>Précédent</button>
      <button type="button" className={button} disabled={running || loading || !!loadError || !hasMore} onClick={()=>setOffset(value=>value+50)}>Suivant</button>
    </div>
    {content && <section className="border rounded bg-white p-4 space-y-3"><div className="flex justify-between gap-3"><h3 className="font-semibold">{content.title}</h3>
      <button type="button" className={button} onClick={()=>setContent(null)}>Fermer le texte</button></div>
      <p className="text-sm text-gray-500">Capture : {content.captured_at}</p>
      {content.published_at && <p className="text-sm">Date du post : {new Date(content.published_at).toLocaleString("fr-FR")}</p>}
      {(content.author_name || content.author_id) && <p className="text-sm">Auteur : {content.author_name || content.author_id}</p>}
      {content.monitored_account_url && <p className="text-sm">Compte suivi : {content.monitored_account_url}. La date de relais n’est pas établie par cette collecte.</p>}<pre className="whitespace-pre-wrap text-sm max-h-96 overflow-auto">{content.text}</pre></section>}
  </section>;
}
