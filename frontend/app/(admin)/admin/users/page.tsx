"use client";

import {
  useEffect,
  useState,
} from "react";

import Link from "next/link";

import {
  api,
} from "@/lib/api";


/* =========================================================
   TYPES
========================================================= */

type User = {

  ID_USER: string;

  EMAIL: string;

  NAME?: string;

  DISPLAY_NAME?: string;

  COMPANY?: string;

  LANGUAGE?: string;

  ROLE?: string;

  PROFILE_TYPE?:
    | "USER"
    | "EXPERT";

  IS_ACTIVE?: boolean;

  CREATED_AT?: string;

  HAS_FAVORITES?: boolean;

  KEYWORDS_COUNT?: number;

  GEOGRAPHY_1?: string;

  HAS_PROFILE?: boolean;

};


/* =========================================================
   PAGE
========================================================= */

export default function UsersPage() {

  const [
    users,
    setUsers,
  ] = useState<User[]>([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    profileType,
    setProfileType,
  ] = useState<
    "USER" | "EXPERT"
  >(
    "USER",
  );

  const [
    deletingId,
    setDeletingId,
  ] = useState<string | null>(
    null,
  );


  /* =====================================================
     LOAD USERS
  ===================================================== */

  useEffect(() => {

    async function load() {

      try {

        setLoading(true);

        const res =
          await api.get(
            `/user/list?profile_type=${profileType}`,
          );

        setUsers(
          res?.users ?? [],
        );

      } catch (error) {

        console.error(
          "❌ error loading users",
          error,
        );

        setUsers([]);

      } finally {

        setLoading(false);

      }

    }

    load();

  }, [
    profileType,
  ]);


  /* =====================================================
     DELETE USER
  ===================================================== */

  async function handleDelete(
    user: User,
  ) {

    const label = (

      user.DISPLAY_NAME

      || user.NAME

      || user.EMAIL

    );

    const confirmed =
      window.confirm(
        `Delete "${label}" ?`,
      );

    if (!confirmed) {

      return;

    }

    try {

      setDeletingId(
        user.ID_USER,
      );

      await api.delete(
        `/user/${user.ID_USER}`,
      );

      setUsers(
        (previousUsers) =>
          previousUsers.filter(
            (item) =>
              item.ID_USER
              !== user.ID_USER,
          ),
      );

    } catch (error) {

      console.error(
        "❌ error deleting user",
        error,
      );

      alert(
        "Unable to delete user",
      );

    } finally {

      setDeletingId(
        null,
      );

    }

  }


  /* =====================================================
     RENDER
  ===================================================== */

  return (

    <div className="space-y-6">

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <div className="flex items-center justify-between">

        <div className="space-y-3">

          <h1 className="text-xl font-semibold">

            Users

          </h1>

          <div className="flex gap-2">

            <button
              type="button"
              onClick={() =>
                setProfileType(
                  "USER",
                )
              }
              className={
                profileType === "USER"
                  ? "rounded-lg bg-ratecard-blue px-3 py-2 text-sm text-white"
                  : "rounded-lg border px-3 py-2 text-sm"
              }
            >
              Users
            </button>

            <button
              type="button"
              onClick={() =>
                setProfileType(
                  "EXPERT",
                )
              }
              className={
                profileType === "EXPERT"
                  ? "rounded-lg bg-ratecard-blue px-3 py-2 text-sm text-white"
                  : "rounded-lg border px-3 py-2 text-sm"
              }
            >
              Experts
            </button>

          </div>

        </div>

        <Link
          href={`/admin/users/create?profile_type=${profileType}`}
          className="rounded-lg bg-ratecard-blue px-4 py-2 text-sm text-white"
        >
          {profileType === "USER"
            ? "+ Create user"
            : "+ Create expert"}
        </Link>

      </div>


      {/* ================================================= */}
      {/* TABLE */}
      {/* ================================================= */}

      <div className="overflow-hidden rounded-xl border bg-white">

        {loading ? (

          <div className="p-6 text-sm text-gray-500">

            Loading...

          </div>

        ) : users.length === 0 ? (

          <div className="p-6 text-sm text-gray-500">

            No users found

          </div>

        ) : (

          <table className="w-full text-sm">

            <thead className="border-b bg-gray-50">

              <tr>

                <th className="p-3 text-left">
                  Email
                </th>

                <th className="p-3 text-left">
                  Name
                </th>

                <th className="p-3 text-left">
                  Company
                </th>

                <th className="p-3 text-left">
                  Language
                </th>

                <th className="p-3 text-left">
                  Role
                </th>

                <th className="p-3 text-left">
                  Status
                </th>

                <th className="p-3 text-left">
                  Favorites
                </th>

                <th className="p-3 text-left">
                  Keywords
                </th>

                <th className="p-3 text-left">
                  Geo
                </th>

                <th className="p-3 text-left">
                  Profile
                </th>

                <th className="p-3 text-left">
                  Actions
                </th>

              </tr>

            </thead>

            <tbody>

              {users.map(
                (user) => (

                  <tr
                    key={user.ID_USER}
                    className="border-b hover:bg-gray-50"
                  >

                    {/* ===================================== */}
                    {/* EMAIL */}
                    {/* ===================================== */}

                    <td className="p-3">

                      {user.EMAIL}

                    </td>

                    {/* ===================================== */}
                    {/* NAME */}
                    {/* ===================================== */}

                    <td className="p-3">

                      {user.DISPLAY_NAME
                        || user.NAME
                        || "-"}

                    </td>

                    {/* ===================================== */}
                    {/* COMPANY */}
                    {/* ===================================== */}

                    <td className="p-3">

                      {user.COMPANY || "-"}

                    </td>

                    {/* ===================================== */}
                    {/* LANGUAGE */}
                    {/* ===================================== */}

                    <td className="p-3">

                      {user.LANGUAGE || "fr"}

                    </td>

                    {/* ===================================== */}
                    {/* ROLE */}
                    {/* ===================================== */}

                    <td className="p-3">

                      {user.ROLE === "admin" ? (

                        <span className="font-medium text-blue-600">

                          Admin

                        </span>

                      ) : (

                        <span className="text-gray-600">

                          User

                        </span>

                      )}

                    </td>

                    {/* ===================================== */}
                    {/* STATUS */}
                    {/* ===================================== */}

                    <td className="p-3">

                      {user.IS_ACTIVE ? (

                        <span className="font-medium text-green-600">

                          Active

                        </span>

                      ) : (

                        <span className="text-gray-400">

                          Inactive

                        </span>

                      )}

                    </td>

                    {/* ===================================== */}
                    {/* FAVORITES */}
                    {/* ===================================== */}

                    <td className="p-3">

                      {user.HAS_FAVORITES ? (

                        <span className="font-medium text-green-600">

                          Yes

                        </span>

                      ) : (

                        <span className="text-gray-400">

                          No

                        </span>

                      )}

                    </td>

                    {/* ===================================== */}
                    {/* KEYWORDS */}
                    {/* ===================================== */}

                    <td className="p-3">

                      {user.KEYWORDS_COUNT ? (

                        <span className="font-medium">

                          {user.KEYWORDS_COUNT}

                        </span>

                      ) : (

                        <span className="text-gray-400">

                          0

                        </span>

                      )}

                    </td>

                    {/* ===================================== */}
                    {/* GEO */}
                    {/* ===================================== */}

                    <td className="p-3">

                      {user.GEOGRAPHY_1 ? (

                        <span>

                          {user.GEOGRAPHY_1}

                        </span>

                      ) : (

                        <span className="text-gray-400">

                          -

                        </span>

                      )}

                    </td>

                    {/* ===================================== */}
                    {/* PROFILE */}
                    {/* ===================================== */}

                    <td className="p-3">

                      {user.HAS_PROFILE ? (

                        <span className="font-medium text-green-600">

                          ✓

                        </span>

                      ) : (

                        <span className="text-gray-400">

                          -

                        </span>

                      )}

                    </td>

                    {/* ===================================== */}
                    {/* ACTIONS */}
                    {/* ===================================== */}

                    <td className="p-3">

                      <div className="flex items-center gap-3">

                        <Link
                          href={`/admin/users/${user.ID_USER}`}
                          className="text-ratecard-blue hover:underline"
                        >
                          Edit
                        </Link>

                        <button
                          type="button"
                          onClick={() =>
                            handleDelete(
                              user,
                            )
                          }
                          disabled={
                            deletingId
                            === user.ID_USER
                          }
                          className="text-red-600 hover:underline disabled:opacity-40"
                        >
                          {deletingId
                            === user.ID_USER
                            ? "Deleting..."
                            : "Delete"}
                        </button>

                      </div>

                    </td>

                  </tr>

                ),
              )}

            </tbody>

          </table>

        )}

      </div>

    </div>

  );

}
