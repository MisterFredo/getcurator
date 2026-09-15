"use client";

import type {
  TouchContentCandidate,
  TouchContentDecision,
} from "@/types/touch";


/* =========================================================
   PROPS
========================================================= */

type Props = {
  candidates: TouchContentCandidate[];

  decisionsByContentId: Map<
    string,
    TouchContentDecision
  >;

  onRemove: (
    contentId: string
  ) => void;

  onOpen?: (
    contentId: string
  ) => void;

  onValidate?: () => void;

  validating?: boolean;
};


/* =========================================================
   FORMAT DATE
========================================================= */

function formatDate(
  value: string | null,
): string {

  if (!value) {
    return "";
  }

  const date =
    new Date(
      value,
    );

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return "";
  }

  return new Intl.DateTimeFormat(
    "fr-FR",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    },
  ).format(
    date,
  );

}


/* =========================================================
   COMPONENT
========================================================= */

export default function TouchSelectedCorpus({
  candidates,
  decisionsByContentId,
  onRemove,
  onOpen,
  onValidate,
  validating = false,
}: Props) {

  return (

    <aside
      className="
        rounded-xl
        border
        border-gray-200
        bg-white
        lg:sticky
        lg:top-6
      "
    >

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <div
        className="
          border-b
          border-gray-100
          px-5
          py-4
        "
      >

        <div
          className="
            flex
            items-center
            justify-between
            gap-3
          "
        >

          <div>

            <h2
              className="
                text-base
                font-semibold
                text-gray-900
              "
            >
              Selected corpus
            </h2>

            <p className="mt-1 text-sm text-gray-500">

              {candidates.length}
              {" "}
              {
                candidates.length === 1
                  ? "content"
                  : "contents"
              }

            </p>

          </div>

          <span
            className="
              inline-flex
              min-w-8
              items-center
              justify-center
              rounded-full
              bg-blue-50
              px-2.5
              py-1
              text-sm
              font-semibold
              text-ratecard-blue
            "
          >
            {candidates.length}
          </span>

        </div>

      </div>

      {/* ================================================= */}
      {/* CONTENTS */}
      {/* ================================================= */}

      <div
        className="
          max-h-[calc(100vh-260px)]
          overflow-y-auto
        "
      >

        {candidates.length === 0 ? (

          <div
            className="
              px-5
              py-10
              text-center
            "
          >

            <p
              className="
                text-sm
                font-medium
                text-gray-700
              "
            >
              Your corpus is empty
            </p>

            <p
              className="
                mt-1
                text-sm
                leading-5
                text-gray-500
              "
            >
              Select contents from the research
              results to build the editorial corpus.
            </p>

          </div>

        ) : (

          <div className="divide-y divide-gray-100">

            {candidates.map(
              (
                candidate,
                index,
              ) => {

                const decision =
                  decisionsByContentId.get(
                    candidate.content_id,
                  );

                const publishedAt =
                  formatDate(
                    candidate.published_at,
                  );

                return (

                  <div
                    key={
                      candidate.content_id
                    }
                    className="
                      px-5
                      py-4
                      space-y-2
                    "
                  >

                    <div
                      className="
                        flex
                        items-start
                        gap-3
                      "
                    >

                      <span
                        className="
                          flex
                          h-6
                          w-6
                          shrink-0
                          items-center
                          justify-center
                          rounded-full
                          bg-gray-100
                          text-xs
                          font-medium
                          text-gray-600
                        "
                      >
                        {index + 1}
                      </span>

                      <div className="min-w-0 flex-1">

                        <p
                          className="
                            text-sm
                            font-medium
                            leading-5
                            text-gray-900
                          "
                        >
                          {candidate.title}
                        </p>

                        <div
                          className="
                            mt-1
                            flex
                            flex-wrap
                            items-center
                            gap-2
                            text-xs
                            text-gray-500
                          "
                        >

                          {decision && (

                            <span>
                              {decision.relevance}
                              {" · "}
                              {decision.relevance_score}
                            </span>

                          )}

                          {publishedAt && (

                            <span>
                              {publishedAt}
                            </span>

                          )}

                        </div>

                      </div>

                    </div>

                    <div
                      className="
                        flex
                        items-center
                        justify-end
                        gap-3
                      "
                    >

                      {onOpen && (

                        <button
                          type="button"
                          onClick={() =>
                            onOpen(
                              candidate.content_id,
                            )
                          }
                          className="
                            text-xs
                            font-medium
                            text-ratecard-blue
                            hover:underline
                          "
                        >
                          Open
                        </button>

                      )}

                      <button
                        type="button"
                        onClick={() =>
                          onRemove(
                            candidate.content_id,
                          )
                        }
                        className="
                          text-xs
                          text-gray-400
                          hover:text-red-600
                        "
                      >
                        Remove
                      </button>

                    </div>

                  </div>

                );

              },
            )}

          </div>

        )}

      </div>

            {/* ================================================= */}
            {/* CONTINUE TO NOTEBOOK */}
            {/* ================================================= */}
      
            <div
              className="
                border-t
                border-gray-100
                p-4
              "
            >
      
              <button
                type="button"
                onClick={
                  onValidate
                }
                disabled={
                  candidates.length === 0
                  || validating
                  || !onValidate
                }
                className="
                  w-full
                  rounded-lg
                  bg-ratecard-blue
                  px-4
                  py-2.5
                  text-sm
                  font-medium
                  text-white
                  hover:opacity-90
                  disabled:cursor-not-allowed
                  disabled:opacity-40
                "
              >
                {
                  validating
                    ? "Preparing notebook…"
                    : "Continue to notebook"
                }
              </button>
      
              <p
                className="
                  mt-2
                  text-center
                  text-xs
                  leading-5
                  text-gray-400
                "
              >
                The notebook will extract and consolidate
                evidence from the selected contents only.
              </p>
      
            </div>
    </aside>

  );

}
