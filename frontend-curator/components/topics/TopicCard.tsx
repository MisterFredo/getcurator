"use client";

import {
  useRouter,
  usePathname,
  useSearchParams,
} from "next/navigation";

import { useDrawer } from "@/contexts/DrawerContext";
import { api } from "@/lib/api";

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

  isFavorite?: boolean;

  onToggleFavorite?: (
    id: string,
    isFavorite: boolean
  ) => void;
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

  isFavorite = false,
  onToggleFavorite,

}: Props) {

  const router = useRouter();

  const pathname =
    usePathname();

  const searchParams =
    useSearchParams();

  const {
    openLeftDrawer,
    openRightDrawer,
  } = useDrawer();

  /* =========================================================
     SAFE DATA
  ========================================================= */

  const isTrending =
    typeof delta30d === "number"
    && delta30d > 0;

  const radarText =
    lastRadar?.key_points?.[0];

  /* =========================================================
     CLICK
  ========================================================= */

  function handleClick() {

    if (isLoading) return;

    if (onClick) {
      onClick();
    }

    openLeftDrawer(
      "topic",
      id
    );

    const params =
      new URLSearchParams(
        searchParams.toString()
      );

    params.set(
      "topic_id",
      id
    );

    router.replace(
      `${pathname}?${params.toString()}`,
      {
        scroll: false,
      }
    );
  }

  /* =========================================================
     RADAR
  ========================================================= */

  function handleRadarClick(
    e: React.MouseEvent
  ) {

    e.stopPropagation();

    if (
      lastRadar?.id_insight
    ) {

      openRightDrawer(
        "radar",
        lastRadar.id_insight
      );
    }
  }

  /* =========================================================
     FAVORITE
  ========================================================= */

  async function handleFavoriteClick(
    e: React.MouseEvent
  ) {

    e.stopPropagation();

    try {

      if (isFavorite) {

        await api.post(
          "/user/preferences/remove",
          {
            type: "TOPIC",
            value_id: id,
          }
        );

      } else {

        await api.post(
          "/user/preferences/add",
          {
            type: "TOPIC",
            value_id: id,
          }
        );
      }

      if (onToggleFavorite) {

        onToggleFavorite(
          id,
          isFavorite
        );
      }

    } catch (e) {

      console.error(
        "❌ favorite error",
        e
      );
    }
  }

  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <div
      onClick={handleClick}
      className="
        group cursor-pointer rounded-xl
        border border-ratecard-border
        bg-white shadow-card transition
        hover:shadow-cardHover overflow-hidden
        relative
      "
    >

      {/* FAVORITE */}

      <div
        onClick={handleFavoriteClick}
        className={`
          absolute top-2 left-2 z-20
          cursor-pointer
          leading-none
          transition
          ${
            isFavorite
              ? "text-[20px]"
              : "text-[20px] text-gray-700 hover:text-black"
          }
        `}
      >
        {isFavorite ? "⭐" : "☆"}
      </div>

      {/* LOADING */}

      {isLoading && (

        <div className="
          absolute inset-0 z-20
          bg-white/70 backdrop-blur-sm
          flex items-center justify-center
        ">

          <div className="
            text-xs text-gray-500
            animate-pulse
          ">
            Chargement...
          </div>

        </div>

      )}

      {/* NUMBERS */}

      {hasNumbers && (

        <div className="
          absolute top-2 left-7 z-10
          text-[10px]
          px-2 py-0.5 rounded
          bg-blue-50 text-blue-600
          border border-blue-100
        ">
          #
        </div>

      )}

      {/* DELTA */}

      {isTrending && (

        <div className="
          absolute top-2 right-2 z-10
          text-[9px]
          px-2 py-0.5 rounded
          bg-orange-100 text-orange-600
        ">
          +{delta30d}
        </div>

      )}

      {/* VISUAL */}

      <div className="
        relative h-24 w-full
        bg-ratecard-light
        overflow-hidden
        flex flex-col
        items-center justify-center
      ">

        <div className="
          text-2xl font-semibold
          text-gray-800
        ">
          {nbAnalyses ?? 0}
        </div>

        <div className="
          text-[10px]
          text-gray-400
        ">
          analyses
        </div>

        {/* RADAR OVERLAY */}

        {radarText && (

          <div
            onClick={handleRadarClick}
            className="
              absolute inset-0
              bg-black/0
              group-hover:bg-black/60
              transition duration-200
              flex items-end p-3
              opacity-0
              group-hover:opacity-100
            "
          >

            <p className="
              text-[11px]
              text-white
              leading-snug
              line-clamp-3
            ">
              {radarText}
            </p>

          </div>

        )}

      </div>

      {/* CONTENT */}

      <div className="
        p-3 space-y-1
        text-center
      ">

        <h3 className="
          text-xs font-semibold
          text-gray-900
          leading-snug
          line-clamp-2
          group-hover:underline
        ">
          {label}
        </h3>

        {typeof nbAnalyses === "number" && (

          <p className="
            text-[10px]
            text-gray-400
          ">
            {nbAnalyses} analyses
          </p>

        )}

        {lastRadar && (

          <div
            onClick={handleRadarClick}
            className="
              text-[10px]
              text-gray-400
              opacity-0
              group-hover:opacity-100
              transition
            "
          >
            Voir la veille →
          </div>

        )}

      </div>

    </div>

  );
}
