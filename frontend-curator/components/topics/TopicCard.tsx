"use client";

import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { useDrawer } from "@/contexts/DrawerContext";

type Props = {
  id: string;
  label: string;

  nbAnalyses?: number;
  delta30d?: number;

  hasNumbers?: boolean;

  lastRadar?: {
    id_insight: string;
    key_points?: string[];
  };

  isLoading?: boolean;
  onClick?: () => void;
};

export default function TopicCard({
  id,
  label,
  nbAnalyses,
  delta30d,
  hasNumbers,
  lastRadar,
  isLoading,
  onClick,
}: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { openLeftDrawer } = useDrawer();

  /* =========================================================
     CLICK SAFE
  ========================================================= */

  function handleClick() {
    if (isLoading) return; // 🔥 bloque double click

    onClick?.();

    openLeftDrawer("topic", id);

    const params = new URLSearchParams(searchParams.toString());
    params.set("topic_id", id);

    router.replace(`${pathname}?${params.toString()}`, {
      scroll: false,
    });
  }

  /* ========================================================= */

  const isTrending =
    typeof delta30d === "number" && delta30d > 0;

  const radarText = lastRadar?.key_points?.[0];

  /* ========================================================= */

  return (
    <div
      onClick={handleClick}
      className="
        group cursor-pointer rounded-xl
        border border-gray-200
        bg-white shadow-sm transition
        hover:shadow-md hover:border-gray-300
        overflow-hidden relative
      "
    >
      {/* =====================================================
          LOADING
      ===================================================== */}
      {isLoading && (
        <div className="
          absolute inset-0 z-20
          bg-white/70 backdrop-blur-sm
          flex items-center justify-center
        ">
          <div className="text-xs text-gray-500 animate-pulse">
            Chargement…
          </div>
        </div>
      )}

      {/* =====================================================
          BADGES
      ===================================================== */}
      {isTrending && (
        <div className="absolute top-2 right-2 text-[9px] px-2 py-0.5 rounded bg-orange-100 text-orange-600 z-10">
          +{delta30d}
        </div>
      )}

      {hasNumbers && (
        <div className="absolute top-2 left-2 text-[9px] px-2 py-0.5 rounded bg-blue-50 text-blue-600 z-10">
          #
        </div>
      )}

      {/* =====================================================
          VISUAL
      ===================================================== */}
      <div className="
        h-20 w-full
        bg-gray-50 flex items-center justify-center
        text-[11px] text-gray-500
        px-2 text-center
      ">
        {label}
      </div>

      {/* =====================================================
          CONTENT
      ===================================================== */}
      <div className="p-3 text-center space-y-1">

        <h3 className="text-xs font-semibold text-gray-900 line-clamp-2">
          {label}
        </h3>

        {typeof nbAnalyses === "number" && (
          <div className="text-[10px] text-gray-500">
            {nbAnalyses}
            {isTrending && (
              <span className="ml-1 text-orange-600">
                +{delta30d}
              </span>
            )}
          </div>
        )}

      </div>

      {/* =====================================================
          RADAR OVERLAY
      ===================================================== */}
      {radarText && (
        <div className="
          absolute inset-0
          bg-black/0 group-hover:bg-black/40
          transition
          flex items-end p-3
          opacity-0 group-hover:opacity-100
        ">
          <p className="text-[11px] text-white line-clamp-3">
            {radarText}
          </p>
        </div>
      )}
    </div>
  );
}
