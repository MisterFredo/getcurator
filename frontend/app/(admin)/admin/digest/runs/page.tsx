"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";

/* ========================================================= */

type Digest = {
ID_DIGEST: string;

ID_USER: string;

DIGEST_NAME: string;

LANGUAGE: string;

STATUS: string;

PERIOD_START: string;

PERIOD_END: string;

GENERATED_AT: string;

SENT_AT?: string | null;

NB_CONTENTS: number;
};

/* ========================================================= */

export default function DigestRunsPage() {

const [digests, setDigests] =
useState<Digest[]>([]);

const [loading, setLoading] =
useState(false);

const router = useRouter();

/* =========================================================
LOAD DIGESTS
========================================================= */

async function loadDigests() {

```
try {

  const res =
    await api.get(
      "/digest/list-all"
    );

  setDigests(
    res?.result || []
  );

} catch (e) {

  console.error(
    "Erreur load digests",
    e
  );

}
```

}

useEffect(() => {

```
loadDigests();
```

}, []);

/* =========================================================
CREATE DIGEST
========================================================= */

function createDigest() {

```
router.push(
  "/admin/digest"
);
```

}

/* =========================================================
OPEN DIGEST
========================================================= */

function openDigest(
id: string
) {

```
router.push(
  `/admin/digest?id_digest=${id}`
);
```

}

/* =========================================================
FORMAT DATE
========================================================= */

function formatDate(
value?: string | null
) {

```
if (!value) {
  return "—";
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
```

}

/* =========================================================
STATUS BADGE
========================================================= */

function StatusBadge(
{
status,
}: {
status: string;
}
) {

```
const value =
  (
    status || ""
  ).toUpperCase();

const styles =

  value === "GENERATED"

    ? "bg-green-100 text-green-700"

  : value === "SENT"

    ? "bg-blue-100 text-blue-700"

  : value === "DRAFT"

    ? "bg-gray-200 text-gray-700"

  : "bg-gray-100 text-gray-500";

return (

  <span
    className={`
      px-2
      py-1
      text-xs
      rounded
      ${styles}
    `}
  >
    {value}
  </span>

);
```

}

/* =========================================================
UI
========================================================= */

return (

```
<div className="space-y-6">

  {/* HEADER */}

  <div className="flex items-center justify-between">

    <div>

      <h1 className="text-lg font-semibold">
        Digests
      </h1>

      <div className="text-sm text-gray-500 mt-1">

        Manage generated digests
        and create new ones.

      </div>

    </div>

    <button
      onClick={createDigest}
      disabled={loading}
      className="
        px-3
        py-2
        bg-black
        text-white
        text-xs
        rounded
      "
    >
      Create Digest
    </button>

  </div>

  {/* TABLE */}

  <div className="bg-white border rounded">

    <div
      className="
        grid
        grid-cols-[2fr_1.5fr_100px_120px_120px_100px]
        px-4
        py-2
        text-xs
        text-gray-500
        border-b
      "
    >

      <div>
        Digest
      </div>

      <div>
        Period
      </div>

      <div>
        Contents
      </div>

      <div>
        Status
      </div>

      <div>
        Generated
      </div>

      <div>
      </div>

    </div>

    {digests.length === 0 && (

      <div className="p-4 text-sm text-gray-500">

        Aucun digest

      </div>

    )}

    {digests.map(
      (d) => (

        <div
          key={
            d.ID_DIGEST
          }
          className="
            grid
            grid-cols-[2fr_1.5fr_100px_120px_120px_100px]
            px-4
            py-3
            text-sm
            border-b
            items-center
            hover:bg-gray-50
          "
        >

          <div>

            <div className="font-medium">

              {d.DIGEST_NAME}

            </div>

            <div className="text-xs text-gray-500">

              {d.ID_USER}

            </div>

          </div>

          <div className="text-xs">

            {formatDate(
              d.PERIOD_START
            )}

            {" → "}

            {formatDate(
              d.PERIOD_END
            )}

          </div>

          <div>

            {d.NB_CONTENTS}

          </div>

          <div>

            <StatusBadge
              status={
                d.STATUS
              }
            />

          </div>

          <div className="text-xs text-gray-500">

            {formatDate(
              d.GENERATED_AT
            )}

          </div>

          <div className="text-right">

            <button
              onClick={() =>
                openDigest(
                  d.ID_DIGEST
                )
              }
              className="
                text-xs
                px-2
                py-1
                border
                rounded
                hover:bg-gray-100
              "
            >
              View
            </button>

          </div>

        </div>

      )
    )}

  </div>

</div>
```

);
}
