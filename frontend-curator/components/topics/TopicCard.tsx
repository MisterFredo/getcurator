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

  label: string;

  universe?: string;

  isLoading?: boolean;
  contentCount?: number;

  onClick?: () => void;

  isFavorite?: boolean;

  onToggleFavorite?: (
    id: string,
    isFavorite: boolean,
  ) => void;

};

/* =========================================================
   COMPONENT
========================================================= */

export default function TopicCard({

  id,

  label,

  universe,
  contentCount,

  isLoading,

  onClick,

  isFavorite = false,

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
      "topic",
      id,
    );

    const params =
      new URLSearchParams(
        searchParams.toString(),
      );

    params.set(
      "topic_id",
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

        await api.post(
          "/user/preferences/remove",
          {
            type: "TOPIC",
            value_id: id,
          },
        );

      } else {

        await api.post(
          "/user/preferences/add",
          {
            type: "TOPIC",
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

      {/* UNIVERSE */}

      <div className="
        relative
        h-24
        w-full
        bg-ratecard-light
        flex
        items-center
        justify-center
        px-4
      ">

        <div className="
          text-xs
          font-semibold
          uppercase
          tracking-wide
          text-gray-500
          text-center
          line-clamp-2
        ">

          {universe || "Topic"}

        </div>

      </div>

      {/* =====================================================
          TOPIC
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
