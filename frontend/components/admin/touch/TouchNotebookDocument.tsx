"use client";

import type {
  TouchContentCandidate,
  TouchCorpusNotebook,
  TouchEvidenceNote,
  TouchEvidenceNoteType,
} from "@/types/touch";


/* =========================================================
   PROPS
========================================================= */

type Props = {
  notebook: TouchCorpusNotebook;

  sources: TouchContentCandidate[];
};


/* =========================================================
   NOTE GROUPS
========================================================= */

type NoteGroup = {
  title: string;
  description: string;

  types: TouchEvidenceNoteType[];
};


const NOTE_GROUPS: NoteGroup[] = [
  {
    title: "Faits documentés",
    description:
      "Les informations établies par les sources sélectionnées.",
    types: [
      "FACT",
      "MILESTONE",
    ],
  },
  {
    title: "Fonctionnement",
    description:
      "Les mécanismes, processus et modalités décrits dans le corpus.",
    types: [
      "MECHANISM",
    ],
  },
  {
    title: "Éléments de contexte",
    description:
      "Les exemples, comparaisons et lectures rapportées par les sources.",
    types: [
      "EXAMPLE",
      "COMPARISON",
      "STRATEGIC_READING",
    ],
  },
  {
    title: "Tensions et limites",
    description:
      "Les restrictions, incertitudes et points de tension documentés.",
    types: [
      "TENSION",
      "LIMITATION",
      "UNCERTAINTY",
    ],
  },
];


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

    return value;

  }

  return new Intl.DateTimeFormat(
    "fr-FR",
    {
      day: "2-digit",
      month: "long",
      year: "numeric",
    },
  ).format(
    date,
  );

}


/* =========================================================
   UNIQUE IDS
========================================================= */

function uniqueIds(
  values: string[],
): string[] {

  return Array.from(
    new Set(
      values,
    ),
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

  const references =
    uniqueIds(
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
        } =>
          reference.number !== undefined,
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
            key={
              reference.contentId
            }
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
              {note.actors.join(
                " · ",
              )}
            </span>

          )}

          {note.geographies.length > 0 && (

            <span>
              {note.geographies.join(
                " · ",
              )}
            </span>

          )}

          {note.dates.length > 0 && (

            <span>
              {note.dates.join(
                " · ",
              )}
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

    <section
      className="
        break-inside-avoid-page
        space-y-4
      "
    >

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
   COMPONENT
========================================================= */

export default function TouchNotebookDocument({
  notebook,
  sources,
}: Props) {

  const sourceNumberById =
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
    );

  const visibleNotes =
    notebook.notes.filter(
      note =>
        note.status
        !== "CONTRADICTED",
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
      {/* DOCUMENT HEADER */}
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
            {visibleNotes.length}
            {" "}
            notes consolidées
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
      {/* DOCUMENT BODY */}
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
        {/* DIMENSIONS */}
        {/* ================================================= */}

        {notebook.dimensions.length > 0 && (

          <DocumentSection
            title="Dimensions documentées"
            description={
              "Les principaux aspects couverts par "
              + "les sources sélectionnées."
            }
          >

            <div
              className="
                grid
                gap-4
                md:grid-cols-2
                print:grid-cols-2
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
                      break-inside-avoid
                      rounded-lg
                      border
                      border-slate-200
                      p-4
                    "
                  >

                    <h3
                      className="
                        text-sm
                        font-semibold
                        text-slate-900
                      "
                    >
                      {dimension.label}
                    </h3>

                    <p
                      className="
                        mt-2
                        text-sm
                        leading-6
                        text-slate-600
                      "
                    >
                      {dimension.summary}
                    </p>

                    <SourceReferences
                      sourceContentIds={
                        dimension
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
        {/* NOTE GROUPS */}
        {/* ================================================= */}

        {NOTE_GROUPS.map(
          group => {

            const notes =
              visibleNotes.filter(
                note =>
                  group.types.includes(
                    note.note_type,
                  ),
              );

            if (
              notes.length === 0
            ) {

              return null;

            }

            return (

              <DocumentSection
                key={group.title}
                title={group.title}
                description={
                  group.description
                }
              >

                <div
                  className="
                    grid
                    gap-3
                    md:grid-cols-2
                    print:grid-cols-2
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
                          item
                            .source_content_ids
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
        {/* VALIDATED NUMBERS */}
        {/* ================================================= */}

        {notebook.validated_numbers.length > 0 && (

          <DocumentSection title="Chiffres documentés">

            <div
              className="
                grid
                gap-4
                sm:grid-cols-2
                lg:grid-cols-3
                print:grid-cols-3
              "
            >

              {notebook.validated_numbers.map(
                number => (

                  <article
                    key={
                      number.number_id
                    }
                    className="
                      break-inside-avoid
                      rounded-lg
                      border
                      border-slate-200
                      p-4
                    "
                  >

                    <p
                      className="
                        text-2xl
                        font-semibold
                        text-slate-900
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

                    <p
                      className="
                        mt-1
                        text-sm
                        font-semibold
                        text-slate-800
                      "
                    >
                      {number.metric}
                    </p>

                    {number.context && (

                      <p
                        className="
                          mt-2
                          text-sm
                          leading-6
                          text-slate-600
                        "
                      >
                        {number.context}
                      </p>

                    )}

                    <div
                      className="
                        mt-3
                        space-y-1
                        text-xs
                        text-slate-500
                      "
                    >

                      {number.actor && (
                        <p>
                          {number.actor}
                        </p>
                      )}

                      {number.geography && (
                        <p>
                          {number.geography}
                        </p>
                      )}

                      {number.period && (
                        <p>
                          {number.period}
                        </p>
                      )}

                    </div>

                    <SourceReferences
                      sourceContentIds={
                        number
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
                        {
                          contradiction
                            .resolution
                        }
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
        {/* CORPUS LIMITS */}
        {/* ================================================= */}

        {notebook.corpus_limits.length > 0 && (

          <DocumentSection
            title="Ce que le corpus ne permet pas d’établir"
          >

            <ul
              className="
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
                          href={
                            source.source_url
                          }
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
