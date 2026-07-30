"use client";

import {
  useEffect,
  useState,
} from "react";

import { X } from "lucide-react";

import { api } from "@/lib/api";

type Props = {
  digestId: string;
  onClose: () => void;
};

export default function DigestPreviewDrawer({
  digestId,
  onClose,
}: Props) {

  const [
    html,
    setHtml,
  ] = useState("");

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState<string | null>(null);

  /* =====================================================
     LOAD
  ===================================================== */

  useEffect(() => {

    async function load() {

      try {

        setLoading(true);

        const res =
          await api.get(
            `/digest/digests/${digestId}/preview`,
          );

        setHtml(
          res.html,
        );

      } catch (err: any) {

        setError(
          err.message ??
          "Unable to load preview.",
        );

      } finally {

        setLoading(false);

      }

    }

    load();

  }, [
    digestId,
  ]);

  /* =====================================================
     RENDER
  ===================================================== */

  return (

    <div className="fixed inset-0 z-50 flex justify-end">

      {/* Overlay */}

      <div
        className="absolute inset-0 bg-black/30"
        onClick={onClose}
      />

      {/* Drawer */}

      <div className="relative flex h-full w-[900px] max-w-full flex-col bg-white shadow-xl">

        {/* Header */}

        <div className="flex items-center justify-between border-b px-6 py-4">

          <h2 className="text-lg font-semibold">

            Digest Preview

          </h2>

          <button
            onClick={onClose}
            className="rounded p-2 hover:bg-gray-100"
          >

            <X size={20} />

          </button>

        </div>

        {/* Content */}

        <div className="flex-1 overflow-hidden">

          {loading && (

            <div className="flex h-full items-center justify-center">

              Loading preview...

            </div>

          )}

          {!loading && error && (

            <div className="p-6 text-red-600">

              {error}

            </div>

          )}

          {!loading && !error && (

            <iframe
              title="Digest Preview"
              srcDoc={html}
              className="h-full w-full border-0"
            />

          )}

        </div>

      </div>

    </div>

  );

}
