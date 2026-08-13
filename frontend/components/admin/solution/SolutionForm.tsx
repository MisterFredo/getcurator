// components/admin/solution/SolutionForm.tsx

"use client";

import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";

import type {
  CompanyOption,
} from "@/types/company";

import {
  EMPTY_SOLUTION,
} from "@/types/solution";

import type {
  SolutionFormData,
} from "@/types/solution";

import SolutionIdentity from "./SolutionIdentity";
import SolutionKnowledge from "./SolutionKnowledge";
import SolutionAliases from "./SolutionAliases";
import SolutionVisuals from "./SolutionVisuals";

/* ========================================================= */

type Props = {
  mode: "create" | "edit";
  solutionId?: string;
};

/* ========================================================= */

export default function SolutionForm({

  mode,
  solutionId: initialSolutionId,

}: Props) {

  const isCreate =
    mode === "create";

  /* =======================================================
     ENTITY
  ======================================================= */

  const [
    solution,
    setSolution,
  ] = useState<SolutionFormData>(
    EMPTY_SOLUTION
  );

  const [
    solutionId,
    setSolutionId,
  ] = useState<string | null>(
    initialSolutionId ?? null
  );

  /* =======================================================
     REFERENCES
  ======================================================= */

  const [
    companies,
    setCompanies,
  ] = useState<
    CompanyOption[]
  >([]);

  /* =======================================================
     VISUALS
  ======================================================= */

  const [
    logoFilename,
    setLogoFilename,
  ] = useState<string | null>(
    null
  );

  /* =======================================================
     UI
  ======================================================= */

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    saving,
    setSaving,
  ] = useState(false);

  /* =======================================================
     LOAD REFERENCES
  ======================================================= */

  async function loadReferenceData() {

    const res =
      await api.get(
        "/company/list"
      );

    setCompanies(
      res.companies ?? []
    );

  }

  /* =======================================================
     LOAD SOLUTION
  ======================================================= */

  async function loadSolution() {

    if (!solutionId) {
      return;
    }

    const s =
      await api.get(
        `/solution/${solutionId}`
      );

    setSolution({

      name:
        s.name ?? "",

      id_company:
        s.id_company ?? "",

      description:
        s.description ?? "",

      content:
        s.content ?? "",

      aliases:
        s.aliases ?? [],

    });

    setLogoFilename(
      s.media_logo_rectangle_id ?? null
    );

  }

  /* =======================================================
     LOAD
  ======================================================= */

  const load =
    useCallback(
      async () => {

        try {

          setLoading(true);

          await loadReferenceData();

          await loadSolution();

        } finally {

          setLoading(false);

        }

      },
      [solutionId],
    );

  useEffect(() => {

    load();

  }, [load]);

  /* =======================================================
     PAYLOADS
  ======================================================= */

  function getPayload() {

    return {

      name:
        solution.name,

      id_company:
        solution.id_company,

      description:
        solution.description || null,

      content:
        solution.content || null,

      aliases:
        solution.aliases.map(
          (a) => a.alias
        ),

    };

  }

  /* =======================================================
     CREATE
  ======================================================= */

  async function handleCreate(): Promise<string> {

    const res =
      await api.post(
        "/solution/create",
        getPayload(),
      );

    return res.id_solution;

  }

  /* =======================================================
     UPDATE
  ======================================================= */

  async function handleUpdate() {

    if (!solutionId) {
      return;
    }

    await api.put(

      `/solution/update/${solutionId}`,

      getPayload(),

    );

  }

  /* =======================================================
     SAVE
  ======================================================= */

  async function handleSave() {

    try {

      setSaving(true);

      if (isCreate) {

        const id =
          await handleCreate();

        setSolutionId(id);

      } else {

        await handleUpdate();

      }

      await load();

    } finally {

      setSaving(false);

    }

  }

  /* =======================================================
     ALIASES
  ======================================================= */

  async function handleAddAlias(
    alias: string,
  ) {

    if (!solutionId) {

      setSolution((prev) => ({

        ...prev,

        aliases: [

          ...prev.aliases,

          { alias },

        ],

      }));

      return;

    }

    await api.post(

      `/solution/${solutionId}/alias`,

      { alias },

    );

    await load();

  }

  async function handleDeleteAlias(
    alias: string,
  ) {

    if (!solutionId) {

      setSolution((prev) => ({

        ...prev,

        aliases:
          prev.aliases.filter(
            (a) =>
              a.alias !== alias
          ),

      }));

      return;

    }

    await api.delete(

      `/solution/${solutionId}/alias?alias=${encodeURIComponent(alias)}`

    );

    await load();

  }

  /* =======================================================
     RENDER
  ======================================================= */

  if (loading) {

    return (
      <div className="text-gray-500">
        Chargement...
      </div>
    );

  }

  return (

    <div className="space-y-10">

      <SolutionIdentity

        name={solution.name}
        setName={(name) =>
          setSolution({
            ...solution,
            name,
          })
        }

        idCompany={solution.id_company}
        setIdCompany={(id_company) =>
          setSolution({
            ...solution,
            id_company,
          })
        }

        companies={companies}

      />

      <SolutionKnowledge

        description={
          solution.description
        }

        setDescription={(
          description,
        ) =>
          setSolution({
            ...solution,
            description,
          })
        }

        content={
          solution.content
        }

        setContent={(
          content,
        ) =>
          setSolution({
            ...solution,
            content,
          })
        }

      />

      <SolutionAliases

        aliases={
          solution.aliases
        }

        onAdd={
          handleAddAlias
        }

        onDelete={
          handleDeleteAlias
        }

      />

      <SolutionVisuals

        solutionId={
          solutionId
        }

        logoFilename={
          logoFilename
        }

        onUpdated={load}

      />

      <div className="flex justify-end pt-8 border-t">

        <button

          onClick={handleSave}

          disabled={saving}

          className="
            bg-ratecard-blue
            text-white
            px-6
            py-3
            rounded
            disabled:opacity-50
          "

        >

          {saving
            ? "Saving..."
            : isCreate
              ? "Create solution"
              : "Save changes"}

        </button>

      </div>

    </div>

  );

}
