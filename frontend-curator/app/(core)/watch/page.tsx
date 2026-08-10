"use client";

import { useEffect, useState } from "react";

import { useUser } from "@/hooks/useUser";

import {
  watchLatest,
  watchSearch,
} from "@/lib/watch";

import WatchHeader from "@/components/watch/WatchHeader";
import WatchList from "@/components/watch/WatchList";
import { useDrawer } from "@/contexts/DrawerContext";
import { useWorkspace } from "@/contexts/WorkspaceContext";
import type {
  WatchItem,
} from "@/types/watch";

/* ========================================================= */

type Universe = {

  id: string;

  label: string;

  count?: number;

};

/* ========================================================= */

export default function WatchPage() {

  const {
    user,
  } = useUser();

  const {
    openRightDrawer,
  } = useDrawer();

  const {
    selectedContentItems,
    toggleContent,
  } = useWorkspace();

  const [
    items,
    setItems,
  ] = useState<WatchItem[]>([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    query,
    setQuery,
  ] = useState("");

  const [
    selectedUniverse,
    setSelectedUniverse,
  ] = useState<string | null>(
    null,
  );

  const [
    total,
    setTotal,
  ] = useState(0);

  // TODO
  const universes: Universe[] = [];

  /* ===================================================== */

  useEffect(() => {

    if (!user) {

      return;

    }

    loadLatest();

  }, [
    user,
    selectedUniverse,
  ]);

  /* =====================================================
     LATEST
  ===================================================== */

  async function loadLatest() {

    if (!user) {

      return;

    }

    setLoading(
      true,
    );

    try {

      const res =
        await watchLatest({

          user_id:
            user.user_id,

          universe_id:
            selectedUniverse,

        });

      setItems(
        res.items,
      );

      setTotal(
        res.count,
      );

    } finally {

      setLoading(
        false,
      );

    }

  }

  /* =====================================================
     SEARCH
  ===================================================== */

  async function handleSearch(
    value: string,
  ) {

    if (!user) {

      return;

    }

    setQuery(
      value,
    );

    setLoading(
      true,
    );

    try {

      const res =
        await watchSearch({

          user_id:
            user.user_id,

          query: value,

          universe_id:
            selectedUniverse,

        });

      setItems(
        res.items,
      );

      setTotal(
        res.count,
      );

    } finally {

      setLoading(
        false,
      );

    }

  }

  /* =====================================================
     OPEN DRAWER
  ===================================================== */

  function openContent(
    item: WatchItem,
  ) {
  
    console.log("OPEN CONTENT", item.id);
  
    openRightDrawer(
      "content",
      item.id,
    );
  
  }

  const selectedIds =
    selectedContentItems.map(
      (item) => item.id,
    );
  
  function toggleSelect(
    item: WatchItem,
  ) {
  
    toggleContent(
      item,
    );
  
  }

  /* ===================================================== */

  return (

    <div className="space-y-8">

      <WatchHeader

        query={query}

        onSearch={
          handleSearch
        }

        universes={
          universes
        }

        selectedUniverse={
          selectedUniverse
        }

        onSelectUniverse={
          setSelectedUniverse
        }

        loading={loading}

      />

     <WatchList

        title="Results"
      
        total={total}
      
        items={items}
      
        loading={loading}
      
        hasMore={false}
      
        onLoadMore={() => {}}
      
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

    </div>

  );

}
