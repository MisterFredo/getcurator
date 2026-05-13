"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

import VisualSection from "@/components/visuals/VisualSection";
import EntityBaseForm from "@/components/forms/EntityBaseForm";
import HtmlEditor from "@/components/admin/HtmlEditor";

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

export default function CreateCompany() {

  const [name, setName] =
    useState("");

  const [type, setType] =
    useState("");

  const [description, setDescription] =
    useState("");

  const [linkedinUrl, setLinkedinUrl] =
    useState("");

  const [websiteUrl, setWebsiteUrl] =
    useState("");

  const [aliases, setAliases] =
    useState("");

  const [isPartner, setIsPartner] =
    useState(false);

  const [wikiContent, setWikiContent] =
    useState("");

  const [
    insightFrequency,
    setInsightFrequency
  ] = useState("QUARTERLY");

  const [
    companyId,
    setCompanyId
  ] = useState<string | null>(null);

  const [
    logoFilename,
    setLogoFilename
  ] = useState<string | null>(null);

  const [saving, setSaving] =
    useState(false);

  const [types, setTypes] =
    useState<CompanyType[]>([]);

  // 🔥 UNIVERS
  const [universes, setUniverses] =
    useState<string[]>([]);

  const [
    availableUniverses,
    setAvailableUniverses
  ] = useState<Universe[]>([]);

  /* =========================================================
     LOAD TYPES + UNIVERS
  ========================================================= */

  useEffect(() => {

    async function load() {

      try {

        const [
          typesRes,
          universesRes
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

    load();

  }, []);

  /* =========================================================
     TOGGLE UNIVERS
  ========================================================= */

  function toggleUniverse(id: string) {

    setUniverses((prev) =>
      prev.includes(id)
        ? prev.filter((u) => u !== id)
        : [...prev, id]
    );

  }

  /* =========================================================
     CREATE
  ========================================================= */

  async function save() {

    if (!name.trim()) {

      alert("Nom requis");

      return;

    }

    setSaving(true);

    try {

      const res = await api.post(
        "/company/create",
        {
          name,

          type: type || null,

          description:
            description || null,

          linkedin_url:
            linkedinUrl || null,

          website_url:
            websiteUrl || null,

          is_partner:
            isPartner,

          insight_frequency:
            insightFrequency,

          aliases: aliases
            .split(";")
            .map((a) => a.trim())
            .filter(Boolean),

          universes,
        }
      );

      if (!res.id_company) {

        throw new Error(
          "ID société manquant"
        );

      }

      const newCompanyId =
        res.id_company;

      setCompanyId(
        newCompanyId
      );

      if (wikiContent.trim()) {

        await api.put(
          `/company/update/${newCompanyId}`,
          {
            wiki_content:
              wikiContent,
          }
        );

      }

      alert(
        "Société créée. Vous pouvez maintenant ajouter un logo."
      );

    } catch (e) {

      console.error(e);

      alert(
        "❌ Erreur création société"
      );

    } finally {

      setSaving(false);

    }

  }

  /* =========================================================
     RELOAD COMPANY
  ========================================================= */

  async function reloadCompany() {

    if (!companyId) return;

    try {

      const c = await api.get(
        `/company/${companyId}`
      );

      setLogoFilename(
        c.media_logo_rectangle_id
        || null
      );

      if (c.insight_frequency) {

        setInsightFrequency(
          c.insight_frequency
        );

      }

    } catch (e) {

      console.error(e);

      alert(
        "❌ Erreur rechargement société"
      );

    }

  }

  /* ========================================================= */

  const rectUrl =
    logoFilename
      ? `${GCS_BASE_URL}/${COMPANY_MEDIA_PATH}/${logoFilename}`
      : null;

  /* =========================================================
     UI
  ========================================================= */

  return (

    <div className="space-y-10">

      {/* HEADER */}

      <div className="flex justify-between">

        <h1 className="
          text-2xl
          font-semibold
          text-ratecard-blue
        ">
          Ajouter une société
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

      {/* ALIASES */}

      <div className="space-y-2">

        <label className="
          block
          font-medium
        ">
          Aliases
        </label>

        <textarea
          value={aliases}
          onChange={(e) =>
            setAliases(
              e.target.value
            )
          }
          placeholder="
Amazon;
Amazon Ads;
Amazon DSP
          "
          className="
            border
            px-3
            py-2
            rounded
            w-full
            max-w-2xl
            min-h-[90px]
          "
        />

        <p className="
          text-xs
          text-gray-500
        ">
          Séparer les aliases avec ;
        </p>

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

      {/* CTA */}

      <button
        onClick={save}
        disabled={saving}
        className="
          bg-ratecard-blue
          px-4
          py-2
          text-white
          rounded
        "
      >

        {saving
          ? "Enregistrement…"
          : "Créer"}

      </button>

      {/* VISUAL */}

      {companyId && (

        <VisualSection
          entityId={companyId}
          entityType="company"
          rectUrl={rectUrl}
          onUpdated={reloadCompany}
        />

      )}

    </div>

  );

}
