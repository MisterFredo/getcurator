"use client";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import { api } from "@/lib/api";

import {
  EMPTY_CONCEPT,
  ConceptFormData,
} from "@/types/concept";

import ConceptIdentity from "./ConceptIdentity";

/* ========================================================= */

type Props = {
  mode: "create" | "edit";
  conceptId?: string;
};

/* ========================================================= */

export default function ConceptForm({

  mode,

  conceptId: initialConceptId,

}: Props) {

  const isCreate =
    mode === "create";

  const [
    concept,
    setConcept,
  ] = useState<ConceptFormData>(
    EMPTY_CONCEPT
  );

  const [
    conceptId,
    setConceptId,
  ] = useState<string | null>(
    initialConceptId ?? null
  );

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    saving,
    setSaving,
  ] = useState(false);

  /* ======================================================= */

  async function loadConcept() {

    if (!conceptId) {
      return;
    }

    const res =
      await api.get(
        `/concept/${conceptId}`
      );

    const c =
      res.concept;

    setConcept({

      label:
        c.label ?? "",

      description:
        c.description ?? "",

    });

  }

  /* ======================================================= */

  const load = useCallback(
    async () => {

      try {

        setLoading(true);

        await loadConcept();

      } catch (e) {

        console.error(e);

        alert(
          "Error loading concept."
        );

      } finally {

        setLoading(false);

      }

    },
    [conceptId]
  );

  useEffect(() => {

    load();

  }, [load]);

  /* ======================================================= */

  function getPayload() {

    return {

      label:
        concept.label,

      description:
        concept.description || null,

    };

  }

  /* ======================================================= */

  async function handleCreate() {

    const res =
      await api.post(
        "/concept/create",
        getPayload()
      );

    if (!res.id_concept) {

      throw new Error(
        "Missing concept id."
      );

    }

    return res.id_concept;

  }

  /* ======================================================= */

  async function handleUpdate() {

    if (!conceptId) {
      return;
    }

    await api.put(

      `/concept/update/${conceptId}`,

      getPayload(),

    );

    await loadConcept();

  }

  /* ======================================================= */

  async function handleSave() {

    if (
      !concept.label.trim()
    ) {

      alert(
        "Label required."
      );

      return;

    }

    try {

      setSaving(true);

      if (isCreate) {

        const id =
          await handleCreate();

        setConceptId(id);

      } else {

        await handleUpdate();

      }

    } catch (e) {

      console.error(e);

      alert(
        "Unable to save concept."
      );

    } finally {

      setSaving(false);

    }

  }

  /* ======================================================= */

  if (loading) {

    return (
      <div>
        Loading...
      </div>
    );

  }

  return (

    <div className="space-y-10">

      <ConceptIdentity

        label={concept.label}

        setLabel={(label) =>
          setConcept((p) => ({
            ...p,
            label,
          }))
        }

        description={
          concept.description
        }

        setDescription={(
          description
        ) =>
          setConcept((p) => ({
            ...p,
            description,
          }))
        }

      />

      <div className="flex justify-end border-t pt-8">

        <button

          onClick={
            handleSave
          }

          disabled={
            saving
          }

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
            ? "Create concept"
            : "Save changes"}

        </button>

      </div>

    </div>

  );

}
