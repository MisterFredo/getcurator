"use client";

import { useEffect, useState } from "react";

import {
  listCampaigns,
} from "@/lib/digest";

import type {
  Campaign,
} from "@/types/digest";

import CampaignTable from "@/components/digest/CampaignTable";
import CreateCampaignDialog from "@/components/digest/CreateCampaignDialog";

/* ========================================================= */

export default function DigestPage() {

  const [
    campaigns,
    setCampaigns,
  ] = useState<Campaign[]>([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  /* =========================================================
     LOAD
  ========================================================= */

  async function load() {

    setLoading(true);

    try {

      const data =
        await listCampaigns();

      setCampaigns(data);

    } catch (error) {

      console.error(
        "Unable to load campaigns",
        error,
      );

    } finally {

      setLoading(false);

    }

  }

  /* ========================================================= */

  useEffect(() => {

    load();

  }, []);

  /* ========================================================= */

  return (

    <div className="space-y-6">

      {/* =====================================================
          HEADER
      ====================================================== */}

      <div className="flex items-center justify-between">

        <div>

          <h1 className="text-2xl font-bold">

            Digest Campaigns

          </h1>

          <p className="text-sm text-gray-500">

            Generate and send weekly or monthly digest campaigns.

          </p>

        </div>

        <CreateCampaignDialog
          onCreated={load}
        />

      </div>

      {/* =====================================================
          TABLE
      ====================================================== */}

      {loading ? (

        <div className="rounded-lg border bg-white p-8 text-center text-gray-500">

          Loading campaigns...

        </div>

      ) : (

        <CampaignTable
          campaigns={campaigns}
        />

      )}

    </div>

  );

}
