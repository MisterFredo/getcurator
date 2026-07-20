"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

import type {
  DigestReview,
} from "@/types/digest";

import ReviewHeader from "./ReviewHeader";
import ReviewPreview from "./ReviewPreview";

/* ========================================================= */

type Props = {
  reviewId: string | null;
  onClose: () => void;
};

/* ========================================================= */

export default function ReviewStudio({

  reviewId,

  onClose,

}: Props) {

  const [
    review,
    setReview,
  ] = useState<DigestReview | null>(null);

  const [
    loading,
    setLoading,
  ] = useState(false);

  /* =======================================================
     LOAD REVIEW
  ======================================================= */

  useEffect(() => {

    if (!reviewId) {

      setReview(null);

      return;

    }

    loadReview();

  }, [reviewId]);

  async function loadReview() {

    if (!reviewId) {
      return;
    }

    try {

      setLoading(true);

      const res =
        await api.get(
          `/digest/reviews/${reviewId}`
        );

      setReview(
        res.review
      );

    } catch (e) {

      console.error(e);

      setReview(null);

    } finally {

      setLoading(false);

    }

  }

  /* =======================================================
     CLOSED
  ======================================================= */

  if (!reviewId) {
    return null;
  }

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div className="fixed inset-0 z-50 flex justify-end bg-black/40">

      <div className="flex h-full w-[720px] flex-col bg-white shadow-xl">

        {/* ================================================ */}
        {/* HEADER */}
        {/* ================================================ */}

        <ReviewHeader

          review={review}

          loading={loading}

          onClose={onClose}

        />

        {/* ================================================ */}
        {/* BODY */}
        {/* ================================================ */}

        <div className="flex-1 overflow-y-auto bg-gray-50 p-6">

          <div className="mx-auto max-w-[820px]">

            {loading ? (

              <div className="py-20 text-center text-sm text-gray-500">

                Loading review...

              </div>

            ) : review ? (

              <ReviewPreview

                document={review.document}

              />

            ) : (

              <div className="py-20 text-center text-sm text-red-600">

                Unable to load review.

              </div>

            )}

          </div>

        </div>

      </div>

    </div>

  );

}
