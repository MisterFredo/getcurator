"use client";

import { useEffect, useState } from "react";

import Link from "next/link";

import { api } from "@/lib/api";

import VisualSection from "@/components/visuals/VisualSection";
import EntityBaseForm from "@/components/forms/EntityBaseForm";
import HtmlEditor from "@/components/admin/HtmlEditor";

/* ========================================================= */

const GCS_BASE_URL =
  process.env.NEXT_PUBLIC_GCS_BASE_URL!;

const COMPANY_MEDIA_PATH =
  "companies";

/* ========================================================= */

type CompanyType = {
  id_type: string;
  label: string;
};

type Universe = {
  id_universe: string;
  label: string;
};

/* ========================================================= */

export default function EditCompany({
  params,
}: {
  params: {
    id: string;
  };
}) {

  const { id } = params;

  /* =========================================================
     STATE
  ========================================================= */

  const [loading, setLoading] =
    useState(true);

  const [saving, setSaving] =
    useState(false);

  const [name, setName] =
    useState("");

  const [type, setType] =
    useState("");

  const [description, setDescription] =
    useState("");

  const [
    linkedinUrl,
    setLinkedinUrl
  ] = useState("");

  const [
    websiteUrl,
    setWebsiteUrl
  ] = useState("");

  const [isPartner, setIsPartner] =
    useState(false);

  const [
    wikiContent,
    setWikiContent
  ] = useState("");

  const [
    logoFilename,
    setLogoFilename
  ] = useState<string | null>(null);

  const [
    insightFrequency,
    setInsightFrequency
  ] = useState("QUARTERLY");

  const [types, setTypes] =
    useState<CompanyType[]>([]);

  // 🔥 UNIVERS

  const [universes, setUniverses] =
    useState<string[]>([]);

  const [
    availableUniverses,
    setAvailableUniverses
  ] = useState<Universe[]>([]);

  // 🔥 ALIASES

  type AliasItem = {
    alias: string;
    match_status?: string;
  };

  const [aliases, setAliases] =
    useState<AliasItem[]>([]);

  const [newAlias, setNewAlias] =
    useState("");

  /* =========================================================
     LOAD TYPES + UNIVERS
  ========================================================= */

  useEffect(() => {

    async function loadMeta() {

      try {

        const [
          typesRes,
          universesRes,
        ] = await Promise.all([
          api.get("/company/types"),
          api.get("/universe/list"),
        ]);

        setTypes(
          typesRes.types || []
        );

        setAvailableUniverses(
          universesRes.universes || []
        );

      } catch (e) {

        console.error(e);

        alert(
          "❌ Erreur chargement données"
        );

      }

    }

    loadMeta();

  }, []);

  /* =========================================================
     LOAD COMPANY
  ========================================================= */

  useEffect(() => {

    async function load() {

      setLoading(true);

      try {

        const c = await api.get(
          `/company/${id}`
        );

        setName(c.name || "");

        setType(c.type || "");

        setDescription(
          c.description || ""
        );

        setLinkedinUrl(
          c.linkedin_url || ""
        );

        setWebsiteUrl(
          c.website_url || ""
        );

        setIsPartner(
          Boolean(c.is_partner)
        );

        setWikiContent(
          c.wiki_content || ""
        );

        setLogoFilename(
          c.media_logo_rectangle_id
          || null
        );

        setInsightFrequency(
          c.insight_frequency
          || "QUARTERLY"
        );

        // 🔥 UNIVERS

        setUniverses(
          c.universes || []
        );

        // 🔥 ALIASES

        const aliasesRes =
          await api.get(
            `/company/${id}/aliases`
          );

        setAliases(
          aliasesRes.aliases || []
        );

      } catch (e) {

        console.error(e);

        alert(
          "❌ Erreur chargement société"
        );

      } finally {

        setLoading(false);

      }

    }

    load();

  }, [id]);

  /* =========================================================
     TOGGLE UNIVERS
  ========================================================= */

  function toggleUniverse(
    uid: string
  ) {

    setUniverses((prev) =>
      prev.includes(uid)
        ? prev.filter(
            (u) => u !== uid
          )
        : [...prev, uid]
    );

  }

  /* =========================================================
     ADD ALIAS
  ========================================================= */

  async function addAlias() {

    const value =
      newAlias.trim();

    if (!value) return;

    try {

      await api.post(
        `/company/${id}/alias`,
        {
          alias: value,
        }
      );

      setAliases((prev) => [

        ...prev,

        value,

      ]);

      setNewAlias("");

    } catch (e) {

      console.error(e);

      alert(
        "❌ Erreur ajout alias"
      );

    }

  }

  /* =========================================================
     DELETE ALIAS
  ========================================================= */

  async function deleteAlias(
    alias: string
  ) {

    const confirmed =
      window.confirm(
        `Supprimer l'alias "${alias}" ?`
      );

    if (!confirmed) return;

    try {

      await api.delete(
        `/company/${id}/alias?alias=${encodeURIComponent(alias)}`
      );

      setAliases((prev) =>
        prev.filter(
          (a) => a !== alias
        )
      );

    } catch (e) {

      console.error(e);

      alert(
        "❌ Erreur suppression alias"
      );

    }

  }

  /* =========================================================
     SAVE
  ========================================================= */

  async function save() {

    setSaving(true);

    try {

      await api.put(
        `/company/update/${id}`,
        {
          name,

          type:
            type || null,

          description:
            description || null,

          linkedin_url:
            linkedinUrl || null,

          website_url:
            websiteUrl || null,

          is_partner:
            isPartner,

          wiki_content:
            wikiContent || null,

          insight_frequency:
            insightFrequency,

          universes,
        }
      );

      alert(
        "Société modifiée"
      );

    } catch (e) {

      console.error(e);

      alert(
        "❌ Erreur mise à jour"
      );

    } finally {

      setSaving(false);

    }

  }

  /* =========================================================
     URL LOGO
  ========================================================= */

  const rectUrl =
    logoFilename
      ? `${GCS_BASE_URL}/${COMPANY_MEDIA_PATH}/${logoFilename}`
      : null;

  /* ========================================================= */

  if (loading) {

    return <p>Chargement…</p>;

  }

  /* =========================================================
     UI
  ========================================================= */

  return (

    <div className="space-y-10">

      {/* HEADER */}

      <div className="
        flex
        justify-between
      ">

        <h1 className="
          text-3xl
          font-semibold
          text-ratecard-blue
        ">
          Modifier la société
        </h1>

        <Link
          href="/admin/company"
          className="underline"
        >
          ← Retour
        </Link>

      </div>

      {/* BASE FORM */}

      <EntityBaseForm
        values={{
          name,
          linkedinUrl,
          websiteUrl,
        }}
        onChange={{
          setName,
          setLinkedinUrl,
          setWebsiteUrl,
        }}
      />

      {/* TYPE */}

      <div className="space-y-2">

        <label className="
          block
          font-medium
        ">
          Type
        </label>

        <select
          value={type}
          onChange={(e) =>
            setType(
              e.target.value
            )
          }
          className="
            border
            px-3
            py-2
            rounded
            w-full
            max-w-md
          "
        >

          <option value="">
            — Sélectionner —
          </option>

          {types.map((t) => (

            <option
              key={t.id_type}
              value={t.label}
            >
              {t.label}
            </option>

          ))}

        </select>

      </div>

      {/* 🔥 ALIASES */}

      <div className="space-y-4">

        <div>

          <label className="
            block
            font-medium
            mb-2
          ">
            Aliases
          </label>

          <div className="
            flex
            gap-2
            max-w-2xl
          ">

            <input
              type="text"
              value={newAlias}
              onChange={(e) =>
                setNewAlias(
                  e.target.value
                )
              }
              placeholder="
Ajouter un alias
              "
              className="
                border
                px-3
                py-2
                rounded
                flex-1
              "
            />

            <button
              type="button"
              onClick={addAlias}
              className="
                bg-ratecard-blue
                text-white
                px-4
                py-2
                rounded
              "
            >
              Ajouter
            </button>

          </div>

        </div>

        <div className="
          flex
          flex-wrap
          gap-2
        ">

          {aliases.map((alias) => (

            <div
              key={alias}
              className="
                flex
                items-center
                gap-2
                bg-gray-100
                px-3
                py-1
                rounded-full
                text-sm
              "
            >

              <span>
                {alias}
              </span>

              <button
                type="button"
                onClick={() =>
                  deleteAlias(
                    alias
                  )
                }
                className="
                  text-red-500
                  font-bold
                "
              >
                ×
              </button>

            </div>

          ))}

        </div>

      </div>

      {/* UNIVERS */}

      <div className="space-y-2">

        <label className="
          block
          font-medium
        ">
          Univers
        </label>

        <div className="
          flex
          flex-col
          gap-2
        ">

          {availableUniverses.map((u) => (

            <label
              key={u.id_universe}
              className="
                flex
                items-center
                gap-2
              "
            >

              <input
                type="checkbox"
                checked={universes.includes(
                  u.id_universe
                )}
                onChange={() =>
                  toggleUniverse(
                    u.id_universe
                  )
                }
              />

              {u.label}

            </label>

          ))}

        </div>

      </div>

      {/* FREQUENCY */}

      <div className="space-y-2">

        <label className="
          block
          font-medium
        ">
          Fréquence des insights
        </label>

        <select
          value={insightFrequency}
          onChange={(e) =>
            setInsightFrequency(
              e.target.value
            )
          }
          className="
            border
            px-3
            py-2
            rounded
            w-full
            max-w-md
          "
        >

          <option value="WEEKLY">
            Weekly
          </option>

          <option value="MONTHLY">
            Monthly
          </option>

          <option value="QUARTERLY">
            Quarterly
          </option>

        </select>

      </div>

      {/* DESCRIPTION */}

      <div className="space-y-2">

        <label className="
          block
          font-medium
        ">
          Description (commerciale)
        </label>

        <HtmlEditor
          value={description}
          onChange={setDescription}
        />

      </div>

      {/* WIKI */}

      <div className="
        border-t
        pt-6
        space-y-2
      ">

        <h2 className="
          text-lg
          font-semibold
        ">
          Wiki
        </h2>

        <HtmlEditor
          value={wikiContent}
          onChange={setWikiContent}
        />

      </div>

      {/* PARTNER */}

      <div className="
        flex
        items-center
        gap-2
      ">

        <input
          type="checkbox"
          checked={isPartner}
          onChange={(e) =>
            setIsPartner(
              e.target.checked
            )
          }
        />

        <label className="text-sm">
          Société partenaire
        </label>

      </div>

      {/* SAVE */}

      <button
        className="
          bg-ratecard-blue
          px-4
          py-2
          text-white
          rounded
        "
        onClick={save}
        disabled={saving}
      >

        {saving
          ? "Enregistrement…"
          : "Enregistrer"}

      </button>

      {/* VISUAL */}

      <VisualSection
        entityId={id}
        entityType="company"
        rectUrl={rectUrl}
        onUpdated={async () => {

          try {

            const c =
              await api.get(
                `/company/${id}`
              );

            setLogoFilename(
              c.media_logo_rectangle_id
              || null
            );

          } catch (e) {

            console.error(e);

          }

        }}
      />

    </div>

  );

}
