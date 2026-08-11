"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  usePathname,
  useRouter,
} from "next/navigation";

import { api } from "@/lib/api";

import {
  watchLatest,
} from "@/lib/watch";

import type {
  WatchItem,
} from "@/types/watch";

import EntityDrawer from "@/components/drawers/EntityDrawer";
import DrawerHeader from "@/components/drawers/DrawerHeader";
import WatchGroupedByMonth from "@/components/watch/WatchGroupedByMonth";

import { useDrawer } from "@/contexts/DrawerContext";
import { useWorkspace } from "@/contexts/WorkspaceContext";
import { useUser } from "@/hooks/useUser";

/* ========================================================= */

const PAGE_SIZE = 20;

/* ========================================================= */

type SolutionData = {

  id_solution: string;

  name: string;

  company_name?: string;

  media_logo_rectangle_id?: string | null;

  logo_type?: "solution" | "company";

};

/* ========================================================= */

export default function SolutionDrawer({
  id,
  onClose,
}: any) {

  const router =
    useRouter();

  const pathname =
    usePathname();

  const {
    user,
  } = useUser();

  const {
    leftDrawer,
    openRightDrawer,
    closeLeftDrawer,
  } = useDrawer();

  const {
    selectedContentItems,
    toggleContent,
  } = useWorkspace();

  const [
    data,
    setData,
  ] = useState<SolutionData | null>(
    null,
  );

  const [
    items,
    setItems,
  ] = useState<WatchItem[]>([]);

  const [
    total,
    setTotal,
  ] = useState(0);

  const [
    offset,
    setOffset,
  ] = useState(0);

  const [
    loading,
    setLoading,
  ] = useState(true);

  /* =========================================================
     CLOSE
  ========================================================= */

  function close() {

    onClose?.();

    closeLeftDrawer();

    if (
      leftDrawer.mode === "route"
      && pathname.startsWith(
        "/solutions",
      )
    ) {

      router.push(
        "/solutions",
        {
          scroll: false,
        },
      );

    }

  }

  /* =========================================================
     LOAD SOLUTION
  ========================================================= */

  useEffect(() => {

    async function loadSolution() {

      try {

        const res =
          await api.get(
            `/solution/${id}/view`,
          );

        setData(
          res,
        );

      } catch (e) {

        console.error(
          "❌ Solution load error:",
          e,
        );

        setData(
          null,
        );

      }

    }

    loadSolution();

  }, [
    id,
  ]);

  /* =========================================================
     LOAD WATCH
  ========================================================= */

  useEffect(() => {

    if (!user) {

      return;

    }

    async function loadContents() {

      setLoading(
        true,
      );

      setItems(
        [],
      );

      setTotal(
        0,
      );

      setOffset(
        0,
      );

      try {

        const res =
          await watchLatest({

            user_id:
              user.user_id,

            solution_id:
              id,

            limit:
              PAGE_SIZE,

            offset:
              0,

          });

        setItems(
          res.items,
        );

        setTotal(
          res.count,
        );

        setOffset(
          res.items.length,
        );

      } catch (e) {

        console.error(
          "❌ Solution contents error:",
          e,
        );

        setItems(
          [],
        );

        setTotal(
          0,
        );

        setOffset(
          0,
        );

      } finally {

        setLoading(
          false,
        );

      }

    }

    loadContents();

  }, [
    id,
    user,
  ]);

  /* =========================================================
     LOAD MORE
  ========================================================= */

  async function loadMoreContents() {

    if (!user) {

      return;

    }

    try {

      const res =
        await watchLatest({

          user_id:
            user.user_id,

          solution_id:
            id,

          limit:
            PAGE_SIZE,

          offset,

        });

      setItems(
        (previous) => {

          const existingIds =
            new Set(
              previous.map(
                (item) =>
                  item.id,
              ),
            );

          const newItems =
            res.items.filter(
              (item) =>
                !existingIds.has(
                  item.id,
                ),
            );

          return [
            ...previous,
            ...newItems,
          ];

        },
      );

      setTotal(
        res.count,
      );

      setOffset(
        (previous) =>
          previous
          + res.items.length,
      );

    } catch (e) {

      console.error(
        "❌ Solution load more error:",
        e,
      );

    }

  }

  const hasMore =
    items.length < total;

  /* =========================================================
     CONTENT
  ========================================================= */

  function openContent(
    item: WatchItem,
  ) {

    openRightDrawer(
      "content",
      item.id,
    );

  }

  const selectedIds =
    selectedContentItems.map(
      (item) =>
        item.id,
    );

  function toggleSelect(
    item: WatchItem,
  ) {

    toggleContent(
      item,
    );

  }

  /* ========================================================= */

  if (!data) {

    return null;

  }

  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <EntityDrawer

      onClose={
        close
      }

      header={

        <DrawerHeader

          title={
            data.name
          }

          subtitle={
            data.company_name
          }

          logoId={
            data.media_logo_rectangle_id
          }

          logoType={
            data.logo_type
          }

          variant="solution"

          onClose={
            close
          }

        />

      }

    >

      <section className="
        pt-4
      ">

        <WatchGroupedByMonth

          title="Key Contents"

          total={
            total
          }

          items={
            items
          }

          loading={
            loading
          }

          hasMore={
            hasMore
          }

          onLoadMore={
            loadMoreContents
          }

          onSelect={
            openContent
          }

          selectedIds={
            selectedIds
          }

          onToggleSelect={
            toggleSelect
          }

        />

      </section>

    </EntityDrawer>

  );

}
