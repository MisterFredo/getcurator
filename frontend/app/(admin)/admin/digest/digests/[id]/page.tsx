"use client";

import { useEffect, useState } from "react";

import { useParams } from "next/navigation";

import {
  getDigest,
} from "@/lib/digest";

import type {
  Digest,
} from "@/types/digest";

import DigestPreview from "@/components/digest/DigestPreview";

/* ========================================================= */

export default function DigestPage() {

  const {
    id,
  } = useParams<{
    id: string;
  }>();

  const [
    digest,
    setDigest,
  ] = useState<Digest | null>(
    null,
  );

  const [
    loading,
    setLoading,
  ] = useState(true);

  /* =========================================================
     LOAD
  ========================================================= */

  async function load() {

    setLoading(true);

    try {

      const data =
        await getDigest(
          id,
        );

      setDigest(
        data,
      );

    }

    catch (error) {

      console.error(
        error,
      );

    }

    finally {

      setLoading(false);

    }

  }

  /* ========================================================= */

  useEffect(() => {

    load();

  }, [id]);

  /* ========================================================= */

  if (loading) {

    return (

      <div className="rounded-lg border bg-white p-10 text-center">

        Loading digest...

      </div>

    );

  }

  if (!digest) {

    return (

      <div className="rounded-lg border bg-white p-10 text-center">

        Digest not found.

      </div>

    );

  }

  /* ========================================================= */

  return (

    <div className="space-y-6">

      <DigestPreview
        document={
          digest.document
        }
      />

    </div>

  );

}
