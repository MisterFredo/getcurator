"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

import SearchableMultiSelect, {
  SelectOption,
} from "@/components/ui/SearchableMultiSelect";

import type {
  CompanyOption,
} from "@/types/company";

import type {
  TopicOption,
} from "@/types/topic";

import type {
  SolutionOption,
} from "@/types/solution";

/* ========================================================= */

type Props = {
  userId: string;
};

/* ========================================================= */

type PreferencesResponse = {
  companies: SelectOption[];
  topics: SelectOption[];
  solutions: SelectOption[];
};

/* ========================================================= */

export default function ProfilePreferencesEditor({
  userId,
}: Props) {

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    saving,
    setSaving,
  ] = useState(false);

  const [
    saved,
    setSaved,
  ] = useState(false);

  /* =======================================================
     OPTIONS
  ======================================================= */

  const [
    companyOptions,
    setCompanyOptions,
  ] = useState<SelectOption[]>([]);

  const [
    topicOptions,
    setTopicOptions,
  ] = useState<SelectOption[]>([]);

  const [
    solutionOptions,
    setSolutionOptions,
  ] = useState<SelectOption[]>([]);

  /* =======================================================
     VALUES
  ======================================================= */

  const [
    selectedCompanies,
    setSelectedCompanies,
  ] = useState<SelectOption[]>([]);

  const [
    selectedTopics,
    setSelectedTopics,
  ] = useState<SelectOption[]>([]);

  const [
    selectedSolutions,
    setSelectedSolutions,
  ] = useState<SelectOption[]>([]);

  /* =======================================================
     LOAD
  ======================================================= */

  useEffect(() => {

    async function load() {

      try {

        const [

          companyRes,

          topicRes,

          solutionRes,

          preferenceRes,

        ] = await Promise.all([

          api.get("/company/list"),

          api.get("/topic/list"),

          api.get("/solution/list"),

          api.get(
            `/user/preferences/${userId}`
          ),

        ]);

        /* ===============================================
           OPTIONS
        =============================================== */

        const companies =
          (
            companyRes?.companies || []
          ).map(
            (
              company: CompanyOption
            ): SelectOption => ({
              id: company.id_company,
              label: company.name,
            })
          );

        const topics =
          (
            topicRes?.topics || []
          ).map(
            (
              topic: TopicOption
            ): SelectOption => ({
              id: topic.id_topic,
              label: topic.label,
            })
          );

        const solutions =
          (
            solutionRes?.solutions || []
          ).map(
            (
              solution: SolutionOption
            ): SelectOption => ({
              id: solution.id_solution,
              label: solution.name,
            })
          );

        setCompanyOptions(
          companies
        );

        setTopicOptions(
          topics
        );

        setSolutionOptions(
          solutions
        );

        /* ===============================================
           USER PREFERENCES
        =============================================== */

        const preferences:
          PreferencesResponse =
          preferenceRes.preferences;

        setSelectedCompanies(
          preferences.companies || []
        );

        setSelectedTopics(
          preferences.topics || []
        );

        setSelectedSolutions(
          preferences.solutions || []
        );

      } catch (e) {

        console.error(
          "preferences load error",
          e
        );

      } finally {

        setLoading(false);

      }

    }

    load();

  }, [userId]);

  /* =======================================================
     SAVE
  ======================================================= */

  async function save() {

    setSaving(true);

    try {

      await api.post(
        "/user/preferences/update",
        {
          user_id: userId,

          companies:
            selectedCompanies.map(
              (c) => c.id
            ),

          topics:
            selectedTopics.map(
              (t) => t.id
            ),

          solutions:
            selectedSolutions.map(
              (s) => s.id
            ),
        }
      );

      setSaved(true);

      setTimeout(
        () => setSaved(false),
        2000
      );

    } catch (e) {

      console.error(
        "preferences save error",
        e
      );

    } finally {

      setSaving(false);

    }

  }

  /* =======================================================
     LOADING
  ======================================================= */

  if (loading) {

    return (
      <div className="text-sm text-gray-500">
        Loading preferences...
      </div>
    );

  }

    /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div
      className="
        border
        rounded-lg
        bg-white
        p-6
        space-y-6
      "
    >

      {/* ===================================================
          HEADER
      =================================================== */}

      <div>

        <h3
          className="
            text-lg
            font-semibold
          "
        >
          Preferences
        </h3>

        <p
          className="
            text-sm
            text-gray-500
            mt-1
          "
        >
          Select the companies, topics and
          solutions followed by this user.
        </p>

      </div>

      {/* ===================================================
          COMPANIES
      =================================================== */}

      <SearchableMultiSelect

        label="Companies"

        placeholder="Search a company..."

        options={companyOptions}

        values={selectedCompanies}

        onChange={setSelectedCompanies}

      />

      {/* ===================================================
          TOPICS
      =================================================== */}

      <SearchableMultiSelect

        label="Topics"

        placeholder="Search a topic..."

        options={topicOptions}

        values={selectedTopics}

        onChange={setSelectedTopics}

      />

      {/* ===================================================
          SOLUTIONS
      =================================================== */}

      <SearchableMultiSelect

        label="Solutions"

        placeholder="Search a solution..."

        options={solutionOptions}

        values={selectedSolutions}

        onChange={setSelectedSolutions}

      />

      {/* ===================================================
          ACTIONS
      =================================================== */}

      <div
        className="
          flex
          justify-end
          pt-2
        "
      >

        <button

          onClick={save}

          disabled={saving}

          className={`
            px-4
            py-2
            rounded-lg
            text-sm
            text-white
            transition

            ${
              saving
                ? "bg-gray-400 cursor-not-allowed"
                : saved
                  ? "bg-emerald-600"
                  : "bg-blue-600 hover:bg-blue-700"
            }
          `}
        >

          {
            saving
              ? "Saving..."

              : saved
                ? "✓ Saved"

                : "Save preferences"
          }

        </button>

      </div>

    </div>

  );

}
