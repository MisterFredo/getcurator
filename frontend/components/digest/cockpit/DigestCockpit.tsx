"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

import type {
  DigestBatch,
  DigestBatchItem,
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
    items,
    setItems,
  ] = useState<DigestBatchItem[]>([]);

  const [
    selectedItem,
    setSelectedItem,
  ] = useState<DigestBatchItem | null>(null);

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
        res
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
     CREATE
  ======================================================= */

  async function createBatch() {

    try {

      await api.post(
        "/digest/batches",
        {
          frequency: "weekly",
          audience: "user",
        }
      );

      await loadBatches();

    } catch (e) {

      console.error(e);

      alert("Unable to create batch.");

    }

  }

  /* =======================================================
     PREPARE
  ======================================================= */

  async function prepareBatch() {

    if (!selectedBatch) {

      alert("Select a batch first.");

      return;

    }

    try {

      await api.post(
        `/digest/batches/${selectedBatch.id}/prepare`,
        {}
      );

      await loadBatches();

      await openBatch(
        selectedBatch
      );

    } catch (e) {

      console.error(e);

      alert("Unable to prepare batch.");

    }

  }

  /* =======================================================
     GENERATE
  ======================================================= */

  async function generateBatch() {

    if (!selectedBatch) {

      alert("Select a batch first.");

      return;

    }

    try {

      await api.post(
        `/digest/batches/${selectedBatch.id}/generate`
        {}
      );

      await loadBatches();

      await openBatch(
        selectedBatch
      );

    } catch (e) {

      console.error(e);

      alert("Unable to generate batch.");

    }

  }

  /* =======================================================
     SEND
  ======================================================= */

  async function sendBatch() {

    if (!selectedBatch) {

      alert("Select a batch first.");

      return;

    }

    try {

      await api.post(
        `/digest/batches/${selectedBatch.id}/send`
        {}
      );

      await loadBatches();

      await openBatch(
        selectedBatch
      );

    } catch (e) {

      console.error(e);

      alert("Unable to send batch.");

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

      setItems(
        res.items
      );

      setSelectedItem(
        null
      );

    } catch (e) {

      console.error(e);

    }

  }

  /* =======================================================
     ITEM
  ======================================================= */

  function openItem(
    item: DigestBatchItem,
  ) {

    setSelectedItem(
      item
    );

  }

  function closeReview() {

    setSelectedItem(
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

        onCreate={createBatch}

        onPrepare={prepareBatch}

        onGenerate={generateBatch}

        onSend={sendBatch}

      />

      <BatchTable

        batches={batches}

        loading={loading}

        selectedBatch={selectedBatch}

        onSelect={openBatch}

      />

      <ReviewTable

        items={items}

        selectedItem={selectedItem}

        onSelect={openItem}

      />

      <ReviewStudio

        reviewId={
          selectedItem?.review_id ?? null
        }

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
