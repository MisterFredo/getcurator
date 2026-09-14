"use client";

import {
  useCallback,
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


/* =========================================================
   COMPONENT
========================================================= */

export default function CampaignsPage() {

  const [
    campaigns,
    setCampaigns,
  ] = useState<
    Campaign[]
  >([]);

  const [
    loading,
    setLoading,
  ] = useState(
    true,
  );

  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null);


  /* =======================================================
     LOAD CAMPAIGNS
  ======================================================= */

  const loadCampaigns =
    useCallback(
      async () => {

        setLoading(
          true,
        );

        setError(
          null,
        );

        try {

          const result =
            await listCampaigns();

          setCampaigns(
            result,
          );

        } catch (loadError) {

          console.error(
            "Unable to load Campaigns",
            loadError,
          );

          setError(
            "Unable to load Campaigns.",
          );

        } finally {

          setLoading(
            false,
          );

        }

      },
      [],
    );


  /* =======================================================
     INITIAL LOAD
  ======================================================= */

  useEffect(() => {

    loadCampaigns();

  }, [
    loadCampaigns,
  ]);


  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div className="space-y-6">

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <div
        className="
          flex
          flex-col
          gap-4
          sm:flex-row
          sm:items-end
          sm:justify-between
        "
      >

        <div>

          <h1
            className="
              text-2xl
              font-bold
              text-gray-900
            "
          >
            Campaigns
          </h1>

          <p
            className="
              mt-1
              text-sm
              text-gray-500
            "
          >
            Create, generate, send and monitor
            Digest campaigns.
          </p>

        </div>

        <div
          className="
            flex
            items-center
            gap-3
          "
        >

          <Link
            href="/admin/digest"
            className="
              rounded-md
              border
              border-gray-300
              bg-white
              px-4
              py-2
              text-sm
              font-medium
              text-gray-700
              transition
              hover:bg-gray-50
            "
          >
            View Digests
          </Link>

          <CreateCampaignDialog
            onCreated={
              loadCampaigns
            }
          />

        </div>

      </div>


      {/* ================================================= */}
      {/* ERROR */}
      {/* ================================================= */}

      {error && (

        <div
          className="
            flex
            items-center
            justify-between
            gap-4
            rounded-lg
            border
            border-red-200
            bg-red-50
            px-4
            py-3
          "
        >

          <span
            className="
              text-sm
              text-red-700
            "
          >
            {error}
          </span>

          <button
            type="button"
            onClick={
              loadCampaigns
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
              transition
              hover:bg-red-100
            "
          >
            Retry
          </button>

        </div>

      )}


      {/* ================================================= */}
      {/* LOADING */}
      {/* ================================================= */}

      {loading && (

        <div
          className="
            rounded-lg
            border
            border-gray-200
            bg-white
            px-6
            py-12
            text-center
            text-sm
            text-gray-500
          "
        >
          Loading Campaigns...
        </div>

      )}


      {/* ================================================= */}
      {/* EMPTY STATE */}
      {/* ================================================= */}

      {!loading
        && !error
        && campaigns.length === 0
        && (

          <div
            className="
              rounded-lg
              border
              border-dashed
              border-gray-300
              bg-white
              px-6
              py-12
              text-center
            "
          >

            <p
              className="
                text-sm
                font-medium
                text-gray-900
              "
            >
              No Campaign yet.
            </p>

            <p
              className="
                mt-1
                text-sm
                text-gray-500
              "
            >
              Create a Campaign for the previous
              complete week.
            </p>

          </div>

        )}


      {/* ================================================= */}
      {/* CAMPAIGNS */}
      {/* ================================================= */}

      {!loading
        && !error
        && campaigns.length > 0
        && (

          <CampaignTable
            campaigns={
              campaigns
            }
          />

        )}

    </div>

  );

}
