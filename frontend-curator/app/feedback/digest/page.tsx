"use client";

import {
  Suspense,
  useEffect,
  useState,
} from "react";

import {
  useSearchParams,
} from "next/navigation";

import {
  api,
} from "@/lib/api";


/* =========================================================
   TYPES
========================================================= */

type FeedbackReason =
  | "WRONG_TOPIC"
  | "WRONG_MARKET"
  | "WRONG_COMPANY"
  | "TOO_GENERAL"
  | "ALREADY_KNOWN"
  | "OTHER";


type FeedbackPreview = {

  token: string;

  digest_id: string;

  content_id: string;

  content_title: string;

  language:
    | "fr"
    | "en";

  feedback_type:
    "NOT_RELEVANT";

  already_recorded: boolean;

};


type FeedbackResponse = {

  status:
    | "recorded"
    | "updated"
    | "removed"
    | "unchanged";

  content_id: string;

  feedback_type?:
    | "RELEVANT"
    | "NOT_RELEVANT"
    | null;

  feedback_reason?:
    | FeedbackReason
    | null;

  source?:
    | "DIGEST"
    | "CONTENT_DRAWER"
    | null;

  is_active: boolean;

  message: string;

};


/* =========================================================
   COPY
========================================================= */

const COPY = {

  en: {

    loading:
      "Loading feedback page…",

    invalidTitle:
      "This feedback link is unavailable",

    invalidDescription:
      "The link may be invalid or may have expired.",

    title:
      "Not relevant for you?",

    description:
      "Confirming this will help improve your future Digests.",

    alreadyRecorded:
      "You already marked this article as not relevant.",

    reasonTitle:
      "Why was it not relevant?",

    reasonOptional:
      "Optional",

    reasons: {

      WRONG_TOPIC:
        "Wrong topic",

      WRONG_MARKET:
        "Wrong market",

      WRONG_COMPANY:
        "Wrong company or platform",

      TOO_GENERAL:
        "Too general",

      ALREADY_KNOWN:
        "Already known",

      OTHER:
        "Other reason",

    },

    confirm:
      "Confirm",

    confirming:
      "Saving…",

    cancel:
      "Cancel",

    successTitle:
      "Feedback saved",

    successDescription:
      "This feedback will help improve your future Digests.",

    undo:
      "Undo",

    undoing:
      "Undoing…",

    undoneTitle:
      "Feedback removed",

    undoneDescription:
      "This article is no longer marked as not relevant.",

    error:
      "Unable to save your feedback. Please try again.",

  },

  fr: {

    loading:
      "Chargement…",

    invalidTitle:
      "Ce lien de feedback n’est pas disponible",

    invalidDescription:
      "Le lien est peut-être invalide ou expiré.",

    title:
      "Ce contenu n’est pas pertinent pour vous ?",

    description:
      "Votre retour permettra d’améliorer vos prochains Digests.",

    alreadyRecorded:
      "Vous avez déjà indiqué que cet article n’était pas pertinent.",

    reasonTitle:
      "Pourquoi n’était-il pas pertinent ?",

    reasonOptional:
      "Facultatif",

    reasons: {

      WRONG_TOPIC:
        "Mauvais sujet",

      WRONG_MARKET:
        "Mauvais marché",

      WRONG_COMPANY:
        "Mauvaise entreprise ou plateforme",

      TOO_GENERAL:
        "Trop général",

      ALREADY_KNOWN:
        "Déjà connu",

      OTHER:
        "Autre raison",

    },

    confirm:
      "Confirmer",

    confirming:
      "Enregistrement…",

    cancel:
      "Annuler",

    successTitle:
      "Retour enregistré",

    successDescription:
      "Ce retour permettra d’améliorer vos prochains Digests.",

    undo:
      "Annuler ce retour",

    undoing:
      "Annulation…",

    undoneTitle:
      "Retour annulé",

    undoneDescription:
      "Ce contenu n’est plus marqué comme non pertinent.",

    error:
      "Impossible d’enregistrer votre retour. Réessayez.",

  },

};


/* =========================================================
   FEEDBACK CONTENT
========================================================= */

function DigestFeedbackContent() {

  const searchParams =
    useSearchParams();

  const token =
    searchParams.get(
      "token",
    )
    ?? "";

  const [
    preview,
    setPreview,
  ] = useState<
    FeedbackPreview | null
  >(
    null,
  );

  const [
    reason,
    setReason,
  ] = useState<
    FeedbackReason | null
  >(
    null,
  );

  const [
    loading,
    setLoading,
  ] = useState(
    true,
  );

  const [
    saving,
    setSaving,
  ] = useState(
    false,
  );

  const [
    saved,
    setSaved,
  ] = useState(
    false,
  );

  const [
    removed,
    setRemoved,
  ] = useState(
    false,
  );

  const [
    error,
    setError,
  ] = useState(
    "",
  );


  /* =======================================================
     LOAD PREVIEW
  ======================================================= */

  useEffect(() => {

    let cancelled = false;

    async function loadPreview() {

      if (!token) {

        setError(
          "INVALID_LINK",
        );

        setLoading(
          false,
        );

        return;

      }

      try {

        setLoading(
          true,
        );

        setError(
          "",
        );

        const response =
          await api.get(
            `/feedback/digest/${encodeURIComponent(
              token,
            )}`,
          );

        if (cancelled) {
          return;
        }

        const nextPreview =
          response as FeedbackPreview;

        setPreview(
          nextPreview,
        );

        setSaved(
          Boolean(
            nextPreview
              .already_recorded,
          ),
        );

      } catch (loadError) {

        console.error(
          loadError,
        );

        if (!cancelled) {

          setError(
            "INVALID_LINK",
          );

        }

      } finally {

        if (!cancelled) {

          setLoading(
            false,
          );

        }

      }

    }

    loadPreview();

    return () => {

      cancelled = true;

    };

  }, [token]);


  /* =======================================================
     CONFIRM
  ======================================================= */

  async function confirmFeedback() {

    if (
      !preview
      || saving
    ) {
      return;
    }

    try {

      setSaving(
        true,
      );

      setError(
        "",
      );

      await api.post(
        "/feedback/digest/confirm",
        {
          token:
            preview.token,

          feedback_reason:
            reason,
        },
      ) as FeedbackResponse;

      setSaved(
        true,
      );

      setRemoved(
        false,
      );

    } catch (saveError) {

      console.error(
        saveError,
      );

      setError(
        "SAVE_ERROR",
      );

    } finally {

      setSaving(
        false,
      );

    }

  }


  /* =======================================================
     UNDO
  ======================================================= */

  async function undoFeedback() {

    if (
      !preview
      || saving
    ) {
      return;
    }

    try {

      setSaving(
        true,
      );

      setError(
        "",
      );

      await api.post(
        "/feedback/digest/undo",
        {
          token:
            preview.token,

          feedback_reason:
            null,
        },
      ) as FeedbackResponse;

      setSaved(
        false,
      );

      setRemoved(
        true,
      );

      setReason(
        null,
      );

    } catch (undoError) {

      console.error(
        undoError,
      );

      setError(
        "SAVE_ERROR",
      );

    } finally {

      setSaving(
        false,
      );

    }

  }


  /* =======================================================
     LANGUAGE
  ======================================================= */

  const language =
    preview?.language
    === "fr"
      ? "fr"
      : "en";

  const copy =
    COPY[
      language
    ];


  /* =======================================================
     LOADING
  ======================================================= */

  if (loading) {

    return (

      <FeedbackLayout>

        <p className="text-sm text-slate-500">

          {COPY.en.loading}

        </p>

      </FeedbackLayout>

    );

  }


  /* =======================================================
     INVALID LINK
  ======================================================= */

  if (
    !preview
    || error === "INVALID_LINK"
  ) {

    return (

      <FeedbackLayout>

        <h1
          className="
            text-2xl
            font-semibold
            text-slate-900
          "
        >

          {COPY.en.invalidTitle}

        </h1>

        <p
          className="
            mt-3
            text-sm
            leading-6
            text-slate-600
          "
        >

          {COPY.en.invalidDescription}

        </p>

      </FeedbackLayout>

    );

  }


  /* =======================================================
     SUCCESS / UNDO
  ======================================================= */

  if (saved) {

    return (

      <FeedbackLayout>

        <StatusIcon>
          ✓
        </StatusIcon>

        <h1
          className="
            mt-5
            text-2xl
            font-semibold
            text-slate-900
          "
        >

          {copy.successTitle}

        </h1>

        <p
          className="
            mt-3
            text-sm
            leading-6
            text-slate-600
          "
        >

          {copy.successDescription}

        </p>

        <ArticleTitle
          title={
            preview.content_title
          }
        />

        {error === "SAVE_ERROR" && (

          <ErrorMessage
            message={
              copy.error
            }
          />

        )}

        <button
          type="button"
          disabled={saving}
          onClick={
            undoFeedback
          }
          className="
            mt-6
            text-sm
            font-medium
            text-slate-500
            underline
            underline-offset-4
            hover:text-slate-900
            disabled:cursor-not-allowed
            disabled:opacity-50
          "
        >

          {saving
            ? copy.undoing
            : copy.undo}

        </button>

      </FeedbackLayout>

    );

  }


  /* =======================================================
     CONFIRMATION
  ======================================================= */

  return (

    <FeedbackLayout>

      {removed && (

        <div
          className="
            mb-6
            rounded-lg
            border
            border-emerald-200
            bg-emerald-50
            px-4
            py-3
          "
        >

          <p
            className="
              text-sm
              font-medium
              text-emerald-900
            "
          >

            {copy.undoneTitle}

          </p>

          <p
            className="
              mt-1
              text-sm
              text-emerald-700
            "
          >

            {copy.undoneDescription}

          </p>

        </div>

      )}

      <h1
        className="
          text-2xl
          font-semibold
          text-slate-900
        "
      >

        {copy.title}

      </h1>

      <p
        className="
          mt-3
          text-sm
          leading-6
          text-slate-600
        "
      >

        {copy.description}

      </p>

      <ArticleTitle
        title={
          preview.content_title
        }
      />

      <div className="mt-7">

        <div
          className="
            flex
            items-baseline
            gap-2
          "
        >

          <h2
            className="
              text-sm
              font-semibold
              text-slate-900
            "
          >

            {copy.reasonTitle}

          </h2>

          <span
            className="
              text-xs
              text-slate-400
            "
          >

            {copy.reasonOptional}

          </span>

        </div>

        <div
          className="
            mt-3
            flex
            flex-wrap
            gap-2
          "
        >

          {(
            Object.keys(
              copy.reasons,
            ) as FeedbackReason[]
          ).map(
            value => {

              const selected =
                reason === value;

              return (

                <button
                  key={value}
                  type="button"
                  onClick={() =>
                    setReason(
                      selected
                        ? null
                        : value,
                    )
                  }
                  className={`
                    rounded-full
                    border
                    px-3
                    py-2
                    text-sm
                    transition
                    ${
                      selected
                        ? `
                          border-slate-900
                          bg-slate-900
                          text-white
                        `
                        : `
                          border-slate-200
                          bg-white
                          text-slate-700
                          hover:border-slate-400
                        `
                    }
                  `}
                >

                  {
                    copy.reasons[
                      value
                    ]
                  }

                </button>

              );

            },
          )}

        </div>

      </div>

      {error === "SAVE_ERROR" && (

        <ErrorMessage
          message={
            copy.error
          }
        />

      )}

      <div
        className="
          mt-8
          flex
          flex-wrap
          items-center
          gap-4
        "
      >

        <button
          type="button"
          disabled={saving}
          onClick={
            confirmFeedback
          }
          className="
            rounded-lg
            bg-slate-900
            px-5
            py-3
            text-sm
            font-semibold
            text-white
            hover:bg-slate-700
            disabled:cursor-not-allowed
            disabled:opacity-50
          "
        >

          {saving
            ? copy.confirming
            : copy.confirm}

        </button>

        <a
          href="/"
          className="
            text-sm
            font-medium
            text-slate-500
            hover:text-slate-900
          "
        >

          {copy.cancel}

        </a>

      </div>

    </FeedbackLayout>

  );

}


/* =========================================================
   LAYOUT
========================================================= */

function FeedbackLayout({
  children,
}: {
  children: React.ReactNode;
}) {

  return (

    <main
      className="
        min-h-screen
        bg-slate-50
        px-4
        py-12
      "
    >

      <div
        className="
          mx-auto
          max-w-xl
          rounded-2xl
          border
          border-slate-200
          bg-white
          p-7
          shadow-sm
          sm:p-10
        "
      >

        <div
          className="
            mb-8
            text-sm
            font-semibold
            tracking-wide
            text-slate-900
          "
        >

          GetCurator

        </div>

        {children}

      </div>

    </main>

  );

}


/* =========================================================
   ARTICLE TITLE
========================================================= */

function ArticleTitle({
  title,
}: {
  title: string;
}) {

  return (

    <div
      className="
        mt-6
        rounded-xl
        border
        border-slate-200
        bg-slate-50
        p-4
      "
    >

      <p
        className="
          text-sm
          font-medium
          leading-6
          text-slate-900
        "
      >

        {title}

      </p>

    </div>

  );

}


/* =========================================================
   STATUS ICON
========================================================= */

function StatusIcon({
  children,
}: {
  children: React.ReactNode;
}) {

  return (

    <div
      className="
        flex
        h-12
        w-12
        items-center
        justify-center
        rounded-full
        bg-emerald-100
        text-xl
        font-semibold
        text-emerald-700
      "
    >

      {children}

    </div>

  );

}


/* =========================================================
   ERROR MESSAGE
========================================================= */

function ErrorMessage({
  message,
}: {
  message: string;
}) {

  return (

    <p
      className="
        mt-5
        rounded-lg
        border
        border-red-200
        bg-red-50
        px-4
        py-3
        text-sm
        text-red-700
      "
    >

      {message}

    </p>

  );

}


/* =========================================================
   PAGE
========================================================= */

export default function DigestFeedbackPage() {

  return (

    <Suspense
      fallback={

        <FeedbackLayout>

          <p className="text-sm text-slate-500">

            Loading feedback page…

          </p>

        </FeedbackLayout>

      }
    >

      <DigestFeedbackContent />

    </Suspense>

  );

}
