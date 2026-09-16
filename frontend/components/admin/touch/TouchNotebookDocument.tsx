"use client";

import type {
  TouchContentCandidate,
  TouchCorpusNotebook,
  TouchEvidenceNote,
  TouchNotebookEvent,
} from "@/types/touch";


/* =========================================================
   PROPS
========================================================= */

type Props = {
  notebook: TouchCorpusNotebook;
  sources: TouchContentCandidate[];
};


/* =========================================================
   GENERIC HELPERS
========================================================= */

function uniqueValues(
  values: string[],
): string[] {

  return Array.from(
    new Set(
      values.filter(
        Boolean,
      ),
    ),
  );

}


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

    return value;

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
   SOURCE REFERENCES
========================================================= */

function SourceReferences({
  sourceContentIds,
  sourceNumberById,
}: {
  sourceContentIds: string[];
  sourceNumberById: Map<string, number>;
}) {

  const references = (
    uniqueValues(
      sourceContentIds,
    )
      .map(
        contentId => ({

          contentId,

          number:
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
          number: number;
        } => (
          reference.number
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

    <span
      className="
        inline-flex
        flex-wrap
        items-center
        gap-1
        text-[11px]
        font-medium
        text-slate-400
      "
    >

      <span>
        [
      </span>

      {references.map(
        (
          reference,
          index,
        ) => (

          <span
            key={
              reference.contentId
            }
          >

            <a
              href={
                `#touch-document-source-`
                + reference.contentId
              }
              className="
                text-slate-500
                no-underline
                hover:text-blue-700
              "
            >
              {reference.number}
            </a>

            {
              index
              < references.length - 1
                ? ","
                : ""
            }

          </span>

        ),
      )}

      <span>
        ]
      </span>

    </span>

  );

}


/* =========================================================
   DOCUMENT SECTION
========================================================= */

function DocumentSection({
  title,
  children,
  className = "",
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
}) {

  return (

    <section
      className={`
        space-y-3
        ${className}
      `}
    >

      <div
        className="
          break-after-avoid
          border-b
          border-slate-300
          pb-2
        "
      >

        <h2
          className="
            text-xl
            font-semibold
            text-slate-900
          "
        >
          {title}
        </h2>

      </div>

      {children}

    </section>

  );

}


/* =========================================================
   EVIDENCE NOTE
========================================================= */

function EvidenceNote({
  note,
  sourceNumberById,
  showContext = true,
}: {
  note: TouchEvidenceNote;
  sourceNumberById: Map<string, number>;
  showContext?: boolean;
}) {

  const exceptionalStatus = (
    note.confidence === "LOW"
    || note.status !== "VALIDATED"
  );

  const context =
    uniqueValues([
      ...note.actors,
      ...note.geographies,
      ...note.dates,
    ]);

  return (

    <div
      className="
        break-inside-avoid
        border-l-2
        border-slate-200
        pl-3
      "
    >

      <div
        className="
          flex
          items-start
          gap-2
        "
      >

        <span
          className="
            mt-[9px]
            h-1.5
            w-1.5
            shrink-0
            rounded-full
            bg-slate-400
          "
        />

        <div className="min-w-0">

          <p
            className="
              text-sm
              font-medium
              leading-5
              text-slate-900
            "
          >
            {note.statement}
          </p>

          {note.explanation && (

            <p
              className="
                mt-1
                text-xs
                leading-5
                text-slate-600
              "
            >
              {note.explanation}
            </p>

          )}

          <div
            className="
              mt-1.5
              flex
              flex-wrap
              items-center
              gap-x-2
              gap-y-1
              text-[11px]
              text-slate-400
            "
          >

            {(
              showContext
              && context.length > 0
            ) && (

              <span>
                {
                  context.join(
                    " · ",
                  )
                }
              </span>

            )}

            {exceptionalStatus && (

              <span
                className="
                  rounded
                  bg-amber-50
                  px-1.5
                  py-0.5
                  font-medium
                  text-amber-700
                "
              >
                {[
                  note.confidence === "LOW"
                    ? "LOW"
                    : null,
                
                  note.status !== "VALIDATED"
                    ? note.status
                    : null,
                ]
                  .filter(Boolean)
                  .join(" · ")
                }
              </span>

            )}

            <SourceReferences
              sourceContentIds={
                note.source_content_ids
              }
              sourceNumberById={
                sourceNumberById
              }
            />

          </div>

        </div>

      </div>

    </div>

  );

}

/* =========================================================
   EVENT
========================================================= */

function EventBlock({
  event,
  notes,
  sourceNumberById,
}: {
  event: TouchNotebookEvent;
  notes: TouchEvidenceNote[];
  sourceNumberById: Map<string, number>;
}) {

  return (

    <article
      className="
        border-l-4
        border-blue-200
        pl-4
      "
    >

      <div
        className="
          break-after-avoid
          flex
          flex-wrap
          items-start
          justify-between
          gap-2
        "
      >

        <div>

          <p
            className="
              text-[10px]
              font-semibold
              uppercase
              tracking-wide
              text-blue-700
            "
          >
            Event
          </p>

          <h3
            className="
              mt-0.5
              text-base
              font-semibold
              leading-5
              text-slate-900
            "
          >
            {event.title}
          </h3>

        </div>

        {event.event_date && (

          <span
            className="
              text-xs
              font-medium
              text-slate-500
            "
          >
            {event.event_date}
          </span>

        )}

      </div>

      {event.actors.length > 0 && (

        <p
          className="
            mt-1
            text-[11px]
            text-slate-400
          "
        >
          {
            event.actors.join(
              " · ",
            )
          }
        </p>

      )}

      {notes.length > 0 && (

        <div className="mt-3 space-y-2.5">

          {notes.map(
            note => (

              <EvidenceNote
                key={
                  note.note_id
                }
                note={note}
                sourceNumberById={
                  sourceNumberById
                }
                showContext={false}
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

export default function TouchNotebookDocument({
  notebook,
  sources,
}: Props) {

  const sourceNumberById = (
    new Map(
      sources.map(
        (
          source,
          index,
        ) => [

          source.content_id,
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

    <article
      id="touch-notebook-document"
      className="
        touch-print-root
        mx-auto
        max-w-5xl
        overflow-hidden
        rounded-xl
        border
        border-slate-200
        bg-white
        shadow-sm
        print:max-w-none
        print:overflow-visible
        print:rounded-none
        print:border-0
        print:shadow-none
      "
    >

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <header
        className="
          bg-slate-950
          px-8
          py-8
          text-white
          print:bg-white
          print:px-0
          print:py-0
          print:text-slate-950
        "
      >

        <p
          className="
            text-xs
            font-semibold
            uppercase
            tracking-[0.2em]
            text-blue-300
            print:text-slate-500
          "
        >
          GetCurator Touch
        </p>

        <h1
          className="
            mt-3
            max-w-4xl
            text-3xl
            font-semibold
            leading-tight
          "
        >
          {notebook.subject}
        </h1>

        {notebook.objective && (

          <p
            className="
              mt-3
              max-w-3xl
              text-sm
              leading-6
              text-slate-300
              print:text-slate-600
            "
          >
            {notebook.objective}
          </p>

        )}

        <p
          className="
            mt-5
            text-xs
            text-slate-300
            print:text-slate-500
          "
        >
          {sources.length}
          {" sources · "}

          {notebook.sections.length}
          {" sections · "}

          {notebook.notes.length}
          {" notes · "}

          {
            new Intl.DateTimeFormat(
              "fr-FR",
              {
                day: "2-digit",
                month: "long",
                year: "numeric",
              },
            ).format(
              new Date(),
            )
          }
        </p>

      </header>

      {/* ================================================= */}
      {/* BODY */}
      {/* ================================================= */}

      <div
        className="
          space-y-8
          px-8
          py-8
          print:px-0
          print:py-6
        "
      >

        {/* ================================================= */}
        {/* CORPUS SUMMARY */}
        {/* ================================================= */}

        {notebook.corpus_summary && (

          <section
            className="
              break-inside-avoid
              border-l-4
              border-blue-300
              bg-blue-50
              px-4
              py-3
              print:bg-white
            "
          >

            <p
              className="
                text-[10px]
                font-semibold
                uppercase
                tracking-wide
                text-blue-700
              "
            >
              Corpus scope
            </p>

            <p
              className="
                mt-1
                text-sm
                leading-6
                text-slate-700
              "
            >
              {notebook.corpus_summary}
            </p>

          </section>

        )}

        {/* ================================================= */}
        {/* EXECUTIVE SUMMARY */}
        {/* ================================================= */}
        
        {notebook.executive_summary?.length > 0 && (
        
          <section className="space-y-4 print:break-after-page">
        
            <div
              className="
                break-after-avoid
                border-b
                border-slate-300
                pb-2
              "
            >
              <h2 className="text-xl font-semibold text-slate-900">
                Executive summary
              </h2>
            </div>
        
            <ol className="space-y-3">
        
              {notebook.executive_summary.map(
                (item, index) => (
        
                  <li
                    key={item.summary_id}
                    className="
                      break-inside-avoid
                      flex
                      gap-3
                      border-l-2
                      border-blue-300
                      pl-3
                    "
                  >
        
                    <span
                      className="
                        shrink-0
                        text-sm
                        font-semibold
                        text-blue-700
                      "
                    >
                      {index + 1}.
                    </span>
        
                    <div className="min-w-0">
        
                      <p
                        className="
                          text-sm
                          leading-6
                          text-slate-900
                        "
                      >
                        {item.statement}
                      </p>
        
                      <div className="mt-1">
        
                        <SourceReferences
                          sourceContentIds={
                            item.source_content_ids
                          }
                          sourceNumberById={
                            sourceNumberById
                          }
                        />
        
                      </div>
        
                    </div>
        
                  </li>
        
                ),
              )}
        
            </ol>
        
          </section>
        
        )}

        {/* ================================================= */}
        {/* DOCUMENTARY PLAN */}
        {/* ================================================= */}

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

              <DocumentSection
                key={
                  section.section_id
                }
                title={
                  `${sectionIndex + 1}. `
                  + section.title
                }
              >

                <div className="space-y-5">

                  {events.map(
                    event => {

                      const eventNotes = (
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

                        <EventBlock
                          key={
                            event.event_id
                          }
                          event={event}
                          notes={
                            eventNotes
                          }
                          sourceNumberById={
                            sourceNumberById
                          }
                        />

                      );

                    },
                  )}

                  {standaloneNotes.length > 0 && (

                    <div className="space-y-2.5">

                      {standaloneNotes.map(
                        note => (

                          <EvidenceNote
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

              </DocumentSection>

            );

          },
        )}

        {/* ================================================= */}
        {/* TIMELINE */}
        {/* ================================================= */}

        {notebook.timeline.length > 0 && (

          <DocumentSection title="Timeline">

            <div
              className="
                grid
                gap-x-6
                gap-y-2
                md:grid-cols-2
                print:grid-cols-2
              "
            >

              {notebook.timeline.map(
                (
                  item,
                  index,
                ) => (

                  <div
                    key={
                      `${item.date}-${item.label}-${index}`
                    }
                    className="
                      break-inside-avoid
                      border-b
                      border-slate-200
                      py-2
                    "
                  >

                    <p
                      className="
                        text-xs
                        font-semibold
                        text-blue-700
                      "
                    >
                      {item.date}
                    </p>

                    <div
                      className="
                        mt-0.5
                        flex
                        flex-wrap
                        items-center
                        gap-2
                      "
                    >

                      <p
                        className="
                          text-sm
                          font-medium
                          text-slate-900
                        "
                      >
                        {item.label}
                      </p>

                      <SourceReferences
                        sourceContentIds={
                          item.source_content_ids
                        }
                        sourceNumberById={
                          sourceNumberById
                        }
                      />

                    </div>

                  </div>

                ),
              )}

            </div>

          </DocumentSection>

        )}

        {/* ================================================= */}
        {/* CONTRADICTIONS */}
        {/* ================================================= */}

        {notebook.contradictions.length > 0 && (

          <DocumentSection
            title="Source discrepancies"
          >

            <div className="space-y-2">

              {notebook.contradictions.map(
                (
                  contradiction,
                  index,
                ) => (

                  <div
                    key={
                      `${contradiction.subject}-${index}`
                    }
                    className="
                      break-inside-avoid
                      border-l-2
                      border-amber-300
                      pl-3
                    "
                  >

                    <p
                      className="
                        text-sm
                        font-semibold
                        text-slate-900
                      "
                    >
                      {contradiction.subject}
                    </p>

                    <p
                      className="
                        mt-1
                        text-xs
                        leading-5
                        text-slate-600
                      "
                    >
                      {contradiction.description}
                    </p>

                    {contradiction.resolution && (

                      <p
                        className="
                          mt-1
                          text-xs
                          leading-5
                          text-slate-600
                        "
                      >
                        <strong>
                          Resolution:
                        </strong>
                        {" "}
                        {contradiction.resolution}
                      </p>

                    )}

                    <div className="mt-1">

                      <SourceReferences
                        sourceContentIds={
                          contradiction
                            .source_content_ids
                        }
                        sourceNumberById={
                          sourceNumberById
                        }
                      />

                    </div>

                  </div>

                ),
              )}

            </div>

          </DocumentSection>

        )}

        {/* ================================================= */}
        {/* CORPUS ASSESSMENT */}
        {/* ================================================= */}

        {(
          notebook.corpus_strengths.length > 0
          || notebook.corpus_limits.length > 0
        ) && (

          <DocumentSection title="Corpus assessment">

            <div
              className="
                grid
                gap-5
                md:grid-cols-2
                print:grid-cols-2
              "
            >

              <div>

                <h3
                  className="
                    text-sm
                    font-semibold
                    text-emerald-800
                  "
                >
                  Strengths
                </h3>

                {notebook.corpus_strengths.length > 0 ? (

                  <ul
                    className="
                      mt-2
                      list-disc
                      space-y-1
                      pl-4
                      text-xs
                      leading-5
                      text-slate-600
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

                ) : (

                  <p
                    className="
                      mt-2
                      text-xs
                      text-slate-400
                    "
                  >
                    No specific strengths identified.
                  </p>

                )}

              </div>

              <div>

                <h3
                  className="
                    text-sm
                    font-semibold
                    text-amber-800
                  "
                >
                  Limits
                </h3>

                {notebook.corpus_limits.length > 0 ? (

                  <ul
                    className="
                      mt-2
                      list-disc
                      space-y-1
                      pl-4
                      text-xs
                      leading-5
                      text-slate-600
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

                ) : (

                  <p
                    className="
                      mt-2
                      text-xs
                      text-slate-400
                    "
                  >
                    No specific limits identified.
                  </p>

                )}

              </div>

            </div>

          </DocumentSection>

        )}
        {/* ================================================= */}
        {/* SOURCES */}
        {/* ================================================= */}

        <DocumentSection
          title="Sources"
          className="print:break-before-page"
        >

          <ol
            className="
              grid
              gap-x-6
              gap-y-2
              md:grid-cols-2
              print:grid-cols-2
            "
          >

            {sources.map(
              (
                source,
                index,
              ) => {

                const publishedAt =
                  formatDate(
                    source.published_at,
                  );

                return (

                  <li
                    id={
                      `touch-document-source-`
                      + source.content_id
                    }
                    key={
                      source.content_id
                    }
                    className="
                      break-inside-avoid
                      border-b
                      border-slate-200
                      py-2
                    "
                  >

                    <div
                      className="
                        flex
                        items-start
                        gap-2
                      "
                    >

                      <span
                        className="
                          shrink-0
                          text-xs
                          font-semibold
                          text-slate-400
                        "
                      >
                        {index + 1}.
                      </span>

                      <div className="min-w-0">

                        {source.source_url ? (

                          <a
                            href={
                              source.source_url
                            }
                            target="_blank"
                            rel="noreferrer"
                            className="
                              text-xs
                              font-semibold
                              leading-5
                              text-slate-900
                              no-underline
                              hover:text-blue-700
                            "
                          >
                            {source.title}
                          </a>

                        ) : (

                          <p
                            className="
                              text-xs
                              font-semibold
                              leading-5
                              text-slate-900
                            "
                          >
                            {source.title}
                          </p>

                        )}

                        <p
                          className="
                            mt-0.5
                            text-[10px]
                            leading-4
                            text-slate-400
                          "
                        >
                          {
                            [
                              source.source_title,
                              publishedAt,
                            ]
                              .filter(
                                Boolean,
                              )
                              .join(
                                " · ",
                              )
                          }
                        </p>

                      </div>

                    </div>

                  </li>

                );

              },
            )}

          </ol>

        </DocumentSection>

      </div>

    </article>

  );

}
