// frontend-curator/app/(core)/watch/page.tsx

"use client";

import { useEffect, useState } from "react";

import { useUser } from "@/hooks/useUser";

import {
  watchLatest,
} from "@/lib/watch";

import type {
  WatchItem,
} from "@/types/watch";

export default function WatchPage() {

  const {
    user,
  } = useUser();

  const [
    items,
    setItems,
  ] = useState<WatchItem[]>([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  useEffect(() => {

    if (!user) return;

    load();

  }, [
    user,
  ]);

  async function load() {

    if (!user) return;

    setLoading(true);

    try {

      const res =
        await watchLatest({

          user_id:
            user.id,

        });

      setItems(
        res.items,
      );

    } finally {

      setLoading(false);

    }

  }

  if (loading) {

    return (
      <div className="p-8">
        Loading...
      </div>
    );

  }

  return (

    <div className="p-8">

      <h1 className="text-2xl font-semibold mb-6">

        Watch

      </h1>

      <div className="space-y-4">

        {items.map(

          item => (

            <div

              key={item.id}

              className="rounded-lg border p-4"

            >

              <h2 className="font-semibold">

                {item.title}

              </h2>

              <p className="text-sm text-gray-600 mt-2">

                {item.excerpt}

              </p>

            </div>

          )

        )}

      </div>

    </div>

  );

}
