"use client";
import {useState} from "react";
import {api} from "@/lib/api";
import type {QualityRow} from "@/types/cockpit";
type Props={title:string;rows:QualityRow[];onDelete?:(id:string)=>void;onReload?:()=>Promise<void>};
function show(value:unknown){if(value===null||value===undefined)return "—";return typeof value==="object"?JSON.stringify(value):String(value);}
export default function ResultsPanel({title,rows,onDelete,onReload}:Props){
 const [busy,setBusy]=useState<string|null>(null);const [error,setError]=useState("");
 const duplicate=title==="Doublons par URL source";
 async function remove(row:QualityRow){
  const id=String(row.ID_CONTENT||"");if(!id||busy)return;
  if(!window.confirm(`Supprimer « ${show(row.TITLE)} » ?\nURL : ${show(row.SOURCE_URL)}\nContenu conservé : ${show(row.KEPT_TITLE)} (${show(row.KEPT_ID_CONTENT)})`))return;
  setBusy(id);setError("");
  try{const res=await api.delete(`/cockpit/quality/duplicate-urls/${encodeURIComponent(id)}`);if(res.status!=="ok"||res.deleted_id!==id)throw new Error(res.message||"Suppression non confirmée.");onDelete?.(id);if(onReload)await onReload();}
  catch(e){setError(e instanceof Error?e.message:"Suppression impossible.");}finally{setBusy(null);}
 }
 if(!title)return <div className="border rounded-xl bg-white p-6 text-gray-500">Lancer un contrôle pour afficher les résultats.</div>;
 const columns=rows.length?Object.keys(rows[0]):[];
 return <section className="border rounded-xl bg-white overflow-hidden"><div className="p-5 border-b"><h2 className="text-xl font-semibold">{title}</h2><p className="text-sm text-gray-500">{rows.length} résultat(s)</p>{duplicate&&<p className="text-sm text-gray-500 mt-2">Le contenu conservé est choisi par date de publication décroissante, puis date de création et identifiant.</p>}{error&&<p role="alert" className="text-red-700 mt-2">{error}</p>}</div>{!rows.length?<p className="p-6">Aucun résultat.</p>:<div className="overflow-auto"><table className="w-full text-sm"><thead><tr>{columns.map(key=><th key={key} className="p-3 text-left border-b">{key}</th>)}{duplicate&&<th className="p-3">Action</th>}</tr></thead><tbody>{rows.map((row,index)=><tr key={String(row.ID_CONTENT||index)} className="border-b">{columns.map(key=><td key={key} className="p-3 align-top max-w-md break-words">{show(row[key])}</td>)}{duplicate&&<td className="p-3"><button disabled={busy!==null||!row.ID_CONTENT} onClick={()=>void remove(row)} className="border rounded text-red-700 px-3 py-2 disabled:opacity-50">{busy===String(row.ID_CONTENT)?"Suppression…":"Supprimer"}</button></td>}</tr>)}</tbody></table></div>}</section>;
}
