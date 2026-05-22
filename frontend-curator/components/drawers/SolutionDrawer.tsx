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

type FeedItem = {
  id: string;
  type: "news" | "analysis";
  title: string;
};

type NumberCategory = any;
type Radar = any;

type SolutionData = {
  id_solution: string;
  name: string;

  company_name?: string;

  // 🔥 logo + type
  media_logo_rectangle_id?: string | null;
  logo_type?: "solution" | "company";

  nb_analyses?: number;
  delta_30d?: number;

  items?: FeedItem[];
};

/* ========================================================= */

export default function SolutionDrawer({ id, onClose }: any) {

  const router = useRouter();
  const pathname = usePathname();
  const { leftDrawer, openRightDrawer, closeLeftDrawer } = useDrawer();

  const [data, setData] = useState<SolutionData | null>(null);
  const [items, setItems] = useState<FeedItem[]>([]);
  const [numbers, setNumbers] = useState<NumberCategory[]>([]);
  const [radar, setRadar] = useState<Radar | null>(null);
  const [userLang, setUserLang] = useState("fr");

  function close() {
    onClose?.();
    closeLeftDrawer();

    if (
      leftDrawer.mode === "route" &&
      pathname.startsWith("/solutions")
    ) {
      router.push("/solutions", { scroll: false });
    }
  }

  /* LOAD DATA */
  useEffect(() => {
    async function load() {
      const res = await api.get(`/solution/${id}/view`);
      setData(res);
      setItems(res.items ?? []);
    }

    load();
  }, [id]);

  /* LOAD RADAR */
  useEffect(() => {
    async function loadRadar() {
      const res = await api.get(
        `/radar/latest?entity_type=solution&entity_id=${id}`
      );
      setRadar(res?.insight ?? null);
    }

    loadRadar();
  }, [id]);

  /* LOAD NUMBERS */
  useEffect(() => {
    async function loadNumbers() {
      const res = await api.get(
        `/numbers/entity?entity_type=solution&entity_id=${id}&limit=4`
      );
      setNumbers(res.items ?? []);
    }

    loadNumbers();
  }, [id]);

  useEffect(() => {

    async function loadUserLang() {

      try {

        const res = await api.get(
          "/user/preferences"
        );

        const lang =
          res?.user?.lang
          || "fr";

        setUserLang(lang);

      } catch {

        setUserLang("fr");

      }
    }

    loadUserLang();

  }, []);

  if (!data) return null;

  return (
    <EntityDrawer
      onClose={close}
      header={
        <DrawerHeader
          title={data.name}
          subtitle={data.company_name}

          // 🔥 IMPORTANT
          logoId={data.media_logo_rectangle_id}
          logoType={data.logo_type}

          variant="solution"
          nbAnalyses={data.nb_analyses}
          delta30d={data.delta_30d}
          onClose={close}
        />
      }
    >
      <NumbersBlock
        numbers={numbers}
        entityId={id}
        entityType="solution"
      />

      <RadarBlock radar={radar} />

      <section className="space-y-4">
        <h2 className="text-xs font-semibold uppercase text-gray-400">
          Contenus liés
        </h2>

        <FeedGroupedByMonth
          userLang={userLang}

          items={items}

          onClickItem={(item) =>
            openRightDrawer(
              "analysis",
              item.id,
              "silent"
            )
          }
        />
      </section>
    </EntityDrawer>
  );
}
