"use client";

import type {
  TouchContentCandidate,
  TouchCorpusNotebook,
  TouchEvidenceNote,
  TouchNotebookEvent,
  TouchNotebookNumber,
} from "@/types/touch";


/* =========================================================
   PROPS
========================================================= */

type Props = {
  notebook: TouchCorpusNotebook;
  sources: TouchContentCandidate[];
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

  const date = new Date(value);

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
      month: "long",
      year: "numeric",
    },
  ).format(date);

}


/* =========================================================
   FORMAT NUMBER
========================================================= */

function formatNumberValue(
  value:
    | string
    | number
    | null,
): string {

  if (
    value === null
    || value === ""
  ) {
    return "—";
  }

  if (
    typeof value === "number"
  ) {

    return new Intl.NumberFormat(
      "fr-FR",
      {
        maximumFractionDigits: 4,
      },
    ).format(value);

  }

  return value;

}


function formatNumberScale(
  scale: string | null,
): string {

  if (!scale) {
    return "";
  }

  const labels:
    Record<string, string> = {

    THOUSAND:
      "milliers",

    MILLION:
      "millions",

    BILLION:
      "milliards",

    TRILLION:
      "billions",

  };

  return (
    labels[scale.toUpperCase()]
    ?? scale.toLowerCase()
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
    Array.from(
      new Set(sourceContentIds),
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
        } =>
          reference.number !== undefined,
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

          <a
            key={reference.contentId}
            href={
              `#touch-document-source-`
              + reference.contentId
            }
            className="
              inline-flex
              h-6
              min-w-6
              items-center
              justify-center
              rounded-full
              bg-slate-100
              px-2
              text-xs
              font-semibold
              text-slate-600
              no-underline
              hover:bg-slate-200
            "
            title={
              `Voir la source ${reference.number}`
            }
          >
            {reference.number}
          </a>

        ),
      )}

    </div>

  );

}


/* =========================================================
   DOCUMENT SECTION
========================================================= */

function DocumentSection({
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

      <div
        className="
          border-b
          border-slate-200
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

        {description && (

          <p
            className="
              mt-1
              text-sm
              leading-6
              text-slate-500
            "
          >
            {description}
          </p>

        )}

      </div>

      {children}

    </section>

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
  sourceNumberById: Map<string, number>;
}) {

  return (

    <article
      className="
        break-inside-avoid
        rounded-lg
        border
        border-slate-200
        bg-white
        p-4
      "
    >

      <p
        className="
          text-sm
          font-semibold
          leading-6
          text-slate-900
        "
      >
        {note.statement}
      </p>

      {note.explanation && (

        <p
          className="
            mt-1.5
            text-sm
            leading-6
            text-slate-600
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
            gap-x-4
            gap-y-1
            text-xs
            text-slate-500
          "
        >

          {note.actors.length > 0 && (
            <span>
              {note.actors.join(" · ")}
            </span>
          )}

          {note.geographies.length > 0 && (
            <span>
              {note.geographies.join(" · ")}
            </span>
          )}

          {note.dates.length > 0 && (
            <span>
              {note.dates.join(" · ")}
            </span>
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
   NUMBER CARD
========================================================= */

function NumberCard({
  number,
  sourceNumberById,
}: {
  number: TouchNotebookNumber;
  sourceNumberById: Map<string, number>;
}) {

  const entityLabels = (
    number.entities
      .map(
        entity =>
          entity.entity_label,
      )
      .filter(
        (
          label,
        ): label is string =>
          Boolean(label),
      )
  );

  const hasRange = (
    number.value_min !== null
    && number.value_max !== null
  );

  return (

    <article
      className="
        break-inside-avoid
        rounded-lg
        border
        border-violet-200
        bg-violet-50/30
        p-4
        print:bg-white
      "
    >

      <div
        className="
          flex
          flex-wrap
          items-baseline
          gap-x-2
          gap-y-1
        "
      >

        <p
          className="
            text-2xl
            font-semibold
            text-slate-900
          "
        >

          {hasRange ? (

            <>
              {
                formatNumberValue(
                  number.value_min,
                )
              }

              {" – "}

              {
                formatNumberValue(
                  number.value_max,
                )
              }
            </>

          ) : (

            formatNumberValue(
              number.value,
            )

          )}

        </p>

        {number.scale && (

          <span
            className="
              text-sm
              font-semibold
              text-slate-700
            "
          >
            {
              formatNumberScale(
                number.scale,
              )
            }
          </span>

        )}

        {number.unit && (

          <span
            className="
              text-sm
              font-semibold
              text-slate-700
            "
          >
            {number.unit}
          </span>

        )}

      </div>

      {number.label && (

        <p
          className="
            mt-2
            text-sm
            font-semibold
            leading-5
            text-slate-800
          "
        >
          {number.label}
        </p>

      )}

      {(
        number.metric_type
        || entityLabels.length > 0
      ) && (

        <div
          className="
            mt-3
            flex
            flex-wrap
            gap-1.5
          "
        >

          {number.metric_type && (

            <span
              className="
                rounded
                bg-violet-100
                px-2
                py-1
                text-xs
                font-medium
                text-violet-700
              "
            >
              {number.metric_type}
            </span>

          )}

          {entityLabels.map(
            (
              label,
              index,
            ) => (

              <span
                key={
                  `${number.number_id}-${label}-${index}`
                }
                className="
                  rounded
                  bg-white
                  px-2
                  py-1
                  text-xs
                  text-slate-600
                "
              >
                {label}
              </span>

            ),
          )}

        </div>

      )}

      {(
        number.zone
        || number.period_label
      ) && (

        <div
          className="
            mt-3
            space-y-1
            text-xs
            text-slate-500
          "
        >

          {number.zone && (
            <p>
              Zone :
              {" "}
              {number.zone}
            </p>
          )}

          {number.period_label && (
            <p>
              Période :
              {" "}
              {number.period_label}
            </p>
          )}

        </div>

      )}

      <SourceReferences
        sourceContentIds={
          number.source_content_ids
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
  numberById,
  sourceNumberById,
}: {
  event: TouchNotebookEvent;
  noteById: Map<string, TouchEvidenceNote>;
  numberById: Map<string, TouchNotebookNumber>;
  sourceNumberById: Map<string, number>;
}) {

  const notes = (
    event.note_ids
      .map(
        noteId =>
          noteById.get(noteId),
      )
      .filter(
        (
          note,
        ): note is TouchEvidenceNote =>
          Boolean(note),
      )
  );

  const numbers = (
    event.number_ids
      .map(
        numberId =>
          numberById.get(numberId),
      )
      .filter(
        (
          number,
        ): number is TouchNotebookNumber =>
          Boolean(number),
      )
  );

  return (

    <article
      className="
        break-inside-avoid
        rounded-xl
        border
        border-slate-200
        bg-slate-50
        p-5
        print:bg-white
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
              text-blue-700
            "
          >
            Événement
          </p>

          <h3
            className="
              mt-1
              text-base
              font-semibold
              text-slate-900
            "
          >
            {event.title}
          </h3>

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
              text-slate-600
            "
          >
            {event.event_date}
          </span>

        )}

      </div>

      {event.description && (

        <p
          className="
            mt-2
            text-sm
            leading-6
            text-slate-600
          "
        >
          {event.description}
        </p>

      )}

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
                  text-slate-600
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
            mt-4
            grid
            gap-3
            md:grid-cols-2
            print:grid-cols-2
          "
        >

          {notes.map(
            note => (

              <NoteCard
                key={note.note_id}
                note={note}
                sourceNumberById={
                  sourceNumberById
                }
              />

            ),
          )}

        </div>

      )}

      {numbers.length > 0 && (

        <div
          className="
            mt-4
            grid
            gap-3
            md:grid-cols-2
            print:grid-cols-2
          "
        >

          {numbers.map(
            number => (

              <NumberCard
                key={number.number_id}
                number={number}
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

  const numberById = (
    new Map(
      notebook.validated_numbers.map(
        number => [
          number.number_id,
          number,
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
          py-10
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
            mt-4
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
              mt-4
              max-w-3xl
              text-base
              leading-7
              text-slate-300
              print:text-slate-600
            "
          >
            {notebook.objective}
          </p>

        )}

        <div
          className="
            mt-6
            flex
            flex-wrap
            gap-3
            text-xs
            text-slate-300
            print:text-slate-500
          "
        >

          <span>
            {sources.length}
            {" "}
            sources analysées
          </span>

          <span aria-hidden="true">
            ·
          </span>

          <span>
            {notebook.sections.length}
            {" "}
            parties documentaires
          </span>

          <span aria-hidden="true">
            ·
          </span>

          <span>
            {notebook.validated_numbers.length}
            {" "}
            chiffres certifiés
          </span>

          <span aria-hidden="true">
            ·
          </span>

          <span>
            Produit le
            {" "}
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
          </span>

        </div>

      </header>

      {/* ================================================= */}
      {/* BODY */}
      {/* ================================================= */}

      <div
        className="
          space-y-10
          px-8
          py-10
          print:px-0
          print:py-8
        "
      >

        {/* ================================================= */}
        {/* CORPUS SUMMARY */}
        {/* ================================================= */}

        {notebook.corpus_summary && (

          <section
            className="
              break-inside-avoid
              rounded-xl
              border
              border-blue-100
              bg-blue-50
              p-5
              print:border-slate-300
              print:bg-white
            "
          >

            <p
              className="
                text-xs
                font-semibold
                uppercase
                tracking-wide
                text-blue-700
                print:text-slate-500
              "
            >
              Périmètre documentaire
            </p>

            <p
              className="
                mt-2
                text-sm
                leading-7
                text-slate-700
              "
            >
              {notebook.corpus_summary}
            </p>

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
                    eventById.get(eventId),
                )
                .filter(
                  (
                    event,
                  ): event is TouchNotebookEvent =>
                    Boolean(event),
                )
            );

            const standaloneNotes = (
              section.note_ids
                .map(
                  noteId =>
                    noteById.get(noteId),
                )
                .filter(
                  (
                    note,
                  ): note is TouchEvidenceNote =>
                    Boolean(note),
                )
            );

            const standaloneNumbers = (
              section.number_ids
                .map(
                  numberId =>
                    numberById.get(numberId),
                )
                .filter(
                  (
                    number,
                  ): number is TouchNotebookNumber =>
                    Boolean(number),
                )
            );

            return (

              <DocumentSection
                key={section.section_id}
                title={
                  `${sectionIndex + 1}. `
                  + section.title
                }
                description={
                  section.description
                }
              >

                <div className="space-y-4">

                  {events.map(
                    event => (

                      <EventCard
                        key={event.event_id}
                        event={event}
                        noteById={noteById}
                        numberById={numberById}
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
                        md:grid-cols-2
                        print:grid-cols-2
                      "
                    >

                      {standaloneNotes.map(
                        note => (

                          <NoteCard
                            key={note.note_id}
                            note={note}
                            sourceNumberById={
                              sourceNumberById
                            }
                          />

                        ),
                      )}

                    </div>

                  )}

                  {standaloneNumbers.length > 0 && (

                    <div
                      className="
                        grid
                        gap-3
                        md:grid-cols-2
                        lg:grid-cols-3
                        print:grid-cols-3
                      "
                    >

                      {standaloneNumbers.map(
                        number => (

                          <NumberCard
                            key={number.number_id}
                            number={number}
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

          <DocumentSection title="Repères chronologiques">

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
                      break-inside-avoid
                      grid
                      gap-2
                      rounded-lg
                      border
                      border-slate-200
                      p-4
                      sm:grid-cols-[140px_minmax(0,1fr)]
                    "
                  >

                    <p
                      className="
                        text-sm
                        font-semibold
                        text-blue-700
                      "
                    >
                      {item.date}
                    </p>

                    <div>

                      <h3
                        className="
                          text-sm
                          font-semibold
                          text-slate-900
                        "
                      >
                        {item.label}
                      </h3>

                      {item.description && (

                        <p
                          className="
                            mt-1
                            text-sm
                            leading-6
                            text-slate-600
                          "
                        >
                          {item.description}
                        </p>

                      )}

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

          </DocumentSection>

        )}

        {/* ================================================= */}
        {/* CONTRADICTIONS */}
        {/* ================================================= */}

        {notebook.contradictions.length > 0 && (

          <DocumentSection
            title="Divergences entre les sources"
          >

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
                      break-inside-avoid
                      rounded-lg
                      border
                      border-amber-200
                      bg-amber-50
                      p-4
                      print:bg-white
                    "
                  >

                    <h3
                      className="
                        text-sm
                        font-semibold
                        text-slate-900
                      "
                    >
                      {contradiction.subject}
                    </h3>

                    <p
                      className="
                        mt-2
                        text-sm
                        leading-6
                        text-slate-600
                      "
                    >
                      {contradiction.description}
                    </p>

                    {contradiction.resolution && (

                      <p
                        className="
                          mt-2
                          text-sm
                          leading-6
                          text-slate-700
                        "
                      >
                        <strong>
                          Élément de résolution :
                        </strong>
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

          </DocumentSection>

        )}

        {/* ================================================= */}
        {/* CORPUS ASSESSMENT */}
        {/* ================================================= */}

        {(
          notebook.corpus_strengths.length > 0
          || notebook.corpus_limits.length > 0
        ) && (

          <DocumentSection title="Évaluation du corpus">

            <div
              className="
                grid
                gap-4
                md:grid-cols-2
                print:grid-cols-2
              "
            >

              <div
                className="
                  break-inside-avoid
                  rounded-lg
                  border
                  border-emerald-200
                  bg-emerald-50
                  p-4
                  print:bg-white
                "
              >

                <h3
                  className="
                    text-sm
                    font-semibold
                    text-emerald-800
                  "
                >
                  Points forts
                </h3>

                {notebook.corpus_strengths.length === 0 ? (

                  <p
                    className="
                      mt-3
                      text-sm
                      text-slate-500
                    "
                  >
                    Aucun point fort spécifique identifié.
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
                      text-slate-700
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
                  break-inside-avoid
                  rounded-lg
                  border
                  border-amber-200
                  bg-amber-50
                  p-4
                  print:bg-white
                "
              >

                <h3
                  className="
                    text-sm
                    font-semibold
                    text-amber-800
                  "
                >
                  Limites
                </h3>

                {notebook.corpus_limits.length === 0 ? (

                  <p
                    className="
                      mt-3
                      text-sm
                      text-slate-500
                    "
                  >
                    Aucune limite spécifique identifiée.
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
                      text-slate-700
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

          </DocumentSection>

        )}

        {/* ================================================= */}
        {/* SOURCES */}
        {/* ================================================= */}

        <DocumentSection
          title="Sources"
          description={
            "Corpus sélectionné et analysé par GetCurator."
          }
        >

          <ol className="space-y-3">

            {sources.map(
              (
                source,
                index,
              ) => {

                const publishedAt = (
                  formatDate(
                    source.published_at,
                  )
                );

                return (

                  <li
                    id={
                      `touch-document-source-`
                      + source.content_id
                    }
                    key={source.content_id}
                    className="
                      break-inside-avoid
                      grid
                      gap-3
                      rounded-lg
                      border
                      border-slate-200
                      p-4
                      sm:grid-cols-[32px_minmax(0,1fr)]
                    "
                  >

                    <span
                      className="
                        flex
                        h-7
                        w-7
                        items-center
                        justify-center
                        rounded-full
                        bg-slate-900
                        text-xs
                        font-semibold
                        text-white
                      "
                    >
                      {index + 1}
                    </span>

                    <div className="min-w-0">

                      <p
                        className="
                          text-sm
                          font-semibold
                          leading-6
                          text-slate-900
                        "
                      >
                        {source.title}
                      </p>

                      <p
                        className="
                          mt-1
                          text-xs
                          leading-5
                          text-slate-500
                        "
                      >

                        {source.source_title}

                        {(
                          source.source_title
                          && publishedAt
                        ) && (
                          <>
                            {" · "}
                          </>
                        )}

                        {publishedAt}

                      </p>

                      {source.source_url && (

                        <a
                          href={source.source_url}
                          target="_blank"
                          rel="noreferrer"
                          className="
                            mt-2
                            inline-block
                            break-all
                            text-xs
                            font-medium
                            text-blue-700
                            hover:underline
                            print:text-slate-600
                          "
                        >
                          {source.source_url}
                        </a>

                      )}

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
