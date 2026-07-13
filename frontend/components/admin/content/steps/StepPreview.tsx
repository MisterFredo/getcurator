"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Props = {
  contentId: string;
  onClose: () => void;
};

export default function StepPreview({
  contentId,
  onClose,
}: Props) {

  const [loading, setLoading] = useState(true);

  const [content, setContent] =
    useState<any | null>(null);

  useEffect(() => {

    async function loadContent() {

      try {

        setLoading(true);

        const res = await api.get(
          `/content/${contentId}`
        );

        setContent(
          res?.content || null
        );

      } catch (e) {

        console.error(e);

        alert("Contenu introuvable");

        setContent(null);

      } finally {

        setLoading(false);

      }

    }

    loadContent();

  }, [contentId]);

  if (!contentId) return null;

  const hasAnalyse =
    content?.mecanique_expliquee ||
    content?.enjeu_strategique ||
    content?.point_de_friction ||
    content?.signal_analytique;

  return (

    <>

      {/* OVERLAY */}

      <div
        className="fixed inset-0 bg-black/40 z-40"
        onClick={onClose}
      />

      {/* DRAWER */}

      <div className="fixed top-0 right-0 h-full w-[700px] bg-white z-50 shadow-xl overflow-y-auto">

        <div className="p-8 space-y-10">

          {/* HEADER */}

          <div className="flex justify-between items-center">

            <h2 className="text-xl font-semibold text-ratecard-blue">
              Aperçu du contenu
            </h2>

            <button
              onClick={onClose}
              className="text-gray-500 hover:text-black"
            >
              ✕
            </button>

          </div>

          {loading && (
            <div>Chargement…</div>
          )}

          {!loading && !content && (
            <div className="text-red-500">
              Aucun contenu à afficher.
            </div>
          )}

          {!loading && content && (

            <div className="space-y-10">

              {/* TITLE */}

              {content.title && (

                <div className="space-y-2">

                  <h1 className="text-3xl font-semibold leading-tight">
                    {content.title}
                  </h1>

                  {content.title_en && (

                    <div className="text-sm text-gray-500">
                      EN: {content.title_en}
                    </div>

                  )}

                </div>

              )}

              {/* EXCERPT */}

              {content.excerpt && (

                <div className="bg-gray-50 border rounded p-5">

                  <div className="space-y-3">

                    <p className="text-base font-medium">
                      {content.excerpt}
                    </p>

                    {content.excerpt_en && (

                      <div className="pt-3 border-t">

                        <div className="text-xs uppercase text-gray-400 mb-1">
                          EN
                        </div>

                        <p className="text-sm text-gray-700">
                          {content.excerpt_en}
                        </p>

                      </div>

                    )}

                  </div>

                </div>

              )}

              {/* CONTEXTE */}

              <div className="text-sm text-gray-600 space-y-2">

                <div>

                  <strong>Topics :</strong>{" "}

                  {content.topics?.length
                    ? content.topics
                        .map((t: any) => t.label)
                        .join(", ")
                    : "—"}

                </div>

                <div>

                  <strong>Sociétés :</strong>{" "}

                  {content.companies?.length
                    ? content.companies
                        .map((c: any) => c.name)
                        .join(", ")
                    : "—"}

                </div>

                <div>

                  <strong>Solutions :</strong>{" "}

                  {content.solutions?.length
                    ? content.solutions
                        .map((s: any) => s.name)
                        .join(", ")
                    : "—"}

                </div>

              </div>

              {/* BODY */}

              {content.content_body && (

                <div
                  className="prose prose-sm max-w-none"
                  dangerouslySetInnerHTML={{
                    __html: content.content_body
                  }}
                />

              )}

              {/* CHIFFRES */}

              {content.chiffres?.length > 0 && (

                <div>

                  <h4 className="font-semibold text-sm mb-2">
                    Chiffres clés
                  </h4>

                  <ul className="list-disc list-inside text-sm">

                    {content.chiffres.map(
                      (
                        c: string,
                        i: number
                      ) => (

                        <li key={i}>
                          {c}
                        </li>

                      )
                    )}

                  </ul>

                </div>

              )}

              {/* ACTEURS */}

              {content.acteurs_cites?.length > 0 && (

                <div>

                  <h4 className="font-semibold text-sm mb-2">
                    Acteurs cités
                  </h4>

                  <p className="text-sm">
                    {content.acteurs_cites.join(", ")}
                  </p>

                </div>

              )}

              {/* ANALYSE */}

              {hasAnalyse && (

                <div className="bg-gray-50 border rounded p-6 space-y-6">

                  <h3 className="text-lg font-semibold text-ratecard-blue">
                    Analyse stratégique
                  </h3>

                  {content.mecanique_expliquee && (

                    <div>

                      <h4 className="font-semibold text-sm mb-1">
                        Mécanique
                      </h4>

                      <p className="text-sm whitespace-pre-line">
                        {content.mecanique_expliquee}
                      </p>

                    </div>

                  )}

                  {content.enjeu_strategique && (

                    <div>

                      <h4 className="font-semibold text-sm mb-1">
                        Enjeu
                      </h4>

                      <p className="text-sm whitespace-pre-line">
                        {content.enjeu_strategique}
                      </p>

                    </div>

                  )}

                  {content.point_de_friction && (

                    <div>

                      <h4 className="font-semibold text-sm mb-1">
                        Friction
                      </h4>

                      <p className="text-sm whitespace-pre-line">
                        {content.point_de_friction}
                      </p>

                    </div>

                  )}

                  {content.signal_analytique && (

                    <div>

                      <h4 className="font-semibold text-sm mb-1">
                        Signal
                      </h4>

                      <p className="text-sm whitespace-pre-line">
                        {content.signal_analytique}
                      </p>

                    </div>

                  )}

                </div>

              )}

            </div>

          )}

        </div>

      </div>

    </>
  );
}
