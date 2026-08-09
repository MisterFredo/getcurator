"use client";

import type {
  WatchBadge,
} from "@/types/watch";

/* ========================================================= */

type Props = {

  badges?: WatchBadge[];

  className?: string;

};

/* ========================================================= */

function getBadgeClass(
  type?: string,
) {

  switch (type) {

    case "company":

      return `
        bg-blue-50
        text-blue-600
        border
        border-blue-100
      `;

    case "solution":

      return `
        bg-purple-50
        text-purple-600
        border
        border-purple-100
      `;

    case "universe":

      return `
        bg-emerald-50
        text-emerald-600
        border
        border-emerald-100
      `;

    case "concept":

      return `
        bg-orange-50
        text-orange-600
        border
        border-orange-100
      `;

    case "topic":

    default:

      return `
        bg-gray-100
        text-gray-600
      `;

  }

}

/* ========================================================= */

export default function ContentBadges({

  badges = [],

  className = "",

}: Props) {

  if (badges.length === 0) {

    return null;

  }

  return (

    <div
      className={`
        flex
        flex-wrap
        gap-2
        ${className}
      `}
    >

      {badges.map(

        (badge, index) => (

          <span

            key={`${badge.type}-${badge.id ?? badge.label}-${index}`}

            className={`
              px-2
              py-0.5
              text-[10px]
              rounded-full
              uppercase
              tracking-wide
              ${getBadgeClass(badge.type)}
            `}

          >

            {badge.label}

          </span>

        )

      )}

    </div>

  );

}
