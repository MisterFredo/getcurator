"use client";

import {
  useCallback,
  useState,
} from "react";

import {
  continueTouchGuidedResearch,
} from "@/lib/touch";

import type {
  TouchConversationMessage,
  TouchEntityReference,
  TouchGuidedResearchAction,
  TouchGuidedResearchOutcome,
  TouchGuidedResearchPhase,
  TouchGuidedResearchPlan,
  TouchGuidedResearchRequest,
} from "@/types/touch";


/* =========================================================
   CONTEXT
========================================================= */

export type TouchGuidedResearchContext = {
  outputLanguage:
    string;

  periodStart:
    string | null;

  periodEnd:
    string | null;

  companies:
    TouchEntityReference[];

  solutions:
    TouchEntityReference[];

  topics:
    TouchEntityReference[];
};


/* =========================================================
   RESULT
========================================================= */

export type UseTouchGuidedResearchResult = {
  loading:
    boolean;

  error:
    string | null;

  warning:
    string | null;

  started:
    boolean;

  phase:
    TouchGuidedResearchPhase | null;

  conversationHistory:
    TouchConversationMessage[];

  questions:
    string[];

  plan:
    TouchGuidedResearchPlan | null;

  missingInformation:
    string[];

  readyForSearch:
    boolean;

  startInterview: (
    message: string,
    context: TouchGuidedResearchContext,
  ) => Promise<
    TouchGuidedResearchOutcome | null
  >;

  answerQuestion: (
    message: string,
    context: TouchGuidedResearchContext,
  ) => Promise<
    TouchGuidedResearchOutcome | null
  >;

  preparePlan: (
    context: TouchGuidedResearchContext,
  ) => Promise<
    TouchGuidedResearchOutcome | null
  >;

  revisePlan: (
    message: string,
    context: TouchGuidedResearchContext,
  ) => Promise<
    TouchGuidedResearchOutcome | null
  >;

  updatePlan: (
    plan: TouchGuidedResearchPlan,
  ) => void;

  applyResolvedEntities: (
    entities: TouchEntityReference[],
  ) => void;

  resetGuidedResearch:
    () => void;
};


/* =========================================================
   HOOK
========================================================= */

export function useTouchGuidedResearch():
  UseTouchGuidedResearchResult {

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
    warning,
    setWarning,
  ] = useState<string | null>(
    null,
  );

  const [
    started,
    setStarted,
  ] = useState(false);

  const [
    phase,
    setPhase,
  ] = useState<
    TouchGuidedResearchPhase | null
  >(null);

  const [
    conversationHistory,
    setConversationHistory,
  ] = useState<
    TouchConversationMessage[]
  >([]);

  const [
    questions,
    setQuestions,
  ] = useState<string[]>([]);

  const [
    plan,
    setPlan,
  ] = useState<
    TouchGuidedResearchPlan | null
  >(null);

  const [
    missingInformation,
    setMissingInformation,
  ] = useState<string[]>([]);

  const [
    readyForSearch,
    setReadyForSearch,
  ] = useState(false);


  /* =======================================================
     RUN TURN
  ======================================================= */

  const runTurn =
    useCallback(
      async (
        action: TouchGuidedResearchAction,
        message: string,
        context: TouchGuidedResearchContext,
        resetBeforeTurn = false,
      ): Promise<
        TouchGuidedResearchOutcome | null
      > => {

        const cleanedMessage =
          message.trim();

        if (loading) {
          return null;
        }

        if (
          action !== "PREPARE_PLAN"
          && !cleanedMessage
        ) {
          return null;
        }

        const baseHistory =
          resetBeforeTurn
            ? []
            : conversationHistory;

        const basePlan =
          resetBeforeTurn
            ? null
            : plan;

        const request:
          TouchGuidedResearchRequest = {

            action,

            message:
              cleanedMessage,

            output_language:
              context.outputLanguage,

            period_start:
              context.periodStart,

            period_end:
              context.periodEnd,

            companies:
              context.companies,

            solutions:
              context.solutions,

            topics:
              context.topics,

            conversation_history:
              baseHistory,

            current_plan:
              basePlan,

          };

        try {

          setLoading(
            true,
          );

          setError(
            null,
          );

          setWarning(
            null,
          );

          const outcome =
            await continueTouchGuidedResearch(
              request,
            );

          const nextHistory = [
            ...baseHistory,
          ];

          if (cleanedMessage) {

            nextHistory.push({

              role:
                "user",

              content:
                cleanedMessage,

            });

          }

          if (
            outcome
              .assistant_message
              .trim()
          ) {

            nextHistory.push({

              role:
                "assistant",

              content:
                outcome
                  .assistant_message
                  .trim(),

            });

          }

          setStarted(
            true,
          );

          setPhase(
            outcome.phase,
          );

          setConversationHistory(
            nextHistory,
          );

          setQuestions(
            outcome.questions,
          );

          setPlan(
            outcome.plan,
          );

          setMissingInformation(
            outcome.missing_information,
          );

          setReadyForSearch(
            outcome.ready_for_search,
          );

          if (
            outcome.used_fallback
            && outcome.error
          ) {

            setWarning(
              outcome.error,
            );

          }

          return outcome;

        } catch (caughtError) {

          console.error(
            "Touch guided research error",
            caughtError,
          );

          setError(
            caughtError instanceof Error
              ? caughtError.message
              : (
                  "Unable to continue "
                  + "guided research."
                ),
          );

          return null;

        } finally {

          setLoading(
            false,
          );

        }

      },
      [
        conversationHistory,
        loading,
        plan,
      ],
    );


  /* =======================================================
     START INTERVIEW
  ======================================================= */

  const startInterview =
    useCallback(
      async (
        message: string,
        context: TouchGuidedResearchContext,
      ) => {

        return runTurn(
          "START",
          message,
          context,
          true,
        );

      },
      [
        runTurn,
      ],
    );


  /* =======================================================
     ANSWER QUESTION
  ======================================================= */

  const answerQuestion =
    useCallback(
      async (
        message: string,
        context: TouchGuidedResearchContext,
      ) => {

        return runTurn(
          "ANSWER",
          message,
          context,
        );

      },
      [
        runTurn,
      ],
    );


  /* =======================================================
     PREPARE PLAN
  ======================================================= */

  const preparePlan =
    useCallback(
      async (
        context: TouchGuidedResearchContext,
      ) => {

        return runTurn(
          "PREPARE_PLAN",
          "",
          context,
        );

      },
      [
        runTurn,
      ],
    );


  /* =======================================================
     REVISE PLAN
  ======================================================= */

  const revisePlan =
    useCallback(
      async (
        message: string,
        context: TouchGuidedResearchContext,
      ) => {

        return runTurn(
          "REVISE",
          message,
          context,
        );

      },
      [
        runTurn,
      ],
    );


  /* =======================================================
     UPDATE PLAN
  ======================================================= */

  const updatePlan =
    useCallback(
      (
        nextPlan:
          TouchGuidedResearchPlan,
      ) => {

        setPlan(
          nextPlan,
        );

        setReadyForSearch(
          nextPlan.ready_for_search,
        );

      },
      [],
    );


  /* =======================================================
     APPLY RESOLVED ENTITIES
  ======================================================= */

  const applyResolvedEntities =
    useCallback(
      (
        entities:
          TouchEntityReference[],
      ) => {

        setPlan(
          currentPlan => {

            if (!currentPlan) {
              return currentPlan;
            }

            return {
              ...currentPlan,

              resolved_entities:
                entities,
            };

          },
        );

      },
      [],
    );


  /* =======================================================
     RESET
  ======================================================= */

  const resetGuidedResearch =
    useCallback(
      () => {

        setLoading(
          false,
        );

        setError(
          null,
        );

        setWarning(
          null,
        );

        setStarted(
          false,
        );

        setPhase(
          null,
        );

        setConversationHistory(
          [],
        );

        setQuestions(
          [],
        );

        setPlan(
          null,
        );

        setMissingInformation(
          [],
        );

        setReadyForSearch(
          false,
        );

      },
      [],
    );


  return {

    loading,
    error,
    warning,

    started,
    phase,

    conversationHistory,

    questions,

    plan,

    missingInformation,

    readyForSearch,

    startInterview,
    answerQuestion,
    preparePlan,
    revisePlan,

    updatePlan,
    applyResolvedEntities,

    resetGuidedResearch,

  };

}
