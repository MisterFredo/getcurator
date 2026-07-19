"use client";

import { useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";

export type ReviewUser = {
  id: string;
  type: "USER" | "EXPERT";
  name: string;
};

type Props = {
  onSelect: (
    user: ReviewUser,
  ) => void;
};

export default function ReviewUserSelector({
  onSelect,
}: Props) {

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    search,
    setSearch,
  ] = useState("");

  const [
    users,
    setUsers,
  ] = useState<
    ReviewUser[]
  >([]);

  /* =====================================================
     LOAD
  ===================================================== */

  useEffect(() => {

    async function load() {

      try {

        const res =
          await api.get(
            "/digest/review-users"
          );

        setUsers(
          res.users || []
        );

      } catch (e) {

        console.error(e);

      } finally {

        setLoading(false);

      }

    }

    load();

  }, []);

  /* =====================================================
     FILTER
  ===================================================== */

  const filtered =
    useMemo(() => {

      if (!search.trim()) {
        return users;
      }

      const q =
        search.toLowerCase();

      return users.filter(
        (u) =>
          u.name
            .toLowerCase()
            .includes(q)
      );

    }, [
      users,
      search,
    ]);

  /* =====================================================
     UI
  ===================================================== */

  return (

    <div className="space-y-4">

      <input
        value={search}
        onChange={(e) =>
          setSearch(
            e.target.value
          )
        }
        placeholder="Search user or expert..."
        className="w-full rounded-lg border px-4 py-2 text-sm"
      />

      <div className="border rounded-lg divide-y max-h-80 overflow-y-auto">

        {loading && (

          <div className="p-4 text-sm text-gray-500">

            Loading...

          </div>

        )}

        {!loading &&
          filtered.length === 0 && (

          <div className="p-4 text-sm text-gray-500">

            No result

          </div>

        )}

        {filtered.map(
          (user) => (

            <button
              key={user.id}
              onClick={() =>
                onSelect(
                  user
                )
              }
              className="w-full px-4 py-3 text-left hover:bg-gray-50 transition flex items-center justify-between"
            >

              <div>

                <div className="font-medium text-sm">

                  {user.name}

                </div>

                <div className="text-xs text-gray-500">

                  {user.type}

                </div>

              </div>

              <div className="text-xs text-ratecard-blue">

                Review →

              </div>

            </button>

          )
        )}

      </div>

    </div>

  );

}
