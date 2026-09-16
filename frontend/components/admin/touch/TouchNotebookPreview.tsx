"use client";

import type {
  TouchCorpusNotebook,
  TouchEvidenceConfidence,
  TouchEvidenceNote,
  TouchEvidenceNoteType,
  TouchEvidenceStatus,
  TouchNotebookEvent,
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
      "border-blue-200 "
      + "bg-blue-50 "
      + "text-blue-700"
    );

  }

  if (
    noteType === "MECHANISM"
    || noteType === "EXAMPLE"
  ) {

    return (
      "border-emerald-200 "
      + "bg-emerald-50 "
      + "text-emerald-700"
    );

  }

  if (
    noteType === "NUMBER"
    || noteType === "COMPARISON"
  ) {

    return (
      "border-violet-200 "
      + "bg-violet-50 "
      + "text-violet-700"
    );

  }

  if (
    noteType === "TENSION"
    || noteType === "LIMITATION"
    || noteType === "UNCERTAINTY"
  ) {

    return (
      "border-amber-200 "
      + "bg-amber-50 "
      + "text-amber-700"
    );

  }

  return (
    "border-gray-200 "
    + "bg-gray-50 "
    + "text-gray-700"
  );

}


function getConfidenceClasses(
  confidence: TouchEvidenceConfidence,
): string {

  if (
    confidence === "HIGH"
  ) {

    return (
      "bg-emerald-50 "
      + "text-emerald-700"
    );

  }

  if (
    confidence === "MEDIUM"
  ) {

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

  if (
    status === "VALIDATED"
  ) {

    return (
      "bg-emerald-50 "
      + "text-emerald-700"
    );

  }

  if (
    status === "TO_VERIFY"
  ) {

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
   NOTEBOOK SECTION
========================================================= */

function NotebookSection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {

  return (

    <section className="space-y-4">

      <h3
        className="
          text-lg
          font-semibold
          text-gray-900
        "
      >
        {title}
      </h3>

      {children}

    </section>

  );

}


/* =========================================================
   SOURCE REFERENCES
========================================================= */

function SourceReferences({
  sourceContentIds,
  sourceNumberById,
}: {
  sourceContentIds: string[];

  sourceNumberById:
    Map<string, number>;
}) {

  const references = (
    Array.from(
      new Set(
        sourceContentIds,
      ),
    )
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
        (
          reference,
        ): reference is {
          contentId: string;
          sourceNumber: number;
        } => (
          reference.sourceNumber
          !== undefined
        ),
      )
  );

  if (
    references.length === 0
  ) {

    return null;

  }

  return (

    <div
      className="
        mt-3
        flex
        flex-wrap
        gap-1.5
      "
    >

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


/* =========================================================
   NOTE CARD
========================================================= */

function NoteCard({
  note,
  sourceNumberById,
}: {
  note: TouchEvidenceNote;

  sourceNumberById:
    Map<string, number>;
}) {

  return (

    <article
      className="
        rounded-lg
        border
        border-gray-200
        bg-white
        p-4
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

        {note.confidence === "LOW" && (

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
        
        )}

        {note.status !== "VALIDATED" && (

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

        )}

      </div>

      <p
        className="
          mt-3
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
            mt-3
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
                key={
                  `actor-${note.note_id}-${actor}`
                }
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
                key={
                  `geography-${note.note_id}-${geography}`
                }
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
                key={
                  `date-${note.note_id}-${date}`
                }
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

      <SourceReferences
        sourceContentIds={
          note.source_content_ids
        }
        sourceNumberById={
          sourceNumberById
        }
      />

    </article>

  );

}


/* =========================================================
   EVENT CARD
========================================================= */

function EventCard({
  event,
  noteById,
  sourceNumberById,
}: {
  event: TouchNotebookEvent;

  noteById:
    Map<string, TouchEvidenceNote>;

  sourceNumberById:
    Map<string, number>;
}) {

  const notes = (
    event.note_ids
      .map(
        noteId =>
          noteById.get(
            noteId,
          ),
      )
      .filter(
        (
          note,
        ): note is TouchEvidenceNote => (
          Boolean(
            note,
          )
        ),
      )
  );

  return (

    <article
      className="
        rounded-xl
        border
        border-gray-200
        bg-gray-50
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

        <div className="min-w-0">

          <p
            className="
              text-xs
              font-semibold
              uppercase
              tracking-wide
              text-ratecard-blue
            "
          >
            Event
          </p>

          <h4
            className="
              mt-1
              text-base
              font-semibold
              text-gray-900
            "
          >
            {event.title}
          </h4>

        </div>

        {event.event_date && (

          <span
            className="
              rounded-full
              bg-white
              px-3
              py-1
              text-xs
              font-medium
              text-gray-600
            "
          >
            {event.event_date}
          </span>

        )}

      </div>

      {event.actors.length > 0 && (

        <div
          className="
            mt-3
            flex
            flex-wrap
            gap-2
          "
        >

          {event.actors.map(
            actor => (

              <span
                key={
                  `${event.event_id}-${actor}`
                }
                className="
                  rounded-full
                  bg-white
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

      {notes.length > 0 && (

        <div
          className="
            mt-5
            grid
            gap-3
            xl:grid-cols-2
          "
        >

          {notes.map(
            note => (

              <NoteCard
                key={
                  note.note_id
                }
                note={note}
                sourceNumberById={
                  sourceNumberById
                }
              />

            ),
          )}

        </div>

      )}

    </article>

  );

}

/* =========================================================
   COMPONENT
========================================================= */

export default function TouchNotebookPreview({
  notebook,
  sourceContentIds,
}: Props) {

  const sourceNumberById = (
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
    )
  );

  const noteById = (
    new Map(
      notebook.notes.map(
        note => [

          note.note_id,
          note,

        ],
      ),
    )
  );

  const eventById = (
    new Map(
      notebook.events.map(
        event => [

          event.event_id,
          event,

        ],
      ),
    )
  );

  return (

    <div className="space-y-8">

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <header
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

              <p
                className="
                  mt-2
                  text-sm
                  leading-6
                  text-gray-500
                "
              >
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
              {notebook.sections.length}
              {" "}
              sections
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
          </div>

        </div>

        {notebook.corpus_summary && (

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

            <p
              className="
                mt-2
                text-sm
                leading-6
                text-gray-700
              "
            >
              {notebook.corpus_summary}
            </p>

          </div>

        )}

      </header>

      {/* ================================================= */}
      {/* DOCUMENTARY PLAN */}
      {/* ================================================= */}

      {notebook.sections.length === 0 ? (

        <div
          className="
            rounded-xl
            border
            border-dashed
            border-gray-300
            bg-white
            p-10
            text-center
            text-sm
            text-gray-500
          "
        >
          No documentary section was produced.
        </div>

      ) : (

        <div className="space-y-8">

          {notebook.sections.map(
            (
              section,
              sectionIndex,
            ) => {

              const events = (
                section.event_ids
                  .map(
                    eventId =>
                      eventById.get(
                        eventId,
                      ),
                  )
                  .filter(
                    (
                      event,
                    ): event is TouchNotebookEvent => (
                      Boolean(
                        event,
                      )
                    ),
                  )
              );

              const standaloneNotes = (
                section.note_ids
                  .map(
                    noteId =>
                      noteById.get(
                        noteId,
                      ),
                  )
                  .filter(
                    (
                      note,
                    ): note is TouchEvidenceNote => (
                      Boolean(
                        note,
                      )
                    ),
                  )
              );

              return (

                <NotebookSection
                  key={
                    section.section_id
                  }
                  title={
                    `${sectionIndex + 1}. `
                    + section.title
                  }
                >

                  <div className="space-y-4">

                    {events.map(
                      event => (

                        <EventCard
                          key={
                            event.event_id
                          }
                          event={event}
                          noteById={
                            noteById
                          }
                          sourceNumberById={
                            sourceNumberById
                          }
                        />

                      ),
                    )}

                    {standaloneNotes.length > 0 && (

                      <div
                        className="
                          grid
                          gap-3
                          xl:grid-cols-2
                        "
                      >

                        {standaloneNotes.map(
                          note => (

                            <NoteCard
                              key={
                                note.note_id
                              }
                              note={note}
                              sourceNumberById={
                                sourceNumberById
                              }
                            />

                          ),
                        )}

                      </div>

                    )}

                  </div>

                </NotebookSection>

              );

            },
          )}

        </div>

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

                    <h4
                      className="
                        font-semibold
                        text-gray-900
                      "
                    >
                      {item.label}
                    </h4>

                    <SourceReferences
                      sourceContentIds={
                        item.source_content_ids
                      }
                      sourceNumberById={
                        sourceNumberById
                      }
                    />

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

                  <h4
                    className="
                      font-semibold
                      text-gray-900
                    "
                  >
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

                  <SourceReferences
                    sourceContentIds={
                      contradiction
                        .source_content_ids
                    }
                    sourceNumberById={
                      sourceNumberById
                    }
                  />

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

              <h4
                className="
                  font-semibold
                  text-emerald-800
                "
              >
                Strengths
              </h4>

              {notebook.corpus_strengths.length === 0 ? (

                <p
                  className="
                    mt-3
                    text-sm
                    text-gray-500
                  "
                >
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

                      <li
                        key={
                          `${strength}-${index}`
                        }
                      >
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

              <h4
                className="
                  font-semibold
                  text-amber-800
                "
              >
                Limits
              </h4>

              {notebook.corpus_limits.length === 0 ? (

                <p
                  className="
                    mt-3
                    text-sm
                    text-gray-500
                  "
                >
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

                      <li
                        key={
                          `${limit}-${index}`
                        }
                      >
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
