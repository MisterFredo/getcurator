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

export default function MatchingPage() {

  const [loading, setLoading] = useState(true);

  const [tab, setTab] = useState<
    "solutions" | "companies"
  >("solutions");

  const [llmSolutions, setLLMSolutions] = useState<LLMItem[]>([]);
  const [llmCompanies, setLLMCompanies] = useState<LLMItem[]>([]);

  const [solutions, setSolutions] = useState<Solution[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);

  const [selected, setSelected] = useState<{
    [key: string]: string;
  }>({});

  const [checked, setChecked] = useState<{
    [key: string]: boolean;
  }>({});

  const [processing, setProcessing] = useState(false);

  const [syncing, setSyncing] = useState(false);

  /* =========================================================
     LOAD
  ========================================================= */

  async function loadData() {

    try {

      setLoading(true);

      const [
        llmSolRes,
        llmCompRes,
        solRes,
        compRes,
      ] = await Promise.all([
        api.get("/matching/solutions"),
        api.get("/matching/companies"),
        api.get("/solution/list"),
        api.get("/company/list"),
      ]);

      setLLMSolutions(
        llmSolRes.solutions || []
      );

      setLLMCompanies(
        llmCompRes.companies || []
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
     CURRENT DATA
  ========================================================= */

  const items = useMemo(() => {

    return tab === "solutions"
      ? llmSolutions
      : llmCompanies;

  }, [
    tab,
    llmSolutions,
    llmCompanies,
  ]);

  const list = useMemo(() => {

    return tab === "solutions"
      ? solutions
      : companies;

  }, [
    tab,
    solutions,
    companies,
  ]);

  /* =========================================================
     AUTO SELECT
  ========================================================= */

  useEffect(() => {

    const auto: Record<string, string> = {};

    items.forEach((item) => {

      if (item.suggested_id) {

        auto[item.value] =
          item.suggested_id;

      }

    });

    setSelected(auto);

  }, [items]);

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

    const values = getCheckedValues();

    if (values.length === 0) {

      alert("Aucune sélection");

      return;

    }

    try {

      setProcessing(true);

      if (tab === "solutions") {

        const payload = {
          items: values
            .filter((value) => selected[value])
            .map((value) => ({
              alias: value,
              id_solution: selected[value],
              action: "MATCH",
            })),
        };

        await api.post(
          "/matching/solutions/bulk-match",
          payload
        );

        setLLMSolutions((prev) =>
          prev.filter(
            (v) => !values.includes(v.value)
          )
        );

      } else {

        const payload = {
          items: values
            .filter((value) => selected[value])
            .map((value) => ({
              alias: value,
              id_company: selected[value],
              action: "MATCH",
            })),
        };

        await api.post(
          "/matching/companies/bulk-match",
          payload
        );

        setLLMCompanies((prev) =>
          prev.filter(
            (v) => !values.includes(v.value)
          )
        );

      }

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

    const values = getCheckedValues();

    if (values.length === 0) {

      alert("Aucune sélection");

      return;

    }

    try {

      setProcessing(true);

      if (tab === "solutions") {

        const payload = {
          items: values.map((value) => ({
            alias: value,
            action: "IGNORE",
          })),
        };

        await api.post(
          "/matching/solutions/bulk-match",
          payload
        );

        setLLMSolutions((prev) =>
          prev.filter(
            (v) => !values.includes(v.value)
          )
        );

      } else {

        const payload = {
          items: values.map((value) => ({
            alias: value,
            action: "IGNORE",
          })),
        };

        await api.post(
          "/matching/companies/bulk-match",
          payload
        );

        setLLMCompanies((prev) =>
          prev.filter(
            (v) => !values.includes(v.value)
          )
        );

      }

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

    const id = selected[value];

    if (!id) {

      alert("Sélectionner une valeur");

      return;

    }

    try {

      setProcessing(true);

      if (tab === "solutions") {

        await api.post(
          "/matching/solutions/match",
          {
            alias: value,
            id_solution: id,
            action: "MATCH",
          }
        );

        setLLMSolutions((prev) =>
          prev.filter(
            (v) => v.value !== value
          )
        );

      } else {

        await api.post(
          "/matching/companies/match",
          {
            alias: value,
            id_company: id,
            action: "MATCH",
          }
        );

        setLLMCompanies((prev) =>
          prev.filter(
            (v) => v.value !== value
          )
        );

      }

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

      if (tab === "solutions") {

        await api.post(
          "/matching/solutions/match",
          {
            alias: value,
            action: "IGNORE",
          }
        );

        setLLMSolutions((prev) =>
          prev.filter(
            (v) => v.value !== value
          )
        );

      } else {

        await api.post(
          "/matching/companies/match",
          {
            alias: value,
            action: "IGNORE",
          }
        );

        setLLMCompanies((prev) =>
          prev.filter(
            (v) => v.value !== value
          )
        );

      }

    } catch (e) {

      console.error(e);

      alert("Erreur ignore");

    } finally {

      setProcessing(false);

    }

  }

  /* =========================================================
     SYNC
  ========================================================= */

  async function syncFeed() {

    try {

      setSyncing(true);

      await api.post(
        "/content/sync-all",
        {}
      );

      alert("Sync terminé");

    } catch (e) {

      console.error(e);

      alert("Erreur sync");

    } finally {

      setSyncing(false);

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

      <div className="flex items-center justify-between">

        <div>

          <h1 className="text-3xl font-semibold">
            Matching LLM
          </h1>

          <p className="text-sm text-gray-500 mt-1">
            Gestion des alias LLM et synchronisation feed
          </p>

        </div>

        <button
          onClick={syncFeed}
          disabled={syncing}
          className="
            bg-black
            text-white
            px-4
            py-2
            rounded
          "
        >
          {syncing
            ? "Synchronisation..."
            : "SYNC FEED"}
        </button>

      </div>

      {/* =====================================================
          TABS
      ===================================================== */}

      <div className="flex gap-4">

        <button
          onClick={() =>
            setTab("solutions")
          }
          className={`
            px-4 py-2 rounded
            ${
              tab === "solutions"
                ? "bg-ratecard-blue text-white"
                : "bg-gray-200"
            }
          `}
        >
          Solutions
        </button>

        <button
          onClick={() =>
            setTab("companies")
          }
          className={`
            px-4 py-2 rounded
            ${
              tab === "companies"
                ? "bg-ratecard-blue text-white"
                : "bg-gray-200"
            }
          `}
        >
          Sociétés
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
        items={items}
        list={list}
        tab={tab}
        selected={selected}
        setSelected={setSelected}
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
