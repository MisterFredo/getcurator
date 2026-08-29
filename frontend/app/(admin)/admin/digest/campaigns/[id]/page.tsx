"use client";

import {
  useEffect,
  useState,
} from "react";

import Link from "next/link";

import {
  listCampaigns,
} from "@/lib/digest";

import type {
  Campaign,
} from "@/types/digest";

import CampaignTable from "@/components/digest/CampaignTable";
import CreateCampaignDialog from "@/components/digest/CreateCampaignDialog";


/* ========================================================= */

export default function DigestCampaignsPage() {

  const [
    campaigns,
    setCampaigns,
  ] = useState<
    Campaign[]
  >([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null);


  /* =========================================================
     LOAD
  ========================================================= */

  async function load() {

    setLoading(
      true,
    );

    setError(
      null,
    );

    try {

      const data =
        await listCampaigns();

      setCampaigns(
        data,
      );

    } catch (loadError) {

      console.error(
        "Unable to load campaigns",
        loadError,
      );

      setError(
        "Unable to load campaigns.",
      );

    } finally {

      setLoading(
        false,
      );

    }

  }


  /* ========================================================= */

  useEffect(() => {

    load();

  }, []);


  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <div className="space-y-6">

      {/* =================================================== */}
      {/* HEADER */}
      {/* =================================================== */}

      <div
        className="
          flex
          flex-col
          gap-4
          sm:flex-row
          sm:items-center
          sm:justify-between
        "
      >

        <div>

          <div
            className="
              mb-2
              flex
              items-center
              gap-2
              text-sm
            "
          >

            <Link
              href="/admin/digest"
              className="
                text-gray-500
                hover:text-gray-900
              "
            >
              Digests
            </Link>

            <span className="text-gray-300">
              /
            </span>

            <span className="text-gray-700">
              Campaigns
            </span>

          </div>

          <h1
            className="
              text-2xl
              font-bold
              text-gray-900
            "
          >
            Digest Campaigns
          </h1>

          <p
            className="
              mt-1
              text-sm
              text-gray-500
            "
          >
            Create, generate and send Digest campaigns manually.
          </p>

        </div>

        <CreateCampaignDialog
          onCreated={
            load
          }
        />

      </div>


      {/* =================================================== */}
      {/* ERROR */}
      {/* =================================================== */}

      {error && (

        <div
          className="
            flex
            items-center
            justify-between
            rounded-lg
            border
            border-red-200
            bg-red-50
            px-4
            py-3
          "
        >

          <span className="text-sm text-red-700">
            {error}
          </span>

          <button
            type="button"
            onClick={
              load
            }
            className="
              rounded-md
              border
              border-red-200
              bg-white
              px-3
              py-1.5
              text-sm
              font-medium
              text-red-700
              hover:bg-red-100
            "
          >
            Retry
          </button>

        </div>

      )}


      {/* =================================================== */}
      {/* TABLE */}
      {/* =================================================== */}

      {loading ? (

        <div
          className="
            rounded-lg
            border
            bg-white
            p-8
            text-center
            text-gray-500
          "
        >
          Loading campaigns...
        </div>

      ) : (

        <CampaignTable
          campaigns={
            campaigns
          }
        />

      )}

    </div>

  );

}
