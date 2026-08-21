"use client";

import {
  useEffect,
  useState,
} from "react";

import Link from "next/link";

import {
  api,
} from "@/lib/api";


/* =========================================================
   TYPES
========================================================= */

type SourceRow = {

  source_id: string;
  name: string;

  domain?: string | null;

  universe_id?: string | null;

  acquisition_mode?: string | null;

};


type Universe = {

  id_universe: string;
  label: string;

};


/* =========================================================
   PAGE
========================================================= */

export default function SourceList() {

  const [
    sources,
    setSources,
  ] =
    useState<SourceRow[]>([]);

  const [
    universes,
    setUniverses,
  ] =
    useState<Universe[]>([]);


  /* =======================================================
     FILTERS
  ======================================================== */

  const [
    search,
    setSearch,
  ] =
    useState("");

  const [
    universeFilter,
    setUniverseFilter,
  ] =
    useState("");

  const [
    sourceFilter,
    setSourceFilter,
  ] =
    useState("");

  const [
    acquisitionFilter,
    setAcquisitionFilter,
  ] =
    useState("");


  /* =======================================================
     LOADING
  ======================================================== */

  const [
    loading,
    setLoading,
  ] =
    useState(true);


  /* =======================================================
     LOAD DATA
  ======================================================== */

  useEffect(() => {

    async function load() {

      try {

        setLoading(
          true
        );

        const [
          sourcesRes,
          universesRes,
        ] =
          await Promise.all([
            api.get(
              "/source/list"
            ),
            api.get(
              "/universe/list"
            ),
          ]);

        setSources(
          sourcesRes.sources || []
        );

        setUniverses(
          universesRes.universes || []
        );

      } catch (e) {

        console.error(
          e
        );

        alert(
          "❌ Erreur chargement sources"
        );

      } finally {

        setLoading(
          false
        );

      }

    }

    load();

  }, []);


  /* =======================================================
     DELETE
  ======================================================== */

  async function deleteSource(
    id: string,
    name: string,
  ) {

    const ok =
      confirm(
        `Supprimer la source "${name}" ?`
      );

    if (!ok) {
      return;
    }

    try {

      await api.delete(
        `/source/${id}`
      );

      setSources(
        (prev) =>
          prev.filter(
            (source) =>
              source.source_id !== id
          )
      );

    } catch (e) {

      console.error(
        e
      );

      alert(
        "❌ Erreur suppression"
      );

    }

  }


  /* =======================================================
     UNIVERSE LABEL
  ======================================================== */

  function getUniverseLabel(
    universeId?: string | null,
  ) {

    if (!universeId) {
      return null;
    }

    const universe =
      universes.find(
        (item) =>
          item.id_universe ===
          universeId
      );

    return (
      universe?.label ||
      null
    );

  }


  /* =======================================================
     ACQUISITION MODES
  ======================================================== */

  const acquisitionModes =
    Array.from(
      new Set(
        sources
          .map(
            (source) =>
              source.acquisition_mode
                ?.toUpperCase()
          )
          .filter(
            (mode): mode is string =>
              Boolean(mode)
          )
      )
    ).sort();


  /* =======================================================
     FILTER SOURCES
  ======================================================== */

  const q =
    search
      .trim()
      .toLowerCase();


  const filteredSources =
    sources.filter(
      (source) => {

        // =================================================
        // SEARCH
        // =================================================

        const matchesSearch =
          !q ||
          source.name
            .toLowerCase()
            .includes(q) ||
          (
            source.domain ||
            ""
          )
            .toLowerCase()
            .includes(q);


        // =================================================
        // UNIVERSE
        // =================================================

        const matchesUniverse =
          !universeFilter ||
          source.universe_id ===
            universeFilter;


        // =================================================
        // SOURCE
        // =================================================

        const matchesSource =
          !sourceFilter ||
          source.source_id ===
            sourceFilter;


        // =================================================
        // ACQUISITION
        // =================================================

        const mode = (
          source.acquisition_mode ||
          ""
        ).toUpperCase();

        const matchesAcquisition =
          !acquisitionFilter ||
          mode ===
            acquisitionFilter;


        return (
          matchesSearch &&
          matchesUniverse &&
          matchesSource &&
          matchesAcquisition
        );

      }
    );


  /* =======================================================
     UI
  ======================================================== */

  return (

    <div className="space-y-8">

      {/* ===================================================
          HEADER
      ==================================================== */}

      <div className="flex justify-between items-center">

        <h1 className="text-3xl font-semibold text-ratecard-blue">
          Sources
        </h1>

        <Link
          href="/admin/source/create"
          className="bg-ratecard-green px-4 py-2 text-white rounded"
        >
          + Ajouter une source
        </Link>

      </div>


      {/* ===================================================
          FILTERS
      ==================================================== */}

      <div className="flex flex-wrap gap-3 items-center">

        {/* SEARCH */}

        <input
          type="text"
          placeholder="Rechercher..."
          value={
            search
          }
          onChange={(e) =>
            setSearch(
              e.target.value
            )
          }
          className="border px-3 py-2 rounded min-w-[240px]"
        />


        {/* UNIVERSE */}

        <select
          value={
            universeFilter
          }
          onChange={(e) =>
            setUniverseFilter(
              e.target.value
            )
          }
          className="border px-3 py-2 rounded"
        >

          <option value="">
            Tous les univers
          </option>

          {universes.map(
            (universe) => (

              <option
                key={
                  universe.id_universe
                }
                value={
                  universe.id_universe
                }
              >
                {universe.label}
              </option>

            )
          )}

        </select>


        {/* SOURCE */}

        <select
          value={
            sourceFilter
          }
          onChange={(e) =>
            setSourceFilter(
              e.target.value
            )
          }
          className="border px-3 py-2 rounded"
        >

          <option value="">
            Toutes les sources
          </option>

          {sources
            .slice()
            .sort(
              (a, b) =>
                a.name.localeCompare(
                  b.name
                )
            )
            .map(
              (source) => (

                <option
                  key={
                    source.source_id
                  }
                  value={
                    source.source_id
                  }
                >
                  {source.name}
                </option>

              )
            )}

        </select>


        {/* ACQUISITION */}

        <select
          value={
            acquisitionFilter
          }
          onChange={(e) =>
            setAcquisitionFilter(
              e.target.value
            )
          }
          className="border px-3 py-2 rounded"
        >

          <option value="">
            Toutes acquisitions
          </option>

          {acquisitionModes.map(
            (mode) => (

              <option
                key={
                  mode
                }
                value={
                  mode
                }
              >
                {mode}
              </option>

            )
          )}

        </select>


        {/* RESET */}

        {(
          search ||
          universeFilter ||
          sourceFilter ||
          acquisitionFilter
        ) && (

          <button
            onClick={() => {

              setSearch(
                ""
              );

              setUniverseFilter(
                ""
              );

              setSourceFilter(
                ""
              );

              setAcquisitionFilter(
                ""
              );

            }}
            className="text-sm text-gray-500 hover:text-black"
          >
            Réinitialiser
          </button>

        )}

      </div>


      {/* ===================================================
          RESULT COUNT
      ==================================================== */}

      {!loading && (

        <div className="text-sm text-gray-500">

          {filteredSources.length} source(s)

        </div>

      )}


      {/* ===================================================
          CONTENT
      ==================================================== */}

      {loading ? (

        <p className="text-gray-500">
          Chargement…
        </p>

      ) : filteredSources.length === 0 ? (

        <p className="italic text-gray-500">
          Aucune source.
        </p>

      ) : (

        <table className="w-full text-sm border-collapse">

          {/* ===============================================
              HEADER
          ================================================ */}

          <thead>

            <tr className="bg-gray-100 border-b text-left">

              <th className="p-3">
                Source
              </th>

              <th className="p-3">
                Domaine
              </th>

              <th className="p-3">
                Univers
              </th>

              <th className="p-3">
                Acquisition
              </th>

              <th className="p-3 text-right">
                Actions
              </th>

            </tr>

          </thead>


          {/* ===============================================
              BODY
          ================================================ */}

          <tbody>

            {filteredSources.map(
              (source) => {

                const acquisitionMode = (
                  source.acquisition_mode ||
                  ""
                ).toUpperCase();

                return (

                  <tr
                    key={
                      source.source_id
                    }
                    className="border-b hover:bg-gray-50"
                  >

                    {/* SOURCE */}

                    <td className="p-3 font-medium">

                      {source.name}

                    </td>


                    {/* DOMAIN */}

                    <td className="p-3">

                      {source.domain || (

                        <span className="text-gray-400">
                          —
                        </span>

                      )}

                    </td>


                    {/* UNIVERSE */}

                    <td className="p-3">

                      {getUniverseLabel(
                        source.universe_id
                      ) || (

                        <span className="text-gray-400">
                          —
                        </span>

                      )}

                    </td>


                    {/* ACQUISITION */}

                    <td className="p-3">

                      {acquisitionMode ? (

                        <span
                          className={
                            acquisitionMode ===
                            "MANUAL"
                              ? "text-orange-600 font-medium"
                              : "text-green-600 font-medium"
                          }
                        >
                          {acquisitionMode}
                        </span>

                      ) : (

                        <span className="text-gray-400">
                          —
                        </span>

                      )}

                    </td>


                    {/* ACTIONS */}

                    <td className="p-3 text-right space-x-3">

                      <Link
                        href={
                          `/admin/source/edit/${source.source_id}`
                        }
                        className="text-blue-600 hover:underline"
                      >
                        Modifier
                      </Link>

                      <button
                        onClick={() =>
                          deleteSource(
                            source.source_id,
                            source.name
                          )
                        }
                        className="text-red-600 hover:underline"
                      >
                        Supprimer
                      </button>

                    </td>

                  </tr>

                );

              }
            )}

          </tbody>

        </table>

      )}

    </div>

  );

}
