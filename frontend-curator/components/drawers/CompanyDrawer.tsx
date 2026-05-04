"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { api } from "@/lib/api";

import EntityDrawer from "@/components/drawers/EntityDrawer";
import DrawerHeader from "@/components/drawers/DrawerHeader";
import FeedGroupedByMonth from "@/components/feed/FeedGroupedByMonth";

import NumbersBlock from "@/components/drawers/blocks/NumbersBlock";
import RadarBlock from "@/components/drawers/blocks/RadarBlock";

import { useDrawer } from "@/contexts/DrawerContext";

/* ========================================================= */

const GCS_BASE_URL = process.env.NEXT_PUBLIC_GCS_BASE_URL!;

/* ========================================================= */

type FeedItem = {
  id: string;
  type: "news" | "analysis";
  title: string;
};

type CompanyData = {
  id_company: string;
  name: string;
  description?: string | null;
  media_logo_rectangle_id?: string | null;

  nb_analyses?: number;
  delta_30d?: number;

  items?: FeedItem[];
};

/* ========================================================= */

export default function CompanyDrawer({ id, onClose }: any) {
  const router = useRouter();
  const pathname = usePathname();
  const { leftDrawer, openRightDrawer, closeLeftDrawer } = useDrawer();

  const [data, setData] = useState<CompanyData | null>(null);
  const [items, setItems] = useState<FeedItem[]>([]);
  const [numbers, setNumbers] = useState<any[]>([]);
  const [radar, setRadar] = useState<any>(null);

  function close() {
    onClose?.();
    closeLeftDrawer();

    if (
      leftDrawer.mode === "route" &&
      pathname.startsWith("/companies")
    ) {
      router.push("/companies", { scroll: false });
    }
  }

  /* =========================================================
     LOAD COMPANY
  ========================================================= */

  useEffect(() => {
    async function load() {
      try {
        const res = await api.get(`/company/${id}/view`);
        setData(res);
        setItems(res?.items ?? []);
      } catch (e) {
        console.error("❌ company load error", e);
      }
    }

    load();
  }, [id]);

  /* =========================================================
     LOAD RADAR
  ========================================================= */

  useEffect(() => {
    async function loadRadar() {
      try {
        const res = await api.get(
          `/radar/latest?entity_type=company&entity_id=${id}`
        );
        setRadar(res?.insight ?? null);
      } catch (e) {
        console.error("❌ radar load error", e);
      }
    }

    loadRadar();
  }, [id]);

  /* =========================================================
     LOAD NUMBERS (🔥 IMPORTANT)
  ========================================================= */

  useEffect(() => {
    async function loadNumbers() {
      try {
        const res = await api.get(
          `/numbers/entity?entity_type=company&entity_id=${id}&limit=4`
        );

        // 🔥 sécurisation → uniquement les numbers officiels
        const items = res?.items ?? [];

        setNumbers(Array.isArray(items) ? items : []);
      } catch (e) {
        console.error("❌ numbers load error", e);
        setNumbers([]);
      }
    }

    loadNumbers();
  }, [id]);

  /* ========================================================= */

  if (!data) return null;

  const logoUrl = data.media_logo_rectangle_id
    ? `${GCS_BASE_URL}/companies/${data.media_logo_rectangle_id}`
    : null;

  /* =========================================================
     RENDER
  ========================================================= */

  return (
    <EntityDrawer
      onClose={close}
      header={
        <DrawerHeader
          title={data.name}
          nbAnalyses={data.nb_analyses}
          delta30d={data.delta_30d}
          onClose={close}
        />
      }
    >
      {/* LOGO */}
      {logoUrl && (
        <div className="w-full border-b border-gray-200 flex justify-center py-4">
          <img
            src={logoUrl}
            alt={data.name}
            className="h-16 object-contain"
          />
        </div>
      )}

      {/* DESCRIPTION */}
      {data.description && (
        <div
          className="prose prose-sm max-w-none"
          dangerouslySetInnerHTML={{
            __html: data.description,
          }}
        />
      )}

      {/* 🔥 NUMBERS OFFICIELS */}
      <NumbersBlock
        numbers={numbers}
        entityId={id}
        entityType="company"
      />

      {/* RADAR */}
      <RadarBlock radar={radar} />

      {/* FEED */}
      <section className="space-y-4">
        <h2 className="text-xs font-semibold uppercase text-gray-400">
          Contenus liés
        </h2>

        <FeedGroupedByMonth
          items={items}
          onClickItem={(item) =>
            openRightDrawer(
              item.type === "news" ? "news" : "analysis",
              item.id,
              "silent"
            )
          }
        />
      </section>
    </EntityDrawer>
  );
}
