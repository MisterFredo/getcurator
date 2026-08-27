"use client";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Languages,
  RefreshCw,
} from "lucide-react";

import {
  api,
} from "@/lib/api";


/* ========================================================= */

const PAGE_SIZE = 20;


/* =========================================================
   TRANSLATED FIELDS
========================================================= */

const TRANSLATION_FIELDS = [

  "TITLE",

  "EXCERPT",

  "CONTENT_BODY",

  "SIGNAL_ANALYTIQUE",

  "MECANIQUE_EXPLIQUEE",

  "ENJEU_STRATEGIQUE",

  "POINT_DE_FRICTION",

];


/* =========================================================
   TYPES
========================================================= */

type TranslationStatus =
  | "MISSING"
  | "PARTIAL"
  | "COMPLETE";


type TranslationContent = {

  id_content: string;

  id_primary_company?: string | null;

  primary_company_name?: string | null;

  source_url?: string | null;

  source_title?: string | null;

  title?: string | null;

  title_en?: string | null;

  excerpt?: string | null;

  excerpt_en?: string | null;

  status?: string | null;

  translation_status:
    TranslationStatus;

  translation_required_count:
    number;

  translation_completed_count:
    number;

  source_date?: string | null;

  published_at?: string | null;

  updated_at?: string | null;

};


/* ========================================================= */

export default function TranslationPage() {

  const [
    contents,
    setContents,
  ] = useState<TranslationContent[]>(
    [],
  );

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    translating,
    setTranslating,
  ] = useState(false);

  const [
    selectedIds,
    setSelectedIds,
  ] = useState<string[]>(
    [],
  );

  const [
    statusFilter,
    setStatusFilter,
  ] = useState("ALL");

  const [
    translationFilter,
    setTranslationFilter,
  ] = useState("ALL");

  const [
    page,
    setPage,
  ] = useState(1);


  /* =====================================================
     LOAD
  ===================================================== */

  async function load() {

    try {

      setLoading(true);

      const response =
        await api.get(
          "/content/list",
        );

      setContents(
        response.contents
        || [],
      );

    } catch (error) {

      console.error(
        error,
      );

      alert(
        "Erreur chargement contenus",
      );

    } finally {

      setLoading(false);

    }

  }


  useEffect(() => {

    load();

  }, []);


  /* =====================================================
     HELPERS
  ===================================================== */

  function toggleSelection(
    id: string,
  ) {

    setSelectedIds(
      (previous) =>

        previous.includes(id)

          ? previous.filter(
              (currentId) =>
                currentId !== id,
            )

          : [
              ...previous,
              id,
            ],
    );

  }


  function formatDate(
    value?: string | null,
  ) {

    if (!value) {
      return "—";
    }

    return new Date(
      value,
    ).toLocaleDateString(
      "fr-FR",
    );

  }


  function getStatusClasses(
    status: TranslationStatus,
  ) {

    if (status === "COMPLETE") {

      return (
        "border-green-200 "
        + "bg-green-50 "
        + "text-green-700"
      );

    }

    if (status === "PARTIAL") {

      return (
        "border-amber-200 "
        + "bg-amber-50 "
        + "text-amber-700"
      );

    }

    return (
      "border-red-200 "
      + "bg-red-50 "
      + "text-red-700"
    );

  }


  /* =====================================================
     FILTERS
  ===================================================== */

  const filteredContents =
    useMemo(() => {

      return contents.filter(
        (content) => {

          const matchesStatus = (

            statusFilter === "ALL"

            || content.status
              === statusFilter

          );

          const matchesTranslation = (

            translationFilter === "ALL"

            || content.translation_status
              === translationFilter

          );

          return (
            matchesStatus
            && matchesTranslation
          );

        },
      );

    }, [
      contents,
      statusFilter,
      translationFilter,
    ]);


  /* =====================================================
     PAGINATION
  ===================================================== */

  const totalPages = Math.max(

    Math.ceil(
      filteredContents.length
      / PAGE_SIZE,
    ),

    1,
  );


  const paginatedContents =
    filteredContents.slice(

      (page - 1)
      * PAGE_SIZE,

      page
      * PAGE_SIZE,
    );


  /* =====================================================
     TRANSLATE ONE
  ===================================================== */

  async function translateOne(
    id: string,
  ) {

    try {

      setTranslating(true);

      await api.post(

        "/translation/content",

        {
          content_id:
            id,

          target_lang:
            "fr",

          fields:
            TRANSLATION_FIELDS,
        },
      );
      
      await load();

    } catch (error) {

      console.error(
        error,
      );

      alert(
        "Erreur traduction",
      );

    } finally {

      setTranslating(false);

    }

  }


  /* =====================================================
     TRANSLATE SELECTED
  ===================================================== */

  async function translateBulk() {

    if (
      selectedIds.length === 0
    ) {
      return;
    }

    try {

      setTranslating(true);

      await api.post(

        "/translation/batch",

        {
          content_ids:
            selectedIds,

          target_lang:
            "fr",

          fields:
            TRANSLATION_FIELDS,

          only_missing:
            false,
        },
      );

      setSelectedIds(
        [],
      );

      await load();

    } catch (error) {

      console.error(
        error,
      );

      alert(
        "Erreur batch traduction",
      );

    } finally {

      setTranslating(false);

    }

  }


  /* =====================================================
     TRANSLATE VISIBLE
  ===================================================== */

  async function translateVisible() {

    if (
      paginatedContents.length === 0
    ) {
      return;
    }

    try {

      setTranslating(true);

      await api.post(

        "/translation/batch",

        {
          content_ids:
            paginatedContents.map(
              (content) =>
                content.id_content,
            ),

          target_lang:
            "fr",

          fields:
            TRANSLATION_FIELDS,

          only_missing:
            false,
        },
      );

      await load();

    } catch (error) {

      console.error(
        error,
      );

      alert(
        "Erreur batch visible",
      );

    } finally {

      setTranslating(false);

    }

  }


  /* =====================================================
     TRANSLATE MISSING
  ===================================================== */

  async function translateMissing() {

    try {

      setTranslating(true);

      await api.post(

        "/translation/batch",

        {
          target_lang:
            "fr",

          fields:
            TRANSLATION_FIELDS,

          only_missing:
            true,

          limit:
            9999,
        },
      );

      await load();

    } catch (error) {

      console.error(
        error,
      );

      alert(
        "Erreur batch traduction",
      );

    } finally {

      setTranslating(false);

    }

  }


  /* =====================================================
     LOADING
  ===================================================== */

  if (loading) {

    return (

      <div>

        Chargement…

      </div>

    );

  }


  /* =====================================================
     RENDER
  ===================================================== */

  return (

    <div className="space-y-8">

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <div className="flex items-center justify-between gap-6">

        <div>

          <h1 className="text-3xl font-semibold text-ratecard-blue">

            Translations

          </h1>

          <p className="mt-1 text-sm text-gray-500">

            English production → French translation

          </p>

        </div>

        <div className="flex items-center gap-2">

          <button
            type="button"
            onClick={
              translateVisible
            }
            disabled={
              translating
              || paginatedContents.length
                === 0
            }
            className="rounded border px-4 py-2 text-sm disabled:opacity-50"
          >

            Traduire les visibles

          </button>

          <button
            type="button"
            onClick={
              translateMissing
            }
            disabled={
              translating
            }
            className="rounded bg-ratecard-blue px-4 py-2 text-sm text-white disabled:opacity-50"
          >

            {translating
              ? "Traduction…"
              : "Traduire les manquants"}

          </button>

        </div>

      </div>


      {/* ================================================= */}
      {/* FILTERS */}
      {/* ================================================= */}

      <div className="flex items-center justify-between gap-6">

        <div className="flex items-center gap-3">

          <select
            value={
              statusFilter
            }
            onChange={
              (event) => {

                setStatusFilter(
                  event.target.value,
                );

                setPage(
                  1,
                );

                setSelectedIds(
                  [],
                );

              }
            }
            className="rounded border px-3 py-2 text-sm"
          >

            <option value="ALL">

              Tous statuts

            </option>

            <option value="DRAFT">

              Draft

            </option>

            <option value="READY">

              Ready

            </option>

            <option value="SCHEDULED">

              Scheduled

            </option>

            <option value="PUBLISHED">

              Published

            </option>

          </select>

          <select
            value={
              translationFilter
            }
            onChange={
              (event) => {

                setTranslationFilter(
                  event.target.value,
                );

                setPage(
                  1,
                );

                setSelectedIds(
                  [],
                );

              }
            }
            className="rounded border px-3 py-2 text-sm"
          >

            <option value="ALL">

              Toutes traductions

            </option>

            <option value="MISSING">

              Missing

            </option>

            <option value="PARTIAL">

              Partial

            </option>

            <option value="COMPLETE">

              Complete

            </option>

          </select>

        </div>

        <div className="text-sm text-gray-500">

          {filteredContents.length}
          {" contenus"}

        </div>

      </div>


      {/* ================================================= */}
      {/* BULK */}
      {/* ================================================= */}

      {selectedIds.length > 0 && (

        <div className="flex items-center gap-3 rounded border bg-gray-50 px-4 py-3">

          <button
            type="button"
            onClick={
              translateBulk
            }
            disabled={
              translating
            }
            className="flex items-center gap-2 rounded bg-green-600 px-3 py-2 text-sm text-white disabled:opacity-50"
          >

            <Languages
              size={16}
            />

            Traduire la sélection

          </button>

          <div className="text-sm text-gray-500">

            {selectedIds.length}
            {" sélectionné(s)"}

          </div>

        </div>

      )}


      {/* ================================================= */}
      {/* TABLE */}
      {/* ================================================= */}

      <div className="overflow-x-auto rounded-lg border">

        <table className="w-full border-collapse text-sm">

          <thead>

            <tr className="border-b bg-gray-100 text-left text-gray-700">

              <th className="p-3">

                <input
                  type="checkbox"
                  checked={
                    paginatedContents.length > 0

                    && paginatedContents.every(
                      (content) =>
                        selectedIds.includes(
                          content.id_content,
                        ),
                    )
                  }
                  onChange={
                    (event) => {

                      const visibleIds =
                        paginatedContents.map(
                          (content) =>
                            content.id_content,
                        );

                      if (
                        event.target.checked
                      ) {

                        setSelectedIds(
                          (
                            previous,
                          ) => Array.from(
                            new Set([
                              ...previous,
                              ...visibleIds,
                            ]),
                          ),
                        );

                      } else {

                        setSelectedIds(
                          (
                            previous,
                          ) => previous.filter(
                            (id) =>
                              !visibleIds.includes(
                                id,
                              ),
                          ),
                        );

                      }

                    }
                  }
                />

              </th>

              <th className="p-3">

                English title

              </th>

              <th className="p-3">

                French title

              </th>

              <th className="p-3">

                Translation

              </th>

              <th className="p-3">

                Content status

              </th>

              <th className="p-3">

                Source date

              </th>

              <th className="p-3 text-right">

                Action

              </th>

            </tr>

          </thead>

          <tbody>

            {paginatedContents.map(
              (content) => {

                const requiredCount = (
                  content
                    .translation_required_count
                  || 0
                );

                const completedCount = (
                  content
                    .translation_completed_count
                  || 0
                );

                const translationStatus = (
                  content.translation_status
                  || "MISSING"
                );

                return (

                  <tr
                    key={
                      content.id_content
                    }
                    className="border-b last:border-b-0 hover:bg-gray-50"
                  >

                    <td className="p-3">

                      <input
                        type="checkbox"
                        checked={
                          selectedIds.includes(
                            content.id_content,
                          )
                        }
                        onChange={
                          () =>
                            toggleSelection(
                              content.id_content,
                            )
                        }
                      />

                    </td>

                    <td className="max-w-[320px] p-3 font-medium">

                      {content.title_en ? (

                        <div className="line-clamp-2">

                          {content.title_en}

                        </div>

                      ) : (

                        <div className="italic text-gray-400">

                          — missing English source —

                        </div>

                      )}

                    </td>

                    <td className="max-w-[320px] p-3">

                      {content.title ? (

                        <div className="line-clamp-2">

                          {content.title}

                        </div>

                      ) : (

                        <div className="italic text-gray-400">

                          — missing French translation —

                        </div>

                      )}

                    </td>

                    <td className="p-3">

                      <span
                        className={[
                          "inline-flex rounded-full border px-2 py-1 text-xs font-medium",
                          getStatusClasses(
                            translationStatus,
                          ),
                        ].join(" ")}
                      >

                        {translationStatus}

                        {" · "}

                        {completedCount}
                        {"/"}
                        {requiredCount}

                      </span>

                    </td>

                    <td className="p-3">

                      <span className="rounded bg-gray-100 px-2 py-1 text-xs">

                        {content.status
                          || "—"}

                      </span>

                    </td>

                    <td className="p-3 text-gray-600">

                      {formatDate(
                        content.source_date,
                      )}

                    </td>

                    <td className="p-3 text-right">

                      <button
                        type="button"
                        title="Retraduire vers le français"
                        onClick={
                          () =>
                            translateOne(
                              content.id_content,
                            )
                        }
                        disabled={
                          translating
                          || requiredCount === 0
                        }
                        className="inline-flex items-center gap-1 rounded px-2 py-1 text-blue-600 hover:bg-blue-50 disabled:opacity-40"
                      >

                        <RefreshCw
                          size={16}
                          className={
                            translating
                              ? "animate-spin"
                              : ""
                          }
                        />

                      </button>

                    </td>

                  </tr>

                );

              },
            )}

            {paginatedContents.length === 0 && (

              <tr>

                <td
                  colSpan={7}
                  className="p-8 text-center text-gray-500"
                >

                  Aucun contenu

                </td>

              </tr>

            )}

          </tbody>

        </table>

      </div>


      {/* ================================================= */}
      {/* PAGINATION */}
      {/* ================================================= */}

      {totalPages > 1 && (

        <div className="flex justify-center gap-4">

          <button
            type="button"
            disabled={
              page === 1
            }
            onClick={
              () => {

                setPage(
                  (currentPage) =>
                    currentPage - 1,
                );

                setSelectedIds(
                  [],
                );

              }
            }
            className="rounded border px-3 py-1 disabled:opacity-50"
          >

            Précédent

          </button>

          <span>

            Page {page}
            {" / "}
            {totalPages}

          </span>

          <button
            type="button"
            disabled={
              page === totalPages
            }
            onClick={
              () => {

                setPage(
                  (currentPage) =>
                    currentPage + 1,
                );

                setSelectedIds(
                  [],
                );

              }
            }
            className="rounded border px-3 py-1 disabled:opacity-50"
          >

            Suivant

          </button>

        </div>

      )}

    </div>

  );

}
