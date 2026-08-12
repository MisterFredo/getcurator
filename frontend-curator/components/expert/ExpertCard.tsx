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
    e: React.MouseEvent,
  ) {

    e.stopPropagation();

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

    } catch (e) {

      console.error(
        "❌ expert favorite error",
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
      >
        {
          isFavorite
            ? "⭐"
            : "☆"
        }
      </button>

      {/* LOADING */}

      {isLoading && (

        <div
          className="
            absolute
            inset-0
            z-30
            bg-white/70
            backdrop-blur-sm
            flex
            items-center
            justify-center
          "
        >
          <div
            className="
              text-xs
              text-gray-500
              animate-pulse
            "
          >
            Loading...
          </div>
        </div>

      )}

      {/* IDENTITY */}

      <div
        className="
          h-24
          w-full
          bg-ratecard-light
          flex
          items-center
          justify-center
          px-6
          text-center
        "
      >

        <div>

          <div
            className="
              text-sm
              font-semibold
              text-gray-900
              line-clamp-2
            "
          >
            {displayName}
          </div>

          {company && (

            <div
              className="
                mt-1
                text-xs
                text-gray-500
                line-clamp-1
              "
            >
              {company}
            </div>

          )}

        </div>

      </div>

      {/* DESCRIPTION */}

      <div
        className="
          p-4
        "
      >

        {description ? (

          <p
            className="
              text-xs
              leading-5
              text-gray-600
              line-clamp-4
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
