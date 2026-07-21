"use client";

import {
  generateCampaign,
  sendCampaign,
} from "@/lib/digest";

import type {
  Campaign,
} from "@/types/digest";

type Props = {
  campaign: Campaign;
};

export default function CampaignActions({
  campaign,
}: Props) {

  async function handleGenerate() {

    await generateCampaign(
      campaign.id,
    );

    window.location.reload();

  }

  async function handleSend() {

    await sendCampaign(
      campaign.id,
    );

    window.location.reload();

  }

  switch (
    campaign.status
  ) {

    case "created":

      return (

        <button
          onClick={handleGenerate}
          className="rounded bg-blue-600 px-3 py-1 text-white hover:bg-blue-700"
        >
          Generate
        </button>

      );

    case "generated":

      return (

        <button
          onClick={handleSend}
          className="rounded bg-green-600 px-3 py-1 text-white hover:bg-green-700"
        >
          Send
        </button>

      );

    case "completed":

      return (
        <span className="text-green-600 font-medium">
          Sent
        </span>
      );

    case "failed":

      return (
        <span className="text-red-600 font-medium">
          Failed
        </span>
      );

    default:

      return (
        <span className="text-gray-500">
          {campaign.status}
        </span>
      );

  }

}
