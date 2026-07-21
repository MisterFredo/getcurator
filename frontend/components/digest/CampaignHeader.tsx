"use client";

import type {
  Campaign,
} from "@/types/digest";

import CampaignActions from "./CampaignActions";

type Props = {
  campaign: Campaign;
};

export default function CampaignHeader({
  campaign,
}: Props) {

  return (

    <div className="rounded-lg border bg-white p-6">

      <div className="flex items-start justify-between">

        <div className="space-y-3">

          <h1 className="text-2xl font-bold capitalize">

            {campaign.frequency} Digest

          </h1>

          <div className="flex flex-wrap items-center gap-6 text-sm text-gray-500">

            <span className="capitalize">
              Audience: {campaign.audience}
            </span>

            <span>
              {formatCoverage(campaign)}
            </span>

            <span>
              Created: {formatDate(campaign.created_at)}
            </span>

            <span className="capitalize">
              Status: {campaign.status}
            </span>

          </div>

        </div>

        <CampaignActions
          campaign={campaign}
        />

      </div>

      <div className="mt-6 grid grid-cols-4 gap-4">

        <StatCard
          label="Recipients"
          value={campaign.digests_count}
        />

        <StatCard
          label="Generated"
          value={campaign.generated_count}
        />

        <StatCard
          label="Sent"
          value={campaign.sent_count}
        />

        <StatCard
          label="Failed"
          value={campaign.failed_count}
        />

      </div>

    </div>

  );

}

/* ========================================================= */

function StatCard({
  label,
  value,
}: {
  label: string;
  value: number;
}) {

  return (

    <div className="rounded border p-4">

      <div className="text-sm text-gray-500">

        {label}

      </div>

      <div className="mt-1 text-2xl font-semibold">

        {value}

      </div>

    </div>

  );

}

/* ========================================================= */

function formatCoverage(
  campaign: Campaign,
): string {

  const start =
    new Date(campaign.period_start);

  const end =
    new Date(campaign.period_end);

  if (
    campaign.frequency === "monthly"
  ) {

    return `Coverage: ${start.toLocaleDateString(
      "en-US",
      {
        month: "long",
        year: "numeric",
      },
    )}`;

  }

  return `Coverage: Week of ${start.toLocaleDateString(
    "en-US",
    {
      month: "short",
      day: "numeric",
    },
  )}–${end.toLocaleDateString(
    "en-US",
    {
      month: "short",
      day: "numeric",
    },
  )}`;

}

/* ========================================================= */

function formatDate(
  value: string,
): string {

  return new Date(value).toLocaleDateString(
    "en-US",
    {
      year: "numeric",
      month: "short",
      day: "numeric",
    },
  );

}
