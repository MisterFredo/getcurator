"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

import SearchableSelect, {
  SelectOption,
} from "@/components/ui/SearchableSelect";

import type {
  CompanyOption,
} from "@/types/company";

import type {
  KnowledgeEntity,
} from "@/types/knowledge";

/* ========================================================= */

export default function KnowledgePage() {

  const [
    companies,
    setCompanies,
  ] = useState<CompanyOption[]>([]);

  const [
    selectedCompany,
    setSelectedCompany,
  ] = useState<SelectOption | null>(
    null,
  );

  const [
    knowledge,
    setKnowledge,
  ] =
    useState<KnowledgeEntity | null>(
      null,
    );

  const [
    signal,
    setSignal,
  ] =
    useState("");

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    building,
    setBuilding,
  ] =
    useState(false);

  const [
    saving,
    setSaving,
  ] =
    useState(false);

  /* =======================================================
     LOAD COMPANIES
  ======================================================= */

  useEffect(() => {

    async function load() {

      try {

        const res =
          await api.get(
            "/company/list"
          );

        setCompanies(
          res.companies || [],
        );

      } catch (e) {

        console.error(e);

        alert(
          "Unable to load companies."
        );

      } finally {

        setLoading(false);

      }

    }

    load();

  }, []);

  /* =======================================================
     LOAD KNOWLEDGE
  ======================================================= */

  async function loadKnowledge(
    companyId: string,
  ) {

    try {

      const res =
        await api.get(
          `/knowledge/company/${companyId}`
        );

      const entity =
        res.knowledge as KnowledgeEntity;

      setKnowledge(
        entity,
      );

      setSignal(
        entity?.signal_analytique
          ?.content || "",
      );

    } catch (e) {

      console.error(e);

      setKnowledge(null);

      setSignal("");

    }

  }

  /* =======================================================
     BUILD
  ======================================================= */

  async function buildKnowledge() {

    if (!selectedCompany) {
      return;
    }

    setBuilding(true);

    try {

      await api.post(
        "/knowledge/build",
        {

          entity_type:
            "company",

          entity_id:
            selectedCompany.id,

        },
      );

      await loadKnowledge(
        selectedCompany.id,
      );

      alert(
        "Knowledge built."
      );

    } catch (e) {

      console.error(e);

      alert(
        "Build failed."
      );

    } finally {

      setBuilding(false);

    }

  }

  /* =======================================================
     SAVE
  ======================================================= */

  async function saveSignal() {

    if (!selectedCompany) {
      return;
    }

    setSaving(true);

    try {

      await api.put(
        "/knowledge/block",
        {

          entity_type:
            "company",

          entity_id:
            selectedCompany.id,

          block_type:
            "signal_analytique",

          content:
            signal,

        },
      );

      await loadKnowledge(
        selectedCompany.id,
      );

      alert(
        "Saved."
      );

    } catch (e) {

      console.error(e);

      alert(
        "Save failed."
      );

    } finally {

      setSaving(false);

    }

  }
