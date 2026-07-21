"use client";

import { useEffect, useState } from "react";

import {
  listCampaigns,
} from "@/lib/digest";

import type {
  Campaign,
} from "@/types/digest";

import CampaignTable from "@/components/digest/CampaignTable";

export default function DigestPage() {

  const [
    campaigns,
    setCampaigns,
  ] = useState<Campaign[]>([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  async function load() {

    setLoading(true);

    try {

      const data =
        await listCampaigns();

      setCampaigns(data);

    }

    finally {

      setLoading(false);

    }

  }

  useEffect(() => {

    load();

  }, []);

  return (

    <div className="space-y-6">

      <div className="flex items-center justify-between">

        <div>

          <h1 className="text-2xl font-bold">

            Digest Campaigns

          </h1>

          <p className="text-sm text-gray-500">

            Generate and send weekly or monthly digests.

          </p>

        </div>

      </div>

      {loading ? (

        <div>

          Loading...

        </div>

      ) : (

        <CampaignTable
          campaigns={campaigns}
        />

      )}

    </div>

  );

}
