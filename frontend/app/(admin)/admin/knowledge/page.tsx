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

type KnowledgeBlockKey =
  | "signal_analytique"
  | "mecanique_expliquee"
  | "enjeu_strategique"
  | "point_de_friction"
  | "chiffres";

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
    selectedBlock,
    setSelectedBlock,
  ] = useState<KnowledgeBlockKey>(
    "signal_analytique",
  );

  const BLOCKS = [
    {
      id: "signal_analytique",
      label: "Signal",
    },
  
    {
      id: "mecanique_expliquee",
      label: "Mécanique",
    },
  
    {
      id: "enjeu_strategique",
      label: "Enjeu",
    },
  
    {
      id: "point_de_friction",
      label: "Friction",
    },
  
  ] as const;

const [
  content,
  setContent,
] = useState("");

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

      setContent(

        entity?.[
          selectedBlock
        ]?.content || "",
      
      );

    } catch (e) {

      console.error(e);

      setKnowledge(null);

      setContent("");

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

  async function saveBlock() {

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
            selectedBlock,
  
          content,
  
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

    /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div className="space-y-8">

      {/* =================================================== */}

      <div>

        <h1 className="text-3xl font-semibold text-ratecard-blue">
          Knowledge
        </h1>

        <p className="text-gray-500 mt-1">
          Build and edit entity knowledge.
        </p>

      </div>

      {/* =================================================== */}

      {loading ? (

        <div>
          Loading...
        </div>

      ) : (

        <div className="space-y-6 max-w-5xl">

          <SearchableSelect

            label="Company"

            placeholder="Search company..."

            options={

              companies.map((c) => ({

                id: c.id_company,

                label: c.name,

              }))

            }

            value={selectedCompany}

            onChange={async (company) => {

              setSelectedCompany(
                company,
              );

              if (company) {

                await loadKnowledge(
                  company.id,
                );

              } else {

                setKnowledge(
                  null,
                );

                setContent("");

              }

            }}

          />

          <div>

            <label className="block text-sm font-medium mb-2">
          
              Knowledge Block
          
            </label>
          
            <select
          
              value={selectedBlock}
          
              onChange={(e) => {
          
                const block =
                  e.target.value as KnowledgeBlockKey;
          
                setSelectedBlock(
                  block,
                );
          
                setContent(
          
                  knowledge?.[
                    block
                  ]?.content || "",
          
                );
          
              }}
          
              className="border rounded px-3 py-2"
          
            >
          
              {
          
                BLOCKS.map((block) => (
          
                  <option
          
                    key={block.id}
          
                    value={block.id}
          
                  >
          
                    {block.label}
          
                  </option>
          
                ))
          
              }
          
            </select>
          
          </div>

          {/* =========================================== */}

          <div>

            <button

              onClick={
                buildKnowledge
              }

              disabled={
                !selectedCompany ||
                building
              }

              className="bg-ratecard-green text-white px-5 py-2 rounded disabled:opacity-50"

            >

              {

                building

                  ? "Building..."

                  : "Build Knowledge"

              }

            </button>

          </div>

          {/* =========================================== */}

          {

            selectedCompany && (

              <>

                <div className="space-y-2">

                  <div className="flex items-center justify-between">

                    <h2 className="text-xl font-semibold">

                      {

                        BLOCKS.find(
                      
                          b =>
                            b.id === selectedBlock
                      
                        )?.label
                      
                      }

                    </h2>

                    {

                      knowledge && (

                        <div className="text-xs text-gray-500">

                          Version {

                            knowledge?.[
                              selectedBlock
                            ]?.version

                          }

                        </div>

                      )

                    }

                  </div>

                  <textarea

                    value={content}

                    onChange={(e) =>

                      setContent(
                          e.target.value
                      )

                    }

                    rows={24}

                    className="w-full border rounded p-4 font-mono text-sm"

                  />

                </div>

                {/* =================================== */}

                <div>

                  <button

                    onClick={
                      saveBlock
                    }

                    disabled={
                      saving
                    }

                    className="bg-ratecard-blue text-white px-5 py-2 rounded disabled:opacity-50"

                  >

                    {

                      saving

                        ? "Saving..."

                        : "Save"

                    }

                  </button>

                </div>

              </>

            )

          }

        </div>

      )}

    </div>

  );

}
