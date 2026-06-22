"use client";

import { useState } from "react";
import { api } from "@/lib/api";

import type {
  DigestContentItem,
  DigestEditorialItem,
} from "@/types/digest";

export function useDigestStudio() {

  const [
    digestId,
    setDigestId,
  ] = useState<string | null>(
    null
  );

  const [
    digestName,
    setDigestName,
  ] = useState("");

  const [
    contents,
    setContents,
  ] = useState<
    DigestContentItem[]
  >([]);

  const [
    summary,
    setSummary,
  ] = useState("");

  const [
    implications,
    setImplications,
  ] = useState("");

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    editorialOrder,
    setEditorialOrder,
  ] = useState<
    DigestEditorialItem[]
  >([]);

  async function loadDigest(
    userId: string
  ) {

    try {

      setLoading(true);

      const response =
        await api.get(
          `/digest/my-feed?user_id=${userId}`
        );

      const result =
        response?.result || {};

      const digestContents =
        result?.contents || [];

      setContents(
        digestContents
      );

      setSummary(
        result?.summary || ""
      );

      setImplications(
        result?.implications || ""
      );

      setEditorialOrder(

        digestContents.map(
          (
            item: DigestContentItem
          ) => ({
            id: item.id,
            type: "content",
          })
        )
      );

    } finally {

      setLoading(false);

    }
  }

  async function loadStoredDigest(
    id: string
  ) {

    try {

      setLoading(true);

      const response =
        await api.get(
          `/digest/${id}`
        );

      const result =
        response?.result || {};

      const digest =
        result?.digest || {};

      const digestContents =
        result?.contents || [];

      setDigestId(
        digest.ID_DIGEST
      );

      setDigestName(
        digest.DIGEST_NAME || ""
      );

      setSummary(
        digest.SUMMARY || ""
      );

      setImplications(
        digest.IMPLICATIONS || ""
      );

      setContents(
        digestContents
      );

      setEditorialOrder(

        digestContents.map(
          (
            item: DigestContentItem
          ) => ({
            id: item.id,
            type: "content",
          })
        )
      );

    } finally {

      setLoading(false);

    }
  }

  async function saveDigest() {

    if (!digestId) {
      return;
    }

    await api.post(
      `/digest/${digestId}/save`,
      {
        digest_name:
          digestName,

        summary,

        implications,

        content_ids:
          editorialOrder
            .filter(
              (i) =>
                i.type ===
                "content"
            )
            .map(
              (i) => i.id
            ),
      }
    );
  }

  return {

    digestId,
    setDigestId,

    digestName,
    setDigestName,

    contents,
    setContents,

    summary,
    setSummary,

    implications,
    setImplications,

    editorialOrder,
    setEditorialOrder,

    loading,

    loadDigest,
    loadStoredDigest,
    saveDigest,
  };
}
