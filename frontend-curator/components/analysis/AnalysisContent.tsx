"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

/* ========================================================= */

type Concept = {
  id_concept: string;
  title: string;
};

type AnalysisData = {
  id_content: string;
  angle_title: string;

  concepts?: Concept[];

  content_body?: string | null;
  chiffres: string[];
  acteurs_cites: string[];

  published_at: string;
};

/* ========================================================= */

export default function AnalysisContent({ id }: { id: string }) {
  const [data, setData] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);

      try {
        const res = await api.get(`/analysis/${id}`);
        setData(res);
      } catch (e) {
        console.error(e);
        setData(null);
      }

      setLoading(false);
    }

    load();
  }, [id]);

  if (loading) {
    return (
      <p className="text-sm text-gray-500">
        Chargement…
      </p>
    );
  }

  if (!data) {
    return (
      <p className="text-sm text-gray-500">
        Analyse introuvable.
      </p>
    );
  }

  return (
    <div className="space-y-10">

      {/* =====================================================
          TITLE
      ===================================================== */}
      <h1 className="text-2xl font-semibold leading-tight text-gray-900">
        {data.angle_title}
      </h1>

      {/* =====================================================
          CONCEPTS (STRUCTURÉS)
      ===================================================== */}
      {data.concepts?.length > 0 && (
        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-2">
            Concepts clés
          </h2>

          <div className="flex flex-wrap gap-2">
            {data.concepts.map((c) => (
              <span
                key={c.id_concept}
                className="px-2 py-1 text-xs rounded bg-gray-100 text-gray-700"
              >
                {c.title}
              </span>
            ))}
          </div>
        </section>
      )}

      {/* =====================================================
          BODY
      ===================================================== */}
      {data.content_body && (
        <div
          className="
            prose prose-sm max-w-none
            prose-p:my-4
            prose-ul:my-4
            prose-ol:my-4
            prose-li:my-1
            prose-strong:font-semibold
            prose-a:text-ratecard-blue
            prose-a:no-underline
            hover:prose-a:underline
          "
          dangerouslySetInnerHTML={{
            __html: data.content_body,
          }}
        />
      )}

      {/* =====================================================
          CHIFFRES
      ===================================================== */}
      {data.chiffres?.length > 0 && (
        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-3">
            Chiffres clés
          </h2>
          <ul className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {data.chiffres.map((c, i) => (
              <li
                key={i}
                className="rounded-lg border border-ratecard-border bg-ratecard-light p-3 text-sm text-gray-700"
              >
                {c}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* =====================================================
          ACTEURS
      ===================================================== */}
      {data.acteurs_cites?.length > 0 && (
        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-3">
            Acteurs cités
          </h2>
          <ul className="flex flex-wrap gap-2">
            {data.acteurs_cites.map((a, i) => (
              <span
                key={i}
                className="px-2 py-1 text-xs rounded bg-ratecard-light text-gray-600"
              >
                {a}
              </span>
            ))}
          </ul>
        </section>
      )}

      {/* =====================================================
          FOOTER
      ===================================================== */}
      <div className="pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-400">
          Publié le{" "}
          {new Date(data.published_at).toLocaleDateString("fr-FR")}
        </p>
      </div>

    </div>
  );
}
