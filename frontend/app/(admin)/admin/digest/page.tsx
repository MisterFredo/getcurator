// app/(admin)/admin/digest/page.tsx

"use client";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import { api } from "@/lib/api";

import DeliveryHeaderConfig from "@/components/delivery/core/DeliveryHeaderConfig";

import DigestUserSelector, {
  DigestUser,
} from "@/components/digest/DigestUserSelector";

import DigestSelectors from "@/components/digest/DigestSelectors";

import DigestEditorialFlow from "@/components/digest/DigestEditorialFlow";

import DigestPreviewPanel from "@/components/digest/delivery/DigestPreviewPanel";

import type {
  DigestContentItem,
  DigestEditorialItem,
} from "@/types/digest";

import type {
  HeaderConfig,
} from "@/types/newsletter";

import { useSearchParams } from "next/navigation";

import DigestStudioHeader from
  "@/components/digest/studio/DigestStudioHeader";
/* ========================================================= */

export default function DigestPage() {

  const searchParams =
    useSearchParams();

  const idDigest =
    searchParams.get(
      "id_digest"
    );

  /* =======================================================
     USER
  ======================================================= */

  const [
    selectedUser,
    setSelectedUser,
  ] = useState<
    DigestUser | null
  >(null);

  const [
    digestId,
    setDigestId,
  ] = useState<
    string | null
  >(null);

  const [
    digestName,
    setDigestName,
  ] = useState("");

  /* =======================================================
     HEADER CONFIG
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
     UI
  ======================================================= */

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
    summary,
    setSummary,
  ] = useState("");

  const [
    implications,
    setImplications,
  ] = useState("");

  const [
    lastSentAt,
    setLastSentAt,
  ] = useState<
    string | null
  >(null);

  /* =======================================================
     FLOW
  ======================================================= */

  const [
    editorialOrder,
    setEditorialOrder,
  ] = useState<
    DigestEditorialItem[]
  >([]);

  const [
    editorialHtml,
    setEditorialHtml,
  ] = useState("");

  /* =======================================================
     LOAD DIGEST
  ======================================================= */

  async function loadDigest(
    userId: string
  ) {

    try {

      setLoading(true);

      const response =
        await api.get(
          `/digest/my-feed?user_id=${userId}`
        );

      console.log("RAW RESPONSE");
      console.log(response);

      console.log("RAW RESULT");
      console.log(response?.result);

      console.log("RAW CONTENTS");
      console.log(response?.result?.contents);

      console.log(
        "DIGEST RESPONSE",
        response
      );

      const result =
        response?.result
          ? response.result
          : response || {};

      console.log(
        "DIGEST RESULT",
        result
      );

      const digestContents =
        result?.contents ||
        [];

      console.log(
        "DIGEST CONTENTS",
        digestContents
      );

      setContents(
        digestContents
      );

      setSummary(
        result?.summary || ""
      );

      setImplications(
        result?.implications || ""
      );

      setLastSentAt(
        result?.last_sent_at ||
        null
      );

      /* ===============================================
         AUTO SELECT ALL
      =============================================== */

      setEditorialOrder(

        digestContents.map(
          (
            item: DigestContentItem
          ) => ({
            id: item.id,

            type:
              "content",
          })
        )
      );

    } catch (
      error
    ) {

      console.error(
        "Digest load error",
        error
      );

    } finally {

      setLoading(false);
    }
  }

  async function loadStoredDigest(
    digestId: string
  ) {

    try {

      setLoading(true);

      const response =
        await api.get(
          `/digest/${digestId}`
        );

      const result =
        response?.result || {};

      const digest =
        result?.digest || {};

      const digestContents =
        result?.contents || [];

      setDigestId(
        digest.ID_DIGEST
      );

      setDigestName(
        digest.DIGEST_NAME || ""
      );

      setSummary(
        digest.SUMMARY || ""
      );

      setImplications(
        digest.IMPLICATIONS || ""
      );

      setContents(
        digestContents
      );

      setEditorialOrder(

        digestContents.map(
          (
            item: DigestContentItem
          ) => ({
            id: item.id,
            type: "content",
          })
        )
      );

    } catch (error) {

      console.error(
        "Digest load error",
        error
      );

    } finally {

      setLoading(false);

    }
  }

  /* =======================================================
     USER SELECT
  ======================================================= */

  async function handleSelectUser(
    user: DigestUser
  ) {

    setSelectedUser(
      user
    );

    await loadDigest(
      user.id_user
    );
  }

    useEffect(() => {

      if (!idDigest) {
        return;
      }

      loadStoredDigest(
        idDigest
      );

    }, [
      idDigest,
    ]);

  /* =======================================================
     SELECTED CONTENTS
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
     FORMAT DATE
  ======================================================= */

  function formatDate(
    value?: string | null
  ) {

    if (!value) {
      return "Jamais";
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

  /* =======================================================
     UI
  ======================================================= */

  return (

    <div className="space-y-4">

      {/* ===================================================
         HEADER
      =================================================== */}

      <div className="flex items-center justify-between">

        <DigestStudioHeader

          digestName={digestName}

          setDigestName={
            setDigestName
          }

          lastSentAt={
            lastSentAt
          }

          isExistingDigest={
            !!digestId
          }

          onSave={
            handleSaveDigest
          }
        />

      {/* ===================================================
         MAIN LAYOUT
      =================================================== */}

      <div className="grid grid-cols-1 xl:grid-cols-[360px_1fr_1.2fr] gap-6 items-start">

        {/* =================================================
           LEFT
        ================================================= */}

        <div className="space-y-5">

          {/* USER SELECTOR */}

          <DigestUserSelector
            selectedUserId={
              selectedUser
                ?.id_user
            }

            onSelectUser={
              handleSelectUser
            }
          />

          {/* CONTENTS */}

          <DigestSelectors
            contents={
              contents
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
           CENTER
        ================================================= */}

        <div className="space-y-5">

          {/* FLOW */}

          <DigestEditorialFlow
            selectedUserId={
              selectedUser?.id_user
            }

            contents={contents}

            editorialOrder={editorialOrder}

            editorialHtml={editorialHtml}

            setEditorialHtml={
              setEditorialHtml
            }

            summary={
              summary
            }

            setSummary={
              setSummary
            }

            implications={
                implications
            }

            setImplications={
              setImplications
            }

            setEditorialOrder={
              setEditorialOrder
            }
          />

          {/* CONFIG */}

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

            summary={
              summary
            }

            implications={
              implications
            }

            contents={
              selectedContents
            }
          />

        </div>

      </div>

      {/* ===================================================
         LOADING
      =================================================== */}

      {loading && (

        <div className="fixed bottom-4 right-4 bg-black text-white text-xs px-3 py-2 rounded-lg shadow-lg z-50">

          Chargement Digest...

        </div>

      )}

    </div>
  );
}
