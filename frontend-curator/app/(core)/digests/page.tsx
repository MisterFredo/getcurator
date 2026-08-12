"use client";

import {
  useEffect,
  useState,
} from "react";

import { api } from "@/lib/api";

import DigestList from "@/components/digest/DigestList";
import {useDrawer,} from "@/contexts/DrawerContext";
import type {DigestHistoryItem,} from "@/types/digest";

/* =========================================================
   TYPES
========================================================= */

type Expert = {
  ID_USER: string;
  DISPLAY_NAME?: string | null;
  NAME?: string | null;
  COMPANY?: string | null;
  IS_SELECTED?: boolean;
};

/* ========================================================= */

export default function DigestsPage() {

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    digests,
    setDigests,
  ] = useState<
    DigestHistoryItem[]
  >([]);

  const [
    experts,
    setExperts,
  ] = useState<Expert[]>([]);

  const [
    activeUserId,
    setActiveUserId,
  ] = useState<
    string | null
  >(null);

  const [
    currentUserId,
    setCurrentUserId,
  ] = useState<
    string | null
  >(null);

  const [
    search,
    setSearch,
  ] = useState("");

  const [
    selectedDigestId,
    setSelectedDigestId,
  ] = useState<
    string | null
  >(null);

  const {
    openRightDrawer,
  } = useDrawer();

  /* =====================================================
     LOAD CURRENT USER + EXPERTS
  ===================================================== */

  useEffect(() => {

    async function loadInitial() {

      try {

        const [
          meRes,
          expertsRes,
        ] = await Promise.all([

          api.get(
            "/user/me",
          ),

          api.get(
            "/user/experts",
          ),

        ]);

        const userId =
          meRes?.user?.ID_USER ??
          null;

        setCurrentUserId(
          userId,
        );

        setActiveUserId(
          userId,
        );

        const rows =
          Array.isArray(
            expertsRes,
          )
            ? expertsRes
            : expertsRes?.experts ??
              [];

        setExperts(
          rows.filter(
            (expert: Expert) =>
              expert.IS_SELECTED,
          ),
        );

      } catch (e) {

        console.error(
          "digest initial load error",
          e,
        );

      }

    }

    loadInitial();

  }, []);

  /* =====================================================
     LOAD DIGESTS
  ===================================================== */

  useEffect(() => {

    if (!activeUserId) {
      return;
    }

    async function loadDigests() {

      try {

        setLoading(true);

        const res =
          activeUserId ===
          currentUserId

            ? await api.get(
                "/digest/me",
              )

            : await api.get(
                `/digest/users/${activeUserId}`,
              );

        setDigests(
          res?.digests ?? [],
        );

      } catch (e) {

        console.error(
          "digest load error",
          e,
        );

        setDigests([]);

      } finally {

        setLoading(false);

      }

    }

    loadDigests();

  }, [
    activeUserId,
    currentUserId,
  ]);

  /* =====================================================
     SEARCH
  ===================================================== */

  async function runSearch() {

    const value =
      search.trim();

    if (!value) {

      if (activeUserId) {

        const res =
          activeUserId ===
          currentUserId

            ? await api.get(
                "/digest/me",
              )

            : await api.get(
                `/digest/users/${activeUserId}`,
              );

        setDigests(
          res?.digests ?? [],
        );

      }

      return;

    }

    try {

      setLoading(true);

      const params =
        new URLSearchParams();

      params.set(
        "query",
        value,
      );

      const res =
        await api.get(
          `/digest/search?${params.toString()}`,
        );

      setDigests(
        res?.digests ?? [],
      );

    } catch (e) {

      console.error(
        "digest search error",
        e,
      );

      setDigests([]);

    } finally {

      setLoading(false);

    }

  }

  /* =====================================================
     RENDER
  ===================================================== */

  return (

    <div className="space-y-6">

      {/* HEADER */}

      <div>

        <h1
          className="
            text-2xl
            font-semibold
            text-gray-900
          "
        >
          Digests
        </h1>

        <div
          className="
            mt-1
            text-sm
            text-gray-500
          "
        >
          Browse your Digests and
          those of your selected Experts.
        </div>

      </div>

      {/* USER SELECTOR */}

      <div
        className="
          flex
          flex-wrap
          gap-2
        "
      >

        {currentUserId && (

          <button
            type="button"
            onClick={() =>
              setActiveUserId(
                currentUserId,
              )
            }
            className={`
              rounded-full
              border
              px-4
              py-2
              text-sm
              font-medium

              ${
                activeUserId ===
                currentUserId
                  ? `
                    border-emerald-600
                    bg-emerald-600
                    text-white
                  `
                  : `
                    bg-white
                    text-gray-700
                  `
              }
            `}
          >
            Me
          </button>

        )}

        {experts.map(
          expert => {

            const label =
              expert.DISPLAY_NAME ??
              expert.NAME ??
              "Expert";

            return (

              <button
                key={
                  expert.ID_USER
                }
                type="button"
                onClick={() =>
                  setActiveUserId(
                    expert.ID_USER,
                  )
                }
                className={`
                  rounded-full
                  border
                  px-4
                  py-2
                  text-sm
                  font-medium

                  ${
                    activeUserId ===
                      expert.ID_USER
                      ? `
                        border-emerald-600
                        bg-emerald-600
                        text-white
                      `
                      : `
                        bg-white
                        text-gray-700
                      `
                  }
                `}
              >
                {label}
              </button>

            );

          },
        )}

      </div>

      {/* SEARCH */}

      <div
        className="
          flex
          gap-2
        "
      >

        <input
          value={search}
          onChange={e =>
            setSearch(
              e.target.value,
            )
          }
          onKeyDown={e => {

            if (
              e.key === "Enter"
            ) {
              runSearch();
            }

          }}
          placeholder="Search experts, companies, topics or solutions..."
          className="
            flex-1
            rounded-lg
            border
            bg-white
            px-4
            py-2.5
            text-sm
          "
        />

        <button
          type="button"
          onClick={
            runSearch
          }
          className="
            rounded-lg
            bg-emerald-600
            px-5
            text-sm
            font-medium
            text-white
          "
        >
          Search
        </button>

      </div>

      {/* RESULTS */}

      {loading ? (

        <div
          className="
            py-10
            text-center
            text-sm
            text-gray-500
          "
        >
          Loading Digests...
        </div>

      ) : digests.length === 0 ? (

        <div
          className="
            rounded-xl
            border
            bg-white
            p-10
            text-center
            text-sm
            text-gray-500
          "
        >
          No Digests available.
        </div>

      ) : (

        <div className="space-y-2">

          {digests.map(
            digest => (

              <DigestList
                key={digest.ID}
                digest={digest}
                onClick={() =>
                  openRightDrawer(
                    "digest",
                    digest.ID,
                  )
                }
              />

            ),
          )}

        </div>
    </div>

  );

}
