"use client";
import {useEffect,useState} from "react";
import {api} from "@/lib/api";
export default function MentionConnectorTest({companyId}:{companyId:string}){
  const [url,setUrl]=useState("");const [format,setFormat]=useState("raw");const [parsed,setParsed]=useState(true);
  const [busy,setBusy]=useState(false);const [ready,setReady]=useState(true);const [results,setResults]=useState<unknown[]>([]);const [error,setError]=useState("");
  useEffect(()=>{if(ready)return;const timer=setTimeout(()=>setReady(true),15000);return()=>clearTimeout(timer);},[ready]);
  async function test(mode:"SINGLE"|"PARALLEL"){
    setBusy(true);setError("");
    try{const result=await api.post("/company/watch/mentions/probe",{id_company:companyId,mode,target_url:url.trim()||null,response_format:format,parsed_response:parsed});setResults(previous=>[...previous,result]);}
    catch(e){setError(e instanceof Error?e.message:"Test impossible");}
    finally{setBusy(false);setReady(false);}
  }
  return <details className="bg-white border rounded p-4"><summary>Test du connecteur Bright Data (facultatif)</summary><div className="space-y-3 mt-3 text-sm"><p>Choisissez une société au-dessus. Ces tests effectuent un ou quatre appels fournisseur, sans import Library. Évitez de les lancer pendant une collecte de cette société.</p><label className="block">URL Google News du Playground (facultatif)<input className="border rounded px-3 py-2 w-full" value={url} onChange={e=>setUrl(e.target.value)} placeholder="Vide : FR/fr" disabled={busy}/></label><div className="flex flex-wrap gap-4"><label>Format API <select className="border rounded px-3 py-2" value={format} onChange={e=>setFormat(e.target.value)} disabled={busy}><option value="raw">raw</option><option value="json">json</option></select></label><label><input type="checkbox" checked={parsed} onChange={e=>setParsed(e.target.checked)} disabled={busy}/> data_format: parsed</label></div><div className="flex gap-3"><button className="border rounded px-3 py-2 disabled:opacity-40" disabled={busy||!ready||!companyId} onClick={()=>test("SINGLE")}>Un appel isolé</button><button className="border rounded px-3 py-2 disabled:opacity-40" disabled={busy||!ready||!companyId} onClick={()=>test("PARALLEL")}>Quatre appels simultanés</button></div>{!ready&&<p className="text-xs text-gray-500">Tests espacés de 15 secondes pour éviter les répétitions immédiates.</p>}{error&&<p className="text-red-700">{error}</p>}{results.map((result,i)=><pre key={i} className="text-xs whitespace-pre-wrap break-all border-t pt-3">{JSON.stringify(result,null,2)}</pre>)}</div></details>;
}
