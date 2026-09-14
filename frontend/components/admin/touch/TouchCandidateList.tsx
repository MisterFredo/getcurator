"use client";

import TouchCandidateCard from "@/components/admin/touch/TouchCandidateCard";

import type {
  TouchContentCandidate,
  TouchContentDecision,
} from "@/types/touch";


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

  const selectedIds =
    new Set(
      selectedContentIds,
    );

  const dismissedIds =
    new Set(
      dismissedContentIds,
    );

  const visibleCandidates =
    candidates.filter(
      candidate => {

        const contentId =
          candidate.content_id;

        if (
          dismissedIds.has(
            contentId,
          )
        ) {
          return false;
        }

        const decision =
          decisionsByContentId.get(
            contentId,
          );

        if (
          decision
          && decision.relevance
            === "OUT_OF_SCOPE"
        ) {
          return false;
        }

        return true;

      },
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
        "
      >

        <h2 className="text-lg font-semibold text-gray-900">
          Proposed contents
        </h2>

        <p className="mt-1 text-sm text-gray-500">
          {visibleCandidates.length}
          {" contents proposed"}
        </p>

      </div>

      {visibleCandidates.length === 0 && (

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
                  dismissed={false}
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
