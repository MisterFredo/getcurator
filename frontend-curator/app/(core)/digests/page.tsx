"use client";

import {
  useEffect,
  useState,
} from "react";

import { api } from "@/lib/api";

import DigestList
  from "@/components/digest/DigestList";

import {
  useDrawer,
} from "@/contexts/DrawerContext";

import type {
  DigestHistoryItem,
} from "@/types/digest";

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

/* =========================================================
   PAGE
========================================================= */

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
  ] = useState<
    Expert[]
  >([]);

  const [
    currentUserId,
    setCurrentUserId,
  ] = useState<
    string | null
  >(null);

  /*
   * null = All
   *
   * currentUserId = Me
   *
   * expert ID = selected Expert
   */

  const [
    activeUserId,
    setActiveUserId,
  ] = useState<
    string | null
  >(null);

  const [
    search,
    setSearch,
  ] = useState("");

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

        /*
         * IMPORTANT
         *
         * All is the default filter.
         */

        setActiveUserId(
          null,
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
     BUILD SEARCH PATH
  ===================================================== */

  function buildSearchPath(
    queryValue?: string,
  ) {

    const params =
      new URLSearchParams();

    /* -----------------------------------------------------
       USER / EXPERT FILTER
    ----------------------------------------------------- */

    if (activeUserId) {

      params.set(
        "target_user_id",
        activeUserId,
      );

    }

    /* -----------------------------------------------------
       TEXT SEARCH
    ----------------------------------------------------- */

    const value =
      queryValue?.trim();

    if (value) {

      params.set(
        "query",
        value,
      );

    }

    /* -----------------------------------------------------
       PATH
    ----------------------------------------------------- */

    const queryString =
      params.toString();

    return queryString
      ? `/digest/search?${queryString}`
      : "/digest/search";

  }

  /* =====================================================
     LOAD DIGESTS
  ===================================================== */

  useEffect(() => {

    async function loadDigests() {

      try {

        setLoading(
          true,
        );

        const path =
          buildSearchPath(
            search,
          );

        const res =
          await api.get(
            path,
          );

        setDigests(
          res?.digests ??
          [],
        );

      } catch (e) {

        console.error(
          "digest load error",
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

    loadDigests();

  }, [
    activeUserId,
  ]);

  /* =====================================================
     SEARCH
  ===================================================== */

  async function runSearch() {

    try {

      setLoading(
        true,
      );

      const path =
        buildSearchPath(
          search,
        );

      const res =
        await api.get(
          path,
        );

      setDigests(
        res?.digests ??
        [],
      );

    } catch (e) {

      console.error(
        "digest search error",
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

  /* =====================================================
     RESET SEARCH
  ===================================================== */

  async function clearSearch() {

    setSearch("");

    try {

      setLoading(
        true,
      );

      const path =
        buildSearchPath(
          "",
        );

      const res =
        await api.get(
          path,
        );

      setDigests(
        res?.digests ??
        [],
      );

    } catch (e) {

      console.error(
        "digest reset error",
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

  /* =====================================================
     RENDER
  ===================================================== */

  return (

    <div
      className="
        space-y-6
      "
    >

      {/* =====================================================
          HEADER
      ===================================================== */}

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
          Browse your Digests
          and those of your
          selected Experts.
        </div>

      </div>

      {/* =====================================================
          USER FILTERS
      ===================================================== */}

      <div
        className="
          flex
          flex-wrap
          gap-2
        "
      >

        {/* ALL */}

        <button
          type="button"
          onClick={() =>
            setActiveUserId(
              null,
            )
          }
          className={`
            rounded-full
            border
            px-4
            py-2
            text-sm
            font-medium
            transition

            ${
              activeUserId === null
                ? `
                  border-emerald-600
                  bg-emerald-600
                  text-white
                `
                : `
                  bg-white
                  text-gray-700
                  hover:bg-gray-50
                `
            }
          `}
        >
          All
        </button>

        {/* ME */}

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
              transition

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
                    hover:bg-gray-50
                  `
              }
            `}
          >
            Me
          </button>

        )}

        {/* EXPERTS */}

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
                  transition

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
                        hover:bg-gray-50
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

      {/* =====================================================
          SEARCH
      ===================================================== */}

      <div
        className="
          flex
          gap-2
        "
      >

        <input

          value={
            search
          }

          onChange={e =>
            setSearch(
              e.target.value,
            )
          }

          onKeyDown={e => {

            if (
              e.key ===
              "Enter"
            ) {

              runSearch();

            }

          }}

          placeholder="
            Search experts, companies,
            topics or solutions...
          "

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

        {search && (

          <button
            type="button"
            onClick={
              clearSearch
            }
            className="
              rounded-lg
              border
              bg-white
              px-4
              text-sm
              font-medium
              text-gray-600
              hover:bg-gray-50
            "
          >
            Clear
          </button>

        )}

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
            hover:bg-emerald-700
          "
        >
          Search
        </button>

      </div>

      {/* =====================================================
          RESULTS
      ===================================================== */}

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

        <div
          className="
            space-y-2
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
                  openRightDrawer(
                    "digest",
                    digest.ID,
                  )
                }

              />

            ),
          )}

        </div>

      )}

    </div>

  );

}
