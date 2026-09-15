"use client";

import type {
  TouchBriefSection,
  TouchBriefStructure,
  TouchCorpusNotebook,
  TouchEvidenceNote,
  TouchNotebookEvent,
  TouchNotebookNumber,
} from "@/types/touch";


/* =========================================================
   PROPS
========================================================= */

type Props = {
  brief: TouchBriefStructure;
  notebook: TouchCorpusNotebook;

  sourceContentIds: string[];
};


/* =========================================================
   SOURCE REFERENCES
========================================================= */

function SourceReferences({
  sourceIds,
  sourceNumberById,
}: {
  sourceIds: string[];

  sourceNumberById:
    Map<string, number>;
}) {

  const references =
    sourceIds
      .map(
        sourceId => ({

          sourceId,

          sourceNumber:
            sourceNumberById.get(
              sourceId,
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

    <div className="mt-3 flex flex-wrap gap-1.5">

      {references.map(
        reference => (

          <span
            key={reference.sourceId}
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
  numbered = false,
  index = 0,
}: {
  note: TouchEvidenceNote;

  sourceNumberById:
    Map<string, number>;

  numbered?: boolean;
  index?: number;
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

      <div className="flex gap-3">

        {numbered && (

          <span
            className="
              flex
              h-7
              w-7
              shrink-0
              items-center
              justify-center
              rounded-full
              bg-ratecard-blue
              text-xs
              font-semibold
              text-white
            "
          >
            {index + 1}
          </span>

        )}

        <div className="min-w-0 flex-1">

          <p
            className="
              text-sm
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
                mt-1.5
                text-sm
                leading-6
                text-gray-600
              "
            >
              {note.explanation}
            </p>

          )}

          <SourceReferences
            sourceIds={
              note.source_content_ids
            }
            sourceNumberById={
              sourceNumberById
            }
          />

        </div>

      </div>

    </article>

  );

}


/* =========================================================
   EVENT CARD
========================================================= */

function EventCard({
  event,
  sourceNumberById,
}: {
  event: TouchNotebookEvent;

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

      {event.event_date && (

        <p
          className="
            text-xs
            font-semibold
            uppercase
            tracking-wide
            text-ratecard-blue
          "
        >
          {event.event_date}
        </p>

      )}

      <h4 className="mt-1 font-semibold text-gray-900">
        {event.title}
      </h4>

      <p
        className="
          mt-2
          text-sm
          leading-6
          text-gray-600
        "
      >
        {event.description}
      </p>

      <SourceReferences
        sourceIds={
          event.source_content_ids
        }
        sourceNumberById={
          sourceNumberById
        }
      />

    </article>

  );

}

/* =========================================================
   FORMAT NUMBER VALUE
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
    ).format(
      value,
    );

  }

  return value;

}


/* =========================================================
   FORMAT NUMBER SCALE
========================================================= */

function formatNumberScale(
  scale: string | null,
): string {

  if (!scale) {
    return "";
  }

  const labels:
    Record<string, string> = {

    THOUSAND:
      "thousand",

    MILLION:
      "million",

    BILLION:
      "billion",

    TRILLION:
      "trillion",

  };

  return (
    labels[
      scale.toUpperCase()
    ]
    ?? scale.toLowerCase()
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

  sourceNumberById:
    Map<string, number>;
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
          Boolean(
            label,
          ),
      )
  );

  const hasRange = (
    number.value_min !== null
    && number.value_max !== null
  );

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

      {/* ================================================= */}
      {/* VALUE */}
      {/* ================================================= */}

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
            text-gray-900
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
              font-medium
              text-gray-700
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
              font-medium
              text-gray-700
            "
          >
            {number.unit}
          </span>

        )}

      </div>

      {/* ================================================= */}
      {/* LABEL */}
      {/* ================================================= */}

      {number.label && (

        <p
          className="
            mt-2
            text-sm
            font-medium
            leading-5
            text-gray-800
          "
        >
          {number.label}
        </p>

      )}

      {/* ================================================= */}
      {/* METADATA */}
      {/* ================================================= */}

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
                bg-violet-50
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
                  bg-gray-100
                  px-2
                  py-1
                  text-xs
                  text-gray-600
                "
              >
                {label}
              </span>

            ),
          )}

        </div>

      )}

      {/* ================================================= */}
      {/* CONTEXT */}
      {/* ================================================= */}

      {(
        number.zone
        || number.period_label
      ) && (

        <div
          className="
            mt-3
            space-y-1
            text-xs
            text-gray-500
          "
        >

          {number.zone && (

            <p>
              Geography:
              {" "}
              {number.zone}
            </p>

          )}

          {number.period_label && (

            <p>
              Period:
              {" "}
              {number.period_label}
            </p>

          )}

        </div>

      )}

      <SourceReferences
        sourceIds={
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
   SECTION CONTENT
========================================================= */

function SectionContent({
  section,
  noteById,
  numberById,
  eventById,
  sourceNumberById,
}: {
  section: TouchBriefSection;

  noteById:
    Map<string, TouchEvidenceNote>;

  numberById:
    Map<string, TouchNotebookNumber>;

  eventById:
    Map<string, TouchNotebookEvent>;

  sourceNumberById:
    Map<string, number>;
}) {

  const notes =
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
        ): note is TouchEvidenceNote =>
          Boolean(
            note,
          ),
      );

  const numbers =
    section.number_ids
      .map(
        numberId =>
          numberById.get(
            numberId,
          ),
      )
      .filter(
        (
          number,
        ): number is TouchNotebookNumber =>
          Boolean(
            number,
          ),
      );

  const events =
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
        ): event is TouchNotebookEvent =>
          Boolean(
            event,
          ),
      );

  if (
    section.layout === "COLUMNS"
    && section.groups.length > 0
  ) {

    return (

      <div
        className="
          grid
          gap-4
          lg:grid-cols-2
        "
      >

        {section.groups.map(
          (
            group,
            groupIndex,
          ) => {

            const groupNotes =
              group.note_ids
                .map(
                  noteId =>
                    noteById.get(
                      noteId,
                    ),
                )
                .filter(
                  (
                    note,
                  ): note is TouchEvidenceNote =>
                    Boolean(
                      note,
                    ),
                );

            const groupNumbers =
              group.number_ids
                .map(
                  numberId =>
                    numberById.get(
                      numberId,
                    ),
                )
                .filter(
                  (
                    number,
                  ): number is TouchNotebookNumber =>
                    Boolean(
                      number,
                    ),
                );

            const groupEvents =
              group.event_ids
                .map(
                  eventId =>
                    eventById.get(
                      eventId,
                    ),
                )
                .filter(
                  (
                    event,
                  ): event is TouchNotebookEvent =>
                    Boolean(
                      event,
                    ),
                );

            return (

              <div
                key={
                  `${group.label}-${groupIndex}`
                }
                className="
                  rounded-xl
                  border
                  border-gray-200
                  bg-gray-50
                  p-4
                "
              >

                <h4
                  className="
                    mb-4
                    text-base
                    font-semibold
                    text-gray-900
                  "
                >
                  {group.label}
                </h4>

                <div className="space-y-3">

                  {groupNotes.map(
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

                  {groupEvents.map(
                    event => (

                      <EventCard
                        key={event.event_id}
                        event={event}
                        sourceNumberById={
                          sourceNumberById
                        }
                      />

                    ),
                  )}

                  {groupNumbers.map(
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

              </div>

            );

          },
        )}

      </div>

    );

  }

  if (
    section.layout === "NUMBER_CARDS"
  ) {

    return (

      <div
        className="
          grid
          gap-4
          md:grid-cols-2
          xl:grid-cols-3
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

    );

  }

  if (
    section.layout === "TIMELINE"
  ) {

    return (

      <div className="space-y-3">

        {events.map(
          event => (

            <EventCard
              key={event.event_id}
              event={event}
              sourceNumberById={
                sourceNumberById
              }
            />

          ),
        )}

      </div>

    );

  }

  const numbered =
    section.layout === "STEPS";

  return (

    <div className="space-y-3">

      {notes.map(
        (
          note,
          index,
        ) => (

          <NoteCard
            key={note.note_id}
            note={note}
            numbered={numbered}
            index={index}
            sourceNumberById={
              sourceNumberById
            }
          />

        ),
      )}

      {events.map(
        event => (

          <EventCard
            key={event.event_id}
            event={event}
            sourceNumberById={
              sourceNumberById
            }
          />

        ),
      )}

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

  );

}


/* =========================================================
   COMPONENT
========================================================= */

export default function TouchBriefPreview({
  brief,
  notebook,
  sourceContentIds,
}: Props) {

  const noteById =
    new Map(
      notebook.notes.map(
        note => [
          note.note_id,
          note,
        ],
      ),
    );

  const numberById =
    new Map(
      notebook.validated_numbers.map(
        number => [
          number.number_id,
          number,
        ],
      ),
    );

  const eventById =
    new Map(
      notebook.events.map(
        event => [
          event.event_id,
          event,
        ],
      ),
    );

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

  return (

    <article
      className="
        touch-print-root
        overflow-hidden
        rounded-xl
        border
        border-gray-200
        bg-white
      "
    >

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <header
        className="
          border-b
          border-gray-200
          bg-gray-900
          px-6
          py-8
          text-white
        "
      >

        <p
          className="
            text-xs
            font-semibold
            uppercase
            tracking-widest
            text-violet-300
          "
        >
          GetCurator Touch · Assisted interpretation
        </p>

        <h2
          className="
            mt-3
            max-w-4xl
            text-3xl
            font-semibold
            leading-tight
          "
        >
          {brief.headline}
        </h2>

        {brief.subheadline && (

          <p
            className="
              mt-3
              max-w-3xl
              text-base
              leading-7
              text-gray-300
            "
          >
            {brief.subheadline}
          </p>

        )}

      </header>

      <div className="space-y-10 px-6 py-8">

        {/* ================================================= */}
        {/* CENTRAL READING */}
        {/* ================================================= */}

        <section
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
              border-gray-200
              bg-gray-50
              p-5
            "
          >

            <p
              className="
                text-xs
                font-semibold
                uppercase
                tracking-wide
                text-gray-500
              "
            >
              Central question
            </p>

            <p
              className="
                mt-2
                font-medium
                leading-6
                text-gray-900
              "
            >
              {brief.central_question}
            </p>

          </div>

          <div
            className="
              rounded-xl
              border
              border-violet-200
              bg-violet-50
              p-5
            "
          >

            <p
              className="
                text-xs
                font-semibold
                uppercase
                tracking-wide
                text-violet-700
              "
            >
              Assisted reading
            </p>

            <p
              className="
                mt-2
                font-medium
                leading-6
                text-gray-900
              "
            >
              {brief.key_message}
            </p>

          </div>

        </section>

        {/* ================================================= */}
        {/* SECTIONS */}
        {/* ================================================= */}

        {brief.sections.map(
          section => (

            <section
              key={section.section_id}
              className="space-y-4"
            >

              <div>

                <h3
                  className="
                    text-xl
                    font-semibold
                    text-gray-900
                  "
                >
                  {section.title}
                </h3>

                {section.introduction && (

                  <p
                    className="
                      mt-1
                      max-w-4xl
                      text-sm
                      leading-6
                      text-gray-600
                    "
                  >
                    {section.introduction}
                  </p>

                )}

              </div>

              <SectionContent
                section={section}
                noteById={noteById}
                numberById={numberById}
                eventById={eventById}
                sourceNumberById={
                  sourceNumberById
                }
              />

            </section>

          ),
        )}

      </div>

    </article>

  );

}
