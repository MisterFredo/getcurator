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


const RELEVANCE_FILTERS: Array<{
  value: RelevanceFilter;
  label: string;
}> = [
  {
    value: "ALL",
    label: "All",
  },
  {
    value: "DIRECT",
    label: "Direct",
  },
  {
    value: "CONTEXT",
    label: "Context",
  },
  {
    value: "RELATED",
    label: "Related",
  },
  {
    value: "OUT_OF_SCOPE",
    label: "Out of scope",
  },
];


function getRelevanceOrder(
  relevance?: TouchContentRelevance,
) {

  if (relevance === "DIRECT") {
    return 0;
  }

  if (relevance === "CONTEXT") {
    return 1;
  }

  if (relevance === "RELATED") {
    return 2;
  }

  if (relevance === "OUT_OF_SCOPE") {
    return 3;
  }

  return 4;

}


function getDateValue(
  value: string | null,
) {

  if (!value) {
    return 0;
  }

  const timestamp =
    new Date(value).getTime();

  return Number.isNaN(timestamp)
    ? 0
    : timestamp;

}


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
      () =>
        new Set(
          selectedContentIds,
        ),
      [
        selectedContentIds,
      ],
    );

  const dismissedIds =
    useMemo(
      () =>
        new Set(
          dismissedContentIds,
        ),
      [
        dismissedContentIds,
      ],
    );

  const counts =
    useMemo(() => {

      const result:
        Record<
          RelevanceFilter,
          number
        > = {
          ALL: candidates.length,
          DIRECT: 0,
          CONTEXT: 0,
          RELATED: 0,
          OUT_OF_SCOPE: 0,
        };

      candidates.forEach(
        candidate => {

          const decision =
            decisionsByContentId.get(
              candidate.content_id,
            );

          if (decision) {

            result[
              decision.relevance
            ] += 1;

          }

        },
      );

      return result;

    }, [
      candidates,
      decisionsByContentId,
    ]);

  const visibleCandidates =
    useMemo(() => {

      const result =
        candidates.filter(
          candidate => {

            if (
              relevanceFilter === "ALL"
            ) {
              return true;
            }

            return (
              decisionsByContentId.get(
                candidate.content_id,
              )?.relevance
              === relevanceFilter
            );

          },
        );

      result.sort(
        (
          left,
          right,
        ) => {

          if (
            sortMode === "DATE_DESC"
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
            sortMode === "DATE_ASC"
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

          const leftDecision =
            decisionsByContentId.get(
              left.content_id,
            );

          const rightDecision =
            decisionsByContentId.get(
              right.content_id,
            );

          const relevanceDifference =
            getRelevanceOrder(
              leftDecision?.relevance,
            )
            - getRelevanceOrder(
              rightDecision?.relevance,
            );

          if (
            relevanceDifference !== 0
          ) {
            return relevanceDifference;
          }

          const leftScore =
            leftDecision
              ?.relevance_score
            ?? -1;

          const rightScore =
            rightDecision
              ?.relevance_score
            ?? -1;

          if (
            leftScore !== rightScore
          ) {
            return rightScore - leftScore;
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

      return result;

    }, [
      candidates,
      decisionsByContentId,
      relevanceFilter,
      sortMode,
    ]);

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

  return (

    <section className="space-y-4">

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
              {" displayed out of "}
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

        <div className="flex flex-wrap gap-2">

          {RELEVANCE_FILTERS.map(
            filter => {

              const active =
                relevanceFilter
                === filter.value;

              return (

                <button
                  key={filter.value}
                  type="button"
                  onClick={() =>
                    setRelevanceFilter(
                      filter.value,
                    )
                  }
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
                    {filter.label}
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
                    {counts[filter.value]}
                  </span>

                </button>

              );

            },
          )}

        </div>

      </div>

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

              return (

                <TouchCandidateCard
                  key={contentId}
                  candidate={candidate}
                  decision={
                    decisionsByContentId.get(
                      contentId,
                    )
                    ?? null
                  }
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
