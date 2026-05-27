// app/(admin)/admin/digest/page.tsx

"use client";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import DeliveryHeaderConfig from "@/components/delivery/core/DeliveryHeaderConfig";

import DigestSelectors from "@/components/digest/DigestSelectors";

import DigestEditorialFlow from "@/components/digest/DigestEditorialFlow";

import DigestPreviewPanel from "@/components/digest/delivery/DigestPreviewPanel";

import type {
  DigestContentItem,
  DigestNumberItem,
  DigestEditorialItem,
} from "@/types/digest";

import type {
  HeaderConfig,
} from "@/types/newsletter";

/* ========================================================= */

export default function DigestPage() {

  /* =======================================================
     HEADER
  ======================================================= */

  const [
    headerConfig,
    setHeaderConfig,
  ] = useState<HeaderConfig>({
    title: "Digest Curator",

    subtitle: "",

    period: "",

    headerCompany:
      undefined,

    topBarEnabled:
      true,

    topBarColor:
      "#111827",

    periodColor:
      "#111827",

    introHtml: "",
  });

  const [
    introText,
    setIntroText,
  ] = useState("");

  /* =======================================================
     SEARCH
  ======================================================= */

  const [
    query,
    setQuery,
  ] = useState("");

  const [
    loading,
    setLoading,
  ] = useState(false);

  /* =======================================================
     DIGEST DATA
  ======================================================= */

  const [
    contents,
    setContents,
  ] = useState<
    DigestContentItem[]
  >([]);

  const [
    numbers,
  ] = useState<
    DigestNumberItem[]
  >([]);

  /* =======================================================
     FLOW
  ======================================================= */

  const [
    editorialOrder,
    setEditorialOrder,
  ] = useState<
    DigestEditorialItem[]
  >([]);

  /* =======================================================
     SEARCH API
  ======================================================= */

  async function searchDigest() {

    try {

      setLoading(true);

      const response =
        await fetch(
          "/api/digest/search",
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body: JSON.stringify({
              query,

              limit: 20,

              content_type:
                "analysis",
            }),
          }
        );

      const data =
        await response.json();

      const results =
        data?.result
          ?.contents || [];

      setContents(
        results
      );

    } catch (
      error
    ) {

      console.error(
        "Digest search error",
        error
      );

    } finally {

      setLoading(false);
    }
  }

  /* =======================================================
     INITIAL LOAD
  ======================================================= */

  useEffect(() => {

    searchDigest();

  }, []);

  /* =======================================================
     CONTENTS SELECTED
  ======================================================= */

  const selectedContents =
    useMemo(() => {

      const selectedIds =
        editorialOrder
          .filter(
            (i) =>
              i.type ===
              "content"
          )
          .map(
            (i) => i.id
          );

      return contents.filter(
        (c) =>
          selectedIds.includes(
            c.id
          )
      );

    }, [
      contents,
      editorialOrder,
    ]);

  /* =======================================================
     UI
  ======================================================= */

  return (

    <div className="space-y-4">

      {/* ===================================================
         HEADER
      =================================================== */}

      <div className="flex items-center justify-between">

        <h1 className="text-lg font-semibold tracking-tight">
          Digest
        </h1>

      </div>

      {/* ===================================================
         SEARCH BAR
      =================================================== */}

      <div className="border border-gray-200 rounded-lg bg-white p-4">

        <div className="flex gap-3">

          <input
            type="text"

            value={query}

            onChange={(e) =>
              setQuery(
                e.target.value
              )
            }

            placeholder="Rechercher des contenus Curator..."

            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm"
          />

          <button
            onClick={
              searchDigest
            }

            disabled={loading}

            className="px-4 py-2 rounded-lg bg-black text-white text-sm"
          >
            {loading
              ? "Recherche..."
              : "Rechercher"}
          </button>

        </div>

      </div>

      {/* ===================================================
         LAYOUT
      =================================================== */}

      <div className="grid grid-cols-1 xl:grid-cols-[1.1fr_1.3fr] gap-6 items-start">

        {/* =================================================
           LEFT
        ================================================= */}

        <div className="space-y-5">

          <DeliveryHeaderConfig
            headerConfig={
              headerConfig
            }

            setHeaderConfig={
              setHeaderConfig
            }

            introText={
              introText
            }

            setIntroText={
              setIntroText
            }
          />

          <DigestSelectors
            contents={
              contents
            }

            numbers={
              numbers
            }

            editorialOrder={
              editorialOrder
            }

            setEditorialOrder={
              setEditorialOrder
            }
          />

          <DigestEditorialFlow
            contents={
              contents
            }

            numbers={
              numbers
            }

            editorialOrder={
              editorialOrder
            }

            setEditorialOrder={
              setEditorialOrder
            }
          />

        </div>

        {/* =================================================
           RIGHT
        ================================================= */}

        <div className="sticky top-6 h-[calc(100vh-4rem)] overflow-y-auto pr-2">

          <DigestPreviewPanel
            headerConfig={
              headerConfig
            }

            editorialHtml={
              introText
            }

            contents={
              selectedContents
            }

            numbers={
              numbers
            }
          />

        </div>

      </div>

    </div>
  );
}
