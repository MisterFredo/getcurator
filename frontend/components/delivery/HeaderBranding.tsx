"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { HeaderConfig } from "@/types/newsletter";

type CompanyOption = {
  id_company: string;
  name: string;
  media_logo_rectangle_id?: string | null;
};

type Props = {
  headerConfig: HeaderConfig;
  setHeaderConfig: React.Dispatch<
    React.SetStateAction<HeaderConfig>
  >;
};

export default function HeaderBranding({
  headerConfig,
  setHeaderConfig,
}: Props) {
  const [companies, setCompanies] = useState<CompanyOption[]>([]);
  const [loading, setLoading] = useState(true);

  const variant = headerConfig.variant || "media";

  /* =========================================================
     LOAD COMPANIES
  ========================================================= */

  useEffect(() => {
    async function loadCompanies() {
      try {
        const res = await api.get("/company/list");

        const data = res.result || res;

        const raw = Array.isArray(data)
          ? data
          : data?.companies || [];

        const mapped: CompanyOption[] = raw.map((c: any) => ({
          id_company: c.id_company ?? c.ID_COMPANY,
          name: c.name ?? c.NAME,
          media_logo_rectangle_id:
            c.media_logo_rectangle_id ??
            c.MEDIA_LOGO_RECTANGLE_ID ??
            null,
        }));

        setCompanies(mapped);

        // auto select si vide
        if (!headerConfig.headerCompany && mapped.length > 0) {
          const ratecard =
            mapped.find((c) =>
              (c.name || "").toLowerCase().includes("ratecard")
            ) || mapped[0];

          setHeaderConfig((prev) => ({
            ...prev,
            headerCompany: ratecard,
          }));
        }
      } catch (e) {
        console.error("Erreur chargement sociétés header", e);
      } finally {
        setLoading(false);
      }
    }

    loadCompanies();
  }, [setHeaderConfig]);

  /* ========================================================= */

  function handleCompanyChange(id: string) {
    if (!id) {
      setHeaderConfig((prev) => ({
        ...prev,
        headerCompany: undefined,
      }));
      return;
    }

    const company = companies.find(
      (c) => c.id_company === id
    );

    if (!company) return;

    setHeaderConfig((prev) => ({
      ...prev,
      headerCompany: company,
    }));
  }

  /* ========================================================= */

  return (
    <div className="col-span-2 space-y-4">

      {/* =====================================================
         VARIANT SWITCH
      ===================================================== */}
      <div className="flex items-center gap-3 text-xs">

        <span className="text-gray-400">Style</span>

        <button
          onClick={() =>
            setHeaderConfig((prev) => ({
              ...prev,
              variant: "media",
            }))
          }
          className={`
            px-3 py-1 rounded border
            ${variant === "media"
              ? "bg-black text-white border-black"
              : "bg-white text-gray-600 border-gray-200"}
          `}
        >
          Média
        </button>

        <button
          onClick={() =>
            setHeaderConfig((prev) => ({
              ...prev,
              variant: "consulting",
            }))
          }
          className={`
            px-3 py-1 rounded border
            ${variant === "consulting"
              ? "bg-black text-white border-black"
              : "bg-white text-gray-600 border-gray-200"}
          `}
        >
          Consulting
        </button>

      </div>

      {/* =====================================================
         DISPLAY OPTIONS
      ===================================================== */}
      <div className="flex flex-wrap items-center gap-4 text-xs text-gray-600">

        {/* BAROMÈTRE */}
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={headerConfig.showTopicStats ?? false}
            onChange={(e) =>
              setHeaderConfig((prev) => ({
                ...prev,
                showTopicStats: e.target.checked,
              }))
            }
            className="h-3 w-3"
          />
          <span>Afficher baromètre</span>
        </label>

        {/* TOP BAR */}
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={headerConfig.topBarEnabled ?? true}
            onChange={(e) =>
              setHeaderConfig((prev) => ({
                ...prev,
                topBarEnabled: e.target.checked,
              }))
            }
            className="h-3 w-3"
          />
          <span>Barre haute</span>
        </label>

        {/* COLOR */}
        <div className="flex items-center gap-2">
          <span className="text-gray-400">Couleur</span>
          <input
            type="color"
            value={
              headerConfig.topBarColor ||
              (variant === "consulting"
                ? "#111827"
                : "#84CC16")
            }
            onChange={(e) =>
              setHeaderConfig((prev) => ({
                ...prev,
                topBarColor: e.target.value,
              }))
            }
            className="h-6 w-8 border rounded cursor-pointer"
          />
        </div>
      </div>

      {/* =====================================================
         COMPANY (LOGO)
      ===================================================== */}
      <div>
        <label className="text-xs text-gray-500 block mb-1">
          Logo header
        </label>

        <select
          value={headerConfig.headerCompany?.id_company ?? ""}
          onChange={(e) =>
            handleCompanyChange(e.target.value)
          }
          disabled={loading}
          className="
            border border-gray-200 rounded
            px-3 py-2 text-sm w-full
          "
        >
          <option value="">
            {loading
              ? "Chargement..."
              : "Aucun logo"}
          </option>

          {companies.map((company) => (
            <option
              key={company.id_company}
              value={company.id_company}
            >
              {company.name}
            </option>
          ))}
        </select>

        {/* PREVIEW */}
        {headerConfig.headerCompany?.media_logo_rectangle_id && (
          <div className="mt-3 flex items-center gap-3">

            <div className="
              border border-gray-200
              rounded
              px-3 py-2
              bg-white
            ">
              <img
                src={`https://storage.googleapis.com/ratecard-media/companies/${headerConfig.headerCompany.media_logo_rectangle_id}`}
                className="h-6 object-contain"
              />
            </div>

            <span className="text-xs text-gray-400">
              aperçu logo
            </span>

          </div>
        )}
      </div>

    </div>
  );
}
