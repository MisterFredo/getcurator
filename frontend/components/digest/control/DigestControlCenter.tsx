"use client";

import { useState } from "react";

import DigestCampaignHeader from "./DigestCampaignHeader";
import DigestCampaignStats from "./DigestCampaignStats";
import DigestCampaignActions from "./DigestCampaignActions";
import ReviewUserSelector, {
  ReviewUser,
} from "./ReviewUserSelector";

export default function DigestControlCenter() {

  const [
    generating,
    setGenerating,
  ] = useState(false);

  const [
    sending,
    setSending,
  ] = useState(false);

  const [
    selectedUser,
    setSelectedUser,
  ] = useState<ReviewUser | null>(null);

  /* =====================================================
     ACTIONS
  ===================================================== */

  async function handleGenerate() {

    console.log(
      "Generate campaign"
    );

  }

  async function handleSend() {

    console.log(
      "Send campaign"
    );

  }

  function handleReview(
    user: ReviewUser,
  ) {

    console.log(
      "Review",
      user,
    );

    setSelectedUser(
      user,
    );

  }

  /* =====================================================
     UI
  ===================================================== */

  return (

    <div className="space-y-6">

      <DigestCampaignHeader
        title="Weekly Digest Campaign"
        period="14 Jul 2026 → 20 Jul 2026"
      />

      <DigestCampaignStats
        generated={1000}
        ready={995}
        review={5}
        failed={0}
      />

      <DigestCampaignActions
        generating={generating}
        sending={sending}
        onGenerate={handleGenerate}
        onSend={handleSend}
      />

      <ReviewUserSelector
        onSelect={handleReview}
      />

    </div>

  );

}
