"use client";
import Link from "next/link";
import NumbersTransformation from "@/components/admin/numbers/NumbersTransformation";
export default function NumbersOperationsPanel(){
 return <section className="space-y-3"><div className="flex justify-between items-center"><h2 className="text-xl font-semibold">Numbers</h2><Link className="underline text-sm" href="/admin/numbers">Ouvrir Numbers</Link></div><NumbersTransformation/></section>;
}
