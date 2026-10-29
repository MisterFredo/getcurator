"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";

type Article = { title: string; body: string; document_title: string; pdf_url: string | null; pages: number[]; evidence: { unit_id: string; page: number | null; fact: string; verification_status: string }[] };
export default function PdfSourcePage() {
  const params = useParams();
  const id = String(params.idRaw || "");
  const [data, setData] = useState<Article | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!id) return;
    api.get(`/discovery/pdf-studio/article/${encodeURIComponent(id)}`)
      .then((r: Article) => setData(r))
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Article indisponible"));
  }, [id]);
  if (error) return <main className="mx-auto max-w-4xl p-8 text-red-700">{error}</main>;
  if (!data) return <main className="mx-auto max-w-4xl p-8">Chargement…</main>;
  return <main className="mx-auto max-w-4xl space-y-6 p-8">
    <p className="text-sm text-gray-500">Article documentaire créé à partir d’un rapport PDF</p>
    <h1 className="text-3xl font-bold">{data.title}</h1>
    <article className="whitespace-pre-wrap leading-relaxed">{data.body}</article>
    <section className="space-y-3 border-t pt-6">
      <h2 className="text-xl font-semibold">Document original et traçabilité</h2>
      <p>{data.document_title} · Pages utilisées : {data.pages.join(", ") || "non précisées"}</p>
      {data.pdf_url && <a className="text-blue-700 underline" href={data.pdf_url} target="_blank" rel="noopener noreferrer">Consulter le PDF original</a>}
      <ul className="space-y-2">{data.evidence.map((e, i) => <li key={`${e.unit_id}-${i}`} className="rounded border p-3 text-sm">Page {e.page ?? "?"} · {e.unit_id} · {e.verification_status} — {e.fact}</li>)}</ul>
    </section>
  </main>;
}
