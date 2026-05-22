"use client";

import { useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";

import {
  Languages,
  RefreshCw,
} from "lucide-react";

const PAGE_SIZE = 20;

type TranslationContent = {
  id_content: string;

  title: string;
  title_en?: string | null;

  excerpt_en?: string | null;

  status: string;

  source_date?: string | null;
};

export default function TranslationPage() {

  const [contents, setContents] =
    useState<TranslationContent[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [translating, setTranslating] =
    useState(false);

  const [selectedIds, setSelectedIds] =
    useState<string[]>([]);

  const [statusFilter, setStatusFilter] =
    useState("ALL");

  const [translationFilter, setTranslationFilter] =
    useState("ALL");

  const [page, setPage] =
    useState(1);

  // =====================================================
  // LOAD
  // =====================================================

  async function load() {

    setLoading(true);

    try {

      const res = await api.get(
        "/content/list"
      );

      setContents(
        res.contents || []
      );

    } catch (e) {

      console.error(e);

      alert(
        "Erreur chargement contenus"
      );

    }

    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  // =====================================================
  // HELPERS
  // =====================================================

  function toggleSelection(
    id: string
  ) {

    setSelectedIds((prev) =>

      prev.includes(id)
        ? prev.filter(
            (x) => x !== id
          )
        : [...prev, id]
    );
  }

  function formatDate(
    value?: string | null
  ) {

    if (!value) return "—";

    return new Date(value)
      .toLocaleDateString(
        "fr-FR"
      );
  }

  function getTranslationStatus(
    c: TranslationContent
  ) {

    const hasTitleEn =
      !!c.title_en?.trim();

    const hasExcerptEn =
      !!c.excerpt_en?.trim();

    if (
      hasTitleEn
      && hasExcerptEn
    ) {
      return "COMPLETE";
    }

    if (
      hasTitleEn
      || hasExcerptEn
    ) {
      return "PARTIAL";
    }

    return "MISSING";
  }

  // =====================================================
  // FILTERS
  // =====================================================

  const filteredContents =
    useMemo(() => {

      return contents.filter((c) => {

        const translationStatus =
          getTranslationStatus(c);

        const matchStatus =
          statusFilter === "ALL"
          || c.status === statusFilter;

        const matchTranslation =
          translationFilter === "ALL"
          || translationStatus
            === translationFilter;

        return (
          matchStatus
          && matchTranslation
        );
      });

    }, [
      contents,
      statusFilter,
      translationFilter,
    ]);

  // =====================================================
  // PAGINATION
  // =====================================================

  const totalPages =
    Math.ceil(
      filteredContents.length
      / PAGE_SIZE
    );

  const paginatedContents =
    filteredContents.slice(
      (page - 1) * PAGE_SIZE,
      page * PAGE_SIZE
    );

  // =====================================================
  // ACTIONS
  // =====================================================

  async function translateOne(
    id: string
  ) {

    try {

      setTranslating(true);

      await api.post(
        "/translation/content",
        {
          content_id: id,
          target_lang: "en",

          fields: [
            "TITLE",
            "EXCERPT",
          ],
        }
      );

      await load();

    } catch (e) {

      console.error(e);

      alert(
        "Erreur traduction"
      );

    }

    setTranslating(false);
  }

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
            "en",

          fields: [
            "TITLE",
            "EXCERPT",
          ],

          only_missing:
            false,
        }
      );

      setSelectedIds([]);

      await load();

    } catch (e) {

      console.error(e);

      alert(
        "Erreur batch traduction"
      );

    }

    setTranslating(false);
  }

  async function translateVisible() {

  try {

    setTranslating(true);

    await api.post(
      "/translation/batch",
      {
        content_ids:
          paginatedContents.map(
            (c) => c.id_content
          ),

        target_lang: "en",

        fields: [
          "TITLE",
          "EXCERPT",
        ],

        only_missing: false,
      }
    );

    await load();

  } catch (e) {

    console.error(e);

    alert(
      "Erreur batch visible"
    );

  }

  setTranslating(false);
}

  async function translateMissing() {

    try {

      setTranslating(true);

      await api.post(
        "/translation/batch",
        {
          target_lang: "en",

          fields: [
            "TITLE",
            "EXCERPT",
          ],

          only_missing: true,

          limit: 500,
        }
      );

      await load();

    } catch (e) {

      console.error(e);

      alert(
        "Erreur batch traduction"
      );

    }

    setTranslating(false);
  }

  // =====================================================
  // LOADING
  // =====================================================

  if (loading) {

    return (
      <div>
        Chargement…
      </div>
    );
  }

  // =====================================================
  // RENDER
  // =====================================================

  return (

    <div className="space-y-8">

      {/* HEADER */}

      <div className="flex justify-between items-center">

        <div>

          <h1 className="text-3xl font-semibold text-ratecard-blue">
            Translations
          </h1>

          <p className="text-sm text-gray-500 mt-1">
            Gestion des traductions
            éditoriales
          </p>

        </div>

        <div className="flex items-center gap-2">

          <button
            onClick={
              translateMissing
            }
            disabled={translating}
            className="px-4 py-2 rounded bg-ratecard-blue text-white text-sm"
          >
            Traduire les manquants
          </button>

        </div>

      </div>

      {/* FILTERS */}

      <div className="flex justify-between items-center">

        <div className="flex items-center gap-3">

          <select
            value={statusFilter}
            onChange={(e) => {

              setStatusFilter(
                e.target.value
              );

              setPage(1);

            }}
            className="border px-3 py-2 rounded text-sm"
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

            <option value="PUBLISHED">
              Published
            </option>

          </select>

          <select
            value={
              translationFilter
            }
            onChange={(e) => {

              setTranslationFilter(
                e.target.value
              );

              setPage(1);

            }}
            className="border px-3 py-2 rounded text-sm"
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
          {" "}
          contenus

        </div>

      </div>

      {/* BULK */}

      {selectedIds.length > 0 && (

        <div className="flex items-center gap-3 bg-gray-50 border rounded px-4 py-3">

          <button
            onClick={
              translateBulk
            }
            disabled={translating}
            className="flex items-center gap-2 px-3 py-2 rounded bg-green-600 text-white text-sm"
          >

            <Languages size={16} />

            Traduire sélection

          </button>

          <div className="text-sm text-gray-500">

            {selectedIds.length}
            {" "}
            sélectionné(s)

          </div>

        </div>

      )}

      {/* TABLE */}

      <table className="w-full border-collapse text-sm">

        <thead>

          <tr className="bg-gray-100 border-b text-left text-gray-700">

            <th className="p-2">

              <input
                type="checkbox"
                checked={
                  selectedIds.length
                    === paginatedContents.length
                  && paginatedContents.length > 0
                }
                onChange={(e) =>

                  e.target.checked

                    ? setSelectedIds(
                        paginatedContents.map(
                          (c) =>
                            c.id_content
                        )
                      )

                    : setSelectedIds([])
                }
              />

            </th>

            <th className="p-2">
              Title
            </th>

            <th className="p-2">
              Title EN
            </th>

            <th className="p-2">
              Excerpt EN
            </th>

            <th className="p-2">
              Status
            </th>

            <th className="p-2">
              SOURCE_DATE
            </th>

            <th className="p-2 text-right">
              Actions
            </th>

          </tr>

        </thead>

        <tbody>

          {paginatedContents.map(
            (c) => {

              const hasExcerpt =
                !!c.excerpt_en?.trim();

              return (

                <tr
                  key={c.id_content}
                  className="border-b hover:bg-gray-50"
                >

                  <td className="p-2">

                    <input
                      type="checkbox"
                      checked={selectedIds.includes(
                        c.id_content
                      )}
                      onChange={() =>
                        toggleSelection(
                          c.id_content
                        )
                      }
                    />

                  </td>

                  <td className="p-2 font-medium max-w-[280px]">

                    <div className="line-clamp-2">
                      {c.title}
                    </div>

                  </td>

                  <td className="p-2 max-w-[280px]">

                    {c.title_en ? (

                      <div className="line-clamp-2">
                        {c.title_en}
                      </div>

                    ) : (

                      <div className="text-gray-400 italic">
                        — missing —
                      </div>

                    )}

                  </td>

                  <td className="p-2">

                    {hasExcerpt ? (
                      <span className="text-green-600 font-medium">
                        ✅
                      </span>
                    ) : (
                      <span className="text-red-500 font-medium">
                        ❌
                      </span>
                    )}

                  </td>

                  <td className="p-2">

                    <span className="px-2 py-1 rounded text-xs bg-gray-100">

                      {c.status}

                    </span>

                  </td>

                  <td className="p-2 text-gray-600">

                    {formatDate(
                      c.source_date
                    )}

                  </td>

                  <td className="p-2 text-right">

                    <button
                      onClick={() =>
                        translateOne(
                          c.id_content
                        )
                      }
                      disabled={
                        translating
                      }
                      className="inline-flex items-center gap-1 px-2 py-1 rounded hover:bg-blue-50 text-blue-600"
                    >

                      <RefreshCw
                        size={16}
                      />

                    </button>

                  </td>

                </tr>

              );
            }
          )}

        </tbody>

      </table>

      {/* PAGINATION */}

      {totalPages > 1 && (

        <div className="flex justify-center gap-4">

          <button
            disabled={page === 1}
            onClick={() =>
              setPage(
                (p) => p - 1
              )
            }
            className="px-3 py-1 border rounded"
          >
            Précédent
          </button>

          <span>

            Page {page}
            {" / "}
            {totalPages}

          </span>

          <button
            disabled={
              page === totalPages
            }
            onClick={() =>
              setPage(
                (p) => p + 1
              )
            }
            className="px-3 py-1 border rounded"
          >
            Suivant
          </button>

        </div>

      )}

    </div>
  );
}
