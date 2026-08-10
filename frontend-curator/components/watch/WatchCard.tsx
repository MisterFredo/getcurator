"use client";

import ContentBadges from "@/components/content/ContentBadges";

import type {
  WatchItem,
} from "@/types/watch";

/* ========================================================= */

const GCS_BASE_URL =
  process.env.NEXT_PUBLIC_GCS_BASE_URL || "";

/* ========================================================= */

type Props = {

  item: WatchItem;

  onClick: () => void;

  selected?: boolean;

  onToggleSelect?: (
    item: WatchItem,
  ) => void;

};

/* ========================================================= */

export default function WatchCard({

  item,

  onClick,

  selected = false,

  onToggleSelect,

}: Props) {

  const formattedDate =

    item.published_at

      ? new Date(
          item.published_at,
        ).toLocaleDateString(
          "fr-FR",
        )

      : null;

  const logoUrl =

    item.primary_company_logo

      ? `${GCS_BASE_URL}/companies/${item.primary_company_logo}`

      : null;

  function handleToggleSelect(
    e: React.MouseEvent,
  ) {
  
    e.stopPropagation();
  
    onToggleSelect?.(
      item,
    );
  
  }

  return (

    <div
      onClick={onClick}
      className="
        cursor-pointer
        py-4
        transition
        hover:bg-gray-50
      "
    >

      <div className="
        flex
        items-start
        gap-5
      ">

        {/* ===================================================
            SELECT
        =================================================== */}
        
        <div
          className="
            w-8
            flex
            justify-center
            pt-1
          "
        >
        
          <input
        
            type="checkbox"
        
            checked={selected}
        
            onClick={(e) =>
              e.stopPropagation()
            }
        
            onChange={
              handleToggleSelect
            }
        
            className="
              h-4
              w-4
              cursor-pointer
            "
        
          />
        
        </div>

        {/* ===================================================
            LEFT
        =================================================== */}

        <div className="
          w-[72px]
          shrink-0
          flex
          flex-col
          items-center
          gap-2
          pt-0.5
        ">

          {formattedDate && (

            <div className="
              text-[11px]
              text-gray-400
              text-center
              leading-none
            ">

              {formattedDate}

            </div>

          )}

          {logoUrl && (

            <div className="
              w-12
              h-12
              rounded-xl
              border
              border-gray-200
              bg-white
              overflow-hidden
              flex
              items-center
              justify-center
            ">

              <img
                src={logoUrl}
                alt={item.title}
                className="
                  w-full
                  h-full
                  object-contain
                "
              />

            </div>

          )}

        </div>

        {/* ===================================================
            CONTENT
        =================================================== */}

        <div className="
          flex-1
          min-w-0
        ">

          <h3
            className="
              text-[14px]
              font-medium
              text-gray-900
              leading-snug
            "
          >

            {item.title}

          </h3>

          {item.excerpt && (

            <p className="
              mt-2
              text-sm
              text-gray-600
              leading-relaxed
            ">

              {item.excerpt}

            </p>

          )}

          {item.badges.length > 0 && (

            <div className="mt-3">

              <ContentBadges
                badges={item.badges}
              />

            </div>

          )}

        </div>

      </div>

    </div>

  );

}
