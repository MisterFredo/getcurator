"use client";

import { useState } from "react";

import {
  createCampaign,
} from "@/lib/digest";

import type {
  CampaignCreateRequest,
} from "@/types/digest";

type Props = {
  onCreated: () => void;
};

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
    form,
    setForm,
  ] = useState<CampaignCreateRequest>({
    frequency: "weekly",
    audience: "user",
    period_start: "",
    period_end: "",
  });

  async function handleCreate() {

    setLoading(true);

    try {

      await createCampaign(
        form,
      );

      setOpen(false);

      onCreated();

    }

    finally {

      setLoading(false);

    }

  }

  if (!open) {

    return (

      <button
        onClick={() => setOpen(true)}
        className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
      >
        New Campaign
      </button>

    );

  }

  return (

    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">

      <div className="w-full max-w-lg rounded-lg bg-white p-6 space-y-5">

        <h2 className="text-lg font-semibold">

          Create Campaign

        </h2>

        <div>

          <label className="block text-sm mb-1">

            Frequency

          </label>

          <select
            value={form.frequency}
            onChange={(e) =>
              setForm({
                ...form,
                frequency:
                  e.target.value as
                    "weekly" | "monthly",
              })
            }
            className="w-full rounded border px-3 py-2"
          >
            <option value="weekly">
              Weekly
            </option>

            <option value="monthly">
              Monthly
            </option>

          </select>

        </div>

        <div>

          <label className="block text-sm mb-1">

            Audience

          </label>

          <select
            value={form.audience}
            onChange={(e) =>
              setForm({
                ...form,
                audience:
                  e.target.value as
                    "user" | "expert",
              })
            }
            className="w-full rounded border px-3 py-2"
          >
            <option value="user">
              Users
            </option>

            <option value="expert">
              Experts
            </option>

          </select>

        </div>

        <div>

          <label className="block text-sm mb-1">

            Period Start

          </label>

          <input
            type="date"
            value={form.period_start}
            onChange={(e) =>
              setForm({
                ...form,
                period_start:
                  e.target.value,
              })
            }
            className="w-full rounded border px-3 py-2"
          />

        </div>

        <div>

          <label className="block text-sm mb-1">

            Period End

          </label>

          <input
            type="date"
            value={form.period_end}
            onChange={(e) =>
              setForm({
                ...form,
                period_end:
                  e.target.value,
              })
            }
            className="w-full rounded border px-3 py-2"
          />

        </div>

        <div className="flex justify-end gap-3">

          <button
            onClick={() => setOpen(false)}
            className="rounded border px-4 py-2"
          >
            Cancel
          </button>

          <button
            disabled={loading}
            onClick={handleCreate}
            className="rounded bg-blue-600 px-4 py-2 text-white"
          >
            Create
          </button>

        </div>

      </div>

    </div>

  );

}
