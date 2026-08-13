"use client";

import {
  useEffect,
  useState,
} from "react";

import { X } from "lucide-react";

import { api } from "@/lib/api";

/* =========================================================
   TYPES
========================================================= */

type Props = {
  digestId: string;
  onClose: () => void;
};

/* =========================================================
   COMPONENT
========================================================= */

export default function DigestDrawer({
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
  ] = useState<
    string | null
  >(null);

  /* =====================================================
     LOAD
  ===================================================== */

  useEffect(() => {

    async function load() {

      try {

        setLoading(true);

        setError(null);

        const res =
          await api.get(
            `/digest/digests/${digestId}/front-preview`,
          );

        setHtml(
          res?.html ?? "",
        );

      } catch (err: any) {

        console.error(
          "digest preview error",
          err,
        );

        setError(
          err?.message ??
          "Unable to load Digest.",
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

    <div
      className="
        fixed
        inset-0
        z-50
        flex
        justify-end
      "
    >

      {/* OVERLAY */}

      <div
        className="
          absolute
          inset-0
          bg-black/30
        "
        onClick={
          onClose
        }
      />

      {/* DRAWER */}

      <div
        className="
          relative
          flex
          h-full
          w-[900px]
          max-w-full
          flex-col
          bg-white
          shadow-xl
        "
      >

        {/* HEADER */}

        <div
          className="
            flex
            items-center
            justify-between
            border-b
            px-6
            py-4
          "
        >

          <h2
            className="
              text-lg
              font-semibold
            "
          >
            Digest
          </h2>

          <button
            type="button"
            onClick={
              onClose
            }
            className="
              rounded
              p-2
              hover:bg-gray-100
            "
          >
            <X size={20} />
          </button>

        </div>

        {/* CONTENT */}

        <div
          className="
            flex-1
            overflow-hidden
          "
        >

          {loading && (

            <div
              className="
                flex
                h-full
                items-center
                justify-center
                text-sm
                text-gray-500
              "
            >
              Loading Digest...
            </div>

          )}

          {!loading &&
            error && (

            <div
              className="
                p-6
                text-sm
                text-red-600
              "
            >
              {error}
            </div>

          )}

          {!loading &&
            !error && (

            <iframe
              title="Digest"
              srcDoc={html}
              className="
                h-full
                w-full
                border-0
              "
            />

          )}

        </div>

      </div>

    </div>

  );

}
