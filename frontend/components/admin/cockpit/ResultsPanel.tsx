"use client";
import {useEffect,useRef,useState} from "react";
import {api} from "@/lib/api";
import type {QualityRow} from "@/types/cockpit";
type Props={title:string;rows:QualityRow[];onDelete?:(id:string)=>void;onReload?:()=>Promise<void>};
function show(value:unknown){if(value===null||value===undefined)return "—";return typeof value==="object"?JSON.stringify(value):String(value);}
export default function ResultsPanel({title,rows,onDelete,onReload}:Props){
 const [busy,setBusy]=useState<string|null>(null);const [error,setError]=useState("");
 const [bulk,setBulk]=useState(false);const [notice,setNotice]=useState("");
 const running=useRef(false);const mounted=useRef(true);
 useEffect(()=>{mounted.current=true;return()=>{mounted.current=false;};},[]);
 const duplicate=title==="Doublons par URL source";
 async function remove(row:QualityRow){
  const id=String(row.ID_CONTENT||"");if(!id||running.current)return;
  if(!window.confirm(`Supprimer « ${show(row.TITLE)} » ?\nURL : ${show(row.SOURCE_URL)}\nContenu conservé : ${show(row.KEPT_TITLE)} (${show(row.KEPT_ID_CONTENT)})`))return;
  running.current=true;setBusy(id);setError("");setNotice("");
  try{const res=await api.delete(`/cockpit/quality/duplicate-urls/${encodeURIComponent(id)}`);if(res.status!=="ok"||res.deleted_id!==id)throw new Error(res.message||"Suppression non confirmée.");if(mounted.current){onDelete?.(id);if(onReload)await onReload();}}
  catch(e){if(mounted.current)setError(e instanceof Error?e.message:"Suppression impossible.");}finally{running.current=false;if(mounted.current)setBusy(null);}
 }
 async function removeAll(){
  if(running.current)return;
  const ids=Array.from(new Set(rows.map(row=>String(row.ID_CONTENT||"")).filter(Boolean)));
  if(!ids.length)return;
  if(!window.confirm(`Supprimer les ${ids.length} doublon(s) affiché(s) en un seul lot ? Le serveur revérifiera les doublons et préservera un contenu par URL. Cette suppression est définitive.`))return;
  running.current=true;setBulk(true);setBusy("bulk");setError("");setNotice("");
  let confirmed=false;
  try{
   const res=await api.post('/cockpit/quality/duplicate-urls/delete-batch',{content_ids:ids});
   if(res.status!=="ok"||!Array.isArray(res.deleted_ids)||!Array.isArray(res.skipped_ids)||res.deleted_count!==res.deleted_ids.length)throw new Error(res.message||"Confirmation de suppression invalide. Relancez le contrôle.");
   confirmed=true;
   if(mounted.current){
    // Backend returns only confirmed deletions; callbacks update the visible list.
    for(const id of res.deleted_ids)onDelete?.(String(id));
    setNotice(`${res.deleted_count} doublon(s) supprimé(s) en un lot · ${res.skipped_ids.length} identifiant(s) devenu(s) non supprimable(s) ignoré(s).`);
    if(onReload)await onReload();
   }
  }catch(e){if(mounted.current)setError(confirmed?"Suppression confirmée, mais actualisation indisponible. Relancez le contrôle.":`${e instanceof Error?e.message:"Suppression impossible."} Relancez le contrôle pour vérifier l’état réel avant de réessayer.`);}
  finally{running.current=false;if(mounted.current){setBulk(false);setBusy(null);}}
 }
 if(!title)return <div className="border rounded-xl bg-white p-6 text-gray-500">Lancer un contrôle pour afficher les résultats.</div>;
 const columns=rows.length?Object.keys(rows[0]):[];
 return <section className="border rounded-xl bg-white overflow-hidden"><div className="p-5 border-b"><h2 className="text-xl font-semibold">{title}</h2><p className="text-sm text-gray-500">{rows.length} résultat(s)</p>{duplicate&&<p className="text-sm text-gray-500 mt-2">Le contenu conservé est choisi par date de publication décroissante, puis date de création et identifiant.</p>}{duplicate&&rows.length>0&&<div className="mt-3 flex flex-wrap items-center gap-3"><button disabled={busy!==null} onClick={()=>void removeAll()} className="border border-red-300 rounded text-red-700 px-3 py-2 disabled:opacity-50">{bulk?"Suppression en cours…":"Supprimer tous les doublons affichés"}</button></div>}{bulk&&<p role="status" className="text-sm text-gray-500 mt-2">Suppression du lot en cours côté serveur. La transaction ne peut pas être interrompue depuis cet écran.</p>}{notice&&<p role="status" className="mt-2 text-sm text-blue-800">{notice}</p>}{error&&<p role="alert" className="text-red-700 mt-2">{error}</p>}</div>{!rows.length?<p className="p-6">Aucun résultat.</p>:<div className="overflow-auto"><table className="w-full text-sm"><thead><tr>{columns.map(key=><th key={key} className="p-3 text-left border-b">{key}</th>)}{duplicate&&<th className="p-3">Action</th>}</tr></thead><tbody>{rows.map((row,index)=><tr key={String(row.ID_CONTENT||index)} className="border-b">{columns.map(key=><td key={key} className="p-3 align-top max-w-md break-words">{show(row[key])}</td>)}{duplicate&&<td className="p-3"><button disabled={busy!==null||!row.ID_CONTENT} onClick={()=>void remove(row)} className="border rounded text-red-700 px-3 py-2 disabled:opacity-50">{busy===String(row.ID_CONTENT)?"Suppression…":"Supprimer"}</button></td>}</tr>)}</tbody></table></div>}</section>;
}
