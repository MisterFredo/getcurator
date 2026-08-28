"use client";

import {
  usePathname,
  useRouter,
  useSearchParams,
} from "next/navigation";

import {
  useDrawer,
} from "@/contexts/DrawerContext";

import {
  api,
} from "@/lib/api";

/* =========================================================
   TYPES
========================================================= */

type Props = {

  id: string;

  displayName: string;

  company?: string | null;

  description?: string | null;

  isFavorite?: boolean;

  isLoading?: boolean;

  onClick?: () => void;

  onToggleFavorite?: (
    id: string,
    isFavorite: boolean,
  ) => void;

};

/* =========================================================
   COMPONENT
========================================================= */

export default function ExpertCard({

  id,

  displayName,

  company,

  description,

  isFavorite = false,

  isLoading = false,

  onClick,

  onToggleFavorite,

}: Props) {

  const router =
    useRouter();

  const pathname =
    usePathname();

  const searchParams =
    useSearchParams();

  const {
    openLeftDrawer,
  } = useDrawer();

  /* =========================================================
     CLICK
  ========================================================= */

  function handleClick() {

    if (isLoading) {

      return;

    }

    onClick?.();

    openLeftDrawer(
      "expert",
      id,
    );

    const params =
      new URLSearchParams(
        searchParams.toString(),
      );

    params.set(
      "expert_id",
      id,
    );

    router.replace(
      `${pathname}?${params.toString()}`,
      {
        scroll: false,
      },
    );

  }

  /* =========================================================
     FAVORITE
  ========================================================= */

  async function handleFavoriteClick(
    event: React.MouseEvent,
  ) {

    event.stopPropagation();

    try {

      if (isFavorite) {

        await api.delete(
          `/user/experts/${id}`,
        );

      } else {

        await api.post(
          `/user/experts/${id}`,
          {},
        );

      }

      onToggleFavorite?.(
        id,
        isFavorite,
      );

    } catch (error) {

      console.error(
        "❌ expert favorite error",
        error,
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
        relative
        h-full
        cursor-pointer
        overflow-hidden
        rounded-xl
        border
        border-ratecard-border
        bg-white
        shadow-card
        transition
        hover:shadow-cardHover
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

        className={`
          absolute
          left-2
          top-2
          z-20
          cursor-pointer
          text-[18px]
          leading-none
          transition

          ${

            isFavorite

              ? ""

              : `
                text-gray-700
                hover:text-black
              `

          }
        `}

      >

        {isFavorite
          ? "⭐"
          : "☆"}

      </button>

      {/* =====================================================
          LOADING
      ===================================================== */}

      {isLoading && (

        <div
          className="
            absolute
            inset-0
            z-30
            flex
            items-center
            justify-center
            bg-white/70
            backdrop-blur-sm
          "
        >

          <div
            className="
              animate-pulse
              text-xs
              text-gray-500
            "
          >
            Loading...
          </div>

        </div>

      )}

      {/* =====================================================
          IDENTITY
      ===================================================== */}

      <div
        className="
          flex
          h-16
          w-full
          items-center
          justify-center
          bg-ratecard-light
          px-8
          text-center
        "
      >

        <div
          className="
            min-w-0
          "
        >

          <div
            className="
              min-h-10
              line-clamp-2
              break-words
              text-sm
              font-semibold
              leading-5
              text-gray-900
            "
          >
            {displayName}
          </div>

          {company && (

            <div
              className="
                mt-0.5
                line-clamp-1
                text-[11px]
                text-gray-500
              "
            >
              {company}
            </div>

          )}

        </div>

      </div>

      {/* =====================================================
          DESCRIPTION
      ===================================================== */}

      <div
        className="
          flex
          min-h-[72px]
          items-start
          p-4
        "
      >

        {description ? (

          <p
            className="
              line-clamp-3
              text-xs
              leading-5
              text-gray-600
            "
          >
            {description}
          </p>

        ) : (

          <p
            className="
              text-xs
              text-gray-400
            "
          >
            Expert profile
          </p>

        )}

      </div>

    </div>

  );

}
