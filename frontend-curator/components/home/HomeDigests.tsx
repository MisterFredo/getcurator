"use client";

import {
  useEffect,
  useState,
} from "react";

import Link from "next/link";

import {
  api,
} from "@/lib/api";

import {
  useDrawer,
} from "@/contexts/DrawerContext";

import DigestList
  from "@/components/digest/DigestList";

import type {
  DigestHistoryItem,
} from "@/types/digest";

/* =========================================================
   TYPES
========================================================= */

type Props = {
  interlocutorId: string;
};

/* =========================================================
   CONSTANTS
========================================================= */

const HOME_DIGEST_LIMIT = 3;

/* =========================================================
   COMPONENT
========================================================= */

export default function HomeDigests({
  interlocutorId,
}: Props) {

  const [
    digests,
    setDigests,
  ] = useState<
    DigestHistoryItem[]
  >([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const {
    openRightDrawer,
  } = useDrawer();

  /* =========================================================
     LOAD
  ========================================================= */

  useEffect(() => {

    async function load() {

      if (!interlocutorId) {

        setDigests(
          [],
        );

        return;

      }

      setLoading(
        true,
      );

      try {

        const params =
          new URLSearchParams();

        params.set(
          "target_user_id",
          interlocutorId,
        );

        const res =
          await api.get(
            `/digest/search?${params.toString()}`,
          );

        const rows =
          Array.isArray(
            res?.digests,
          )
            ? res.digests
            : [];

        setDigests(
          rows.slice(
            0,
            HOME_DIGEST_LIMIT,
          ),
        );

      } catch (e) {

        console.error(
          "❌ Home digests load error:",
          e,
        );

        setDigests(
          [],
        );

      } finally {

        setLoading(
          false,
        );

      }

    }

    load();

  }, [
    interlocutorId,
  ]);

  /* =========================================================
     OPEN
  ========================================================= */

  function openDigest(
    digest: DigestHistoryItem,
  ) {

    openRightDrawer(
      "digest",
      digest.ID,
    );

  }

  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <section
      className="
        space-y-4
      "
    >

      {/* =====================================================
          HEADER
      ===================================================== */}

      <div
        className="
          flex
          items-center
          justify-between
          gap-4
        "
      >

        <div>

          <h2
            className="
              text-base
              font-semibold
              text-gray-900
            "
          >
            Latest Digests
          </h2>

          <p
            className="
              mt-1
              text-xs
              text-gray-500
            "
          >
            Recent syntheses produced
            for this profile.
          </p>

        </div>

        <Link
          href="/digests"
          className="
            shrink-0
            text-xs
            font-medium
            text-gray-500
            transition
            hover:text-gray-900
          "
        >
          View all →
        </Link>

      </div>

      {/* =====================================================
          CONTENT
      ===================================================== */}

      <div
        className="
          rounded-xl
          border
          border-gray-200
          bg-white
          overflow-hidden
        "
      >

        {loading ? (

          <div
            className="
              px-5
              py-10
              text-center
              text-sm
              text-gray-400
            "
          >
            Loading Digests...
          </div>

        ) : digests.length === 0 ? (

          <div
            className="
              px-5
              py-10
              text-center
              text-sm
              text-gray-400
            "
          >
            No recent Digests available.
          </div>

        ) : (

          <div
            className="
              divide-y
              divide-gray-100
            "
          >

            {digests.map(
              digest => (

                <DigestList

                  key={
                    digest.ID
                  }

                  digest={
                    digest
                  }

                  onClick={() =>
                    openDigest(
                      digest,
                    )
                  }

                />

              ),
            )}

          </div>

        )}

      </div>

    </section>

  );

}
