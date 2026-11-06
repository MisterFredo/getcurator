"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { listCompanyWatches, scanCorpoSource, listCorpoDiscovery, storeCorpoDiscovery,
  getCorpoStoredContent } from "@/lib/companyWatch";
import type { CompanyWatch, CorpoDiscovery } from "@/lib/companyWatch";

const button = "border rounded px-3 py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed";
const labels = { NEW_URL: "Nouvelle URL", NEW_PAGE: "Nouvelle page", UPDATED_PAGE: "Mise à jour" };
const errorText = (error: unknown) => error instanceof Error ? error.message : "Erreur de traitement";
function safeUrl(value: string) {
  try { const u = new URL(value); return ["http:", "https:"].includes(u.protocol) ? u.href : undefined; }
  catch { return undefined; }
}

export default function WatchDiscoveryWorkspace({ companyId, watch, onBusyChange }: {
  companyId?: string; watch?: CompanyWatch; onBusyChange?: (busy: boolean) => void;
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
  const [content, setContent] = useState<{title:string;text:string;captured_at:string;url:string} | null>(null);
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
      const response = await listCorpoDiscovery({ companyId: scopeCompany, watchId: scopeWatch, status, offset });
      if (!mounted.current || sequence.current !== request) return;
      if (!response.items.length && offset > 0) { setOffset(value => Math.max(0, value - 50)); return; }
      setItems(response.items); setHasMore(response.has_more);
    } catch (error) {
      if (mounted.current && sequence.current === request) setLoadError(errorText(error));
    } finally {
      if (mounted.current && sequence.current === request) setLoading(false);
    }
  }, [scopeCompany, scopeWatch, status, offset]);
  useEffect(() => { setItems([]); void reload(); }, [reload]);
  useEffect(() => { setSelected([]); setContent(null); setOffset(0); }, [scopeCompany, scopeWatch, status]);
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
    if (stop.current) setProgress("Arrêt effectué. Les découvertes et stockages terminés sont conservés.");
    await reload();
  }
  async function sourcesToScan(): Promise<CompanyWatch[]> {
    if (watch) return watch.collection_method === "HTML" && watch.is_active && watch.source_type !== "PDF" ? [watch] : [];
    const result: CompanyWatch[] = [];
    let pageOffset = 0;
    while (mounted.current && !stop.current) {
      const response = await listCompanyWatches({id_company:scopeCompany,is_active:true,limit:500,offset:pageOffset});
      result.push(...response.watches.filter(source => source.collection_method === "HTML" && source.source_type !== "PDF"));
      if (!response.has_more) break;
      pageOffset += 500;
    }
    return result;
  }
  async function scan() {
    if (!begin()) return;
    let found = 0, known = 0, unchanged = 0;
    try {
      setProgress("Chargement des points HTML actifs…");
      const sources = await sourcesToScan();
      if (!sources.length && mounted.current && !stop.current) {
        setProgress("Aucun point HTML actif dans ce périmètre. Modifier sa méthode de récupération si nécessaire.");
      }
      for (let index=0;index<sources.length && mounted.current && !stop.current;index++) {
        const source = sources[index];
        setProgress(`Scan ${index+1}/${sources.length} — ${source.company_name || ""} / ${source.label}`);
        try {
          const response = await scanCorpoSource(source);
          if (!mounted.current) break;
          found += response.new;
          known += response.known; unchanged += response.unchanged;
          setWarnings(previous => [...previous,...response.warnings.map(w => `${source.label} : ${w}`)]);
          await reload();
        } catch (error) {
          if (mounted.current) setErrors(previous => [...previous,`${source.label} : ${errorText(error)}`]);
        }
      }
      if (sources.length && mounted.current && !stop.current) setProgress(`Scan terminé : ${found} nouvelle(s) URL ou version(s), ${known} URL connues, ${unchanged} page(s) inchangée(s). Sélectionnez les lignes à stocker.`);
    } catch (error) { if (mounted.current) setErrors(previous => [...previous,errorText(error)]); }
    finally { await finish(); }
  }
  async function storeSelected() {
    if (!selected.length || !begin()) return;
    const ids = [...selected]; let stored = 0;
    try {
      for (let index=0;index<ids.length && mounted.current && !stop.current;index++) {
        setProgress(`Stockage ${index+1}/${ids.length}…`);
        try {
          await storeCorpoDiscovery(ids[index]);
          if (!mounted.current) break;
          stored++;
          setSelected(previous => previous.filter(id => id !== ids[index]));
          await reload();
        } catch (error) {
          if (mounted.current) setErrors(previous => [...previous,`${ids[index]} : ${errorText(error)}`]);
        }
      }
      if (mounted.current && !stop.current) setProgress(`${stored}/${ids.length} capture(s) stockée(s). Aucun déstockage ni extraction lancé.`);
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
  const eligible = items.filter(row => row.status === "NEW" && row.watch_active && row.collection_method === "HTML");
  const allPageSelected = eligible.length > 0 && eligible.every(row => selected.includes(row.id_discovery));
  function togglePage() {
    const ids = eligible.map(row => row.id_discovery);
    setSelected(previous => allPageSelected ? previous.filter(id => !ids.includes(id)) : [...new Set([...previous,...ids])]);
  }
  return <section className="space-y-4" aria-label="Discovery Corpo">
    <div className="flex flex-wrap justify-between gap-3 items-center">
      <div><h2 className="text-xl font-semibold text-ratecard-blue">{watch ? watch.label : "URL découvertes — Corpo"}</h2>
        <p className="text-sm text-gray-500">Scanner → sélectionner → stocker les captures.</p></div>
      <button type="button" className="bg-ratecard-green text-white rounded px-4 py-2 disabled:opacity-50" disabled={running || !!(watch && (!watch.is_active || watch.collection_method !== "HTML" || watch.source_type === "PDF"))}
        onClick={() => void scan()}>{watch ? "Scanner ce point" : "SCAN ALL — points HTML actifs"}</button>
    </div>
    {watch && watch.collection_method !== "HTML" && <p className="text-sm text-gray-500">Le scan est disponible pour les points configurés en méthode HTML. L’entrée Manuel / Studio sera raccordée au stock séparément.</p>}
    <div className="flex flex-wrap gap-3 items-center">
      <label className="text-sm">Afficher <select className="border rounded px-3 py-2" value={status} disabled={running}
        onChange={event => setStatus(event.target.value)}>
        <option value="NEW">À stocker</option><option value="STORED">Stockés</option><option value="ALL">Tous</option>
      </select></label>
      <button type="button" className={button} disabled={running || loading} onClick={() => void reload()}>Actualiser</button>
      <button type="button" className={button} disabled={running || !eligible.length} onClick={togglePage}>
        {allPageSelected ? "Désélectionner cette page" : "Tout sélectionner sur cette page"}</button>
      <button type="button" className="bg-ratecard-blue text-white rounded px-4 py-2 disabled:opacity-50"
        disabled={running || !selected.length} onClick={() => void storeSelected()}>Stocker la sélection ({selected.length})</button>
    </div>
    {progress && <p role="status" className="bg-blue-50 p-3 rounded">{progress}</p>}
    {running && <button type="button" className={button} onClick={() => {stop.current=true;setProgress("Arrêt demandé après la requête en cours…");}}>Arrêter après l’étape en cours</button>}
    {!!warnings.length && <details><summary className="cursor-pointer text-amber-800">Couverture et avertissements ({warnings.length})</summary>
      <ul className="list-disc pl-5 text-sm text-amber-800">{warnings.map((w,i)=><li key={i}>{w}</li>)}</ul></details>}
    {!!errors.length && <div role="alert" className="bg-red-50 text-red-700 p-3 rounded">{errors.map((error,i)=><p className="break-words" key={i}>{error}</p>)}</div>}
    {loading ? <p role="status">Chargement des URL…</p> : loadError ? <p role="alert" className="text-red-700">{loadError}</p>
      : !items.length ? <div className="border rounded bg-white p-8 text-center text-gray-500">Aucune URL pour ce filtre. Lancez un scan ou consultez les éléments stockés.</div>
      : <div className="border rounded bg-white overflow-x-auto"><table className="w-full text-sm text-left"><thead className="bg-gray-50"><tr>
        <th className="p-3"><input type="checkbox" aria-label="Sélectionner cette page" checked={allPageSelected} disabled={running || !eligible.length} onChange={togglePage}/></th>
        <th className="p-3">Société / point</th><th className="p-3">URL / titre</th><th className="p-3">Découverte</th><th className="p-3">Détecté le</th><th className="p-3">État</th><th className="p-3">Capture</th>
      </tr></thead><tbody>{items.map(row=><tr key={row.id_discovery} className="border-t align-top">
        <td className="p-3"><input type="checkbox" aria-label={`Sélectionner ${row.title || row.url}`} checked={selected.includes(row.id_discovery)}
          disabled={running || row.status !== "NEW" || !row.watch_active || row.collection_method !== "HTML"}
          onChange={()=>setSelected(previous=>previous.includes(row.id_discovery)?previous.filter(id=>id!==row.id_discovery):[...previous,row.id_discovery])}/></td>
        <td className="p-3">{row.company_name}<div className="text-gray-500">{row.watch_label}</div></td>
        <td className="p-3 max-w-xl"><p className="font-medium">{row.title || row.url}</p>
          <a href={safeUrl(row.url)} target="_blank" rel="noopener noreferrer" className="underline text-ratecard-blue break-all">{row.url}</a>
          {row.error && <p className="text-red-700 break-words">{row.error}</p>}</td>
        <td className="p-3">{labels[row.change_type]}</td>
        <td className="p-3">{row.date_found ? new Date(row.date_found).toLocaleString("fr-FR", {timeZone:"Europe/Paris"}) : "—"}</td>
        <td className="p-3">{row.status === "STORED" ? "Stocké" : "À stocker"}</td>
        <td className="p-3">{row.status === "STORED" && <button type="button" className={button} disabled={running || contentLoading} onClick={()=>void view(row)}>Voir le texte</button>}</td>
      </tr>)}</tbody></table></div>}
    <div className="flex justify-end gap-2">
      <button type="button" className={button} disabled={running || loading || !!loadError || offset===0} onClick={()=>setOffset(value=>Math.max(0,value-50))}>Précédent</button>
      <button type="button" className={button} disabled={running || loading || !!loadError || !hasMore} onClick={()=>setOffset(value=>value+50)}>Suivant</button>
    </div>
    {content && <section className="border rounded bg-white p-4 space-y-3"><div className="flex justify-between gap-3"><h3 className="font-semibold">{content.title}</h3>
      <button type="button" className={button} onClick={()=>setContent(null)}>Fermer le texte</button></div>
      <p className="text-sm text-gray-500">Capture : {content.captured_at}</p><pre className="whitespace-pre-wrap text-sm max-h-96 overflow-auto">{content.text}</pre></section>}
  </section>;
}
