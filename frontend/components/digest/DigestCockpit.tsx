"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

import type {
  DigestBatch,
  DigestBatchItem,
} from "@/types/digest";

import CampaignPanel from "./CampaignPanel";
import CampaignTable from "./CampaignTable";
import RecipientTable from "./RecipientTable";
import DigestPreview from "./DigestPreview";

/* ========================================================= */

export default function DigestCockpit() {

  const [
    campaigns,
    setCampaigns,
  ] = useState<DigestBatch[]>([]);

  const [
    selectedCampaign,
    setSelectedCampaign,
  ] = useState<DigestBatch | null>(null);

  const [
    recipients,
    setRecipients,
  ] = useState<DigestBatchItem[]>([]);

  const [
    selectedRecipient,
    setSelectedRecipient,
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
     LOAD CAMPAIGNS
  ======================================================= */

  useEffect(() => {

    loadCampaigns();

  }, []);

  async function loadCampaigns() {

    try {

      setLoading(true);

      const res =
        await api.get(
          "/digest/batches"
        );

      setCampaigns(
        res
      );

    } catch (e) {

      console.error(e);

      setError(
        "Unable to load campaigns."
      );

    } finally {

      setLoading(false);

    }

  }

  /* =======================================================
     NEW CAMPAIGN
  ======================================================= */

  async function createCampaign() {

    try {

      await api.post(
        "/digest/batches",
        {
          frequency: "weekly",
          audience: "user",
        }
      );

      await loadCampaigns();

    } catch (e) {

      console.error(e);

      alert(
        "Unable to create campaign."
      );

    }

  }

  /* =======================================================
     GENERATE
  ======================================================= */

  async function generateCampaign() {

    if (!selectedCampaign) {

      alert(
        "Select a campaign first."
      );

      return;

    }

    try {

      await api.post(

        `/digest/batches/${selectedCampaign.id}/generate`,

        {},

      );

      await loadCampaigns();

      await openCampaign(
        selectedCampaign,
      );

    } catch (e) {

      console.error(e);

      alert(
        "Unable to generate digests."
      );

    }

  }

  /* =======================================================
     SEND
  ======================================================= */

  async function sendCampaign() {

    if (!selectedCampaign) {

      alert(
        "Select a campaign first."
      );

      return;

    }

    try {

      await api.post(

        `/digest/batches/${selectedCampaign.id}/send`,

        {},

      );

      await loadCampaigns();

      await openCampaign(
        selectedCampaign,
      );

    } catch (e) {

      console.error(e);

      alert(
        "Unable to send digests."
      );

    }

  }

  /* =======================================================
     OPEN CAMPAIGN
  ======================================================= */

  async function openCampaign(
    campaign: DigestBatch,
  ) {

    try {

      const res =
        await api.get(
          `/digest/batches/${campaign.id}`
        );

      setSelectedCampaign(
        res.batch
      );

      setRecipients(
        res.items
      );

      setSelectedRecipient(
        null
      );

    } catch (e) {

      console.error(e);

    }

  }

  /* =======================================================
     OPEN RECIPIENT
  ======================================================= */

  function openRecipient(
    recipient: DigestBatchItem,
  ) {

    setSelectedRecipient(
      recipient
    );

  }

  function closePreview() {

    setSelectedRecipient(
      null
    );

  }

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div className="space-y-6">

      <CampaignPanel

        campaign={selectedCampaign}

        onNewCampaign={
          createCampaign
        }

        onGenerate={
          generateCampaign
        }

        onSend={
          sendCampaign
        }

      />

      <CampaignTable

        campaigns={campaigns}

        loading={loading}

        selectedCampaign={
          selectedCampaign
        }

        onSelect={
          openCampaign
        }

      />

      <RecipientTable

        recipients={recipients}

        selectedRecipient={
          selectedRecipient
        }

        onSelect={
          openRecipient
        }

      />

      <DigestPreview

        reviewId={
          selectedRecipient?.review_id ?? null
        }

        onClose={
          closePreview
        }

      />

      {error && (

        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">

          {error}

        </div>

      )}

    </div>

  );

}
