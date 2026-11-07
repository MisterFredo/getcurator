"use client";
import Link from "next/link";
import CompanyWatchManager from "@/components/admin/company/CompanyWatchManager";
export default function CompanyWatchPage(){
  return <div className="space-y-6"><section className="bg-white border rounded p-4"><h2 className="font-semibold">Mentions externes — collecte serveur</h2><p className="text-sm text-gray-600 mt-2">Lancer un relevé global des sociétés éligibles ou une collecte individuelle. Le traitement continue sans garder la page ouverte.</p><Link className="inline-block underline mt-3" href="/admin/discovery/corpo/mentions">Lancer et suivre les collectes Mentions →</Link></section><CompanyWatchManager/></div>;
}
