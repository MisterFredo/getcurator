"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

import type {
  DigestReview,
} from "@/types/digest";

/* ========================================================= */

type Props = {

  reviewId: string | null;

  onClose: () => void;

};

/* ========================================================= */

export default function DigestPreview({

  reviewId,

  onClose,

}: Props) {

  const [
    review,
    setReview,
  ] = useState<DigestReview | null>(
    null,
  );

  const [
    loading,
    setLoading,
  ] = useState(false);

  /* ===================================================== */

  useEffect(() => {

    if (!reviewId) {

      setReview(null);

      return;

    }

    loadReview();

  }, [reviewId]);

  /* ===================================================== */

  async function loadReview() {

    if (!reviewId) return;

    try {

      setLoading(true);

      const res =
        await api.get(
          `/digest/reviews/${reviewId}`
        );

      setReview(
        res
      );

    } catch (e) {

      console.error(e);

    } finally {

      setLoading(false);

    }

  }

  /* ===================================================== */

  if (!reviewId) {

    return (

      <div className="rounded-xl border bg-white p-12 text-center text-gray-500">

        Select a recipient to preview the generated digest.

      </div>

    );

  }

  if (loading || !review) {

    return (

      <div className="rounded-xl border bg-white p-12 text-center text-gray-500">

        Loading digest...

      </div>

    );

  }

  const document =
    review.document;

  if (!document) {

    return (

      <div className="rounded-xl border bg-white p-12 text-center text-gray-500">

        Digest has not been generated yet.

      </div>

    );

  }

  return (

    <div className="rounded-xl border bg-white">

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <div className="flex items-center justify-between border-b px-6 py-5">

        <div>

          <h2 className="text-xl font-semibold">

            {document.title}

          </h2>

          {document.subtitle && (

            <p className="mt-1 text-gray-500">

              {document.subtitle}

            </p>

          )}

          <div className="mt-3 text-sm text-gray-400">

            {document.period}

          </div>

        </div>

        <button

          onClick={onClose}

          className="rounded border px-3 py-2 text-sm hover:bg-gray-50"

        >

          Close

        </button>

      </div>

      {/* ================================================= */}
      {/* CONTENT */}
      {/* ================================================= */}

      <div className="space-y-8 p-8">

        {document.sections.map((section) => (

          <section key={section.id}>

            <h3 className="mb-4 text-lg font-semibold">

              {section.title}

            </h3>

            <div className="whitespace-pre-wrap text-sm leading-7 text-gray-700">

              {section.body}

            </div>

            {!!section.cards.length && (

              <div className="mt-6 space-y-4">

                {section.cards.map((card) => (

                  <article

                    key={card.id}

                    className="rounded-lg border p-5"

                  >

                    <h4 className="font-medium">

                      {card.title}

                    </h4>

                    <p className="mt-2 text-sm text-gray-600">

                      {card.excerpt}

                    </p>

                    <div className="mt-4 flex items-center justify-between">

                      <span className="text-xs uppercase tracking-wide text-gray-400">

                        {card.source_title}

                      </span>

                      <a

                        href={card.url}

                        target="_blank"

                        rel="noopener noreferrer"

                        className="text-sm font-medium text-ratecard-blue hover:underline"

                      >

                        Read article →

                      </a>

                    </div>

                  </article>

                ))}

              </div>

            )}

          </section>

        ))}

      </div>

    </div>

  );

}
