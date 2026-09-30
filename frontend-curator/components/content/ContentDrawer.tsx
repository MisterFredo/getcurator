"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  useRouter,
  usePathname,
} from "next/navigation";

import {
  X,
  ExternalLink,
  ThumbsUp,
  ThumbsDown,
} from "lucide-react";

import {
  api,
} from "@/lib/api";

import {
  useUser,
} from "@/hooks/useUser";

import {
  getContent,
} from "@/lib/watch";

import {
  useDrawer,
} from "@/contexts/DrawerContext";

import ContentNumbers from "@/components/content/ContentNumbers";

import type {
  Content,
} from "@/types/watch";


/* =========================================================
   FEEDBACK TYPES
========================================================= */

type FeedbackType =
  | "RELEVANT"
  | "NOT_RELEVANT";


type ContentFeedback = {

  id: string;

  user_id: string;

  content_id: string;

  digest_id?: string | null;

  feedback_type: FeedbackType;

  feedback_reason?: string | null;

  source:
    | "DIGEST"
    | "CONTENT_DRAWER";

  is_active: boolean;

};


type CurrentFeedbackResponse = {

  feedback:
    | ContentFeedback
    | null;

};


/* =========================================================
   PROPS
========================================================= */

type Props = {

  contentId: string;

  onClose: () => void;

};


/* =========================================================
   CONTENT DRAWER
========================================================= */

export default function ContentDrawer({
  contentId,
  onClose,
}: Props) {

  const router =
    useRouter();

  const pathname =
    usePathname();

  const {
    rightDrawer,
    closeRightDrawer,
  } = useDrawer();

  const {
    user,
  } = useUser();

  const [
    content,
    setContent,
  ] = useState<
    Content | null
  >(
    null,
  );

  const [
    isOpen,
    setIsOpen,
  ] = useState(
    false,
  );

  const [
    feedback,
    setFeedback,
  ] = useState<
    FeedbackType | null
  >(
    null,
  );

  const [
    feedbackAvailable,
    setFeedbackAvailable,
  ] = useState(
    false,
  );

  const [
    feedbackLoading,
    setFeedbackLoading,
  ] = useState(
    true,
  );

  const [
    feedbackSaving,
    setFeedbackSaving,
  ] = useState(
    false,
  );

  const [
    feedbackError,
    setFeedbackError,
  ] = useState(
    "",
  );


  /* =======================================================
     CLOSE
  ======================================================= */

  function close() {

    setIsOpen(
      false,
    );

    onClose();

    closeRightDrawer();

    if (
      rightDrawer.mode
      === "route"
    ) {

      router.replace(
        pathname,
        {
          scroll: false,
        },
      );

    }

  }


  /* =======================================================
     LOAD CONTENT
  ======================================================= */

  useEffect(() => {

    let cancelled = false;

    async function load() {

      if (!user) {
        return;
      }

      try {

        setContent(
          null,
        );

        setIsOpen(
          false,
        );

        const response =
          await getContent(

            contentId,

            user.user_id,

          );

        if (cancelled) {
          return;
        }

        setContent(
          response,
        );

        requestAnimationFrame(
          () => {

            if (!cancelled) {

              setIsOpen(
                true,
              );

            }

          },
        );

      } catch (error) {

        console.error(
          "❌ ContentDrawer load error",
          error,
        );

      }

    }

    load();

    return () => {

      cancelled = true;

    };

  }, [
    contentId,
    user,
  ]);


  /* =======================================================
     LOAD CURRENT FEEDBACK
  ======================================================= */

  useEffect(() => {

    let cancelled = false;

    async function loadFeedback() {

      if (!user) {

        setFeedbackLoading(
          false,
        );

        setFeedbackAvailable(
          false,
        );

        return;

      }

      try {

        setFeedbackLoading(
          true,
        );

        setFeedbackAvailable(
          false,
        );

        setFeedback(
          null,
        );

        setFeedbackError(
          "",
        );

        const response =
          await api.get(
            `/feedback/current/${encodeURIComponent(
              contentId,
            )}`,
          ) as CurrentFeedbackResponse;

        if (cancelled) {
          return;
        }

        setFeedbackAvailable(
          true,
        );

        setFeedback(
          response.feedback
            ?.feedback_type
          ?? null,
        );

      } catch (error) {

        console.error(
          "Unable to load content feedback",
          error,
        );

        if (!cancelled) {

          setFeedbackAvailable(
            false,
          );

          setFeedback(
            null,
          );

          setFeedbackError(
            "Unable to load your current feedback.",
          );

        }

      } finally {

        if (!cancelled) {

          setFeedbackLoading(
            false,
          );

        }

      }

    }

    loadFeedback();

    return () => {

      cancelled = true;

    };

  }, [
    contentId,
    user,
  ]);


  /* =======================================================
     UPDATE FEEDBACK
  ======================================================= */

  async function handleFeedback(
    nextFeedback: FeedbackType,
  ) {

    if (
      feedbackSaving
      || !feedbackAvailable
      || !user
    ) {
      return;
    }

    try {

      setFeedbackSaving(
        true,
      );

      setFeedbackError(
        "",
      );

      /*
       * Clicking the active choice again
       * removes the current feedback.
       */

      if (
        feedback
        === nextFeedback
      ) {

        await api.delete(
          `/feedback/current/${encodeURIComponent(
            contentId,
          )}`,
        );

        setFeedback(
          null,
        );

        return;

      }

      await api.post(
        "/feedback/",
        {
          content_id:
            contentId,

          feedback_type:
            nextFeedback,

          feedback_reason:
            null,

          source:
            "CONTENT_DRAWER",
        },
      );

      setFeedback(
        nextFeedback,
      );

    } catch (error) {

      console.error(
        "Unable to save content feedback",
        error,
      );

      setFeedbackError(
        "Unable to save your feedback.",
      );

    } finally {

      setFeedbackSaving(
        false,
      );

    }

  }


  /* =======================================================
     LOADING
  ======================================================= */

  if (!content) {

    return (

      <div
        className="
          fixed
          inset-0
          z-[100]
          flex
          items-center
          justify-center
          bg-black/40
        "
      >

        <div
          className="
            rounded
            bg-white
            px-4
            py-2
            text-sm
          "
        >

          Loading…

        </div>

      </div>

    );

  }


  /* =======================================================
     BADGES
  ======================================================= */

  const badges = [

    ...(
      content.companies
      ?? []
    ).map(
      company => ({
        label:
          company.name,

        type:
          "company",
      }),
    ),

    ...(
      content.topics
      ?? []
    ).map(
      topic => ({
        label:
          topic.label,

        type:
          "topic",
      }),
    ),

    ...(
      content.solutions
      ?? []
    ).map(
      solution => ({
        label:
          solution.name,

        type:
          "solution",
      }),
    ),

  ];


  function getBadgeClass(
    type?: string,
  ) {

    switch (type) {

      case "company":

        return (
          "bg-blue-50 text-blue-600 "
          + "border border-blue-100"
        );

      case "solution":

        return (
          "bg-purple-50 text-purple-600 "
          + "border border-purple-100"
        );

      case "topic":

        return (
          "bg-gray-100 text-gray-700 "
          + "border border-gray-200"
        );

      default:

        return (
          "bg-gray-100 text-gray-600"
        );

    }

  }


  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div
      className="
        fixed
        inset-0
        z-[100]
        flex
      "
    >

      <div
        className="
          absolute
          inset-0
          bg-black/40
        "
        onClick={
          close
        }
      />

      <aside
        className={`
          relative
          ml-auto
          w-full
          transform
          overflow-y-auto
          bg-white
          shadow-xl
          transition-transform
          duration-300
          ease-out
          md:w-[780px]
          ${
            isOpen
              ? "translate-x-0"
              : "translate-x-full"
          }
        `}
      >

        {/* =============================================== */}
        {/* HEADER */}
        {/* =============================================== */}

        <div
          className="
            sticky
            top-0
            z-10
            space-y-3
            border-b
            border-gray-200
            bg-white
            px-5
            py-4
          "
        >

          <div
            className="
              flex
              items-start
              justify-between
            "
          >

            <h1
              className="
                max-w-xl
                text-xl
                font-semibold
                text-gray-900
              "
            >

              {content.title}

            </h1>

            <button
              type="button"
              onClick={
                close
              }
              aria-label="Close"
              className="
                rounded
                p-1
                text-gray-500
                hover:bg-gray-100
                hover:text-gray-900
              "
            >

              <X
                size={18}
              />

            </button>

          </div>

          {badges.length > 0 && (

            <div
              className="
                flex
                flex-wrap
                gap-2
              "
            >

              {badges.map(
                (
                  badge,
                  index,
                ) => (

                  <span
                    key={`${badge.label}-${index}`}
                    className={`
                      rounded-full
                      px-2
                      py-0.5
                      text-[10px]
                      uppercase
                      tracking-wide
                      ${getBadgeClass(
                        badge.type,
                      )}
                    `}
                  >

                    {badge.label}

                  </span>

                ),
              )}

            </div>

          )}

          {content.source_url && (

            <div
              className="
                flex
                items-center
              "
            >

              <a
                href={
                  content.source_url
                }
                target="_blank"
                rel="noopener noreferrer"
                className="
                  inline-flex
                  items-center
                  gap-1
                  text-xs
                  text-blue-600
                  hover:text-blue-800
                  hover:underline
                "
              >

                <ExternalLink
                  size={12}
                />

                {
                  content.source_title
                  || "Read source article"
                }

              </a>

            </div>

          )}

        </div>

        {/* =============================================== */}
        {/* CONTENT */}
        {/* =============================================== */}

        <div
          className="
            space-y-8
            px-5
            py-6
          "
        >

          {content.excerpt && (

            <p
              className="
                max-w-2xl
                text-base
                font-medium
                text-gray-800
              "
            >

              {content.excerpt}

            </p>

          )}

          {content.content_body && (

            <div
              className="
                prose
                prose-sm
                max-w-none
              "
              dangerouslySetInnerHTML={{
                __html:
                  content.content_body,
              }}
            />

          )}

          {content.signal_analytique && (

            <div
              className="
                rounded
                border
                border-teal-100
                bg-teal-50
                p-4
              "
            >

              <h3
                className="
                  mb-1
                  text-xs
                  uppercase
                  text-teal-600
                "
              >

                Insight

              </h3>

              <p
                className="
                  text-sm
                  text-teal-800
                "
              >

                {
                  content.signal_analytique
                }

              </p>

            </div>

          )}

          {/* ============================================= */}
          {/* STRUCTURED CONCEPTS */}
          {/* ============================================= */}

          {(
            content.concepts
            ?.length
            ?? 0
          ) > 0 && (

            <div>

              <h3
                className="
                  mb-2
                  text-xs
                  uppercase
                  text-gray-500
                "
              >

                Key Concepts

              </h3>

              <div
                className="
                  flex
                  flex-wrap
                  gap-2
                "
              >

                {content.concepts?.map(
                  concept => (

                    <span
                      key={
                        concept.id_concept
                      }
                      className="
                        rounded
                        bg-gray-200
                        px-2
                        py-1
                        text-xs
                        text-gray-800
                      "
                    >

                      {concept.label}

                    </span>

                  ),
                )}

              </div>

            </div>

          )}

          {content.mecanique_expliquee && (

            <div>

              <h3
                className="
                  mb-2
                  text-xs
                  uppercase
                  text-gray-500
                "
              >

                Mechanism Explained

              </h3>

              <p
                className="
                  text-sm
                  text-gray-700
                "
              >

                {
                  content.mecanique_expliquee
                }

              </p>

            </div>

          )}

          {content.enjeu_strategique && (

            <div>

              <h3
                className="
                  mb-2
                  text-xs
                  uppercase
                  text-gray-500
                "
              >

                Strategic Implication

              </h3>

              <p
                className="
                  text-sm
                  text-gray-700
                "
              >

                {
                  content.enjeu_strategique
                }

              </p>

            </div>

          )}

          {content.point_de_friction && (

            <div>

              <h3
                className="
                  mb-2
                  text-xs
                  uppercase
                  text-gray-500
                "
              >

                Friction Point

              </h3>

              <p
                className="
                  text-sm
                  text-gray-700
                "
              >

                {
                  content.point_de_friction
                }

              </p>

            </div>

          )}

          <ContentNumbers
            numbers={
              content.numbers
            }
          />

          {(
            content.acteurs_cites
            ?.length
            ?? 0
          ) > 0 && (

            <div
              className="
                text-sm
                text-gray-600
              "
            >

              <strong>
                Actors:
              </strong>{" "}

              {
                content.acteurs_cites
                  ?.join(
                    ", ",
                  )
              }

            </div>

          )}

          {/* ============================================= */}
          {/* CONTENT FEEDBACK */}
          {/* ============================================= */}

          <div
            className="
              border-t
              border-gray-200
              pt-6
            "
          >

            <div
              className="
                flex
                flex-col
                gap-4
                sm:flex-row
                sm:items-center
                sm:justify-between
              "
            >

              <div>

                <h3
                  className="
                    text-sm
                    font-semibold
                    text-gray-900
                  "
                >

                  Was this useful?

                </h3>

                <p
                  className="
                    mt-1
                    text-xs
                    text-gray-500
                  "
                >

                  Your feedback helps improve
                  your future Digests.

                </p>

              </div>

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
                    feedbackSaving
                    || feedbackLoading
                    || !feedbackAvailable
                  }
                  onClick={() =>
                    handleFeedback(
                      "RELEVANT",
                    )
                  }
                  className={`
                    inline-flex
                    items-center
                    gap-2
                    rounded-lg
                    border
                    px-3
                    py-2
                    text-sm
                    font-medium
                    transition
                    disabled:cursor-not-allowed
                    disabled:opacity-50
                    ${
                      feedback
                      === "RELEVANT"
                        ? `
                          border-emerald-600
                          bg-emerald-600
                          text-white
                        `
                        : `
                          border-gray-200
                          bg-white
                          text-gray-700
                          hover:border-emerald-300
                          hover:text-emerald-700
                        `
                    }
                  `}
                >

                  <ThumbsUp
                    size={15}
                  />

                  Relevant

                </button>

                <button
                  type="button"
                  disabled={
                    feedbackSaving
                    || feedbackLoading
                    || !feedbackAvailable
                  }
                  onClick={() =>
                    handleFeedback(
                      "NOT_RELEVANT",
                    )
                  }
                  className={`
                    inline-flex
                    items-center
                    gap-2
                    rounded-lg
                    border
                    px-3
                    py-2
                    text-sm
                    font-medium
                    transition
                    disabled:cursor-not-allowed
                    disabled:opacity-50
                    ${
                      feedback
                      === "NOT_RELEVANT"
                        ? `
                          border-slate-700
                          bg-slate-700
                          text-white
                        `
                        : `
                          border-gray-200
                          bg-white
                          text-gray-700
                          hover:border-slate-400
                          hover:text-slate-900
                        `
                    }
                  `}
                >

                  <ThumbsDown
                    size={15}
                  />

                  Not relevant

                </button>

              </div>

            </div>

            {feedbackLoading && (

              <p
                className="
                  mt-3
                  text-xs
                  text-gray-400
                "
              >

                Loading your feedback…

              </p>

            )}

            {feedbackError && (

              <p
                className="
                  mt-3
                  text-xs
                  text-red-600
                "
              >

                {feedbackError}

              </p>

            )}

            {(
              feedback
              && !feedbackLoading
              && !feedbackError
            ) && (

              <p
                className="
                  mt-3
                  text-xs
                  text-gray-400
                "
              >

                Click the selected option again
                to undo your feedback.

              </p>

            )}

          </div>

          {/* ============================================= */}
          {/* PUBLICATION DATE */}
          {/* ============================================= */}

          {content.published_at && (

            <div
              className="
                border-t
                pt-4
                text-xs
                text-gray-400
              "
            >

              Published on{" "}

              {
                new Date(
                  content.published_at,
                ).toLocaleDateString(
                  "en-GB",
                )
              }

            </div>

          )}

        </div>

      </aside>

    </div>

  );

}
