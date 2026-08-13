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

const GCS_BASE_URL =
  process.env.NEXT_PUBLIC_GCS_BASE_URL!;

/* =========================================================
   TYPES
========================================================= */

type Props = {

  id: string;

  name: string;

  visualRectId?: string | null;
  contentCount?: number;

  isLoading?: boolean;

  isFavorite?: boolean;

  maxFavoritesReached?: boolean;

  onClick?: () => void;

  onToggleFavorite?: (
    id: string,
    isFavorite: boolean,
  ) => void;

};


/* =========================================================
   COMPONENT
========================================================= */

export default function CompanyCard({

  id,

  name,

  visualRectId,
  contentCount,
  isLoading,

  isFavorite = false,

  maxFavoritesReached = false,

  onClick,

  onToggleFavorite,

}: Props) {

  const router =
    useRouter();

  const pathname =
    usePathname();

  const {
    openLeftDrawer,
  } = useDrawer();


  /* =========================================================
     VISUAL
  ========================================================= */

  const visualUrl =

    visualRectId

      ? `${GCS_BASE_URL}/companies/${visualRectId}`

      : null;


  /* =========================================================
     OPEN
  ========================================================= */

  function handleClick() {

    if (isLoading) {

      return;

    }

    onClick?.();

    openLeftDrawer(
      "company",
      id,
    );

    router.replace(
      `${pathname}?company_id=${id}`,
      {
        scroll: false,
      },
    );

  }


  /* =========================================================
     FAVORITE
  ========================================================= */

  async function handleFavoriteClick(
    e: React.MouseEvent,
  ) {

    e.stopPropagation();

    /* =====================================================
       LIMIT
    ===================================================== */

    if (
      !isFavorite &&
      maxFavoritesReached
    ) {

      return;

    }

    try {

      if (isFavorite) {

        await api.post(
          "/user/preferences/remove",
          {
            type: "COMPANY",
            value_id: id,
          },
        );

      } else {

        await api.post(
          "/user/preferences/add",
          {
            type: "COMPANY",
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


  /* =========================================================
     RENDER
  ========================================================= */

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

      {/* =====================================================
          FAVORITE
      ===================================================== */}

      <button

        type="button"

        onClick={
          handleFavoriteClick
        }

        disabled={
          !isFavorite &&
          maxFavoritesReached
        }

        className={`
          absolute
          top-2
          left-2
          z-20
          leading-none
          transition
          text-[20px]

          ${
            !isFavorite &&
            maxFavoritesReached
              ? "cursor-not-allowed opacity-30"
              : "cursor-pointer"
          }

          ${
            isFavorite
              ? ""
              : "text-gray-700 hover:text-black"
          }
        `}

        aria-label={
          isFavorite
            ? "Retirer des favoris"
            : maxFavoritesReached
              ? "Maximum de 10 favoris atteint"
              : "Ajouter aux favoris"
        }

        title={
          !isFavorite &&
          maxFavoritesReached
            ? "Maximum de 10 favoris atteint"
            : undefined
        }

      >

        {
          isFavorite
            ? "⭐"
            : "☆"
        }

      </button>


      {/* =====================================================
          LOADING
      ===================================================== */}

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


      {/* =====================================================
          VISUAL
      ===================================================== */}

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
