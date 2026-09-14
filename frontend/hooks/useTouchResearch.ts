"use client";

import {
  useCallback,
  useMemo,
  useState,
} from "react";

import {
  searchTouchContents,
} from "@/lib/touch";

import type {
  TouchCandidateEvaluation,
  TouchConsolidation,
  TouchContentCandidate,
  TouchContentDecision,
  TouchConversationMessage,
  TouchEntityReference,
  TouchResearchBrief,
  TouchResearchInterpretation,
} from "@/types/touch";


/* =========================================================
   TYPES
========================================================= */

export type TouchResearchRequest = {
  query: string;

  outputLanguage?: string;

  periodStart?: string | null;
  periodEnd?: string | null;

  companies?: TouchEntityReference[];
  solutions?: TouchEntityReference[];
  topics?: TouchEntityReference[];
};


export type UseTouchResearchResult = {
  loading: boolean;
  error: string | null;
  backendErrors: string[];

  interpretation:
    TouchResearchInterpretation | null;

  candidates: TouchContentCandidate[];

  decisions: TouchContentDecision[];

  decisionsByContentId: Map<
    string,
    TouchContentDecision
  >;

  consolidation:
    TouchConsolidation | null;

  conversationHistory:
    TouchConversationMessage[];

  selectedContentIds: string[];

  selectedCandidates:
    TouchContentCandidate[];

  dismissedContentIds: string[];

  runSearch: (
    request: TouchResearchRequest
  ) => Promise<void>;

  toggleContent: (
    contentId: string
  ) => void;

  selectContent: (
    contentId: string
  ) => void;

  unselectContent: (
    contentId: string
  ) => void;

  dismissContent: (
    contentId: string
  ) => void;

  restoreContent: (
    contentId: string
  ) => void;

  resetResearch: () => void;
};


/* =========================================================
   MERGE CANDIDATES
========================================================= */

function mergeCandidates(
  current: TouchContentCandidate[],
  incoming: TouchContentCandidate[],
): TouchContentCandidate[] {

  const candidatesById =
    new Map<
      string,
      TouchContentCandidate
    >();

  for (const candidate of current) {

    candidatesById.set(
      candidate.content_id,
      candidate,
    );

  }

  for (const candidate of incoming) {

    candidatesById.set(
      candidate.content_id,
      candidate,
    );

  }

  return Array.from(
    candidatesById.values(),
  );

}


/* =========================================================
   MERGE DECISIONS
========================================================= */

function mergeDecisions(
  current: TouchContentDecision[],
  incoming: TouchContentDecision[],
): TouchContentDecision[] {

  const decisionsById =
    new Map<
      string,
      TouchContentDecision
    >();

  for (const decision of current) {

    decisionsById.set(
      decision.content_id,
      decision,
    );

  }

  for (const decision of incoming) {

    decisionsById.set(
      decision.content_id,
      decision,
    );

  }

  return Array.from(
    decisionsById.values(),
  );

}


/* =========================================================
   HOOK
========================================================= */

export function useTouchResearch():
  UseTouchResearchResult {

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );

  const [
    backendErrors,
    setBackendErrors,
  ] = useState<string[]>([]);

  const [
    interpretation,
    setInterpretation,
  ] = useState<
    TouchResearchInterpretation | null
  >(null);

  const [
    candidates,
    setCandidates,
  ] = useState<
    TouchContentCandidate[]
  >([]);

  const [
    evaluation,
    setEvaluation,
  ] = useState<
    TouchCandidateEvaluation
  >({
    decisions: [],
  });

  const [
    consolidation,
    setConsolidation,
  ] = useState<
    TouchConsolidation | null
  >(null);

  const [
    conversationHistory,
    setConversationHistory,
  ] = useState<
    TouchConversationMessage[]
  >([]);

  const [
    selectedContentIds,
    setSelectedContentIds,
  ] = useState<string[]>([]);

  const [
    dismissedContentIds,
    setDismissedContentIds,
  ] = useState<string[]>([]);

  /* =======================================================
     DERIVED DECISIONS
  ======================================================= */

  const decisionsByContentId =
    useMemo(() => {

      return new Map(
        evaluation.decisions.map(
          decision => [
            decision.content_id,
            decision,
          ],
        ),
      );

    }, [
      evaluation.decisions,
    ]);

  /* =======================================================
     DERIVED SELECTED CONTENTS
  ======================================================= */

  const selectedCandidates =
    useMemo(() => {

      const selectedIds =
        new Set(
          selectedContentIds,
        );

      return candidates.filter(
        candidate =>
          selectedIds.has(
            candidate.content_id,
          ),
      );

    }, [
      candidates,
      selectedContentIds,
    ]);

  /* =======================================================
     RUN SEARCH
  ======================================================= */

  const runSearch =
    useCallback(
      async (
        request: TouchResearchRequest,
      ) => {

        const query =
          request.query.trim();

        if (!query || loading) {
          return;
        }

        setLoading(true);
        setError(null);
        setBackendErrors([]);

        const userMessage:
          TouchConversationMessage = {

            role: "user",

            content: query,

          };

        const nextConversationHistory = [

          ...conversationHistory,

          userMessage,

        ];

        const brief:
          TouchResearchBrief = {

            query,

            output_language:
              request.outputLanguage
              ?? "fr",

            period_start:
              request.periodStart
              ?? null,

            period_end:
              request.periodEnd
              ?? null,

            companies:
              request.companies
              ?? [],

            solutions:
              request.solutions
              ?? [],

            topics:
              request.topics
              ?? [],

            conversation_history:
              conversationHistory,

            selected_content_ids:
              selectedContentIds,

            dismissed_content_ids:
              dismissedContentIds,

            previously_proposed_content_ids:
              candidates.map(
                candidate =>
                  candidate.content_id,
              ),

          };

        try {

          const result =
            await searchTouchContents(
              brief,
              "full",
            );

          setInterpretation(
            result.interpretation,
          );

          setCandidates(
            current =>
              mergeCandidates(
                current,
                result.candidates,
              ),
          );

          setEvaluation(
            current => ({

              decisions:
                mergeDecisions(
                  current.decisions,
                  result
                    .evaluation
                    .decisions,
                ),

            }),
          );

          setConsolidation(
            result.consolidation,
          );

          setBackendErrors(
            result.errors,
          );

          const assistantMessage =
            result
              .interpretation
              .response_message
              .trim();

          if (assistantMessage) {

            nextConversationHistory.push({

              role: "assistant",

              content:
                assistantMessage,

            });

          }

          setConversationHistory(
            nextConversationHistoryHistory
          );

        } catch (caughtError) {

          console.error(
            "Touch search error",
            caughtError,
          );

          setError(
            caughtError instanceof Error
              ? caughtError.message
              : (
                  "Unable to run Touch "
                  + "editorial research."
                ),
          );

        } finally {

          setLoading(false);

        }

      },
      [
        candidates,
        conversationHistory,
        dismissedContentIds,
        loading,
        selectedContentIds,
      ],
    );

  /* =======================================================
     SELECT CONTENT
  ======================================================= */

  const selectContent =
    useCallback(
      (
        contentId: string,
      ) => {

        setSelectedContentIds(
          current => {

            if (
              current.includes(
                contentId,
              )
            ) {
              return current;
            }

            return [
              ...current,
              contentId,
            ];

          },
        );

        setDismissedContentIds(
          current =>
            current.filter(
              id => id !== contentId,
            ),
        );

      },
      [],
    );

  /* =======================================================
     UNSELECT CONTENT
  ======================================================= */

  const unselectContent =
    useCallback(
      (
        contentId: string,
      ) => {

        setSelectedContentIds(
          current =>
            current.filter(
              id => id !== contentId,
            ),
        );

      },
      [],
    );

  /* =======================================================
     TOGGLE CONTENT
  ======================================================= */

  const toggleContent =
    useCallback(
      (
        contentId: string,
      ) => {

        if (
          selectedContentIds.includes(
            contentId,
          )
        ) {

          unselectContent(
            contentId,
          );

          return;
        }

        selectContent(
          contentId,
        );

      },
      [
        selectedContentIds,
        selectContent,
        unselectContent,
      ],
    );

  /* =======================================================
     DISMISS CONTENT
  ======================================================= */

  const dismissContent =
    useCallback(
      (
        contentId: string,
      ) => {

        setSelectedContentIds(
          current =>
            current.filter(
              id => id !== contentId,
            ),
        );

        setDismissedContentIds(
          current => {

            if (
              current.includes(
                contentId,
              )
            ) {
              return current;
            }

            return [
              ...current,
              contentId,
            ];

          },
        );

      },
      [],
    );

  /* =======================================================
     RESTORE CONTENT
  ======================================================= */

  const restoreContent =
    useCallback(
      (
        contentId: string,
      ) => {

        setDismissedContentIds(
          current =>
            current.filter(
              id => id !== contentId,
            ),
        );

      },
      [],
    );

  /* =======================================================
     RESET
  ======================================================= */

  const resetResearch =
    useCallback(
      () => {

        setLoading(false);

        setError(null);

        setBackendErrors([]);

        setInterpretation(null);

        setCandidates([]);

        setEvaluation({
          decisions: [],
        });

        setConsolidation(null);

        setConversationHistory([]);

        setSelectedContentIds([]);

        setDismissedContentIds([]);

      },
      [],
    );

  return {

    loading,
    error,
    backendErrors,

    interpretation,

    candidates,

    decisions:
      evaluation.decisions,

    decisionsByContentId,

    consolidation,

    conversationHistory,

    selectedContentIds,

    selectedCandidates,

    dismissedContentIds,

    runSearch,

    toggleContent,

    selectContent,

    unselectContent,

    dismissContent,

    restoreContent,

    resetResearch,

  };

}
