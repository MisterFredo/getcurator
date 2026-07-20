"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

import type {
  DigestBatch,
  DigestReview,
} from "@/types/digest";

import BatchHeader from "./BatchHeader";
import BatchToolbar from "./BatchToolbar";
import BatchTable from "./BatchTable";

import ReviewTable from "../review/ReviewTable";
import ReviewStudio from "../review/ReviewStudio";

/* ========================================================= */

export default function DigestCockpit() {

  const [
    batches,
    setBatches,
  ] = useState<DigestBatch[]>([]);

  const [
    selectedBatch,
    setSelectedBatch,
  ] = useState<DigestBatch | null>(null);

  const [
    reviews,
    setReviews,
  ] = useState<DigestReview[]>([]);

  const [
    selectedReview,
    setSelectedReview,
  ] = useState<DigestReview | null>(null);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState("");

  /* =======================================================
     LOAD BATCHES
  ======================================================= */

  useEffect(() => {

    loadBatches();

  }, []);

  async function loadBatches() {

    try {

      setLoading(true);

      const res =
        await api.get(
          "/digest/batches"
        );

      setBatches(
        res.batches || []
      );

    } catch (e) {

      console.error(e);

      setError(
        "Unable to load batches."
      );

    } finally {

      setLoading(false);

    }

  }

  /* =======================================================
     LOAD BATCH
  ======================================================= */

  async function openBatch(
    batch: DigestBatch,
  ) {

    try {

      const res =
        await api.get(
          `/digest/batches/${batch.id}`
        );

      setSelectedBatch(
        res.batch
      );

      setReviews(
        res.reviews || []
      );

      setSelectedReview(
        null
      );

    } catch (e) {

      console.error(e);

    }

  }

  /* =======================================================
     REVIEW
  ======================================================= */

  function openReview(
    review: DigestReview,
  ) {

    setSelectedReview(
      review
    );

  }

  function closeReview() {

    setSelectedReview(
      null
    );

  }

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div className="space-y-6">

      <BatchHeader
        onRefresh={loadBatches}
      />

      <BatchToolbar

        onCreate={() => {}}

        onPrepare={() => {}}

        onGenerate={() => {}}

        onSend={() => {}}

      />

      <BatchTable

        batches={batches}

        loading={loading}

        selectedBatch={selectedBatch}

        onSelect={openBatch}

      />

      <ReviewTable

        reviews={reviews}

        selectedReview={selectedReview}

        onSelect={openReview}

      />

      <ReviewStudio

        review={selectedReview}

        onClose={closeReview}

      />

      {error && (

        <div className="text-sm text-red-600">

          {error}

        </div>

      )}

    </div>

  );

}
