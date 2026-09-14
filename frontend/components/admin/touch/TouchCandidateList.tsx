"use client";

import {
  useMemo,
  useState,
} from "react";

import TouchCandidateCard from "@/components/admin/touch/TouchCandidateCard";

import type {
  TouchContentCandidate,
  TouchContentDecision,
  TouchContentRelevance,
} from "@/types/touch";


/* =========================================================
   TYPES
========================================================= */

type RelevanceFilter =
  | "ALL"
  | TouchContentRelevance;

type SortMode =
  | "RELEVANCE"
  | "DATE_DESC"
  | "DATE_ASC";


type Props = {
  candidates: TouchContentCandidate[];

  decisionsByContentId: Map<
    string,
    TouchContentDecision
  >;

  selectedContentIds: string[];
  dismissedContentIds: string[];

  onToggleContent: (
    contentId: string
  ) => void;

  onDismissContent: (
    contentId: string
  ) => void;

  onRestoreContent: (
    contentId: string
  ) => void;

  onOpenContent?: (
    contentId: string
  ) => void;
};


/* =========================================================
   RELEVANCE ORDER
========================================================= */

function getRelevanceOrder(
  relevance:
    TouchContentRelevance | null,
): number {

  const order:
    Record<
      TouchContentRelevance,
      number
    > = {

      DIRECT: 0,
      CONTEXT: 1,
      RELATED: 2,
      OUT_OF_SCOPE: 3,

    };

  if (!relevance) {
    return 4;
  }

  return order[
    relevance
  ];

}


/* =========================================================
   DATE VALUE
========================================================= */

function getDateValue(
  publishedAt: string | null,
): number {

  if (!publishedAt) {
    return 0;
  }

  const value =
    new Date(
      publishedAt,
    ).getTime();

  return Number.isNaN(
    value,
  )
    ? 0
    : value;

}


/* =========================================================
   COMPONENT
========================================================= */

export default function TouchCandidateList({
  candidates,
  decisionsByContentId,

  selectedContentIds,
  dismissedContentIds,

  onToggleContent,
  onDismissContent,
  onRestoreContent,

  onOpenContent,
}: Props) {

  const [
    relevanceFilter,
    setRelevanceFilter,
  ] = useState<RelevanceFilter>(
    "ALL",
  );

  const [
    sortMode,
    setSortMode,
  ] = useState<SortMode>(
    "RELEVANCE",
  );

  const selectedIds =
    useMemo(
      () => new Set(
        selectedContentIds,
      ),
      [
        selectedContentIds,
      ],
    );

  const dismissedIds =
    useMemo(
      () => new Set(
        dismissedContentIds,
      ),
      [
        dismissedContentIds,
      ],
    );

  /* =======================================================
     COUNTS
  ======================================================= */

  const counts =
    useMemo(() => {

      const result = {
        ALL: candidates.length,
        DIRECT: 0,
        CONTEXT: 0,
        RELATED: 0,
        OUT_OF_SCOPE: 0,
      };

      for (const candidate of candidates) {

        const decision =
          decisionsByContentId.get(
            candidate.content_id,
          );

        if (!decision) {
          continue;
        }

        result[
          decision.relevance
        ] += 1;

      }

      return result;

    }, [
      candidates,
      decisionsByContentId,
    ]);

  /* =======================================================
     FILTERED AND SORTED
  ======================================================= */

  const visibleCandidates =
    useMemo(() => {

      const filtered =
        candidates.filter(
          candidate => {

            if (
              relevanceFilter
              === "ALL"
            ) {
              return true;
            }

            const decision =
              decisionsByContentId.get(
                candidate.content_id,
              );

            return (
              decision?.relevance
              === relevanceFilter
            );

          },
        );

      return [
        ...filtered,
      ].sort(
        (
          left,
          right,
        ) => {

          const leftDecision =
            decisionsByContentId.get(
              left.content_id,
            );

          const rightDecision =
            decisionsByContentId.get(
              right.content_id,
            );

          if (
            sortMode
            === "DATE_DESC"
          ) {

            return (

              getDateValue(
                right.published_at,
              )

              - getDateValue(
                left.published_at,
              )

            );

          }

          if (
            sortMode
            === "DATE_ASC"
          ) {

            return (

              getDateValue(
                left.published_at,
              )

              - getDateValue(
                right.published_at,
              )

            );

          }

          const relevanceDifference = (

            getRelevanceOrder(
              leftDecision?.relevance
              ?? null,
            )

            - getRelevanceOrder(
              rightDecision?.relevance
              ?? null,
            )

          );

          if (
            relevanceDifference !== 0
          ) {
            return relevanceDifference;
          }

          const scoreDifference = (

            (
              rightDecision
                ?.relevance_score
              ?? -1
            )

            - (
              leftDecision
                ?.relevance_score
              ?? -1
            )

          );

          if (
            scoreDifference !== 0
          ) {
            return scoreDifference;
          }

          return (

            getDateValue(
              right.published_at,
            )

            - getDateValue(
              left.published_at,
            )

          );

        },
      );

    }, [
      candidates,
      decisionsByContentId,
      relevanceFilter,
      sortMode,
    ]);

  /* =======================================================
     EMPTY
  ======================================================= */

  if (
    candidates.length === 0
  ) {

    return (

      <div
        className="
          rounded-xl
          border
          border-dashed
          border-gray-300
          bg-white
          px-6
          py-16
          text-center
        "
      >

        <p className="text-sm font-medium text-gray-700">
          No content proposed yet
        </p>

        <p className="mt-1 text-sm text-gray-500">
          Start an editorial research to retrieve
          contents from GetCurator.
        </p>

      </div>

    );

  }

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <section className="space-y-4">

      {/* ================================================= */}
      {/* TOOLBAR */}
      {/* ================================================= */}

      <div
        className="
          rounded-xl
          border
          border-gray-200
          bg-white
          p-4
          space-y-4
        "
      >

        <div
          className="
            flex
            flex-wrap
            items-center
            justify-between
            gap-4
          "
        >

          <div>

            <h2 className="text-lg font-semibold text-gray-900">
              Proposed contents
            </h2>

            <p className="mt-1 text-sm text-gray-500">

              {visibleCandidates.length}
              {" "}
              displayed out of
              {" "}
              {candidates.length}

            </p>

          </div>

          <select
            value={sortMode}
            onChange={event =>
              setSortMode(
                event.target.value
                as SortMode,
              )
            }
            className="
              rounded-lg
              border
              border-gray-300
              bg-white
              px-3
              py-2
              text-sm
              text-gray-700
            "
          >
            <option value="RELEVANCE">
              Sort by relevance
            </option>

            <option value="DATE_DESC">
              Most recent first
            </option>

            <option value="DATE_ASC">
              Oldest first
            </option>
          </select>

        </div>

        {/* ================================================= */}
        {/* FILTERS */}
        {/* ================================================= */}

        <div className="flex flex-wrap gap-2">

          <FilterButton
            active={
              relevanceFilter === "ALL"
            }
            label="All"
            count={counts.ALL}
            onClick={() =>
              setRelevanceFilter(
                "ALL",
              )
            }
          />

          <FilterButton
            active={
              relevanceFilter
              === "DIRECT"
            }
            label="Direct"
            count={counts.DIRECT}
            onClick={() =>
              setRelevanceFilter(
                "DIRECT",
              )
            }
          />

          <FilterButton
            active={
              relevanceFilter
              === "CONTEXT"
            }
            label="Context"
            count={counts.CONTEXT}
            onClick={() =>
              setRelevanceFilter(
                "CONTEXT",
              )
            }
          />

          <FilterButton
            active={
              relevanceFilter
              === "RELATED"
            }
            label="Related"
            count={counts.RELATED}
            onClick={() =>
              setRelevanceFilter(
                "RELATED",
              )
            }
          />

          <FilterButton
            active={
              relevanceFilter
              === "OUT_OF_SCOPE"
            }
            label="Out of scope"
            count={
              counts.OUT_OF_SCOPE
            }
            onClick={() =>
              setRelevanceFilter(
                "OUT_OF_SCOPE",
              )
            }
          />

        </div>

      </div>

      {/* ================================================= */}
      {/* RESULTS */}
      {/* ================================================= */}

      {visibleCandidates.length === 0 ? (

        <div
          className="
            rounded-xl
            border
            border-dashed
            border-gray-300
            bg-white
            px-6
            py-12
            text-center
            text-sm
            text-gray-500
          "
        >
          No content matches this display filter.
        </div>

      ) : (

        <div className="space-y-4">

          {visibleCandidates.map(
            candidate => {

              const contentId =
                candidate.content_id;

              const decision =
                decisionsByContentId.get(
                  contentId,
                )
                ?? null;

              return (

                <TouchCandidateCard
                  key={contentId}
                  candidate={candidate}
                  decision={decision}
                  selected={
                    selectedIds.has(
                      contentId,
                    )
                  }
                  dismissed={
                    dismissedIds.has(
                      contentId,
                    )
                  }
                  onToggle={() =>
                    onToggleContent(
                      contentId,
                    )
                  }
                  onDismiss={() =>
                    onDismissContent(
                      contentId,
                    )
                  }
                  onRestore={() =>
                    onRestoreContent(
                      contentId,
                    )
                  }
                  onOpen={
                    onOpenContent
                      ? () =>
                          onOpenContent(
                            contentId,
                          )
                      : undefined
                  }
                />

              );

            },
          )}

        </div>

      )}

    </section>

  );

}


/* =========================================================
   FILTER BUTTON
========================================================= */

type FilterButtonProps = {
  active: boolean;
  label: string;
  count: number;
  onClick: () => void;
};


function FilterButton({
  active,
  label,
  count,
  onClick,
}: FilterButtonProps) {

  return (

    <button
      type="button"
      onClick={onClick}
      className={`
        inline-flex
        items-center
        gap-2
        rounded-full
        border
        px-3
        py-1.5
        text-sm
        transition
        ${
          active
            ? (
                "border-ratecard-blue "
                + "bg-ratecard-blue "
                + "text-white"
              )
            : (
                "border-gray-200 "
                + "bg-white "
                + "text-gray-600 "
                + "hover:bg-gray-50"
              )
        }
      `}
    >
      <span>
        {label}
      </span>

      <span
        className={`
          rounded-full
          px-1.5
          py-0.5
          text-xs
          ${
            active
              ? "bg-white/20"
              : "bg-gray-100"
          }
        `}
      >
        {count}
      </span>
    </button>

  );

}
