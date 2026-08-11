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

type TopicData = {

  id_topic: string;

  label?: string;

  topic_axis?: string;

  description?: string | null;

};

/* ========================================================= */

export default function TopicDrawer({
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
  ] = useState<TopicData | null>(
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
        "/topics",
      )
    ) {

      router.push(
        "/topics",
        {
          scroll: false,
        },
      );

    }

  }

  /* =========================================================
     LOAD TOPIC
  ========================================================= */

  useEffect(() => {

    async function loadTopic() {

      try {

        const res =
          await api.get(
            `/topic/${id}/view`,
          );

        setData(
          res,
        );

      } catch (e) {

        console.error(
          "❌ Topic load error:",
          e,
        );

        setData(
          null,
        );

      }

    }

    loadTopic();

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

            topic_id:
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
          "❌ Topic contents error:",
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

          topic_id:
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
        "❌ Topic load more error:",
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
            data.label
            || "Topic"
          }

          subtitle={
            data.topic_axis
          }

          variant="topic"

          onClose={
            close
          }

        />

      }

    >

      {/* =====================================================
          DESCRIPTION
      ===================================================== */}

      {data.description && (

        <div className="
          border-b
          border-gray-200
          py-4
        ">

          <div

            className="
              prose
              prose-sm
              max-w-none
            "

            dangerouslySetInnerHTML={{
              __html:
                data.description,
            }}

          />

        </div>

      )}

      {/* =====================================================
          CONTENTS
      ===================================================== */}

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
