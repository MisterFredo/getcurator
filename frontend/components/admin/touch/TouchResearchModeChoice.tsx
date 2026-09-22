"use client";

import type {
  TouchResearchMode,
} from "@/types/touch";


/* =========================================================
   PROPS
========================================================= */

type Props = {
  value:
    TouchResearchMode | null;

  onChange: (
    mode: TouchResearchMode,
  ) => void;

  disabled?:
    boolean;
};


/* =========================================================
   MODE OPTION
========================================================= */

type ModeOptionProps = {
  selected:
    boolean;

  title:
    string;

  description:
    string;

  badge:
    string;

  onClick:
    () => void;

  disabled:
    boolean;
};


function ModeOption({
  selected,
  title,
  description,
  badge,
  onClick,
  disabled,
}: ModeOptionProps) {

  return (

    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`
        w-full
        rounded-xl
        border
        p-5
        text-left
        transition
        ${
          selected
            ? (
                "border-ratecard-blue "
                + "bg-blue-50 "
                + "ring-2 "
                + "ring-blue-100"
              )
            : (
                "border-gray-200 "
                + "bg-white "
                + "hover:border-gray-300 "
                + "hover:bg-gray-50"
              )
        }
        ${
          disabled
            ? (
                "cursor-not-allowed "
                + "opacity-60"
              )
            : ""
        }
      `}
    >

      <div
        className="
          flex
          items-start
          justify-between
          gap-4
        "
      >

        <div>

          <p
            className={`
              text-base
              font-semibold
              ${
                selected
                  ? "text-blue-900"
                  : "text-gray-900"
              }
            `}
          >
            {title}
          </p>

          <p
            className="
              mt-2
              text-sm
              leading-6
              text-gray-600
            "
          >
            {description}
          </p>

        </div>

        <span
          className={`
            shrink-0
            rounded-full
            px-2.5
            py-1
            text-xs
            font-medium
            ${
              selected
                ? (
                    "bg-ratecard-blue "
                    + "text-white"
                  )
                : (
                    "bg-gray-100 "
                    + "text-gray-600"
                  )
            }
          `}
        >
          {badge}
        </span>

      </div>

      <div
        className="
          mt-4
          flex
          items-center
          gap-2
        "
      >

        <span
          aria-hidden="true"
          className={`
            flex
            h-5
            w-5
            items-center
            justify-center
            rounded-full
            border
            ${
              selected
                ? (
                    "border-ratecard-blue "
                    + "bg-ratecard-blue"
                  )
                : (
                    "border-gray-300 "
                    + "bg-white"
                  )
            }
          `}
        >

          {selected && (

            <span
              className="
                h-2
                w-2
                rounded-full
                bg-white
              "
            />

          )}

        </span>

        <span
          className={`
            text-sm
            font-medium
            ${
              selected
                ? "text-blue-800"
                : "text-gray-500"
            }
          `}
        >
          {
            selected
              ? "Selected"
              : "Select this mode"
          }
        </span>

      </div>

    </button>

  );

}


/* =========================================================
   COMPONENT
========================================================= */

export default function TouchResearchModeChoice({
  value,
  onChange,
  disabled = false,
}: Props) {

  return (

    <section
      className="
        rounded-xl
        border
        border-gray-200
        bg-white
        p-6
      "
    >

      <div>

        <p
          className="
            text-xs
            font-medium
            uppercase
            tracking-wide
            text-gray-500
          "
        >
          Research mode
        </p>

        <h2
          className="
            mt-1
            text-lg
            font-semibold
            text-gray-900
          "
        >
          How do you want to prepare the research?
        </h2>

        <p
          className="
            mt-2
            max-w-3xl
            text-sm
            leading-6
            text-gray-600
          "
        >
          Use direct research for a clearly defined
          request. Choose guided research when the
          subject requires a deeper editorial framing
          before the corpus is built.
        </p>

      </div>

      <div
        className="
          mt-5
          grid
          grid-cols-1
          gap-4
          lg:grid-cols-2
        "
      >

        <ModeOption
          selected={
            value === "DIRECT"
          }
          title="Direct research"
          description={
            "Use the current workflow: enter a request, "
            + "apply optional entity and period filters, "
            + "then build the corpus immediately."
          }
          badge="Fast"
          onClick={() =>
            onChange(
              "DIRECT",
            )
          }
          disabled={disabled}
        />

        <ModeOption
          selected={
            value === "GUIDED"
          }
          title="AI-guided research"
          description={
            "Conduct a detailed research-design interview, "
            + "clarify the scope and validate a structured "
            + "plan before retrieving contents."
          }
          badge="Advanced"
          onClick={() =>
            onChange(
              "GUIDED",
            )
          }
          disabled={disabled}
        />

      </div>

      {disabled && (

        <p
          className="
            mt-4
            text-xs
            text-gray-500
          "
        >
          Reset the current research before changing
          the research mode.
        </p>

      )}

    </section>

  );

}
