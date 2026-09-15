"use client";

import type {
  TouchCorpusNotebook,
  TouchEvidenceConfidence,
  TouchEvidenceNoteType,
  TouchEvidenceStatus,
} from "@/types/touch";


/* =========================================================
   PROPS
========================================================= */

type Props = {
  notebook: TouchCorpusNotebook;

  sourceContentIds: string[];
};


/* =========================================================
   LABELS
========================================================= */

const NOTE_TYPE_LABELS:
  Record<
    TouchEvidenceNoteType,
    string
  > = {

    FACT:
      "Fact",

    MECHANISM:
      "Mechanism",

    NUMBER:
      "Number",

    STRATEGIC_READING:
      "Strategic reading",

    TENSION:
      "Tension",

    LIMITATION:
      "Limitation",

    UNCERTAINTY:
      "Uncertainty",

    COMPARISON:
      "Comparison",

    MILESTONE:
      "Milestone",

    EXAMPLE:
      "Example",

  };


const CONFIDENCE_LABELS:
  Record<
    TouchEvidenceConfidence,
    string
  > = {

    HIGH:
      "High confidence",

    MEDIUM:
      "Medium confidence",

    LOW:
      "Low confidence",

  };


const STATUS_LABELS:
  Record<
    TouchEvidenceStatus,
    string
  > = {

    VALIDATED:
      "Validated",

    TO_VERIFY:
      "To verify",

    CONTRADICTED:
      "Contradicted",

  };


/* =========================================================
   BADGE CLASSES
========================================================= */

function getNoteTypeClasses(
  noteType: TouchEvidenceNoteType,
): string {

  if (
    noteType === "FACT"
    || noteType === "MILESTONE"
  ) {

    return (
      "bg-blue-50 "
      + "text-blue-700 "
      + "border-blue-200"
    );

  }

  if (
    noteType === "MECHANISM"
    || noteType === "EXAMPLE"
  ) {

    return (
      "bg-emerald-50 "
      + "text-emerald-700 "
      + "border-emerald-200"
    );

  }

  if (
    noteType === "NUMBER"
    || noteType === "COMPARISON"
  ) {

    return (
      "bg-violet-50 "
      + "text-violet-700 "
      + "border-violet-200"
    );

  }

  if (
    noteType === "TENSION"
    || noteType === "LIMITATION"
    || noteType === "UNCERTAINTY"
  ) {

    return (
      "bg-amber-50 "
      + "text-amber-700 "
      + "border-amber-200"
    );

  }

  return (
    "bg-gray-50 "
    + "text-gray-700 "
    + "border-gray-200"
  );

}


function getConfidenceClasses(
  confidence: TouchEvidenceConfidence,
): string {

  if (confidence === "HIGH") {

    return (
      "bg-emerald-50 "
      + "text-emerald-700"
    );

  }

  if (confidence === "MEDIUM") {

    return (
      "bg-amber-50 "
      + "text-amber-700"
    );

  }

  return (
    "bg-red-50 "
    + "text-red-700"
  );

}


function getStatusClasses(
  status: TouchEvidenceStatus,
): string {

  if (status === "VALIDATED") {

    return (
      "bg-emerald-50 "
      + "text-emerald-700"
    );

  }

  if (status === "TO_VERIFY") {

    return (
      "bg-amber-50 "
      + "text-amber-700"
    );

  }

  return (
    "bg-red-50 "
    + "text-red-700"
  );

}

/* =========================================================
   SECTION
========================================================= */

function NotebookSection({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {

  return (

    <section className="space-y-4">

      <div>

        <h3 className="text-lg font-semibold text-gray-900">
          {title}
        </h3>

        {description && (

          <p className="mt-1 text-sm text-gray-500">
            {description}
          </p>

        )}

      </div>

      {children}

    </section>

  );

}


/* =========================================================
   COMPONENT
========================================================= */

export default function TouchNotebookPreview({
  notebook,
  sourceContentIds,
}: Props) {

  const sourceNumberById =
    new Map(
      sourceContentIds.map(
        (
          contentId,
          index,
        ) => [

          contentId,
          index + 1,

        ],
      ),
    );

  function renderSourceReferences(
    referencedContentIds: string[],
  ) {

    const references =
      referencedContentIds
        .map(
          contentId => ({

            contentId,

            sourceNumber:
              sourceNumberById.get(
                contentId,
              ),

          }),
        )
        .filter(
          reference =>
            reference.sourceNumber
            !== undefined,
        );

    if (
      references.length === 0
    ) {

      return null;

    }

    return (

      <div className="flex flex-wrap gap-1.5">

        {references.map(
          reference => (

            <span
              key={
                reference.contentId
              }
              className="
                rounded
                bg-gray-100
                px-2
                py-1
                text-xs
                font-medium
                text-gray-600
              "
            >
              Source
              {" "}
              {reference.sourceNumber}
            </span>

          ),
        )}

      </div>

    );

  }

  return (

    <div className="space-y-8">

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <div
        className="
          rounded-xl
          border
          border-gray-200
          bg-white
          p-6
        "
      >

        <div
          className="
            flex
            flex-wrap
            items-start
            justify-between
            gap-4
          "
        >

          <div className="min-w-0 flex-1">

            <p
              className="
                text-xs
                font-semibold
                uppercase
                tracking-wide
                text-ratecard-blue
              "
            >
              Editorial notebook
            </p>

            <h2
              className="
                mt-2
                text-2xl
                font-semibold
                text-gray-900
              "
            >
              {notebook.subject}
            </h2>

            {notebook.objective && (

              <p className="mt-2 text-sm text-gray-500">
                {notebook.objective}
              </p>

            )}

          </div>

          <div className="flex flex-wrap gap-2">

            <span
              className="
                rounded-full
                bg-gray-100
                px-3
                py-1.5
                text-xs
                font-medium
                text-gray-600
              "
            >
              {notebook.notes.length}
              {" "}
              notes
            </span>

            <span
              className="
                rounded-full
                bg-gray-100
                px-3
                py-1.5
                text-xs
                font-medium
                text-gray-600
              "
            >
              {notebook.events.length}
              {" "}
              events
            </span>

            <span
              className="
                rounded-full
                bg-gray-100
                px-3
                py-1.5
                text-xs
                font-medium
                text-gray-600
              "
            >
              {notebook.validated_numbers.length}
              {" "}
              validated numbers
            </span>

          </div>

        </div>

        <div
          className="
            mt-6
            rounded-lg
            border
            border-blue-100
            bg-blue-50
            p-4
          "
        >

          <p
            className="
              text-xs
              font-semibold
              uppercase
              tracking-wide
              text-blue-700
            "
          >
            Corpus summary
          </p>

          <p className="mt-2 text-sm leading-6 text-gray-700">
            {notebook.corpus_summary}
          </p>

        </div>

      </div>

      {/* ================================================= */}
      {/* DIMENSIONS */}
      {/* ================================================= */}

      {notebook.dimensions.length > 0 && (

        <NotebookSection
          title="Covered dimensions"
          description={
            "The main analytical facets supported "
            + "by the selected corpus."
          }
        >

          <div
            className="
              grid
              gap-4
              xl:grid-cols-2
            "
          >

            {notebook.dimensions.map(
              (
                dimension,
                index,
              ) => (

                <article
                  key={
                    `${dimension.label}-${index}`
                  }
                  className="
                    rounded-xl
                    border
                    border-gray-200
                    bg-white
                    p-5
                  "
                >

                  <h4 className="font-semibold text-gray-900">
                    {dimension.label}
                  </h4>

                  <p
                    className="
                      mt-2
                      text-sm
                      leading-6
                      text-gray-600
                    "
                  >
                    {dimension.summary}
                  </p>

                  <div className="mt-4">

                    {renderSourceReferences(
                      dimension.source_content_ids,
                    )}

                  </div>

                </article>

              ),
            )}

          </div>

        </NotebookSection>

      )}

      {/* ================================================= */}
      {/* EVIDENCE NOTES */}
      {/* ================================================= */}

      <NotebookSection
        title="Evidence notes"
        description={
          "Atomic facts, mechanisms, interpretations "
          + "and limitations extracted from the corpus."
        }
      >

        {notebook.notes.length === 0 ? (

          <div
            className="
              rounded-xl
              border
              border-dashed
              border-gray-300
              bg-white
              p-8
              text-center
              text-sm
              text-gray-500
            "
          >
            No evidence note was produced.
          </div>

        ) : (

          <div className="space-y-3">

            {notebook.notes.map(
              note => (

                <article
                  key={note.note_id}
                  className="
                    rounded-xl
                    border
                    border-gray-200
                    bg-white
                    p-5
                  "
                >

                  <div
                    className="
                      flex
                      flex-wrap
                      items-center
                      gap-2
                    "
                  >

                    <span
                      className={`
                        rounded-full
                        border
                        px-2.5
                        py-1
                        text-xs
                        font-medium
                        ${getNoteTypeClasses(
                          note.note_type,
                        )}
                      `}
                    >
                      {
                        NOTE_TYPE_LABELS[
                          note.note_type
                        ]
                      }
                    </span>

                    <span
                      className={`
                        rounded-full
                        px-2.5
                        py-1
                        text-xs
                        font-medium
                        ${getConfidenceClasses(
                          note.confidence,
                        )}
                      `}
                    >
                      {
                        CONFIDENCE_LABELS[
                          note.confidence
                        ]
                      }
                    </span>

                    <span
                      className={`
                        rounded-full
                        px-2.5
                        py-1
                        text-xs
                        font-medium
                        ${getStatusClasses(
                          note.status,
                        )}
                      `}
                    >
                      {
                        STATUS_LABELS[
                          note.status
                        ]
                      }
                    </span>

                  </div>

                  <p
                    className="
                      mt-4
                      font-medium
                      leading-6
                      text-gray-900
                    "
                  >
                    {note.statement}
                  </p>

                  {note.explanation && (

                    <p
                      className="
                        mt-2
                        text-sm
                        leading-6
                        text-gray-600
                      "
                    >
                      {note.explanation}
                    </p>

                  )}

                  {(
                    note.actors.length > 0
                    || note.geographies.length > 0
                    || note.dates.length > 0
                  ) && (

                    <div
                      className="
                        mt-4
                        flex
                        flex-wrap
                        gap-2
                        text-xs
                        text-gray-500
                      "
                    >

                      {note.actors.map(
                        actor => (

                          <span
                            key={`actor-${actor}`}
                            className="
                              rounded
                              bg-gray-50
                              px-2
                              py-1
                            "
                          >
                            Actor:
                            {" "}
                            {actor}
                          </span>

                        ),
                      )}

                      {note.geographies.map(
                        geography => (

                          <span
                            key={`geography-${geography}`}
                            className="
                              rounded
                              bg-gray-50
                              px-2
                              py-1
                            "
                          >
                            Geography:
                            {" "}
                            {geography}
                          </span>

                        ),
                      )}

                      {note.dates.map(
                        date => (

                          <span
                            key={`date-${date}`}
                            className="
                              rounded
                              bg-gray-50
                              px-2
                              py-1
                            "
                          >
                            Date:
                            {" "}
                            {date}
                          </span>

                        ),
                      )}

                    </div>

                  )}

                  <div className="mt-4">

                    {renderSourceReferences(
                      note.source_content_ids,
                    )}

                  </div>

                </article>

              ),
            )}

          </div>

        )}

      </NotebookSection>

      {/* ================================================= */}
      {/* EVENTS */}
      {/* ================================================= */}

      {notebook.events.length > 0 && (

        <NotebookSection
          title="Events"
          description={
            "Underlying developments reconstructed "
            + "from complementary sources."
          }
        >

          <div className="space-y-3">

            {notebook.events.map(
              event => (

                <article
                  key={event.event_id}
                  className="
                    rounded-xl
                    border
                    border-gray-200
                    bg-white
                    p-5
                  "
                >

                  <div
                    className="
                      flex
                      flex-wrap
                      items-start
                      justify-between
                      gap-3
                    "
                  >

                    <div>

                      <h4 className="font-semibold text-gray-900">
                        {event.title}
                      </h4>

                      {event.event_date && (

                        <p className="mt-1 text-xs text-gray-500">
                          {event.event_date}
                        </p>

                      )}

                    </div>
                  <p
                    className="
                      mt-3
                      text-sm
                      leading-6
                      text-gray-600
                    "
                  >
                    {event.description}
                  </p>

                  {event.actors.length > 0 && (

                    <div className="mt-3 flex flex-wrap gap-2">

                      {event.actors.map(
                        actor => (

                          <span
                            key={actor}
                            className="
                              rounded-full
                              bg-gray-100
                              px-2.5
                              py-1
                              text-xs
                              text-gray-600
                            "
                          >
                            {actor}
                          </span>

                        ),
                      )}

                    </div>

                  )}

                  <div className="mt-4">

                    {renderSourceReferences(
                      event.source_content_ids,
                    )}

                  </div>

                </article>

              ),
            )}

          </div>

        </NotebookSection>

      )}

      {/* ================================================= */}
      {/* TIMELINE */}
      {/* ================================================= */}

      {notebook.timeline.length > 0 && (

        <NotebookSection title="Timeline">

          <div className="space-y-3">

            {notebook.timeline.map(
              (
                item,
                index,
              ) => (

                <article
                  key={
                    `${item.date}-${item.label}-${index}`
                  }
                  className="
                    flex
                    gap-4
                    rounded-xl
                    border
                    border-gray-200
                    bg-white
                    p-5
                  "
                >

                  <div
                    className="
                      min-w-24
                      text-sm
                      font-semibold
                      text-ratecard-blue
                    "
                  >
                    {item.date}
                  </div>

                  <div className="min-w-0 flex-1">

                    <h4 className="font-semibold text-gray-900">
                      {item.label}
                    </h4>

                    {item.description && (

                      <p
                        className="
                          mt-1
                          text-sm
                          leading-6
                          text-gray-600
                        "
                      >
                        {item.description}
                      </p>

                    )}

                    <div className="mt-3">

                      {renderSourceReferences(
                        item.source_content_ids,
                      )}

                    </div>

                  </div>

                </article>

              ),
            )}

          </div>

        </NotebookSection>

      )}

      {/* ================================================= */}
      {/* VALIDATED NUMBERS */}
      {/* ================================================= */}

      {notebook.validated_numbers.length > 0 && (

        <NotebookSection title="Validated numbers">

          <div
            className="
              grid
              gap-4
              md:grid-cols-2
              xl:grid-cols-3
            "
          >

            {notebook.validated_numbers.map(
              number => (

                <article
                  key={number.number_id}
                  className="
                    rounded-xl
                    border
                    border-gray-200
                    bg-white
                    p-5
                  "
                >

                  <p
                    className="
                      text-2xl
                      font-semibold
                      text-gray-900
                    "
                  >
                    {number.value}
                    {number.unit && (
                      <>
                        {" "}
                        {number.unit}
                      </>
                    )}
                  </p>

                  <p className="mt-2 font-medium text-gray-800">
                    {number.metric}
                  </p>

                  <p
                    className="
                      mt-2
                      text-sm
                      leading-6
                      text-gray-600
                    "
                  >
                    {number.context}
                  </p>

                  <div
                    className="
                      mt-3
                      space-y-1
                      text-xs
                      text-gray-500
                    "
                  >

                    {number.actor && (
                      <p>
                        Actor:
                        {" "}
                        {number.actor}
                      </p>
                    )}

                    {number.geography && (
                      <p>
                        Geography:
                        {" "}
                        {number.geography}
                      </p>
                    )}

                    {number.period && (
                      <p>
                        Period:
                        {" "}
                        {number.period}
                      </p>
                    )}

                  </div>

                  <div className="mt-4">

                    {renderSourceReferences(
                      number.source_content_ids,
                    )}

                  </div>

                </article>

              ),
            )}

          </div>

        </NotebookSection>

      )}

      {/* ================================================= */}
      {/* QUARANTINED NUMBERS */}
      {/* ================================================= */}

      {notebook.quarantined_numbers.length > 0 && (

        <NotebookSection
          title="Numbers to verify"
          description={
            "These figures must not be used in the "
            + "final document without verification."
          }
        >

          <div className="space-y-3">

            {notebook.quarantined_numbers.map(
              (
                number,
                index,
              ) => (

                <article
                  key={
                    `${number.value}-${number.metric}-${index}`
                  }
                  className="
                    rounded-xl
                    border
                    border-amber-200
                    bg-amber-50
                    p-5
                  "
                >

                  <p className="font-semibold text-gray-900">

                    {number.value}

                    {number.unit && (
                      <>
                        {" "}
                        {number.unit}
                      </>
                    )}

                    {number.metric && (
                      <>
                        {" — "}
                        {number.metric}
                      </>
                    )}

                  </p>

                  {number.context && (

                    <p
                      className="
                        mt-2
                        text-sm
                        text-gray-600
                      "
                    >
                      {number.context}
                    </p>

                  )}

                  <p
                    className="
                      mt-2
                      text-sm
                      font-medium
                      text-amber-800
                    "
                  >
                    {number.reason}
                  </p>

                  <div className="mt-4">

                    {renderSourceReferences(
                      number.source_content_ids,
                    )}

                  </div>

                </article>

              ),
            )}

          </div>

        </NotebookSection>

      )}

      {/* ================================================= */}
      {/* CONTRADICTIONS */}
      {/* ================================================= */}

      {notebook.contradictions.length > 0 && (

        <NotebookSection title="Contradictions">

          <div className="space-y-3">

            {notebook.contradictions.map(
              (
                contradiction,
                index,
              ) => (

                <article
                  key={
                    `${contradiction.subject}-${index}`
                  }
                  className="
                    rounded-xl
                    border
                    border-red-200
                    bg-red-50
                    p-5
                  "
                >

                  <h4 className="font-semibold text-gray-900">
                    {contradiction.subject}
                  </h4>

                  <p
                    className="
                      mt-2
                      text-sm
                      leading-6
                      text-gray-700
                    "
                  >
                    {contradiction.description}
                  </p>

                  {contradiction.resolution && (

                    <p
                      className="
                        mt-3
                        text-sm
                        font-medium
                        text-emerald-700
                      "
                    >
                      Resolution:
                      {" "}
                      {contradiction.resolution}
                    </p>

                  )}

                  <div className="mt-4">

                    {renderSourceReferences(
                      contradiction.source_content_ids,
                    )}

                  </div>

                </article>

              ),
            )}

          </div>

        </NotebookSection>

      )}

      {/* ================================================= */}
      {/* CORPUS ASSESSMENT */}
      {/* ================================================= */}

      {(
        notebook.corpus_strengths.length > 0
        || notebook.corpus_limits.length > 0
      ) && (

        <NotebookSection title="Corpus assessment">

          <div
            className="
              grid
              gap-4
              lg:grid-cols-2
            "
          >

            <div
              className="
                rounded-xl
                border
                border-emerald-200
                bg-emerald-50
                p-5
              "
            >

              <h4 className="font-semibold text-emerald-800">
                Strengths
              </h4>

              {notebook.corpus_strengths.length === 0 ? (

                <p className="mt-3 text-sm text-gray-500">
                  No specific strength identified.
                </p>

              ) : (

                <ul
                  className="
                    mt-3
                    list-disc
                    space-y-2
                    pl-5
                    text-sm
                    leading-6
                    text-gray-700
                  "
                >

                  {notebook.corpus_strengths.map(
                    (
                      strength,
                      index,
                    ) => (

                      <li key={`${strength}-${index}`}>
                        {strength}
                      </li>

                    ),
                  )}

                </ul>

              )}

            </div>

            <div
              className="
                rounded-xl
                border
                border-amber-200
                bg-amber-50
                p-5
              "
            >

              <h4 className="font-semibold text-amber-800">
                Limits
              </h4>

              {notebook.corpus_limits.length === 0 ? (

                <p className="mt-3 text-sm text-gray-500">
                  No specific limitation identified.
                </p>

              ) : (

                <ul
                  className="
                    mt-3
                    list-disc
                    space-y-2
                    pl-5
                    text-sm
                    leading-6
                    text-gray-700
                  "
                >

                  {notebook.corpus_limits.map(
                    (
                      limit,
                      index,
                    ) => (

                      <li key={`${limit}-${index}`}>
                        {limit}
                      </li>

                    ),
                  )}

                </ul>

              )}

            </div>

          </div>

        </NotebookSection>

      )}

    </div>

  );

}
