"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { scanWatch, collectWatchUrl, extractWatchStep, importWatchText,
  listWatchPublications, getWatchPublication } from "@/lib/companyWatch";
import type { CompanyWatch, WatchPublication, WatchDetail } from "@/lib/companyWatch";

const button = "border rounded px-3 py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed";
const input = "border rounded px-3 py-2 w-full";
function errorMessage(error: unknown) { return error instanceof Error ? error.message : "Erreur de traitement"; }
function dateToday() {
  const parts = new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Paris", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(new Date());
  return `${parts.find(p => p.type === "year")?.value}-${parts.find(p => p.type === "month")?.value}-${parts.find(p => p.type === "day")?.value}`;
}

export default function WatchCollectionPanel({ watch, onClose, onBusyChange }: {
  watch: CompanyWatch; onClose: () => void; onBusyChange: (busy: boolean) => void;
}) {
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState("");
  const [errors, setErrors] = useState<string[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [items, setItems] = useState<WatchPublication[]>([]);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState("");
  const [hasMore, setHasMore] = useState(false);
  const [offset, setOffset] = useState(0);
  const [format, setFormat] = useState<"SINGLE" | "LINKEDIN_ACTIVITY">("SINGLE");
  const [text, setText] = useState("");
  const [title, setTitle] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [referenceDate, setReferenceDate] = useState(dateToday);
  const [publishedDate, setPublishedDate] = useState("");
  const [detail, setDetail] = useState<WatchDetail | null>(null);
  const [detailOffset, setDetailOffset] = useState(0);
  const [detailBusy, setDetailBusy] = useState(false);
  const active = useRef(true);
  const working = useRef(false);
  const stop = useRef(false);
  const listSequence = useRef(0);
  const detailSequence = useRef(0);

  useEffect(() => {
    active.current = true;
    return () => { active.current = false; stop.current = true; onBusyChange(false); };
  }, [onBusyChange]);

  const reload = useCallback(async () => {
    const sequence = ++listSequence.current;
    setLoading(true); setListError("");
    try {
      const result = await listWatchPublications(watch, offset);
      if (!active.current || sequence !== listSequence.current) return;
      setItems(result.items); setHasMore(result.has_more);
    } catch (error) {
      if (active.current && sequence === listSequence.current) setListError(errorMessage(error));
    } finally {
      if (active.current && sequence === listSequence.current) setLoading(false);
    }
  }, [watch, offset]);
  useEffect(() => { void reload(); }, [reload]);
  useEffect(() => {
    if (!running && !text.trim()) return;
    const handler = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ""; };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [running, text]);

  function close() {
    if (running) return;
    if (text.trim() && !window.confirm("Abandonner le texte non importé ?")) return;
    onClose();
  }
  function begin() {
    if (working.current || !watch.is_active) return false;
    working.current = true; stop.current = false; setRunning(true); onBusyChange(true);
    setErrors([]); setWarnings([]); setDetail(null); detailSequence.current += 1; setDetailBusy(false);
    return true;
  }
  async function finish() {
    working.current = false;
    if (!active.current) return;
    setRunning(false); onBusyChange(false);
    if (stop.current) setProgress("Traitement arrêté. Les publications et segments terminés sont conservés.");
    await reload();
  }
  async function extract(document: WatchPublication) {
    let current = document;
    while (active.current && !stop.current && (current.status || current.extraction_status) !== "COMPLETE") {
      setProgress(`${current.title} — segment ${current.next_chunk + 1}/${current.chunk_count}`);
      const previous = current.next_chunk;
      current = await extractWatchStep(watch, current.id_document);
      if (current.status !== "COMPLETE" && current.next_chunk <= previous) throw new Error("L'extraction n'a pas progressé.");
    }
  }
  async function collect() {
    if (!begin()) return;
    let preserved = 0;
    try {
      setProgress("Découverte des publications…");
      const result = await scanWatch(watch);
      if (!active.current) return;
      setWarnings(result.warnings || []);
      for (let index = 0; index < result.items.length && active.current && !stop.current; index++) {
        const item = result.items[index];
        setProgress(`Récupération ${index + 1}/${result.items.length} — ${item.url}`);
        try {
          const document = await collectWatchUrl(watch, item.url);
          if (!active.current) break;
          preserved++;
          await extract(document);
        } catch (error) {
          if (active.current) setErrors(previous => [...previous, `${item.url} : ${errorMessage(error)}`]);
        }
      }
      if (active.current && !stop.current) setProgress(`${preserved}/${result.items.length} publication(s) conservée(s) ou déjà connues. Consulter les erreurs et les états d'extraction ci-dessous.`);
    } catch (error) { if (active.current) setErrors(previous => [...previous, errorMessage(error)]); }
    finally { await finish(); }
  }
  async function importPaste(event: FormEvent) {
    event.preventDefault();
    if (!text.trim() || !begin()) return;
    try {
      setProgress("Conservation des publications…");
      const result = await importWatchText(watch, {
        text, format, title: title || undefined, source_url: sourceUrl || undefined,
        reference_date: format === "LINKEDIN_ACTIVITY" ? referenceDate || undefined : undefined,
        published_date: format === "SINGLE" ? publishedDate || undefined : undefined,
      });
      if (!active.current) return;
      setWarnings(result.warnings || []);
      setErrors(result.errors.map(error => `Publication ${error.index + 1} : ${error.error}`));
      // Garder le texte en cas d'échec partiel pour pouvoir relancer l'import.
      if (!result.errors.length) setText("");
      for (const document of result.items) {
        if (!active.current || stop.current) break;
        try { await extract(document); }
        catch (error) { if (active.current) setErrors(previous => [...previous, `${document.title} : ${errorMessage(error)}`]); }
      }
      if (active.current && !stop.current) setProgress(`${result.items.length} publication(s) conservée(s) ou déjà connues. Vérifier les états d'extraction.`);
    } catch (error) { if (active.current) setErrors(previous => [...previous, errorMessage(error)]); }
    finally { await finish(); }
  }
  async function resume(document: WatchPublication) {
    if (!begin()) return;
    try { await extract(document); if (active.current && !stop.current) setProgress("Extraction terminée."); }
    catch (error) { if (active.current) setErrors([errorMessage(error)]); }
    finally { await finish(); }
  }
  async function openDetail(document: WatchPublication, nextOffset=0) {
    const sequence = ++detailSequence.current;
    setDetailBusy(true);
    try {
      const result = await getWatchPublication(watch, document.id_document, nextOffset);
      if (active.current && sequence === detailSequence.current) { setDetail(result); setDetailOffset(nextOffset); }
    } catch (error) { if (active.current) setErrors(previous => [...previous, errorMessage(error)]); }
    finally { if (active.current && sequence === detailSequence.current) setDetailBusy(false); }
  }
  return <section className="border rounded bg-white p-5 space-y-4" aria-label="Collecte et publications">
    <div className="flex justify-between gap-3 items-start">
      <div><h2 className="text-lg font-semibold text-ratecard-blue">{watch.label} — collecte et Library</h2>
        <p className="text-sm text-gray-500">{watch.company_name || watch.id_company}</p></div>
      <button type="button" className={button} disabled={running} onClick={close}>Fermer</button>
    </div>
    {watch.collection_method === "HTML" && watch.source_type !== "PDF" && <div className="space-y-2">
      <button type="button" disabled={running || !watch.is_active} onClick={collect}
        className="bg-ratecard-green text-white rounded px-4 py-2 disabled:opacity-50">Collecter les publications web</button>
      <p className="text-sm text-gray-500">La collecte et l’extraction avancent tant que cette page reste ouverte. Une extraction interrompue peut être reprise.</p>
    </div>}
    {watch.source_type === "PDF" ? <p className="text-gray-500">Utilisez PDF Studio pour importer les PDF.</p> : <details>
      <summary className="cursor-pointer font-medium">Importer du texte {watch.collection_method !== "HTML" ? "— Manuel / Studio" : "en complément"}</summary>
      <form onSubmit={importPaste} className="space-y-3 mt-3">
        <fieldset disabled={running || !watch.is_active} className="space-y-3">
          <label className="block">Format<select className={input} value={format} onChange={event => setFormat(event.target.value as typeof format)}>
            <option value="SINGLE">Publication unique</option><option value="LINKEDIN_ACTIVITY">Activités LinkedIn — format du Studio</option>
          </select></label>
          <label className="block">Titre (facultatif)<input className={input} maxLength={1000} value={title} onChange={event => setTitle(event.target.value)} /></label>
          <label className="block">URL de la publication (facultatif)<input type="url" className={input} value={sourceUrl} onChange={event => setSourceUrl(event.target.value)} />
            <span className="text-xs text-gray-500">Pour un lot d’activités, laissez vide pour utiliser l’URL du compte.</span></label>
          {format === "LINKEDIN_ACTIVITY" ? <label className="block">Date de référence de la capture<input type="date" className={input}
            value={referenceDate} onChange={event => setReferenceDate(event.target.value)} /></label>
            : <label className="block">Date de publication (si connue)<input type="date" className={input} value={publishedDate} onChange={event => setPublishedDate(event.target.value)} /></label>}
          <label className="block">Texte complet<textarea required maxLength={200000} rows={8} className={input} value={text} onChange={event => setText(event.target.value)} /></label>
          <button type="submit" className={button} disabled={!text.trim()}>Conserver et extraire les informations</button>
        </fieldset>
      </form>
    </details>}
    {!watch.is_active && <p className="text-gray-500">Point suspendu : consultation uniquement.</p>}
    {progress && <p role="status" className="bg-blue-50 rounded p-3 break-words">{progress}</p>}
    {running && <button type="button" className={button} onClick={() => { stop.current = true; setProgress("Arrêt demandé à la fin de la requête en cours…"); }}>Arrêter après l’étape en cours</button>}
    {!!warnings.length && <ul className="list-disc pl-5 text-sm text-amber-800">{warnings.map((warning, i) => <li key={i}>{warning}</li>)}</ul>}
    {!!errors.length && <div role="alert" className="bg-red-50 rounded p-3 space-y-1 text-red-700 text-sm">{errors.map((error, i) => <p className="break-words" key={i}>{error}</p>)}</div>}
    <div className="flex items-center justify-between"><h3 className="font-medium">Publications conservées</h3>
      <button type="button" disabled={running || loading} className={button} onClick={() => void reload()}>Actualiser</button></div>
    {loading ? <p>Chargement…</p> : listError ? <p role="alert" className="text-red-700">{listError}</p>
      : !items.length ? <p className="text-gray-500">Aucune publication conservée.</p>
      : <div className="overflow-x-auto"><table className="w-full text-sm text-left"><thead><tr>
        <th className="p-2">Publication</th><th className="p-2">Extraction</th><th className="p-2">Informations</th><th className="p-2">Actions</th>
      </tr></thead><tbody>{items.map(item => <tr key={item.id_document} className="border-t">
        <td className="p-2 max-w-md break-words">{item.title}{item.extraction_error && <p className="text-red-700">{item.extraction_error}</p>}</td>
        <td className="p-2">{item.extraction_status === "COMPLETE" ? "Terminée" : item.extraction_status === "ERROR" ? "Erreur — reprise possible" : "À poursuivre"}
          <div>{item.next_chunk}/{item.chunk_count} segments</div></td>
        <td className="p-2">{item.unit_count ?? 0}<div className="text-gray-500">{item.review_count ?? 0} citations à contrôler</div></td>
        <td className="p-2"><div className="flex gap-2">
          <button type="button" className={button} disabled={running || detailBusy} onClick={() => void openDetail(item)}>Voir les preuves</button>
          {item.extraction_status !== "COMPLETE" && <button type="button" className={button} disabled={running || !watch.is_active} onClick={() => void resume(item)}>Reprendre</button>}
        </div></td>
      </tr>)}</tbody></table></div>}
    <div className="flex justify-end gap-2">
      <button type="button" className={button} disabled={running || loading || offset === 0} onClick={() => setOffset(value => Math.max(0, value - 50))}>Précédent</button>
      <button type="button" className={button} disabled={running || loading || !hasMore} onClick={() => setOffset(value => value + 50)}>Suivant</button>
    </div>
    {detail && <section className="border-t pt-4 space-y-3">
      <h3 className="font-semibold">{detail.title}</h3><p className="text-sm text-gray-500">{detail.warning}</p>
      <details><summary className="cursor-pointer">Texte source conservé</summary><pre className="whitespace-pre-wrap text-sm max-h-96 overflow-auto p-3 bg-gray-50">{detail.text}</pre></details>
      {detail.units.map(unit => <article key={unit.unit_id} className="border rounded p-3 space-y-2">
        <p>{unit.fact || "Candidat sans fait valide"}</p><blockquote className="border-l-2 pl-3 text-gray-600 whitespace-pre-wrap">{unit.quote || "Citation absente"}</blockquote>
        <p className="text-xs text-gray-500">{unit.verification_status} · {unit.verification_reason} · {unit.source_locator}</p>
      </article>)}
      {!detail.units.length && <p className="text-gray-500">Aucune information extraite à ce stade.</p>}
      <div className="flex gap-2"><button type="button" className={button} disabled={detailBusy || detailOffset === 0}
        onClick={() => void openDetail(detail, Math.max(0, detailOffset - 100))}>Preuves précédentes</button>
        <button type="button" className={button} disabled={detailBusy || !detail.has_more}
          onClick={() => void openDetail(detail, detailOffset + 100)}>Preuves suivantes</button></div>
    </section>}
  </section>;
}
