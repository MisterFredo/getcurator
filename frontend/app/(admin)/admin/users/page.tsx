"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

type User = {
  ID_USER: string;
  EMAIL: string;

  NAME?: string;
  DISPLAY_NAME?: string;

  COMPANY?: string;

  LANGUAGE?: string;

  ROLE?: string;

  PROFILE_TYPE?: "USER" | "EXPERT";

  FREQUENCY?: string;

  IS_ACTIVE?: boolean;

  CREATED_AT?: string;

  KEYWORDS_COUNT?: number;
  GEOGRAPHY_1?: string;
  HAS_PROFILE?: boolean;
};

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
  ] = useState<"USER" | "EXPERT">(
    "USER"
  );

  // =====================================================
  // LOAD USERS
  // =====================================================

  useEffect(() => {

    async function load() {

      setLoading(true);

      try {

        const res =
          await api.get(
            `/user/list?profile_type=${profileType}`
          );

        setUsers(
          res?.users ?? []
        );

      } catch (e) {

        console.error(
          "❌ error loading users",
          e
        );

        setUsers([]);

      } finally {

        setLoading(false);

      }
    }

    load();

  }, [profileType]);

  // =====================================================
  // RENDER
  // =====================================================

  return (
    <div className="space-y-6">

      {/* HEADER */}

      <div className="flex items-center justify-between">

        <div className="space-y-3">

          <h1 className="text-xl font-semibold">
            Users
          </h1>

          <div className="flex gap-2">

            <button
              onClick={() =>
                setProfileType("USER")
              }
              className={
                profileType === "USER"
                  ? "px-3 py-2 rounded-lg bg-ratecard-blue text-white text-sm"
                  : "px-3 py-2 rounded-lg border text-sm"
              }
            >
              Users
            </button>

            <button
              onClick={() =>
                setProfileType("EXPERT")
              }
              className={
                profileType === "EXPERT"
                  ? "px-3 py-2 rounded-lg bg-ratecard-blue text-white text-sm"
                  : "px-3 py-2 rounded-lg border text-sm"
              }
            >
              Experts
            </button>

          </div>

        </div>

        <Link
          href={`/admin/users/create?profile_type=${profileType}`}
          className="bg-ratecard-blue text-white px-4 py-2 rounded-lg text-sm"
        >
          {profileType === "USER"
            ? "+ Create user"
            : "+ Create expert"}
        </Link>

      </div>

      {/* TABLE */}

      <div className="bg-white border rounded-xl overflow-hidden">

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

            <thead className="bg-gray-50 border-b">

              <tr>

                <th className="text-left p-3">
                  Email
                </th>

                <th className="text-left p-3">
                  Name
                </th>

                <th className="text-left p-3">
                  Company
                </th>

                <th className="text-left p-3">
                  Language
                </th>

                <th className="text-left p-3">
                  Role
                </th>

                <th className="text-left p-3">
                  Status
                </th>

                <th className="text-left p-3">
                  Keywords
                </th>

                <th className="text-left p-3">
                  Geo
                </th>

                <th className="text-left p-3">
                  Profile
                </th>

                <th className="text-left p-3">
                  Actions
                </th>

              </tr>

            </thead>

            <tbody>

              {users.map((u) => (

                <tr
                  key={u.ID_USER}
                  className="border-b hover:bg-gray-50"
                >

                  <td className="p-3">
                    {u.EMAIL}
                  </td>

                  <td className="p-3">
                    {u.DISPLAY_NAME ||
                      u.NAME ||
                      "-"}
                  </td>

                  <td className="p-3">
                    {u.COMPANY || "-"}
                  </td>

                  <td className="p-3">
                    {u.LANGUAGE || "fr"}
                  </td>

                  {/* ROLE */}

                  <td className="p-3">

                    {u.ROLE === "admin" ? (

                      <span className="text-blue-600 font-medium">
                        Admin
                      </span>

                    ) : (

                      <span className="text-gray-600">
                        User
                      </span>

                    )}

                  </td>

                  {/* STATUS */}

                  <td className="p-3">

                    {u.IS_ACTIVE ? (

                      <span className="text-green-600 font-medium">
                        Active
                      </span>

                    ) : (

                      <span className="text-gray-400">
                        Inactive
                      </span>

                    )}

                  </td>

                  {/* KEYWORDS */}

                  <td className="p-3">

                    {u.KEYWORDS_COUNT ? (

                      <span className="font-medium">
                        {u.KEYWORDS_COUNT}
                      </span>

                    ) : (

                      <span className="text-gray-400">
                        0
                      </span>

                    )}

                  </td>

                  {/* GEO */}

                  <td className="p-3">

                    {u.GEOGRAPHY_1 ? (

                      <span>
                        {u.GEOGRAPHY_1}
                      </span>

                    ) : (

                      <span className="text-gray-400">
                        -
                      </span>

                    )}

                  </td>

                  {/* PROFILE */}

                  <td className="p-3">

                    {u.HAS_PROFILE ? (

                      <span className="text-green-600 font-medium">
                        ✓
                      </span>

                    ) : (

                      <span className="text-gray-400">
                        -
                      </span>

                    )}

                  </td>

                  {/* ACTIONS */}

                  <td className="p-3">

                    <Link
                      href={`/admin/users/${u.ID_USER}`}
                      className="text-ratecard-blue hover:underline"
                    >
                      Edit
                    </Link>

                  </td>

                </tr>

              ))}

            </tbody>

          </table>

        )}

      </div>

    </div>
  );
}
