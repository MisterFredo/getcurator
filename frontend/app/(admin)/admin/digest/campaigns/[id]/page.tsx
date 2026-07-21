"use client";

import { useEffect, useState } from "react";

import { useParams } from "next/navigation";

import {
  getCampaign,
} from "@/lib/digest";

import type {
  CampaignDetail,
} from "@/types/digest";

import CampaignHeader from "@/components/digest/CampaignHeader";
import DigestList from "@/components/digest/DigestList";

/* ========================================================= */

export default function CampaignPage() {

  const {
    id,
  } = useParams<{
    id: string;
  }>();

  const [
    detail,
    setDetail,
  ] =
    useState<CampaignDetail | null>(
      null,
    );

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  /* ========================================================= */

  async function load() {

    setLoading(true);

    try {

      const data =
        await getCampaign(id);

      setDetail(
        data,
      );

    }

    catch (error) {

      console.error(
        error,
      );

    }

    finally {

      setLoading(false);

    }

  }

  /* ========================================================= */

  useEffect(() => {

    load();

  }, [id]);

  /* ========================================================= */

  if (loading) {

    return (

      <div className="rounded-lg border bg-white p-10 text-center">

        Loading campaign...

      </div>

    );

  }

  if (!detail) {

    return (

      <div className="rounded-lg border bg-white p-10 text-center">

        Campaign not found.

      </div>

    );

  }

  /* ========================================================= */

  return (

    <div className="space-y-6">

      <CampaignHeader
        campaign={
          detail.campaign
        }
      />

      <DigestList
        digests={
          detail.digests
        }
      />

    </div>

  );

}
