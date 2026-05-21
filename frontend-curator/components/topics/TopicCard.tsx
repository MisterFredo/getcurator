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

  // 🔥 NEW
  isFavorite?: boolean;
  onToggleFavorite?: () => void;
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

  // 🔥 NEW
  isFavorite = false,
  onToggleFavorite,

}: Props) {

  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { openLeftDrawer } = useDrawer();

  /* =========================================================
     CLICK SAFE
  ========================================================= */

  function handleClick() {
    if (isLoading) return;

    onClick?.();

    openLeftDrawer("topic", id);

    const params = new URLSearchParams(searchParams.toString());
    params.set("topic_id", id);

    router.replace(`${pathname}?${params.toString()}`, {
      scroll: false,
    });
  }

  // 🔥 FAVORITE CLICK
  function handleFavoriteClick(e: React.MouseEvent) {
    e.stopPropagation();

    if (onToggleFavorite) {
      onToggleFavorite();
    }
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

      {/* 🔥 FAVORITE */}
      <div
        onClick={handleFavoriteClick}
        className="
          absolute top-2 left-2 z-20
          cursor-pointer text-[12px]
        "
      >
        {isFavorite ? "⭐" : "☆"}
      </div>

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
        <div className="absolute top-2 left-7 text-[9px] px-2 py-0.5 rounded bg-blue-50 text-blue-600 z-10">
          #
        </div>
      )}

      {/* =====================================================
          VISUAL DATA BLOCK
      ===================================================== */}
      <div className="
        h-20 w-full
        bg-gradient-to-br from-gray-50 to-gray-100
        flex flex-col items-center justify-center
      ">
        <div className="text-lg font-semibold text-gray-800">
          {nbAnalyses ?? 0}
        </div>
        <div className="text-[10px] text-gray-400">
          analyses
        </div>
      </div>

      {/* =====================================================
          CONTENT
      ===================================================== */}
      <div className="p-3 text-center space-y-1">

        <h3 className="
          text-xs font-semibold text-gray-900
          line-clamp-2
          group-hover:underline
        ">
          {label}
        </h3>

        {isTrending && (
          <div className="text-[11px] text-orange-600 font-medium">
            +{delta30d} (30j)
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
