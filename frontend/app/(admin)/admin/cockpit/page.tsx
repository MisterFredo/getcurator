"use client";
import {useState} from "react";
import {api} from "@/lib/api";
import type {QualityRow} from "@/types/cockpit";
import CockpitHeader from "@/components/admin/cockpit/CockpitHeader";
import MonitoringPanel from "@/components/admin/cockpit/MonitoringPanel";
import DiscoveryOperationsPanel from "@/components/admin/cockpit/DiscoveryOperationsPanel";
import OperationsPanel from "@/components/admin/cockpit/OperationsPanel";
import NumbersOperationsPanel from "@/components/admin/cockpit/NumbersOperationsPanel";
import QualityPanel from "@/components/admin/cockpit/QualityPanel";
import ResultsPanel from "@/components/admin/cockpit/ResultsPanel";
import TranslationBackfillOperation from "@/components/admin/cockpit/TranslationBackfillOperation";
export default function CockpitPage(){
 const [title,setTitle]=useState("");const [rows,setRows]=useState<QualityRow[]>([]);
 function results(nextTitle:string,nextRows:QualityRow[]){setTitle(nextTitle);setRows(nextRows);}
 async function reloadDuplicates(){const res=await api.get('/cockpit/quality/duplicate-urls');if(res.status!=="ok"||!Array.isArray(res.results))throw new Error('Suppression effectuée, mais actualisation indisponible. Relancer le contrôle.');setTitle('Doublons par URL source');setRows(res.results);}
 return <div className="space-y-8"><CockpitHeader/><MonitoringPanel/><DiscoveryOperationsPanel/><OperationsPanel/><NumbersOperationsPanel/><QualityPanel onResults={results}/><ResultsPanel key={title} title={title} rows={rows} onDelete={id=>setRows(prev=>prev.filter(row=>String(row.ID_CONTENT)!==id))} onReload={title==='Doublons par URL source'?reloadDuplicates:undefined}/><details className="border rounded-xl bg-white p-6"><summary className="font-semibold cursor-pointer">Bonus — outils ponctuels et diagnostics</summary><div className="space-y-6 mt-5"><section><h2 className="font-semibold mb-3">Backfill historique des traductions</h2><TranslationBackfillOperation/></section><QualityPanel bonus onResults={results}/></div></details></div>;
}
