"use client";
import {useEffect,useRef,useState} from "react";
import {api} from "@/lib/api";
import type {QualityRow} from "@/types/cockpit";
type Props={title:string;rows:QualityRow[];onDelete?:(id:string)=>void;onReload?:()=>Promise<void>};
function show(value:unknown){if(value===null||value===undefined)return "—";return typeof value==="object"?JSON.stringify(value):String(value);}
type DeleteResponse={status?:string;deleted_id?:string;message?:string};
export async function deleteSequentially(ids:string[],request:(id:string)=>Promise<DeleteResponse>,onDeleted:(id:string)=>void,shouldContinue:()=>boolean){
 let completed=0;
 for(const id of ids){
  if(!shouldContinue())break;
  const response=await request(id);
  if(response.status!=="ok"||response.deleted_id!==id)throw new Error(response.message||"Suppression non confirmée.");
  onDeleted(id);completed++;
 }
 return completed;
}
export default function ResultsPanel({title,rows,onDelete,onReload}:Props){
 const [busy,setBusy]=useState<string|null>(null);const [error,setError]=useState("");
 const [bulk,setBulk]=useState(false);const [progress,setProgress]=useState<{done:number;total:number}|null>(null);const [notice,setNotice]=useState("");
 const running=useRef(false);const stop=useRef(false);const mounted=useRef(true);
 useEffect(()=>{mounted.current=true;return()=>{mounted.current=false;stop.current=true;};},[]);
 const duplicate=title==="Doublons par URL source";
 async function remove(row:QualityRow){
  const id=String(row.ID_CONTENT||"");if(!id||running.current)return;
  if(!window.confirm(`Supprimer « ${show(row.TITLE)} » ?\nURL : ${show(row.SOURCE_URL)}\nContenu conservé : ${show(row.KEPT_TITLE)} (${show(row.KEPT_ID_CONTENT)})`))return;
  running.current=true;setBusy(id);setError("");setNotice("");setProgress(null);
  try{const res=await api.delete(`/cockpit/quality/duplicate-urls/${encodeURIComponent(id)}`);if(res.status!=="ok"||res.deleted_id!==id)throw new Error(res.message||"Suppression non confirmée.");if(mounted.current){onDelete?.(id);if(onReload)await onReload();}}
  catch(e){if(mounted.current)setError(e instanceof Error?e.message:"Suppression impossible.");}finally{running.current=false;if(mounted.current)setBusy(null);}
 }
 async function removeAll(){
  if(running.current)return;
  const ids=Array.from(new Set(rows.map(row=>String(row.ID_CONTENT||"")).filter(Boolean)));
  if(!ids.length)return;
  if(!window.confirm(`Supprimer les ${ids.length} doublon(s) affiché(s), un par un ? Les contenus indiqués comme conservés ne font pas partie de cette liste. Cette suppression est définitive.`))return;
  running.current=true;stop.current=false;setBulk(true);setBusy("bulk");setError("");setNotice("");setProgress({done:0,total:ids.length});
  let done=0;let failed=false;
  try{
   await deleteSequentially(ids,id=>api.delete(`/cockpit/quality/duplicate-urls/${encodeURIComponent(id)}`),id=>{
    done++;if(mounted.current){onDelete?.(id);setProgress({done,total:ids.length});}
   },()=>mounted.current&&!stop.current);
   if(mounted.current)setNotice(done===ids.length?`${done} doublon(s) supprimé(s).`:`Arrêt après ${done} suppression(s) sur ${ids.length}.`);
  }catch(e){failed=true;if(mounted.current)setError(`Traitement arrêté après ${done} suppression(s) sur ${ids.length}. ${e instanceof Error?e.message:"Suppression impossible."}`);}
  finally{
   if(mounted.current&&onReload){try{await onReload();}catch{if(!failed)setError("Les suppressions confirmées sont conservées, mais l’actualisation a échoué. Relancez le contrôle.");}}
   running.current=false;if(mounted.current){setBulk(false);setBusy(null);}
  }
 }
 if(!title)return <div className="border rounded-xl bg-white p-6 text-gray-500">Lancer un contrôle pour afficher les résultats.</div>;
 const columns=rows.length?Object.keys(rows[0]):[];
 return <section className="border rounded-xl bg-white overflow-hidden"><div className="p-5 border-b"><h2 className="text-xl font-semibold">{title}</h2><p className="text-sm text-gray-500">{rows.length} résultat(s)</p>{duplicate&&<p className="text-sm text-gray-500 mt-2">Le contenu conservé est choisi par date de publication décroissante, puis date de création et identifiant.</p>}{duplicate&&rows.length>0&&<div className="mt-3 flex flex-wrap items-center gap-3"><button disabled={busy!==null} onClick={()=>void removeAll()} className="border border-red-300 rounded text-red-700 px-3 py-2 disabled:opacity-50">{bulk?"Suppression en cours…":"Supprimer tous les doublons affichés"}</button>{bulk&&<button className="border rounded px-3 py-2" onClick={()=>{stop.current=true;setNotice("Arrêt demandé après la suppression en cours.");}}>Arrêter après la suppression en cours</button>}</div>}{progress&&<p role="status" className="mt-2 text-sm">{progress.done}/{progress.total} suppression(s) confirmée(s)</p>}{bulk&&<p className="text-sm text-gray-500 mt-2">Gardez cette page ouverte pendant la suppression.</p>}{notice&&<p role="status" className="mt-2 text-sm text-blue-800">{notice}</p>}{error&&<p role="alert" className="text-red-700 mt-2">{error}</p>}</div>{!rows.length?<p className="p-6">Aucun résultat.</p>:<div className="overflow-auto"><table className="w-full text-sm"><thead><tr>{columns.map(key=><th key={key} className="p-3 text-left border-b">{key}</th>)}{duplicate&&<th className="p-3">Action</th>}</tr></thead><tbody>{rows.map((row,index)=><tr key={String(row.ID_CONTENT||index)} className="border-b">{columns.map(key=><td key={key} className="p-3 align-top max-w-md break-words">{show(row[key])}</td>)}{duplicate&&<td className="p-3"><button disabled={busy!==null||!row.ID_CONTENT} onClick={()=>void remove(row)} className="border rounded text-red-700 px-3 py-2 disabled:opacity-50">{busy===String(row.ID_CONTENT)?"Suppression…":"Supprimer"}</button></td>}</tr>)}</tbody></table></div>}</section>;
}
