"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";

import MatchingTable from "@/components/admin/matching/MatchingTable";

type LLMItem = {
  value: string;
  count: number;

  type_hint?: "company" | "solution" | "unknown";

  suggested_id?: string | null;
  suggested_label?: string | null;
};

type Solution = {
  id_solution: string;
  name: string;
};

type Company = {
  id_company: string;
  name: string;
};

type MatchOption = {
  id: string;
  label: string;
  type: "company" | "solution";
};

export default function MatchingPage() {

  const [loading, setLoading] =
    useState(true);

  const [entities, setEntities] =
    useState<LLMItem[]>([]);

  const [solutions, setSolutions] =
    useState<Solution[]>([]);

  const [companies, setCompanies] =
    useState<Company[]>([]);

  const [selected, setSelected] =
    useState<{
      [key: string]: string;
    }>({});

  const [selectedType, setSelectedType] =
    useState<{
      [key: string]: "company" | "solution";
    }>({});

  const [checked, setChecked] =
    useState<{
      [key: string]: boolean;
    }>({});

  const [processing, setProcessing] =
    useState(false);

  const [syncingFeed, setSyncingFeed] =
    useState(false);

  const [syncingNumbers, setSyncingNumbers] =
    useState(false);

  /* =========================================================
     LOAD
  ========================================================= */

  async function loadData() {

    try {

      setLoading(true);

      const [
        entityRes,
        solRes,
        compRes,
      ] = await Promise.all([
        @router.get("/entities"),
        api.get("/solution/list"),
        api.get("/company/list"),
      ]);

      setEntities(
        entityRes.entities || []
      );

      setSolutions(
        solRes.solutions || []
      );

      setCompanies(
        compRes.companies || []
      );

    } catch (e) {

      console.error(
        "Erreur chargement matching",
        e
      );

    } finally {

      setLoading(false);

    }

  }

  useEffect(() => {

    loadData();

  }, []);

  /* =========================================================
     OPTIONS
  ========================================================= */

  const options = useMemo(() => {

    const companyOptions =
      companies.map((c) => ({
        id: c.id_company,
        label: c.name,
        type: "company" as const,
      }));

    const solutionOptions =
      solutions.map((s) => ({
        id: s.id_solution,
        label: s.name,
        type: "solution" as const,
      }));

    return [
      ...companyOptions,
      ...solutionOptions,
    ].sort((a, b) =>
      a.label.localeCompare(b.label)
    );

  }, [
    companies,
    solutions,
  ]);

  /* =========================================================
     AUTO SELECT
  ========================================================= */

  useEffect(() => {

    const autoSelected:
      Record<string, string> = {};

    const autoTypes:
      Record<
        string,
        "company" | "solution"
      > = {};

    entities.forEach((item) => {

      if (
        item.suggested_id
        &&
        item.type_hint
        &&
        item.type_hint !== "unknown"
      ) {

        autoSelected[item.value] =
          item.suggested_id;

        autoTypes[item.value] =
          item.type_hint;

      }

    });

    setSelected(autoSelected);

    setSelectedType(autoTypes);

  }, [entities]);

  /* =========================================================
     HELPERS
  ========================================================= */

  function getCheckedValues() {

    return Object.keys(checked)
      .filter((k) => checked[k]);

  }

  /* =========================================================
     BULK MATCH
  ========================================================= */

  async function matchBulk() {

    const values =
      getCheckedValues();

    if (values.length === 0) {

      alert("Aucune sélection");

      return;

    }

    try {

      setProcessing(true);

      const payload = {
        items: values
          .filter((value) =>
            selected[value]
            &&
            selectedType[value]
          )
          .map((value) => ({
            alias: value,
            target_id:
              selected[value],
            target_type:
              selectedType[value],
          })),
      };

      await api.post(
        "/matching/bulk-match",
        payload
      );

      setEntities((prev) =>
        prev.filter(
          (v) =>
            !values.includes(v.value)
        )
      );

      setChecked({});

    } catch (e) {

      console.error(e);

      alert("Erreur bulk match");

    } finally {

      setProcessing(false);

    }

  }

  /* =========================================================
     BULK IGNORE
  ========================================================= */

  async function ignoreBulk() {

    const values =
      getCheckedValues();

    if (values.length === 0) {

      alert("Aucune sélection");

      return;

    }

    try {

      setProcessing(true);

      const payload = {
        items: values.map(
          (value) => ({
            alias: value,
            target_type: "ignore",
          })
        ),
      };

      await api.post(
        "/matching/bulk-match",
        payload
      );

      setEntities((prev) =>
        prev.filter(
          (v) =>
            !values.includes(v.value)
        )
      );

      setChecked({});

    } catch (e) {

      console.error(e);

      alert("Erreur bulk ignore");

    } finally {

      setProcessing(false);

    }

  }

  /* =========================================================
     SINGLE MATCH
  ========================================================= */

  async function applyMatch(
    value: string
  ) {

    const id =
      selected[value];

    const type =
      selectedType[value];

    if (!id || !type) {

      alert(
        "Sélectionner une cible"
      );

      return;

    }

    try {

      setProcessing(true);

      await api.post(
        "/matching/match",
        {
          alias: value,
          target_id: id,
          target_type: type,
        }
      );

      setEntities((prev) =>
        prev.filter(
          (v) =>
            v.value !== value
        )
      );

    } catch (e) {

      console.error(e);

      alert("Erreur matching");

    } finally {

      setProcessing(false);

    }

  }

  /* =========================================================
     SINGLE IGNORE
  ========================================================= */

  async function ignore(
    value: string
  ) {

    try {

      setProcessing(true);

      await api.post(
        "/matching/match",
        {
          alias: value,
          target_type: "ignore",
        }
      );

      setEntities((prev) =>
        prev.filter(
          (v) =>
            v.value !== value
        )
      );

    } catch (e) {

      console.error(e);

      alert("Erreur ignore");

    } finally {

      setProcessing(false);

    }

  }

  /* =========================================================
     SYNC FEED
  ========================================================= */

  async function syncFeed() {

    try {

      setSyncingFeed(true);

      await api.post(
        "/content/sync-all",
        {}
      );

      alert(
        "SYNC FEED terminé"
      );

    } catch (e) {

      console.error(e);

      alert(
        "Erreur sync feed"
      );

    } finally {

      setSyncingFeed(false);

    }

  }

  /* =========================================================
     SYNC NUMBERS
  ========================================================= */

  async function syncNumbers() {

    try {

      setSyncingNumbers(true);

      await api.post(
        "/content/sync-numbers",
        {}
      );

      alert(
        "SYNC NUMBERS terminé"
      );

    } catch (e) {

      console.error(e);

      alert(
        "Erreur sync numbers"
      );

    } finally {

      setSyncingNumbers(false);

    }

  }

  /* =========================================================
     UI
  ========================================================= */

  if (loading) {

    return (
      <p>Chargement…</p>
    );

  }

  return (

    <div className="space-y-8">

      {/* =====================================================
          HEADER
      ===================================================== */}

      <div className="
        flex
        items-center
        justify-between
      ">

        <div>

          <h1 className="
            text-3xl
            font-semibold
          ">
            Matching & Sync
          </h1>

          <p className="
            text-sm
            text-gray-500
            mt-1
          ">
            Gouvernance des entités extraites par LLM
          </p>

        </div>

      </div>

      {/* =====================================================
          SYNC ACTIONS
      ===================================================== */}

      <div className="flex gap-3">

        <button
          onClick={syncFeed}
          disabled={syncingFeed}
          className="
            bg-black
            text-white
            px-4
            py-2
            rounded
          "
        >

          {syncingFeed
            ? "SYNC FEED..."
            : "SYNC FEED"}

        </button>

        <button
          onClick={syncNumbers}
          disabled={syncingNumbers}
          className="
            bg-blue-700
            text-white
            px-4
            py-2
            rounded
          "
        >

          {syncingNumbers
            ? "SYNC NUMBERS..."
            : "SYNC NUMBERS"}

        </button>

      </div>

      {/* =====================================================
          ACTIONS
      ===================================================== */}

      <div className="flex gap-2">

        <button
          onClick={matchBulk}
          disabled={processing}
          className="
            bg-green-700
            text-white
            px-4
            py-2
            rounded
          "
        >
          MATCH sélection
        </button>

        <button
          onClick={ignoreBulk}
          disabled={processing}
          className="
            bg-red-600
            text-white
            px-4
            py-2
            rounded
          "
        >
          IGNORE sélection
        </button>

      </div>

      {/* =====================================================
          TABLE
      ===================================================== */}

      <MatchingTable
        items={entities}
        options={options}
        selected={selected}
        setSelected={setSelected}
        selectedType={selectedType}
        setSelectedType={setSelectedType}
        checked={checked}
        setChecked={setChecked}
        processing={
          processing
            ? "processing"
            : null
        }
        applyMatch={applyMatch}
        ignore={ignore}
      />

    </div>

  );

}
