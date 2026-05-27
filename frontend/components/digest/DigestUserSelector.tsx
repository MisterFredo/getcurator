// frontend/components/digest/DigestUserSelector.tsx

"use client";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import { api } from "@/lib/api";

/* ========================================================= */

export type DigestUser = {
  id_user: string;

  email: string;

  name?: string;

  company?: string;

  last_sent_at?: string | null;
};

/* ========================================================= */

type Props = {
  selectedUserId?: string;

  onSelectUser: (
    user: DigestUser
  ) => void;
};

/* ========================================================= */

export default function DigestUserSelector({
  selectedUserId,

  onSelectUser,
}: Props) {

  /* =======================================================
     STATE
  ======================================================= */

  const [
    users,
    setUsers,
  ] = useState<
    DigestUser[]
  >([]);

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    query,
    setQuery,
  ] = useState("");

  /* =======================================================
     LOAD USERS
  ======================================================= */

  useEffect(() => {

    async function loadUsers() {

      try {

        setLoading(true);

        const data =
          await api.get(
            "/user/list"
          );

        const rows =
          data?.result?.users ||
          data?.users ||
          data ||
          [];

        setUsers(
          rows.map(
            (u: any) => ({
              id_user:
                u.ID_USER ||
                u.id_user,

              email:
                u.EMAIL ||
                u.email,

              name:
                u.NAME ||
                u.name,

              company:
                u.COMPANY ||
                u.company,

              last_sent_at:
                u.LAST_SENT_AT ||
                u.last_sent_at ||
                null,
            })
          )
        );

      } catch (
        error
      ) {

        console.error(
          "Digest users load error",
          error
        );

      } finally {

        setLoading(false);
      }
    }

    loadUsers();

  }, []);

  /* =======================================================
     FILTERED USERS
  ======================================================= */

  const filteredUsers =
    useMemo(() => {

      if (!query.trim()) {
        return users;
      }

      const q =
        query.toLowerCase();

      return users.filter(
        (u) => {

          return (
            u.email
              ?.toLowerCase()
              .includes(q)

            ||

            u.name
              ?.toLowerCase()
              .includes(q)

            ||

            u.company
              ?.toLowerCase()
              .includes(q)
          );
        }
      );

    }, [
      users,
      query,
    ]);

  /* =======================================================
     FORMAT DATE
  ======================================================= */

  function formatDate(
    value?: string | null
  ) {

    if (!value) {
      return "Jamais";
    }

    try {

      return new Date(
        value
      ).toLocaleDateString(
        "fr-FR",
        {
          day: "2-digit",
          month: "2-digit",
          year: "numeric",
        }
      );

    } catch {

      return "—";
    }
  }

  /* =======================================================
     UI
  ======================================================= */

  return (

    <div className="bg-white border border-gray-200 rounded-lg">

      {/* ===================================================
         HEADER
      =================================================== */}

      <div className="px-4 py-4 border-b border-gray-100">

        <div className="flex items-center justify-between">

          <div>

            <div className="text-sm font-semibold tracking-tight">
              Utilisateurs Digest
            </div>

            <div className="text-xs text-gray-500 mt-1">
              Sélectionnez un utilisateur pour générer son digest.
            </div>

          </div>

          <div className="text-xs text-gray-400">
            {filteredUsers.length} user
            {filteredUsers.length > 1
              ? "s"
              : ""}
          </div>

        </div>

        {/* SEARCH */}

        <div className="mt-4">

          <input
            type="text"

            value={query}

            onChange={(e) =>
              setQuery(
                e.target.value
              )
            }

            placeholder="Rechercher un utilisateur..."

            className="
              w-full
              h-10
              border border-gray-300
              rounded-lg
              px-3
              text-sm
            "
          />

        </div>

      </div>

      {/* ===================================================
         LIST
      =================================================== */}

      <div className="max-h-[520px] overflow-y-auto">

        {loading ? (

          <div className="p-6 text-sm text-gray-500">
            Chargement...
          </div>

        ) : filteredUsers.length === 0 ? (

          <div className="p-6 text-sm text-gray-500">
            Aucun utilisateur.
          </div>

        ) : (

          <div className="divide-y divide-gray-100">

            {filteredUsers.map(
              (user) => {

                const active =
                  selectedUserId ===
                  user.id_user;

                return (

                  <button
                    key={
                      user.id_user
                    }

                    onClick={() =>
                      onSelectUser(
                        user
                      )
                    }

                    className={`
                      w-full text-left px-4 py-4 transition
                      hover:bg-gray-50
                      ${
                        active
                          ? "bg-gray-50"
                          : ""
                      }
                    `}
                  >

                    {/* NAME */}

                    <div className="flex items-start justify-between gap-3">

                      <div className="min-w-0">

                        <div className="text-sm font-medium text-gray-900 truncate">

                          {user.name ||
                            user.email}

                        </div>

                        <div className="text-xs text-gray-500 mt-1 truncate">

                          {user.email}

                        </div>

                        {user.company && (

                          <div className="text-xs text-gray-400 mt-1 truncate">

                            {user.company}

                          </div>

                        )}

                      </div>

                      {/* LAST SENT */}

                      <div className="text-right shrink-0">

                        <div className="text-[11px] uppercase tracking-wide text-gray-400">
                          Dernier envoi
                        </div>

                        <div className="text-xs text-gray-600 mt-1">
                          {formatDate(
                            user.last_sent_at
                          )}
                        </div>

                      </div>

                    </div>

                  </button>
                );
              }
            )}

          </div>

        )}

      </div>

    </div>
  );
}
