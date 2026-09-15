"use client";

import type {
  TouchContentCandidate,
  TouchCorpusNotebook,
  TouchEvidenceNote,
  TouchNotebookEvent,
  TouchNotebookNumber,
} from "@/types/touch";


/* =========================================================
   CONFIGURATION
========================================================= */

const MAX_FEATURED_NUMBERS_PER_SECTION = 4;


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
      values.filter(Boolean),
    ),
  );

}


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
      month: "short",
      year: "numeric",
    },
  ).format(date);

}


/* =========================================================
   NUMBER FORMATTERS
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

  const numericValue = Number(
    value
  );

  if (
    !Number.isNaN(
      numericValue
    )
  ) {

    return new Intl.NumberFormat(
      "fr-FR",
      {
        maximumFractionDigits: 4,
      },
    ).format(
      numericValue
    );

  }

  return String(value);

}


function isSingleValue(
  value:
    | string
    | number
    | null,
): boolean {

  if (
    value === null
    || value === ""
  ) {
    return false;
  }

  return Number(value) === 1;

}


function formatNumberScale(
  scale: string | null,
  value:
    | string
    | number
    | null,
): string {

  if (!scale) {
    return "";
  }

  const normalized =
    scale.toUpperCase();

  if (
    normalized === "NONE"
    || normalized === "UNIT"
  ) {
    return "";
  }

  const singular =
    isSingleValue(value);

  const labels:
    Record<
      string,
      [string, string]
    > = {

    THOUSAND:
      [
        "millier",
        "milliers",
      ],

    MILLION:
      [
        "million",
        "millions",
      ],

    BILLION:
      [
        "milliard",
        "milliards",
      ],

    TRILLION:
      [
        "billion",
        "billions",
      ],

  };

  const label =
    labels[normalized];

  if (!label) {
    return scale.toLowerCase();
  }

  return singular
    ? label[0]
    : label[1];

}


function formatNumberUnit(
  unit: string | null,
): string {

  if (!unit) {
    return "";
  }

  const normalized =
    unit.toUpperCase();

  const labels:
    Record<string, string> = {

    NONE:
      "",

    PERCENT:
      "%",

    USD:
      "USD",

    EUR:
      "EUR",

    GBP:
      "GBP",

    USERS:
      "utilisateurs",

    ACCOUNTS:
      "comptes",

    LOCATIONS:
      "marchés",

  };

  return (
    labels[normalized]
    ?? unit
  );

}


function formatNumberHeadline(
  number: TouchNotebookNumber,
): string {

  const hasRange = (
    number.value_min !== null
    && number.value_max !== null
  );

  const value = hasRange
    ? (
        formatNumberValue(
          number.value_min,
        )
        + " – "
        + formatNumberValue(
          number.value_max,
        )
      )
    : formatNumberValue(
        number.value,
      );

  const scale =
    formatNumberScale(
      number.scale,
      number.value,
    );

  const unit =
    formatNumberUnit(
      number.unit,
    );

  return [
    value,
    scale,
    unit,
  ]
    .filter(Boolean)
    .join(" ");

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
      sourceContentIds
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

          <span key={reference.contentId}>

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
  description,
  children,
  className = "",
}: {
  title: string;
  description?: string;
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

        {description && (

          <p
            className="
              mt-1
              text-sm
              leading-5
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
    note.confidence !== "HIGH"
    || note.status !== "VALIDATED"
  );

  const context = uniqueValues([
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

            {showContext && context.length > 0 && (

              <span>
                {context.join(" · ")}
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
                {note.confidence}
                {" · "}
                {note.status}
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
   FEATURED NUMBER
========================================================= */

function FeaturedNumber({
  number,
  sourceNumberById,
}: {
  number: TouchNotebookNumber;
  sourceNumberById: Map<string, number>;
}) {

  const entityLabels = uniqueValues(
    number.entities
      .map(
        entity =>
          entity.entity_label
          ?? "",
      ),
  );

  const context = [
    number.zone
      && number.zone !== "UNKNOWN"
        ? number.zone
        : "",

    number.period_label
      && number.period_label !== "UNKNOWN"
        ? number.period_label
        : "",

    ...entityLabels,
  ].filter(Boolean);

  return (

    <div
      className="
        break-inside-avoid
        border-l-2
        border-violet-300
        pl-3
      "
    >

      <p
        className="
          text-lg
          font-semibold
          text-slate-900
        "
      >
        {formatNumberHeadline(number)}
      </p>

      {number.label && (

        <p
          className="
            text-xs
            font-medium
            leading-5
            text-slate-700
          "
        >
          {number.label}
        </p>

      )}

      <div
        className="
          mt-1
          flex
          flex-wrap
          items-center
          gap-x-2
          text-[11px]
          text-slate-400
        "
      >

        {context.length > 0 && (

          <span>
            {context.join(" · ")}
          </span>

        )}

        <SourceReferences
          sourceContentIds={
            number.source_content_ids
          }
          sourceNumberById={
            sourceNumberById
          }
        />

      </div>

    </div>

  );

}


/* =========================================================
   NUMBER REGISTER ITEM
========================================================= */

function NumberRegisterItem({
  number,
  sourceNumberById,
}: {
  number: TouchNotebookNumber;
  sourceNumberById: Map<string, number>;
}) {

  const entities = uniqueValues(
    number.entities
      .map(
        entity =>
          entity.entity_label
          ?? "",
      ),
  );

  const context = [
    number.metric_type,
    ...entities,
    (
      number.zone
      && number.zone !== "UNKNOWN"
        ? number.zone
        : ""
    ),
    (
      number.period_label
      && number.period_label !== "UNKNOWN"
        ? number.period_label
        : ""
    ),
  ].filter(Boolean);

  return (

    <li
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
          items-baseline
          justify-between
          gap-3
        "
      >

        <p
          className="
            text-sm
            font-semibold
            text-slate-900
          "
        >
          {formatNumberHeadline(number)}
        </p>

        <SourceReferences
          sourceContentIds={
            number.source_content_ids
          }
          sourceNumberById={
            sourceNumberById
          }
        />

      </div>

      {number.label && (

        <p
          className="
            mt-0.5
            text-xs
            font-medium
            leading-4
            text-slate-700
          "
        >
          {number.label}
        </p>

      )}

      {context.length > 0 && (

        <p
          className="
            mt-0.5
            text-[10px]
            leading-4
            text-slate-400
          "
        >
          {context.join(" · ")}
        </p>

      )}

    </li>

  );

}


/* =========================================================
   EVENT
========================================================= */

function isRedundantDescription(
  event: TouchNotebookEvent,
  notes: TouchEvidenceNote[],
): boolean {

  const description = (
    event.description
    || ""
  )
    .trim()
    .toLowerCase();

  if (!description) {
    return true;
  }

  return notes.some(
    note => {

      const statement = (
        note.statement
        || ""
      )
        .trim()
        .toLowerCase();

      return (
        statement === description
        || statement.includes(
          description
        )
        || description.includes(
          statement
        )
      );

    },
  );

}


function EventBlock({
  event,
  notes,
  numbers,
  sourceNumberById,
}: {
  event: TouchNotebookEvent;
  notes: TouchEvidenceNote[];
  numbers: TouchNotebookNumber[];
  sourceNumberById: Map<string, number>;
}) {

  const showDescription = (
    event.description
    && !isRedundantDescription(
      event,
      notes,
    )
  );

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
            Événement
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

      {showDescription && (

        <p
          className="
            mt-1
            text-xs
            leading-5
            text-slate-600
          "
        >
          {event.description}
        </p>

      )}

      {event.actors.length > 0 && (

        <p
          className="
            mt-1
            text-[11px]
            text-slate-400
          "
        >
          {event.actors.join(" · ")}
        </p>

      )}

      <div className="mt-3 space-y-2.5">

        {notes.map(
          note => (

            <EvidenceNote
              key={note.note_id}
              note={note}
              sourceNumberById={
                sourceNumberById
              }
              showContext={false}
            />

          ),
        )}

      </div>

      {numbers.length > 0 && (

        <div
          className="
            mt-3
            grid
            gap-3
            sm:grid-cols-2
            print:grid-cols-2
          "
        >

          {numbers.map(
            number => (

              <FeaturedNumber
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

  const sourceNumberById = new Map(
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

  const noteById = new Map(
    notebook.notes.map(
      note => [
        note.note_id,
        note,
      ],
    ),
  );

  const eventById = new Map(
    notebook.events.map(
      event => [
        event.event_id,
        event,
      ],
    ),
  );

  const numberById = new Map(
    notebook.validated_numbers.map(
      number => [
        number.number_id,
        number,
      ],
    ),
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

      {/* HEADER */}

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
          {" parties · "}

          {notebook.notes.length}
          {" notes · "}

          {notebook.validated_numbers.length}
          {" chiffres certifiés · "}

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

      {/* BODY */}

      <div
        className="
          space-y-8
          px-8
          py-8
          print:px-0
          print:py-6
        "
      >

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
              Périmètre documentaire
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

        {/* DOCUMENTARY PLAN */}

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

            const orderedNumberIds =
              uniqueValues([
                ...events.flatMap(
                  event =>
                    event.number_ids,
                ),
                ...section.number_ids,
              ]);

            const featuredNumberIds =
              new Set(
                orderedNumberIds.slice(
                  0,
                  MAX_FEATURED_NUMBERS_PER_SECTION,
                ),
              );

            const standaloneNumbers = (
              section.number_ids
                .filter(
                  numberId =>
                    featuredNumberIds.has(
                      numberId,
                    ),
                )
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

                <div className="space-y-5">

                  {events.map(
                    event => {

                      const eventNotes = (
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

                      const eventNumbers = (
                        event.number_ids
                          .filter(
                            numberId =>
                              featuredNumberIds.has(
                                numberId,
                              ),
                          )
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

                        <EventBlock
                          key={event.event_id}
                          event={event}
                          notes={eventNotes}
                          numbers={eventNumbers}
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
                        sm:grid-cols-2
                        print:grid-cols-2
                      "
                    >

                      {standaloneNumbers.map(
                        number => (

                          <FeaturedNumber
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

        {/* TIMELINE */}

        {notebook.timeline.length > 0 && (

          <DocumentSection title="Repères chronologiques">

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

                    <p
                      className="
                        mt-0.5
                        text-sm
                        font-medium
                        text-slate-900
                      "
                    >
                      {item.label}
                    </p>

                    {item.description && (

                      <p
                        className="
                          mt-0.5
                          text-xs
                          leading-5
                          text-slate-500
                        "
                      >
                        {item.description}
                      </p>

                    )}

                  </div>

                ),
              )}

            </div>

          </DocumentSection>

        )}

        {/* CONTRADICTIONS */}

        {notebook.contradictions.length > 0 && (

          <DocumentSection
            title="Divergences entre les sources"
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
                          Résolution :
                        </strong>
                        {" "}
                        {contradiction.resolution}
                      </p>

                    )}

                  </div>

                ),
              )}

            </div>

          </DocumentSection>

        )}

        {/* CORPUS ASSESSMENT */}

        {(
          notebook.corpus_strengths.length > 0
          || notebook.corpus_limits.length > 0
        ) && (

          <DocumentSection title="Évaluation du corpus">

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
                  Points forts
                </h3>

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

              </div>

              <div>

                <h3
                  className="
                    text-sm
                    font-semibold
                    text-amber-800
                  "
                >
                  Limites
                </h3>

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

              </div>

            </div>

          </DocumentSection>

        )}

        {/* COMPLETE NUMBER REGISTER */}

        {notebook.validated_numbers.length > 0 && (

          <DocumentSection
            title="Annexe — Registre des chiffres certifiés"
            description={
              `${notebook.validated_numbers.length} `
              + "observations validées issues du corpus."
            }
            className="print:break-before-page"
          >

            <ol
              className="
                grid
                gap-x-6
                md:grid-cols-2
                print:grid-cols-2
              "
            >

              {notebook.validated_numbers.map(
                number => (

                  <NumberRegisterItem
                    key={number.number_id}
                    number={number}
                    sourceNumberById={
                      sourceNumberById
                    }
                  />

                ),
              )}

            </ol>

          </DocumentSection>

        )}

        {/* SOURCES */}

        <DocumentSection
          title="Sources"
          description={
            "Corpus sélectionné et analysé par GetCurator."
          }
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
                    key={source.content_id}
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
                            href={source.source_url}
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
                              .filter(Boolean)
                              .join(" · ")
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
