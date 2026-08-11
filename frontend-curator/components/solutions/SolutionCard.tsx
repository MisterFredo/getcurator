"use client";

import {
  usePathname,
  useRouter,
} from "next/navigation";

import {
  useDrawer,
} from "@/contexts/DrawerContext";

import {
  api,
} from "@/lib/api";

/* ========================================================= */

type Props = {

  id: string;

  name: string;

  visualRectId?: string | null;

  visualType?: "solution" | "company";
  contentCount?: number;

  isPartner?: boolean;

  isLoading?: boolean;

  onClick?: () => void;

  isFavorite?: boolean;

  onToggleFavorite?: (
    id: string,
    isFavorite: boolean,
  ) => void;

};

/* ========================================================= */

const GCS_BASE_URL =
  process.env.NEXT_PUBLIC_GCS_BASE_URL!;

/* ========================================================= */

export default function SolutionCard({

  id,

  name,
  contentCount,

  visualRectId,

  visualType,

  isPartner,

  isLoading,

  onClick,

  isFavorite = false,

  onToggleFavorite,

}: Props) {

  const router =
    useRouter();

  const pathname =
    usePathname();

  const {
    openLeftDrawer,
  } = useDrawer();

  /* =====================================================
     VISUAL URL
  ===================================================== */

  let visualUrl:
    string | null = null;

  if (visualRectId) {

    const folder =
      visualType === "solution"
        ? "solutions"
        : "companies";

    visualUrl =
      `${GCS_BASE_URL}/${folder}/${visualRectId}`;

  }

  /* =====================================================
     CLICK
  ===================================================== */

  function handleClick() {

    if (isLoading) {

      return;

    }

    onClick?.();

    openLeftDrawer(
      "solution",
      id,
    );

    router.replace(
      `${pathname}?solution_id=${id}`,
      {
        scroll: false,
      },
    );

  }

  /* =====================================================
     FAVORITE
  ===================================================== */

  async function handleFavoriteClick(
    e: React.MouseEvent,
  ) {

    e.stopPropagation();

    try {

      if (isFavorite) {

        await api.post(
          "/user/preferences/remove",
          {
            type: "SOLUTION",
            value_id: id,
          },
        );

      } else {

        await api.post(
          "/user/preferences/add",
          {
            type: "SOLUTION",
            value_id: id,
          },
        );

      }

      onToggleFavorite?.(
        id,
        isFavorite,
      );

    } catch (e) {

      console.error(
        "❌ favorite error",
        e,
      );

    }

  }

  /* =====================================================
     RENDER
  ===================================================== */

  return (

    <div

      onClick={
        handleClick
      }

      className="
        group
        cursor-pointer
        rounded-xl
        border
        border-ratecard-border
        bg-white
        shadow-card
        transition
        hover:shadow-cardHover
        overflow-hidden
        relative
      "

    >

      {/* FAVORITE */}

      <button

        type="button"

        onClick={
          handleFavoriteClick
        }

        className={`
          absolute
          top-2
          left-2
          z-20
          cursor-pointer
          leading-none
          transition
          text-[20px]

          ${
            isFavorite
              ? ""
              : "text-gray-700 hover:text-black"
          }
        `}

        aria-label={
          isFavorite
            ? "Retirer des favoris"
            : "Ajouter aux favoris"
        }

      >

        {
          isFavorite
            ? "⭐"
            : "☆"
        }

      </button>

      {/* LOADING */}

      {isLoading && (

        <div className="
          absolute
          inset-0
          z-30
          bg-white/70
          backdrop-blur-sm
          flex
          items-center
          justify-center
        ">

          <div className="
            text-xs
            text-gray-500
            animate-pulse
          ">
            Chargement...
          </div>

        </div>

      )}

      {/* PARTNER */}

      {isPartner && (

        <div className="
          absolute
          top-2
          right-2
          z-10
        ">

          <span className="
            text-[9px]
            px-2
            py-0.5
            rounded
            bg-teal-600
            text-white
          ">
            Partner
          </span>

        </div>

      )}

      {/* VISUAL */}

      <div className="
        relative
        h-24
        w-full
        bg-ratecard-light
        overflow-hidden
      ">

        {visualUrl ? (

          <img

            src={
              visualUrl
            }

            alt={
              name
            }

            className="
              h-full
              w-full
              object-contain
              p-4
              transition-transform
              duration-300
              group-hover:scale-[1.02]
            "

          />

        ) : (

          <div className="
            h-full
            w-full
            flex
            items-center
            justify-center
            text-[10px]
            text-gray-400
            px-2
            text-center
          ">

            {name}

          </div>

        )}

      </div>

      {/* =====================================================
          NAME
      ===================================================== */}
      
      <div className="
        p-3
        text-center
      ">
      
        <h3 className="
          text-xs
          font-semibold
          text-gray-900
          leading-snug
          line-clamp-2
          group-hover:underline
        ">
      
          {name}
      
        </h3>
      
        {typeof contentCount === "number" && (
      
          <p className="
            mt-1
            text-[10px]
            text-gray-400
          ">
      
            {contentCount} contents
      
          </p>
      
        )}
      
      </div>

    </div>

  );

}
