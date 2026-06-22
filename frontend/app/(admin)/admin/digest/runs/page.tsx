"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";

/* ========================================================= */

type Digest = {
  ID_DIGEST: string;
  ID_USER: string;

  DIGEST_NAME: string;

  DIGEST_FREQUENCY: string;

  LANGUAGE: string;

  STATUS: string;

  PERIOD_START: string;
  PERIOD_END: string;

  GENERATED_AT: string;
  SENT_AT?: string | null;

  NB_CONTENTS: number;
};

/* ========================================================= */

export default function DigestRunsPage() {

  const [digests, setDigests] =
    useState<Digest[]>([]);

  const [loading, setLoading] =
    useState(false);

  const router = useRouter();

  /* =========================================================
     LOAD DIGESTS
  ========================================================= */

  async function loadDigests() {

    try {

      setLoading(true);

      const res =
        await api.get(
          "/digest/list-all"
        );

      const items =
        res?.result || [];

      items.sort(
        (a, b) =>
          new Date(
            b.GENERATED_AT
          ).getTime()
          -
          new Date(
            a.GENERATED_AT
          ).getTime()
      );

      setDigests(
        items
      );

    } catch (e) {

      console.error(
        "Erreur load digests",
        e
      );

    } finally {

      setLoading(false);

    }
  }

  useEffect(() => {

    loadDigests();

  }, []);

  /* =========================================================
     CREATE DIGEST
  ========================================================= */

  function createDigest() {

    router.push(
      "/admin/digest"
    );

  }

  /* =========================================================
     OPEN DIGEST
  ========================================================= */

  function openDigest(
    id: string
  ) {

    router.push(
      `/admin/digest?id_digest=${id}`
    );

  }

  /* =========================================================
     FORMAT DATE
  ========================================================= */

  function formatDate(
    value?: string | null
  ) {

    if (!value) {
      return "—";
    }

    try {

      return new Date(
        value
      ).toLocaleDateString(
        "fr-FR",
        {
          day: "2-digit",
          month: "2-digit",
          year: "numeric",
        }
      );

    } catch {

      return "—";

    }
  }

  /* =========================================================
     STATUS BADGE
  ========================================================= */

  function StatusBadge(
    {
      status,
    }: {
      status: string;
    }
  ) {

    const value =
      (status || "")
        .toUpperCase();

    const styles =

      value === "GENERATED"

        ? "bg-green-100 text-green-700"

      : value === "SENT"

        ? "bg-blue-100 text-blue-700"

      : value === "DRAFT"

        ? "bg-gray-200 text-gray-700"

      : "bg-gray-100 text-gray-500";

    return (

      <span
        className={`
          px-2
          py-1
          text-xs
          rounded
          ${styles}
        `}
      >
        {value}
      </span>

    );
  }

  /* =========================================================
     UI
  ========================================================= */

  return (

    <div className="space-y-6">

      {/* HEADER */}

      <div className="flex items-center justify-between">

        <div>

          <h1 className="text-lg font-semibold">
            Digest Manager
          </h1>

          <div className="text-sm text-gray-500 mt-1">

            Create, manage and edit
            saved digests.

          </div>

        </div>

        <button
          onClick={createDigest}
          className="
            px-3
            py-2
            bg-black
            text-white
            text-xs
            rounded
          "
        >
          Create Digest
        </button>

      </div>

      {/* TABLE */}

      <div className="bg-white border rounded-lg overflow-hidden">

        <div
          className="
            grid
            grid-cols-[2fr_120px_1.5fr_100px_120px_120px_100px]
            px-4
            py-3
            text-xs
            text-gray-500
            border-b
            bg-gray-50
          "
        >

          <div>
            Digest
          </div>

          <div>
            Frequency
          </div>

          <div>
            Period
          </div>

          <div>
            Contents
          </div>

          <div>
            Status
          </div>

          <div>
            Generated
          </div>

          <div>
          </div>

        </div>

        {!loading &&
          digests.length === 0 && (

          <div className="p-4 text-sm text-gray-500">

            Aucun digest

          </div>

        )}

        {digests.map(
          (digest) => (

            <div
              key={
                digest.ID_DIGEST
              }
              className="
                grid
                grid-cols-[2fr_120px_1.5fr_100px_120px_120px_100px]
                px-4
                py-3
                text-sm
                border-b
                items-center
                hover:bg-gray-50
              "
            >

              <div>

                <div className="font-medium">

                  {digest.DIGEST_NAME}

                </div>

                <div className="text-xs text-gray-500 mt-1">

                  {digest.ID_USER}

                </div>

              </div>

              <div
                className="
                  text-xs
                  uppercase
                  font-medium
                "
              >
                {digest.DIGEST_FREQUENCY}
              </div>

              <div className="text-xs">

                {formatDate(
                  digest.PERIOD_START
                )}

                {" → "}

                {formatDate(
                  digest.PERIOD_END
                )}

              </div>

              <div>

                {digest.NB_CONTENTS}

              </div>

              <div>

                <StatusBadge
                  status={
                    digest.STATUS
                  }
                />

              </div>

              <div className="text-xs text-gray-500">

                {formatDate(
                  digest.GENERATED_AT
                )}

              </div>

              <div className="text-right">

                <button
                  onClick={() =>
                    openDigest(
                      digest.ID_DIGEST
                    )
                  }
                  className="
                    text-xs
                    px-2
                    py-1
                    border
                    rounded
                    hover:bg-gray-100
                  "
                >
                  View
                </button>

              </div>

            </div>

          )
        )}

      </div>

    </div>

  );
}
