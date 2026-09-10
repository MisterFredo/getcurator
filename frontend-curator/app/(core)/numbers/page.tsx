"use client";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  api,
} from "@/lib/api";

import {
  useUser,
} from "@/hooks/useUser";

import {
  searchValidatedNumbers,
} from "@/lib/numbers";

import ValidatedNumberCard from "@/components/numbers/ValidatedNumberCard";
import ValidatedNumbersSearchBar from "@/components/numbers/ValidatedNumbersSearchBar";

import type {
  PublicNumber,
} from "@/types/numbers";


/* ============================================================
   TYPES
============================================================ */

type Universe = {

  id_universe: string;

  label: string;

};


/* ============================================================
   CONFIG
============================================================ */

const PAGE_SIZE = 50;


/* ============================================================
   PAGE
============================================================ */

export default function NumbersPage() {

  /* ========================================================
     USER
  ======================================================== */

  const {
    user,
    loading: userLoading,
  } = useUser();


  /* ========================================================
     UNIVERSES
  ======================================================== */

  const [
    universes,
    setUniverses,
  ] = useState<Universe[]>(
    [],
  );

  const [
    activeUniverse,
    setActiveUniverse,
  ] = useState<string | null>(
    null,
  );


  /* ========================================================
     NUMBERS
  ======================================================== */

  const [
    items,
    setItems,
  ] = useState<PublicNumber[]>(
    [],
  );

  const [
    query,
    setQuery,
  ] = useState("");

  const [
    total,
    setTotal,
  ] = useState(0);

  const [
    hasMore,
    setHasMore,
  ] = useState(false);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    loadingMore,
    setLoadingMore,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );


  /* ========================================================
     LOAD UNIVERSES
  ======================================================== */

  useEffect(() => {

    if (
      userLoading
      || !user?.id_user
    ) {

      return;

    }

    async function loadUniverses() {

      try {

        const response = await api.get(
          "/universe/list-for-user",
        );

        setUniverses(
          response?.universes
          || [],
        );

      } catch (loadError) {

        console.error(
          "Unable to load universes:",
          loadError,
        );

      }

    }

    loadUniverses();

  }, [
    user?.id_user,
    userLoading,
  ]);


  /* ========================================================
     LOAD NUMBERS
  ======================================================== */

  const loadNumbers = useCallback(

    async ({
      searchQuery,
      universeId,
      offset = 0,
      append = false,
    }: {
      searchQuery: string;
      universeId: string | null;
      offset?: number;
      append?: boolean;
    }) => {

      const userId =
        user?.id_user;

      if (!userId) {

        return;

      }

      if (append) {

        setLoadingMore(
          true,
        );

      } else {

        setLoading(
          true,
        );

      }

      setError(
        null,
      );

      try {

        const response =
          await searchValidatedNumbers({

            user_id:
              userId,

            query:
              searchQuery
              || undefined,

            universe_id:
              universeId
              || undefined,

            limit:
              PAGE_SIZE,

            offset,

          });

        const nextItems =
          response.items
          || [];

        setItems(
          current =>
            append
              ? [
                  ...current,
                  ...nextItems,
                ]
              : nextItems,
        );

        setTotal(
          response.pagination?.total
          ?? nextItems.length,
        );

        setHasMore(
          response.pagination?.has_more
          ?? false,
        );

      } catch (loadError) {

        console.error(
          "Unable to load validated Numbers:",
          loadError,
        );

        setError(
          "Unable to load Numbers.",
        );

        if (!append) {

          setItems(
            [],
          );

          setTotal(
            0,
          );

          setHasMore(
            false,
          );

        }

      } finally {

        setLoading(
          false,
        );

        setLoadingMore(
          false,
        );

      }

    },

    [
      user?.id_user,
    ],
  );


  /* ========================================================
     INITIAL LOAD / UNIVERSE CHANGE
  ======================================================== */

  useEffect(() => {

    if (
      userLoading
      || !user?.id_user
    ) {

      return;

    }

    loadNumbers({

      searchQuery:
        query,

      universeId:
        activeUniverse,

    });

  }, [
    activeUniverse,
    loadNumbers,
    user?.id_user,
    userLoading,
  ]);


  /* ========================================================
     SEARCH
  ======================================================== */

  function handleSearch(
    nextQuery: string,
  ) {

    if (
      userLoading
      || !user?.id_user
    ) {

      return;

    }

    setQuery(
      nextQuery,
    );

    loadNumbers({

      searchQuery:
        nextQuery,

      universeId:
        activeUniverse,

    });

  }


  /* ========================================================
     LOAD MORE
  ======================================================== */

  function handleLoadMore() {

    if (
      userLoading
      || !user?.id_user
      || loading
      || loadingMore
      || !hasMore
    ) {

      return;

    }

    loadNumbers({

      searchQuery:
        query,

      universeId:
        activeUniverse,

      offset:
        items.length,

      append:
        true,

    });

  }


  /* ========================================================
     PAGE LOADING
  ======================================================== */

  const pageLoading =
    userLoading
    || loading;


  /* ========================================================
     RENDER
  ======================================================== */

  return (

    <div

      className="
        space-y-8
      "

    >

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <header>

        <h1

          className="
            text-2xl
            font-semibold
            tracking-tight
            text-gray-900
          "

        >

          Numbers

        </h1>

        <p

          className="
            mt-2
            max-w-3xl
            text-sm
            leading-6
            text-gray-500
          "

        >

          Explore verified business metrics extracted from
          GetCurator&apos;s editorial intelligence.

        </p>

      </header>


      {/* ================================================= */}
      {/* SEARCH */}
      {/* ================================================= */}

      <ValidatedNumbersSearchBar

        query={
          query
        }

        loading={
          pageLoading
        }

        onSearch={
          handleSearch
        }

      />


      {/* ================================================= */}
      {/* UNIVERSES */}
      {/* ================================================= */}

      {universes.length > 0 && (

        <div

          className="
            flex
            flex-wrap
            gap-2
          "

        >

          <button

            type="button"

            disabled={
              pageLoading
            }

            onClick={() =>
              setActiveUniverse(
                null,
              )
            }

            className={`
              rounded-full
              px-3
              py-1.5
              text-xs
              font-medium
              transition
              disabled:opacity-50

              ${
                activeUniverse === null

                  ? `
                    bg-gray-900
                    text-white
                  `

                  : `
                    bg-gray-100
                    text-gray-600
                    hover:bg-gray-200
                  `
              }
            `}

          >

            All

          </button>

          {universes.map(
            universe => (

              <button

                key={
                  universe.id_universe
                }

                type="button"

                disabled={
                  pageLoading
                }

                onClick={() =>
                  setActiveUniverse(
                    universe.id_universe,
                  )
                }

                className={`
                  rounded-full
                  px-3
                  py-1.5
                  text-xs
                  font-medium
                  transition
                  disabled:opacity-50

                  ${
                    activeUniverse
                    === universe.id_universe

                      ? `
                        bg-gray-900
                        text-white
                      `

                      : `
                        bg-gray-100
                        text-gray-600
                        hover:bg-gray-200
                      `
                  }
                `}

              >

                {universe.label}

              </button>

            ),
          )}

        </div>

      )}


      {/* ================================================= */}
      {/* COUNTER */}
      {/* ================================================= */}

      {!pageLoading && !error && (

        <div

          className="
            text-xs
            text-gray-400
          "

        >

          {total} validated Number
          {total !== 1
            ? "s"
            : ""}

        </div>

      )}


      {/* ================================================= */}
      {/* LOADING */}
      {/* ================================================= */}

      {pageLoading && (

        <div

          className="
            rounded-2xl
            border
            border-gray-200
            bg-white
            p-8
            text-center
            text-sm
            text-gray-400
          "

        >

          Loading Numbers...

        </div>

      )}


      {/* ================================================= */}
      {/* ERROR */}
      {/* ================================================= */}

      {!pageLoading && error && (

        <div

          className="
            rounded-2xl
            border
            border-red-100
            bg-red-50
            p-5
            text-sm
            text-red-700
          "

        >

          {error}

        </div>

      )}


      {/* ================================================= */}
      {/* EMPTY */}
      {/* ================================================= */}

      {!pageLoading
        && !error
        && items.length === 0
        && (

          <div

            className="
              rounded-2xl
              border
              border-gray-200
              bg-white
              p-8
              text-center
            "

          >

            <div

              className="
                text-sm
                font-medium
                text-gray-700
              "

            >

              No validated Number found.

            </div>

            <div

              className="
                mt-1
                text-xs
                text-gray-400
              "

            >

              Try another search or universe.

            </div>

          </div>

        )}


      {/* ================================================= */}
      {/* GRID */}
      {/* ================================================= */}

      {!pageLoading
        && !error
        && items.length > 0
        && (

          <div

            className="
              grid
              grid-cols-1
              gap-4
              sm:grid-cols-2
              lg:grid-cols-3
              xl:grid-cols-4
            "

          >

            {items.map(
              item => (

                <ValidatedNumberCard

                  key={
                    item.id_number
                  }

                  item={
                    item
                  }

                />

              ),
            )}

          </div>

        )}


      {/* ================================================= */}
      {/* LOAD MORE */}
      {/* ================================================= */}

      {!pageLoading
        && !error
        && hasMore
        && (

          <div

            className="
              flex
              justify-center
              pt-2
            "

          >

            <button

              type="button"

              disabled={
                loadingMore
              }

              onClick={
                handleLoadMore
              }

              className="
                rounded-xl
                border
                border-gray-200
                bg-white
                px-5
                py-2.5
                text-sm
                font-medium
                text-gray-700
                transition
                hover:bg-gray-50
                disabled:cursor-not-allowed
                disabled:opacity-50
              "

            >

              {loadingMore
                ? "Loading..."
                : "Load more"}

            </button>

          </div>

        )}

    </div>

  );

}
