"use client";

import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { useDrawer } from "@/contexts/DrawerContext";

type Props = {
  id: string;
  label: string;
  nbAnalyses?: number;
  delta30d?: number;
};

export default function TopicCard({
  id,
  label,
  nbAnalyses,
  delta30d,
}: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { openLeftDrawer } = useDrawer();

  function handleClick() {
    openLeftDrawer("topic", id);

    const params = new URLSearchParams(searchParams.toString());
    params.set("topic_id", id);

    router.replace(`${pathname}?${params.toString()}`, {
      scroll: false,
    });
  }

  const isTrending =
    typeof delta30d === "number" && delta30d > 0;

  return (
    <div
      onClick={handleClick}
      className="
        group cursor-pointer
        rounded-xl border border-gray-200
        bg-white p-4
        transition
        hover:border-gray-300 hover:shadow-sm
      "
    >
      {/* HEADER */}
      <div className="flex items-start justify-between gap-2">
        <h3 className="
          text-sm font-semibold text-gray-900
          leading-snug line-clamp-2
        ">
          {label}
        </h3>

        {isTrending && (
          <span className="
            text-[11px] px-2 py-0.5 rounded
            bg-orange-100 text-orange-600
            whitespace-nowrap
          ">
            +{delta30d}
          </span>
        )}
      </div>

      {/* KPI */}
      {typeof nbAnalyses === "number" && (
        <div className="mt-2 text-xs text-gray-500">
          {nbAnalyses} analyses
        </div>
      )}

      {/* CTA */}
      <div className="
        mt-3 text-[11px] text-gray-400
        opacity-0 group-hover:opacity-100
        transition
      ">
        Voir →
      </div>
    </div>
  );
}
