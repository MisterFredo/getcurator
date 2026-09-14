"use client";

import {
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


function getDateValue(
  value: string | null,
) {

  if (!value) {
    return 0;
  }

  const timestamp =
    new Date(value).getTime();

  if (
    Number.isNaN(timestamp)
  ) {
    return 0;
  }

  return timestamp;

}


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


function getRelevanceCount(
  candidates: TouchContentCandidate[],
  decisionsByContentId: Map<
    string,
    TouchContentDecision
  >,
  relevance: TouchContentRelevance,
) {

  return candidates.filter(
    candidate => {

      const decision =
        decisionsByContentId.get(
          candidate.content_id,
        );

      if (!decision) {
          return false;
        }

        return (
          decision.relevance
          === relevanceFilter
        );

    },
  ).length;

}


function sortCandidates(
  candidates: TouchContentCandidate[],
  decisionsByContentId: Map<
    string,
    TouchContentDecision
  >,
  sortMode: SortMode,
) {

  return [...candidates].sort(
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

      const leftRelevance =
        leftDecision
          ? leftDecision.relevance
          : undefined;

      const rightRelevance =
        rightDecision
          ? rightDecision.relevance
          : undefined;

      const relevanceDifference =
        getRelevanceOrder(
          leftRelevance,
        )
        - getRelevanceOrder(
          rightRelevance,
        );

      if (
        relevanceDifference !== 0
      ) {
        return relevanceDifference;
      }

      const leftScore =
        leftDecision
          ? leftDecision.relevance_score
          : -1;

      const rightScore =
        rightDecision
          ? rightDecision.relevance_score
          : -1;

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
    new Set(
      selectedContentIds,
    );

  const dismissedIds =
    new Set(
      dismissedContentIds,
    );

  const filteredCandidates =
    candidates.filter(
      candidate => {

        if (
          relevanceFilter === "ALL"
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

  const visibleCandidates =
    sortCandidates(
      filteredCandidates,
      decisionsByContentId,
      sortMode,
    );

  const directCount =
    getRelevanceCount(
      candidates,
      decisionsByContentId,
      "DIRECT",
    );

  const contextCount =
    getRelevanceCount(
      candidates,
      decisionsByContentId,
      "CONTEXT",
    );

  const relatedCount =
    getRelevanceCount(
      candidates,
      decisionsByContentId,
      "RELATED",
    );

  const outOfScopeCount =
    getRelevanceCount(
      candidates,
      decisionsByContentId,
      "OUT_OF_SCOPE",
    );

  return (

    <div className="space-y-4">

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
            onChange={event => {

              setSortMode(
                event.target.value
                as SortMode,
              );

            }}
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

          <FilterButton
            label="All"
            count={candidates.length}
            active={
              relevanceFilter === "ALL"
            }
            onClick={() => {
              setRelevanceFilter("ALL");
            }}
          />

          <FilterButton
            label="Direct"
            count={directCount}
            active={
              relevanceFilter === "DIRECT"
            }
            onClick={() => {
              setRelevanceFilter("DIRECT");
            }}
          />

          <FilterButton
            label="Context"
            count={contextCount}
            active={
              relevanceFilter === "CONTEXT"
            }
            onClick={() => {
              setRelevanceFilter("CONTEXT");
            }}
          />

          <FilterButton
            label="Related"
            count={relatedCount}
            active={
              relevanceFilter === "RELATED"
            }
            onClick={() => {
              setRelevanceFilter("RELATED");
            }}
          />

          <FilterButton
            label="Out of scope"
            count={outOfScopeCount}
            active={
              relevanceFilter
              === "OUT_OF_SCOPE"
            }
            onClick={() => {
              setRelevanceFilter(
                "OUT_OF_SCOPE",
              );
            }}
          />

        </div>

      </div>

      {candidates.length === 0 && (

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

      )}

      {(
        candidates.length > 0
        && visibleCandidates.length === 0
      ) && (

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

      )}

      {visibleCandidates.length > 0 && (

        <div className="space-y-4">

          {visibleCandidates.map(
            candidate => {

              const contentId =
                candidate.content_id;

              const decision =
                decisionsByContentId.get(
                  contentId,
                ) || null;

              const handleOpen =
                onOpenContent
                  ? () => {
                      onOpenContent(
                        contentId,
                      );
                    }
                  : undefined;

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
                  onToggle={() => {
                    onToggleContent(
                      contentId,
                    );
                  }}
                  onDismiss={() => {
                    onDismissContent(
                      contentId,
                    );
                  }}
                  onRestore={() => {
                    onRestoreContent(
                      contentId,
                    );
                  }}
                  onOpen={handleOpen}
                />

              );

            },
          )}

        </div>

      )}

    </div>

  );

}


type FilterButtonProps = {
  label: string;
  count: number;
  active: boolean;
  onClick: () => void;
};


function FilterButton({
  label,
  count,
  active,
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
