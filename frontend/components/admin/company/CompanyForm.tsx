"use client";

import { useEffect, useState, useCallback } from "react";

import { api } from "@/lib/api";

import {
  EMPTY_COMPANY,
  CompanyFormData,
  CompanyType,
  Universe,
} from "@/types/company";

import CompanyIdentity from "./CompanyIdentity";
import CompanyKnowledge from "./CompanyKnowledge";
import CompanyAliases from "./CompanyAliases";
import CompanyVisuals from "./CompanyVisuals";

/* ========================================================= */

type Props = {
  mode: "create" | "edit";
  companyId?: string;
};

/* ========================================================= */

export default function CompanyForm({

  mode,
  companyId: initialCompanyId,

}: Props) {

  const isCreate =
    mode === "create";

  /* =======================================================
     ENTITY
  ======================================================= */

  const [
    company,
    setCompany,
  ] = useState<CompanyFormData>(
    EMPTY_COMPANY
  );

  const [
    companyId,
    setCompanyId,
  ] = useState<string | null>(
    initialCompanyId ?? null
  );

  /* =======================================================
     REFERENCES
  ======================================================= */

  const [
    companyTypes,
    setCompanyTypes,
  ] = useState<
    CompanyType[]
  >([]);

  const [
    availableUniverses,
    setAvailableUniverses,
  ] = useState<
    Universe[]
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
     LOAD REFERENCE DATA
  ======================================================= */

  async function loadReferenceData() {

    const [
      typesRes,
      universesRes,
    ] = await Promise.all([

      api.get("/company/types"),

      api.get("/universe/list"),

    ]);

    setCompanyTypes(
      typesRes.types ?? []
    );

    setAvailableUniverses(
      universesRes.universes ?? []
    );

  }

  /* =======================================================
     LOAD COMPANY
  ======================================================= */

  async function loadCompany(
    id: string | null = companyId,
  ) {

    if (!id) {
      return;
    }

    const c = await api.get(
      `/company/${id}`
    );
    
    setCompany({

      name:
        c.name ?? "",

      type:
        c.type ?? "",

      description:
        c.description ?? "",

      wiki_content:
        c.wiki_content ?? "",

      linkedin_url:
        c.linkedin_url ?? "",

      website_url:
        c.website_url ?? "",

      is_partner:
        c.is_partner ?? false,

      universes:
        c.universes ?? [],

      aliases:
        c.aliases ?? [],

    });

    setLogoFilename(
      c.media_logo_rectangle_id ?? null
    );

  }

  /* =======================================================
   LOAD
======================================================= */

const load = useCallback(
  async () => {

    try {

      setLoading(true);

      await loadReferenceData();

      await loadCompany();

    } catch (e) {

      console.error(e);

      alert(
        "Erreur chargement société."
      );

    } finally {

      setLoading(false);

    }

  },
  [companyId],
);

/* =======================================================
   INITIAL LOAD
======================================================= */

useEffect(() => {

  load();

}, [load]);

  /* =======================================================
     BUILD PAYLOAD
  ======================================================= */

  function getCompanyPayload() {

    return {

      name:
        company.name,

      type:
        company.type || null,

      description:
        company.description || null,

      linkedin_url:
        company.linkedin_url || null,

      website_url:
        company.website_url || null,

      wiki_content:
        company.wiki_content || null,

      is_partner:
        company.is_partner,

      universes:
        company.universes,

      aliases:
        company.aliases.map(
          (a) => a.alias
        ),

    };

  }

  /* =======================================================
     CREATE
  ======================================================= */

  async function handleCreate(): Promise<string> {

    const payload =
      getCompanyPayload();

    console.log(
      "Company payload",
      payload,
    );

    const res =
      await api.post(
        "/company/create",
        payload,
      );

    if (!res.id_company) {

      throw new Error(
        "Missing company id."
      );

    }

    return res.id_company;

  }

  /* =======================================================
     UPDATE
  ======================================================= */

  async function handleUpdate() {

    if (!companyId) {
      return;
    }

    await api.put(

      `/company/update/${companyId}`,

      getCompanyPayload(),

    );

    await loadCompany();

  }

  /* =======================================================
     SAVE
  ======================================================= */

  async function handleSave() {

    try {

      setSaving(true);

      if (isCreate) {

        const newCompanyId =
          await handleCreate();

        setCompanyId(
          newCompanyId
        );

        await loadCompany(
          newCompanyId
        );

      } else {

        await handleUpdate();

      }

    } catch (e) {

      console.error(e);

      alert(
        "Erreur sauvegarde société."
      );

    } finally {

      setSaving(false);

    }

  }

  /* =======================================================
     ADD ALIAS
  ======================================================= */

  async function handleAddAlias(
    alias: string,
  ) {

    if (!companyId) {

      setCompany((prev) => ({

        ...prev,

        aliases: [

          ...prev.aliases,

          {
            alias,
          },

        ],

      }));

      return;

    }

    await api.post(

      `/company/${companyId}/alias`,

      {
        alias,
      },

    );

    await loadCompany();

  }

  /* =======================================================
     DELETE ALIAS
  ======================================================= */

  async function handleDeleteAlias(
    alias: string,
  ) {

    if (!companyId) {

      setCompany((prev) => ({

        ...prev,

        aliases:

          prev.aliases.filter(

            (a) =>
              a.alias !== alias,

          ),

      }));

      return;

    }

    await api.delete(

      `/company/${companyId}/alias?alias=${encodeURIComponent(alias)}`

    );

    await loadCompany();

  }

  /* =======================================================
     VISUAL UPDATED
  ======================================================= */

  async function handleVisualUpdated() {

    await loadCompany();

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

      {/* ===================================================
          IDENTITY
      ==================================================== */}

      <CompanyIdentity

        company={company}

        setCompany={setCompany}

        companyTypes={companyTypes}

        universes={availableUniverses}

      />

      {/* ===================================================
          KNOWLEDGE
      ==================================================== */}

      <CompanyKnowledge

        company={company}

        setCompany={setCompany}

      />

      {/* ===================================================
          ALIASES
      ==================================================== */}

      <CompanyAliases

        aliases={company.aliases}

        onAdd={handleAddAlias}

        onDelete={handleDeleteAlias}

      />

      {/* ===================================================
          VISUALS
      ==================================================== */}

      <CompanyVisuals

        companyId={companyId}

        logoFilename={logoFilename}

        onUpdated={handleVisualUpdated}

      />

      {/* ===================================================
          ACTIONS
      ==================================================== */}

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
              ? "Create company"
              : "Save changes"}

        </button>

      </div>

    </div>

  );

}
