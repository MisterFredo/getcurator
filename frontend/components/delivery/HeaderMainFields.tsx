"use client";

import type { HeaderConfig } from "@/types/newsletter";

type Props = {
  headerConfig: HeaderConfig;
  setHeaderConfig: React.Dispatch<
    React.SetStateAction<HeaderConfig>
  >;
};

export default function HeaderMainFields({
  headerConfig,
  setHeaderConfig,
}: Props) {
  const variant = headerConfig.variant || "media";

  return (
    <div className="col-span-2 space-y-4">

      {/* =====================================================
         VARIANT SWITCH (🔥 CORE UX)
      ===================================================== */}
      <div className="flex items-center justify-between">
        <label className="text-xs font-medium text-gray-500">
          Type de header
        </label>

        <div className="flex border rounded overflow-hidden text-xs">
          <button
            onClick={() =>
              setHeaderConfig((prev) => ({
                ...prev,
                variant: "media",
              }))
            }
            className={`px-3 py-1.5 ${
              variant === "media"
                ? "bg-black text-white"
                : "bg-white text-gray-600"
            }`}
          >
            Media
          </button>

          <button
            onClick={() =>
              setHeaderConfig((prev) => ({
                ...prev,
                variant: "consulting",
              }))
            }
            className={`px-3 py-1.5 border-l ${
              variant === "consulting"
                ? "bg-black text-white"
                : "bg-white text-gray-600"
            }`}
          >
            Consulting
          </button>
        </div>
      </div>

      {/* =====================================================
         TITLE
      ===================================================== */}
      <div>
        <label className="text-xs text-gray-500 block mb-1">
          Titre principal
        </label>

        <input
          type="text"
          placeholder={
            variant === "consulting"
              ? "Ex: Les tendances du retail media en 2026"
              : "Newsletter Ratecard"
          }
          value={headerConfig.title}
          onChange={(e) =>
            setHeaderConfig((prev) => ({
              ...prev,
              title: e.target.value,
            }))
          }
          className="
            border border-gray-200 rounded
            px-3 py-2 text-sm w-full
          "
        />
      </div>

      {/* =====================================================
         SUBTITLE (CONTEXT)
      ===================================================== */}
      <div>
        <label className="text-xs text-gray-500 block mb-1">
          Contexte / univers
        </label>

        <input
          type="text"
          placeholder={
            variant === "consulting"
              ? "Ex: Retail Media / IA / Amazon"
              : "Sous-titre (optionnel)"
          }
          value={headerConfig.subtitle ?? ""}
          onChange={(e) =>
            setHeaderConfig((prev) => ({
              ...prev,
              subtitle: e.target.value,
            }))
          }
          className="
            border border-gray-200 rounded
            px-3 py-2 text-sm w-full
          "
        />
      </div>

      {/* =====================================================
         PERIOD + COLOR
      ===================================================== */}
      <div>
        <label className="text-xs text-gray-500 block mb-1">
          Période / date
        </label>

        <div className="flex gap-2 items-center">
          <input
            type="text"
            placeholder={
              variant === "consulting"
                ? "Ex: Mars 2026"
                : "Ex: semaine du 27 mars"
            }
            value={headerConfig.period ?? ""}
            onChange={(e) =>
              setHeaderConfig((prev) => ({
                ...prev,
                period: e.target.value,
              }))
            }
            className="
              border border-gray-200 rounded
              px-3 py-2 text-sm flex-1
            "
          />

          <input
            type="color"
            value={headerConfig.periodColor || "#84CC16"}
            onChange={(e) =>
              setHeaderConfig((prev) => ({
                ...prev,
                periodColor: e.target.value,
              }))
            }
            className="h-9 w-10 border rounded"
            title="Couleur période"
          />
        </div>
      </div>

    </div>
  );
}
