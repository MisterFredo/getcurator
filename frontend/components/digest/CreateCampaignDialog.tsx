"use client";

import {
  useState,
} from "react";

import {
  createCampaign,
} from "@/lib/digest";

import type {
  CampaignCreateRequest,
  DigestAudience,
} from "@/types/digest";


/* ========================================================= */

type Props = {

  onCreated: () => void;

};


/* ========================================================= */

export default function CreateCampaignDialog({
  onCreated,
}: Props) {

  const [
    open,
    setOpen,
  ] = useState(false);

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    audience,
    setAudience,
  ] = useState<DigestAudience>(
    "user",
  );


  /* =====================================================
     CREATE
  ===================================================== */

  async function handleCreate() {

    try {

      setLoading(true);

      const payload:
        CampaignCreateRequest = {

          audience,

        };

      await createCampaign(
        payload,
      );

      setOpen(false);

      onCreated();

    } catch (error) {

      console.error(
        error,
      );

      alert(
        "Unable to create Campaign.",
      );

    } finally {

      setLoading(false);

    }

  }


  /* =====================================================
     CLOSED
  ===================================================== */

  if (!open) {

    return (

      <button
        type="button"
        onClick={() =>
          setOpen(true)
        }
        className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
      >
        New Campaign
      </button>

    );

  }


  /* =====================================================
     DIALOG
  ===================================================== */

  return (

    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">

      <div className="w-full max-w-lg space-y-5 rounded-lg bg-white p-6">

        <h2 className="text-lg font-semibold">

          Create Campaign

        </h2>

        {/* ================================================= */}
        {/* AUDIENCE */}
        {/* ================================================= */}

        <div>

          <label className="mb-1 block text-sm">

            Audience

          </label>

          <select
            value={audience}
            disabled={loading}
            onChange={(event) =>
              setAudience(
                event.target.value as
                  DigestAudience,
              )
            }
            className="w-full rounded border px-3 py-2 disabled:opacity-50"
          >
            <option value="user">
              Users
            </option>

            <option value="expert">
              Experts
            </option>

          </select>

        </div>

        {/* ================================================= */}
        {/* PERIOD */}
        {/* ================================================= */}

        <div>

          <label className="mb-1 block text-sm">

            Period

          </label>

          <div className="rounded border bg-gray-50 px-3 py-2 text-sm text-gray-600">

            Previous complete week

          </div>

        </div>

        {/* ================================================= */}
        {/* ACTIONS */}
        {/* ================================================= */}

        <div className="flex justify-end gap-3">

          <button
            type="button"
            disabled={loading}
            onClick={() =>
              setOpen(false)
            }
            className="rounded border px-4 py-2 disabled:opacity-50"
          >
            Cancel
          </button>

          <button
            type="button"
            disabled={loading}
            onClick={handleCreate}
            className="rounded bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
          >
            {loading
              ? "Creating..."
              : "Create"}
          </button>

        </div>

      </div>

    </div>

  );

}
