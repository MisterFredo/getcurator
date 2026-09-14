"use client";

import type {
  FormEvent,
} from "react";

import SearchableMultiSelect, {
  type SelectOption,
} from "@/components/ui/SearchableMultiSelect";


/* =========================================================
   PROPS
========================================================= */

type Props = {
  query: string;

  onQueryChange: (
    value: string
  ) => void;

  companyOptions: SelectOption[];
  solutionOptions: SelectOption[];
  topicOptions: SelectOption[];

  selectedCompanies: SelectOption[];
  selectedSolutions: SelectOption[];
  selectedTopics: SelectOption[];

  onCompaniesChange: (
    values: SelectOption[]
  ) => void;

  onSolutionsChange: (
    values: SelectOption[]
  ) => void;

  onTopicsChange: (
    values: SelectOption[]
  ) => void;

  periodStart: string;
  periodEnd: string;

  onPeriodStartChange: (
    value: string
  ) => void;

  onPeriodEndChange: (
    value: string
  ) => void;

  loading: boolean;
  hasResearch: boolean;

  onSubmit: () => void;
  onReset: () => void;
};


/* =========================================================
   COMPONENT
========================================================= */

export default function TouchResearchForm({
  query,
  onQueryChange,

  companyOptions,
  solutionOptions,
  topicOptions,

  selectedCompanies,
  selectedSolutions,
  selectedTopics,

  onCompaniesChange,
  onSolutionsChange,
  onTopicsChange,

  periodStart,
  periodEnd,

  onPeriodStartChange,
  onPeriodEndChange,

  loading,
  hasResearch,

  onSubmit,
  onReset,
}: Props) {

  /* =======================================================
     SUBMIT
  ======================================================= */

  function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {

    event.preventDefault();

    if (
      !query.trim()
      || loading
    ) {
      return;
    }

    onSubmit();

  }

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <form
      onSubmit={handleSubmit}
      className="
        rounded-xl
        border
        border-gray-200
        bg-white
        p-6
        space-y-6
      "
    >

      {/* ================================================= */}
      {/* QUESTION */}
      {/* ================================================= */}

      <div className="space-y-2">

        <label
          htmlFor="touch-query"
          className="text-sm font-medium text-gray-900"
        >
          Editorial research request
        </label>

        <textarea
          id="touch-query"
          value={query}
          onChange={event =>
            onQueryChange(
              event.target.value,
            )
          }
          placeholder={
            hasResearch
              ? (
                  "Continue the research, narrow the scope "
                  + "or investigate a missing angle…"
                )
              : (
                  "Example: Find the contents needed to "
                  + "understand the partnership between "
                  + "Amazon Ads and OpenAI."
                )
          }
          rows={4}
          className="
            w-full
            resize-y
            rounded-lg
            border
            border-gray-300
            px-4
            py-3
            text-sm
            text-gray-900
            outline-none
            focus:border-ratecard-blue
            focus:ring-2
            focus:ring-blue-100
          "
        />

        <p className="text-xs text-gray-500">
          Describe the subject, event or market
          mechanism you want to investigate.
        </p>

      </div>

      {/* ================================================= */}
      {/* ENTITIES */}
      {/* ================================================= */}

      <div
        className="
          grid
          grid-cols-1
          gap-5
          lg:grid-cols-3
        "
      >

        <SearchableMultiSelect
          label="Companies"
          placeholder="Search companies…"
          options={companyOptions}
          values={selectedCompanies}
          onChange={onCompaniesChange}
        />

        <SearchableMultiSelect
          label="Solutions"
          placeholder="Search solutions…"
          options={solutionOptions}
          values={selectedSolutions}
          onChange={onSolutionsChange}
        />

        <SearchableMultiSelect
          label="Topics"
          placeholder="Search topics…"
          options={topicOptions}
          values={selectedTopics}
          onChange={onTopicsChange}
        />

      </div>

      {/* ================================================= */}
      {/* PERIOD */}
      {/* ================================================= */}

      <div
        className="
          grid
          grid-cols-1
          gap-5
          sm:grid-cols-2
          lg:max-w-2xl
        "
      >

        <div className="space-y-2">

          <label
            htmlFor="touch-period-start"
            className="text-sm font-medium text-gray-900"
          >
            From
          </label>

          <input
            id="touch-period-start"
            type="date"
            value={periodStart}
            onChange={event =>
              onPeriodStartChange(
                event.target.value,
              )
            }
            className="
              w-full
              rounded-lg
              border
              border-gray-300
              px-3
              py-2
              text-sm
              outline-none
              focus:border-ratecard-blue
              focus:ring-2
              focus:ring-blue-100
            "
          />

        </div>

        <div className="space-y-2">

          <label
            htmlFor="touch-period-end"
            className="text-sm font-medium text-gray-900"
          >
            To
          </label>

          <input
            id="touch-period-end"
            type="date"
            value={periodEnd}
            onChange={event =>
              onPeriodEndChange(
                event.target.value,
              )
            }
            className="
              w-full
              rounded-lg
              border
              border-gray-300
              px-3
              py-2
              text-sm
              outline-none
              focus:border-ratecard-blue
              focus:ring-2
              focus:ring-blue-100
            "
          />

        </div>

      </div>

      {/* ================================================= */}
      {/* ACTIONS */}
      {/* ================================================= */}

      <div
        className="
          flex
          flex-wrap
          items-center
          justify-between
          gap-3
          border-t
          border-gray-100
          pt-5
        "
      >

        <button
          type="button"
          onClick={onReset}
          disabled={loading}
          className="
            px-4
            py-2
            text-sm
            text-gray-600
            hover:text-gray-900
            disabled:opacity-50
          "
        >
          Reset research
        </button>

        <button
          type="submit"
          disabled={
            loading
            || !query.trim()
          }
          className="
            rounded-lg
            bg-ratecard-blue
            px-5
            py-2.5
            text-sm
            font-medium
            text-white
            hover:opacity-90
            disabled:cursor-not-allowed
            disabled:opacity-50
          "
        >
          {
            loading
              ? "Researching…"
              : (
                  hasResearch
                    ? "Continue research"
                    : "Start research"
                )
          }
        </button>

      </div>

    </form>

  );

}
