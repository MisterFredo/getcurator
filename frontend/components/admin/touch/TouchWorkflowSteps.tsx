"use client";


/* =========================================================
   TYPES
========================================================= */

export type TouchWorkflowStep =
  | "RESEARCH"
  | "CORPUS"
  | "NOTEBOOK"
  | "OUTPUT";


type StepDefinition = {
  id: TouchWorkflowStep;
  number: number;
  label: string;
  description: string;
};


type Props = {
  currentStep: TouchWorkflowStep;

  researchReady: boolean;
  corpusReady: boolean;
  notebookReady: boolean;

  onStepChange: (
    step: TouchWorkflowStep
  ) => void;
};


/* =========================================================
   STEPS
========================================================= */

const STEPS: StepDefinition[] = [
  {
    id: "RESEARCH",
    number: 1,
    label: "Research",
    description: "Define and explore the subject",
  },
  {
    id: "CORPUS",
    number: 2,
    label: "Corpus",
    description: "Select the useful contents",
  },
  {
    id: "NOTEBOOK",
    number: 3,
    label: "Notebook",
    description: "Extract and consolidate evidence",
  },
  {
    id: "OUTPUT",
    number: 4,
    label: "Output",
    description: "Choose the final reading mode",
  },
];


/* =========================================================
   COMPONENT
========================================================= */

export default function TouchWorkflowSteps({
  currentStep,
  researchReady,
  corpusReady,
  notebookReady,
  onStepChange,
}: Props) {

  function isStepAvailable(
    step: TouchWorkflowStep,
  ): boolean {

    if (step === "RESEARCH") {
      return true;
    }

    if (step === "CORPUS") {
      return researchReady;
    }

    if (step === "NOTEBOOK") {
      return corpusReady;
    }

    return notebookReady;

  }


  function isStepCompleted(
    step: TouchWorkflowStep,
  ): boolean {

    if (step === "RESEARCH") {
      return researchReady;
    }

    if (step === "CORPUS") {
      return corpusReady;
    }

    if (step === "NOTEBOOK") {
      return notebookReady;
    }

    return false;

  }


  return (

    <nav
      aria-label="Touch workflow"
      className="
        rounded-xl
        border
        border-gray-200
        bg-white
        p-4
      "
    >

      <ol
        className="
          grid
          gap-3
          lg:grid-cols-4
        "
      >

        {STEPS.map(
          step => {

            const active =
              currentStep === step.id;

            const available =
              isStepAvailable(
                step.id,
              );

            const completed =
              isStepCompleted(
                step.id,
              );

            return (

              <li key={step.id}>

                <button
                  type="button"
                  disabled={!available}
                  onClick={() =>
                    onStepChange(
                      step.id,
                    )
                  }
                  className={`
                    flex
                    w-full
                    items-start
                    gap-3
                    rounded-lg
                    border
                    px-4
                    py-3
                    text-left
                    transition
                    ${
                      active
                        ? (
                            "border-ratecard-blue "
                            + "bg-blue-50"
                          )
                        : completed
                          ? (
                              "border-emerald-200 "
                              + "bg-emerald-50 "
                              + "hover:bg-emerald-100"
                            )
                          : available
                            ? (
                                "border-gray-200 "
                                + "bg-white "
                                + "hover:bg-gray-50"
                              )
                            : (
                                "cursor-not-allowed "
                                + "border-gray-100 "
                                + "bg-gray-50 "
                                + "opacity-50"
                              )
                    }
                  `}
                >

                  <span
                    className={`
                      flex
                      h-8
                      w-8
                      shrink-0
                      items-center
                      justify-center
                      rounded-full
                      text-sm
                      font-semibold
                      ${
                        active
                          ? (
                              "bg-ratecard-blue "
                              + "text-white"
                            )
                          : completed
                            ? (
                                "bg-emerald-600 "
                                + "text-white"
                              )
                            : (
                                "bg-gray-200 "
                                + "text-gray-600"
                              )
                      }
                    `}
                  >
                    {completed && !active
                      ? "✓"
                      : step.number
                    }
                  </span>

                  <span className="min-w-0">

                    <span
                      className={`
                        block
                        text-sm
                        font-semibold
                        ${
                          active
                            ? "text-ratecard-blue"
                            : "text-gray-900"
                        }
                      `}
                    >
                      {step.label}
                    </span>

                    <span
                      className="
                        mt-0.5
                        block
                        text-xs
                        leading-5
                        text-gray-500
                      "
                    >
                      {step.description}
                    </span>

                  </span>

                </button>

              </li>

            );

          },
        )}

      </ol>

    </nav>

  );

}
