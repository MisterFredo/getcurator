"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  useSearchParams,
} from "next/navigation";

import {
  useEntityDrawer,
} from "@/hooks/useEntityDrawer";

import CompanyCard from "@/components/companies/CompanyCard";
import FavoritesStrip from "@/components/favorites/FavoritesStrip";

import {
  api,
} from "@/lib/api";

export const dynamic =
  "force-dynamic";

export const fetchCache =
  "force-no-store";


/* =========================================================
   TYPES
========================================================= */

type Company = {

  id_company: string;

  name: string;

  media_logo_rectangle_id?:
    string | null;

  universes: string[];

};


/* =========================================================
   FETCH
========================================================= */

async function fetchCompanies():
  Promise<Company[]> {

  try {

    const json =
      await api.get(
        "/company/list-curator",
      );

    console.log(
      "COMPANIES RAW",
      json,
    );

    const data =
      json?.companies ?? [];

    console.log(
      "COMPANIES DATA",
      data,
    );

    if (!Array.isArray(data)) {

      console.warn(
        "COMPANIES is not an array",
        data,
      );

      return [];

    }

    const companies =
      data.map(
        (c: any) => ({

          id_company:
            c.id_company,

          name:
            c.name,

          media_logo_rectangle_id:
            c.media_logo_rectangle_id,

          universes:
            c.universes ?? [],

        }),
      );

    console.log(
      "COMPANIES MAPPED",
      companies,
    );

    return companies;

  } catch (e: any) {

    console.error(
      "❌ fetchCompanies error:",
      e,
    );

    if (
      e?.message?.includes(
        "401",
      )
    ) {

      window.location.href =
        "/login";

    }

    return [];

  }

}
/* =========================================================
   SORT
========================================================= */

function sortCompanies(
  companies: Company[],
): Company[] {

  return [...companies].sort(
    (a, b) =>
      a.name.localeCompare(
        b.name,
      ),
  );

}


/* =========================================================
   GROUP
========================================================= */

function groupByUniverse(
  companies: Company[],
) {

  const map:
    Record<
      string,
      Company[]
    > = {};

  companies.forEach(
    (company) => {

      (
        company.universes
        || []
      ).forEach(
        (universe) => {

          if (!map[universe]) {

            map[universe] = [];

          }

          map[universe].push(
            company,
          );

        },
      );

    },
  );

  Object.keys(
    map,
  ).forEach(
    (universe) => {

      map[universe] =
        sortCompanies(
          map[universe],
        );

    },
  );

  return map;

}


/* =========================================================
   PAGE
========================================================= */

export default function CompaniesPage() {

  const [
    companies,
    setCompanies,
  ] = useState<Company[]>([]);

  const [
    preferences,
    setPreferences,
  ] = useState<string[]>([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    ready,
    setReady,
  ] = useState(false);

  const [
    openUniverses,
    setOpenUniverses,
  ] = useState<
    Record<string, boolean>
  >({});

  const searchParams =
    useSearchParams();

  const {
    loadingId,
  } = useEntityDrawer(
    "company",
    "company_id",
  );


  /* =========================================================
     AUTH
  ========================================================= */

  useEffect(() => {

    const userId =
      localStorage.getItem(
        "user_id",
      );

    if (!userId) {

      window.location.href =
        "/login";

      return;

    }

    setReady(
      true,
    );

  }, []);


  /* =========================================================
     LOAD
  ========================================================= */

  useEffect(() => {

    if (!ready) {

      return;

    }

    async function load() {

      setLoading(
        true,
      );

      try {

        const [
          data,
          prefsRes,
        ] = await Promise.all([

          fetchCompanies(),

          api.get(
            "/user/preferences",
          ),

        ]);

        setCompanies(
          data,
        );

        const companyPrefs =
          Array.isArray(
            prefsRes?.preferences?.COMPANY,
          )
            ? prefsRes.preferences.COMPANY
            : [];

        setPreferences(
          companyPrefs,
        );

      } catch (e) {

        console.error(
          "❌ Companies load error:",
          e,
        );

        setCompanies(
          [],
        );

        setPreferences(
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
    ready,
  ]);


  /* =========================================================
     AUTO OPEN CURRENT UNIVERSE
  ========================================================= */

  useEffect(() => {

    const companyId =
      searchParams.get(
        "company_id",
      );

    if (!companyId) {

      return;

    }

    const company =
      companies.find(
        (item) =>
          item.id_company
          === companyId,
      );

    if (!company) {

      return;

    }

    const universe =
      company.universes?.[0];

    if (!universe) {

      return;

    }

    setOpenUniverses(
      (prev) => ({

        ...prev,

        [universe]:
          true,

      }),
    );

  }, [
    companies,
    searchParams,
  ]);


  /* =========================================================
     HELPERS
  ========================================================= */

  function toggleUniverse(
    universe: string,
  ) {

    setOpenUniverses(
      (prev) => ({

        ...prev,

        [universe]:
          !prev[universe],

      }),
    );

  }


  /* =========================================================
     DATA
  ========================================================= */

  const favorites =
    sortCompanies(
      companies.filter(
        (company) =>
          preferences.includes(
            company.id_company,
          ),
      ),
    );

  const others =
    companies.filter(
      (company) =>
        !preferences.includes(
          company.id_company,
        ),
    );

  const groupedOthers =
    groupByUniverse(
      others,
    );

  const hasContent =
    companies.length > 0;


  /* =========================================================
     READY
  ========================================================= */

  if (!ready) {

    return (

      <div className="
        p-6
        text-sm
        text-gray-400
      ">
        Chargement…
      </div>

    );

  }


  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <div className="
      space-y-8
    ">

      {/* =====================================================
          HEADER
      ===================================================== */}

      <div>

        <h1 className="
          text-lg
          font-semibold
          text-gray-900
        ">
          Companies
        </h1>

      </div>


      {/* =====================================================
          LOADING
      ===================================================== */}

      {loading && (

        <p className="
          text-sm
          text-gray-400
        ">
          Chargement des sociétés...
        </p>

      )}


      {/* =====================================================
          FAVORITES
      ===================================================== */}

      {!loading
        && favorites.length > 0
        && (

        <FavoritesStrip>

          <div className="
            grid
            grid-cols-3
            sm:grid-cols-4
            md:grid-cols-6
            lg:grid-cols-7
            xl:grid-cols-8
            gap-3
          ">

            {favorites.map(
              (company) => (

                <CompanyCard

                  key={
                    company.id_company
                  }

                  id={
                    company.id_company
                  }

                  name={
                    company.name
                  }

                  visualRectId={
                    company.media_logo_rectangle_id
                  }

                  isLoading={
                    loadingId
                    === company.id_company
                  }

                  isFavorite

                  onToggleFavorite={(
                    id,
                    isFavorite,
                  ) => {

                    setPreferences(
                      (prev) =>

                        isFavorite

                          ? prev.filter(
                              (value) =>
                                value !== id,
                            )

                          : [
                              ...prev,
                              id,
                            ],

                    );

                  }}

                />

              ),
            )}

          </div>

        </FavoritesStrip>

      )}


      {/* =====================================================
          OTHER COMPANIES
      ===================================================== */}

      {!loading
        && hasContent
        && Object.entries(
          groupedOthers,
        )
          .sort(
            ([a], [b]) =>
              a.localeCompare(
                b,
              ),
          )
          .map(
            ([
              universe,
              items,
            ]) => (

              <section

                key={
                  universe
                }

                className="
                  space-y-2
                "

              >

                <div

                  onClick={() =>
                    toggleUniverse(
                      universe,
                    )
                  }

                  className="
                    flex
                    items-center
                    justify-between
                    cursor-pointer
                    py-2
                    px-1
                    border-b
                    border-gray-100
                    hover:bg-gray-50
                  "

                >

                  <h2 className="
                    text-xs
                    font-semibold
                    uppercase
                    text-gray-500
                  ">

                    {universe}

                  </h2>

                  <span className="
                    text-xs
                    text-gray-400
                  ">

                    {items.length}

                  </span>

                </div>


                {openUniverses[
                  universe
                ] && (

                  <div className="
                    grid
                    grid-cols-3
                    sm:grid-cols-4
                    md:grid-cols-6
                    lg:grid-cols-7
                    xl:grid-cols-8
                    gap-3
                    pt-2
                  ">

                    {items.map(
                      (company) => (

                        <CompanyCard

                          key={
                            company.id_company
                          }

                          id={
                            company.id_company
                          }

                          name={
                            company.name
                          }

                          visualRectId={
                            company.media_logo_rectangle_id
                          }

                          isLoading={
                            loadingId
                            === company.id_company
                          }

                          isFavorite={
                            preferences.includes(
                              company.id_company,
                            )
                          }

                          onToggleFavorite={(
                            id,
                            isFavorite,
                          ) => {

                            setPreferences(
                              (prev) =>

                                isFavorite

                                  ? prev.filter(
                                      (value) =>
                                        value !== id,
                                    )

                                  : [
                                      ...prev,
                                      id,
                                    ],

                            );

                          }}

                        />

                      ),
                    )}

                  </div>

                )}

              </section>

            ),
          )}

    </div>

  );

}
