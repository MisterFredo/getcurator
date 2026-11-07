"use client";
import {useCockpitQuality} from "@/hooks/useCockpitQuality";
import type {QualityRow} from "@/types/cockpit";
type Props={onResults:(title:string,rows:QualityRow[])=>void;bonus?:boolean};
const bonusReports=[
 {endpoint:"unmatched-companies",title:"Unmatched Companies",description:"Valeurs d’ACTEURS_CITES sans alias société ni rejet correspondant."},
 {endpoint:"unmatched-solutions",title:"Unmatched Solutions",description:"Valeurs de SOLUTIONS_LLM sans alias solution ni rejet correspondant."},
 {endpoint:"numbers-structure",title:"Numbers Structure",description:"Contrôle du format historique CHIFFRES ; ne valide pas la fiabilité des chiffres."},
];
export default function QualityPanel({onResults,bonus=false}:Props){
 const {loading,error,load}=useCockpitQuality();
 const reports=bonus?bonusReports:[{endpoint:"duplicate-urls",title:"Doublons par URL source",description:"URL identiques, hors valeurs vides. Comparer chaque contenu au contenu conservé avant suppression."}];
 return <section className="border rounded-xl bg-white p-6 space-y-4"><h2 className="text-xl font-semibold">{bonus?"Diagnostics complémentaires":"Qualité"}</h2>{error&&<p role="alert" className="text-red-700">{error}</p>}{reports.map(report=><div key={report.endpoint} className="border rounded p-4 flex flex-wrap gap-3 items-center justify-between"><div><strong>{report.title}</strong><p className="text-sm text-gray-500">{report.description}</p></div><button disabled={loading} className="bg-ratecard-blue rounded px-4 py-2 text-white disabled:opacity-50" onClick={async()=>{try{const rows=await load(report.endpoint);onResults(report.title,rows);}catch{/* hook displays failure; existing results retained */}}}>{loading?"Contrôle…":"Contrôler"}</button></div>)}</section>;
}
