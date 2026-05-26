"use client";

import { useRouter, usePathname } from "next/navigation";
import { useDrawer } from "@/contexts/DrawerContext";
import { api } from "@/lib/api";

const GCS_BASE_URL = process.env.NEXT_PUBLIC_GCS_BASE_URL!;

type Props = {
  id: string;
  name: string;

  visualRectId?: string | null;

  totalAnalyses?: number;
  totalNews?: number;

  delta30d?: number;

  universes?: string[];

  lastRadar?: {
    id_insight: string;
    key_points: string[];
  };

  isLoading?: boolean;
  isFavorite?: boolean;

  onClick?: () => void;

  onToggleFavorite?: (
    id: string,
    isFavorite: boolean
  ) => void;
};

export default function CompanyCard({
  id,
  name,
  visualRectId,
  totalAnalyses,
  totalNews,
  delta30d,
  universes,
  lastRadar,
  isLoading,
  isFavorite = false,
  onClick,
  onToggleFavorite,
}: Props) {

  const router = useRouter();

  const pathname =
    usePathname();

  const {
    openLeftDrawer,
    openRightDrawer,
  } = useDrawer();

  /* =====================================================
     VISUAL
  ===================================================== */

  const visualUrl =
    visualRectId
      ? `${GCS_BASE_URL}/companies/${visualRectId}`
      : null;

  const totalContent =
    (totalAnalyses ?? 0)
    + (totalNews ?? 0);

  const mainUniverse =
    universes?.[0];

  /* =====================================================
     HANDLERS
  ===================================================== */

  function handleClick() {

    if (isLoading) return;

    if (onClick) {
      onClick();
    }

    openLeftDrawer(
      "company",
      id
    );

    router.replace(
      `${pathname}?company_id=${id}`,
      { scroll: false }
    );
  }

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

  /* =====================================================
     FAVORITE
  ===================================================== */

  async function handleFavoriteClick(
    e: React.MouseEvent
  ) {

    e.stopPropagation();

    try {

      if (isFavorite) {

        await api.post(
          "/user/preferences/remove",
          {
            type: "COMPANY",
            value_id: id,
          }
        );

      } else {

        await api.post(
          "/user/preferences/add",
          {
            type: "COMPANY",
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

  /* =====================================================
     RENDER
  ===================================================== */

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

      {/* UNIVERSE */}

      {mainUniverse && (

        <div className="
          absolute top-2 left-7 z-10
          text-[9px]
          px-2 py-0.5 rounded
          bg-gray-900 text-white
        ">
          {mainUniverse}
        </div>

      )}

      {/* DELTA */}

      {typeof delta30d === "number"
        && delta30d > 0 && (

        <div className="
          absolute top-2 right-2 z-10
          text-[9px]
          px-2 py-0.5 rounded
          bg-green-100 text-green-600
        ">
          +{delta30d}
        </div>

      )}

      {/* VISUAL */}

      <div className="
        relative h-24 w-full
        bg-ratecard-light
        overflow-hidden
      ">

        {visualUrl ? (

          <img
            src={visualUrl}
            alt={name}
            className="
              h-full w-full object-contain
              p-4 transition-transform
              duration-300
              group-hover:scale-[1.02]
            "
          />

        ) : (

          <div className="
            h-full w-full
            flex items-center justify-center
            text-[10px]
            text-gray-400
            px-2 text-center
          ">
            {name}
          </div>

        )}

        {/* RADAR */}

        {lastRadar?.key_points?.[0] && (

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
              {lastRadar.key_points[0]}
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
          {name}
        </h3>

        {(typeof totalAnalyses === "number"
          || typeof totalNews === "number") && (

          <p className="
            text-[10px]
            text-gray-400
          ">
            {totalContent} contents
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
