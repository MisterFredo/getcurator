"use client";

import type {
  DigestHistoryItem,
} from "@/types/digest";

import DigestRow from "./AdminDigestRow";


/* =========================================================
   TYPES
========================================================= */

type Props = {

  digests: DigestHistoryItem[];

  loading?: boolean;

  onChanged: () => void;

};


/* =========================================================
   COMPONENT
========================================================= */

export default function AdminDigestList({

  digests,

  loading = false,

  onChanged,

}: Props) {

  /* =====================================================
     LOADING
  ===================================================== */

  if (
    loading
    && digests.length === 0
  ) {

    return (

      <div
        className="
          rounded-lg
          border
          bg-white
          p-10
          text-center
          text-sm
          text-gray-500
        "
      >
        Loading Digests...
      </div>

    );

  }


  /* =====================================================
     EMPTY
  ===================================================== */

  if (
    !loading
    && digests.length === 0
  ) {

    return (

      <div
        className="
          rounded-lg
          border
          bg-white
          p-10
          text-center
        "
      >

        <div
          className="
            text-sm
            font-medium
            text-gray-900
          "
        >
          No Digests found
        </div>

        <div
          className="
            mt-1
            text-sm
            text-gray-500
          "
        >
          Try changing or resetting the current filters.
        </div>

      </div>

    );

  }


  /* =====================================================
     TABLE
  ===================================================== */

  return (

    <div
      className="
        relative
        overflow-hidden
        rounded-lg
        border
        bg-white
      "
    >

      {loading && (

        <div
          className="
            absolute
            inset-x-0
            top-0
            z-10
            h-1
            overflow-hidden
            bg-blue-100
          "
        >

          <div
            className="
              h-full
              w-1/3
              animate-pulse
              bg-blue-600
            "
          />

        </div>

      )}

      <div className="overflow-x-auto">

        <table
          className="
            min-w-[1180px]
            w-full
            text-sm
          "
        >

          <thead className="bg-gray-50">

            <tr>

              <th
                className="
                  px-4
                  py-3
                  text-left
                  font-medium
                  text-gray-600
                "
              >
                Recipient
              </th>

              <th
                className="
                  px-4
                  py-3
                  text-left
                  font-medium
                  text-gray-600
                "
              >
                Profile
              </th>

              <th
                className="
                  px-4
                  py-3
                  text-left
                  font-medium
                  text-gray-600
                "
              >
                Period
              </th>

              <th
                className="
                  px-4
                  py-3
                  text-left
                  font-medium
                  text-gray-600
                "
              >
                Status
              </th>

              <th
                className="
                  px-4
                  py-3
                  text-right
                  font-medium
                  text-gray-600
                "
              >
                Analysed / Total
              </th>

              <th
                className="
                  px-4
                  py-3
                  text-left
                  font-medium
                  text-gray-600
                "
              >
                Generated
              </th>

              <th
                className="
                  px-4
                  py-3
                  text-right
                  font-medium
                  text-gray-600
                "
              >
                Actions
              </th>

            </tr>

          </thead>

          <tbody>

            {digests.map(
              (
                digest,
              ) => (

                <AdminDigestRow

                  key={
                    digest.id
                  }

                  digest={
                    digest
                  }

                  onChanged={
                    onChanged
                  }

                />

              ),
            )}

          </tbody>

        </table>

      </div>

    </div>

  );

}
