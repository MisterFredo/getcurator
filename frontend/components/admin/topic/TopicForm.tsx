// components/admin/topic/TopicForm.tsx

"use client";

import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";

import {
  EMPTY_TOPIC,
  TopicFormData,
  Universe,
} from "@/types/topic";

import TopicIdentity from "./TopicIdentity";
import TopicKnowledge from "./TopicKnowledge";
import TopicVisuals from "./TopicVisuals";

/* ========================================================= */

type Props = {
  mode: "create" | "edit";
  topicId?: string;
};

/* ========================================================= */

export default function TopicForm({

  mode,
  topicId: initialTopicId,

}: Props) {

  const isCreate =
    mode === "create";

  /* =======================================================
     ENTITY
  ======================================================= */

  const [
    topic,
    setTopic,
  ] = useState<TopicFormData>(
    EMPTY_TOPIC
  );

  const [
    topicId,
    setTopicId,
  ] = useState<string | null>(
    initialTopicId ?? null
  );

  /* =======================================================
     REFERENCES
  ======================================================= */

  const [
    availableUniverses,
    setAvailableUniverses,
  ] = useState<Universe[]>([]);

  /* =======================================================
     VISUALS
  ======================================================= */

  const [
    squareFilename,
    setSquareFilename,
  ] = useState<string | null>(
    null
  );

  const [
    rectangleFilename,
    setRectangleFilename,
  ] = useState<string | null>(
    null
  );

  /* =======================================================
     UI
  ======================================================= */

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    saving,
    setSaving,
  ] = useState(false);

  /* =======================================================
     LOAD REFERENCES
  ======================================================= */

  async function loadReferenceData() {

    const res =
      await api.get(
        "/universe/list"
      );

    setAvailableUniverses(
      res.universes ?? []
    );

  }

  /* =======================================================
     LOAD TOPIC
  ======================================================= */

  async function loadTopic() {

    if (!topicId) {
      return;
    }

    const t =
      await api.get(
        `/topic/${topicId}`
      );

    setTopic({

      label:
        t.label ?? "",

      description:
        t.description ?? "",

      seo_title:
        t.seo_title ?? "",

      seo_description:
        t.seo_description ?? "",

      universes:
        (t.universes ?? []).map(
          (u: Universe) =>
            u.id_universe
        ),

    });

    setSquareFilename(
      t.media_square_id ?? null
    );

    setRectangleFilename(
      t.media_rectangle_id ?? null
    );

  }

  /* =======================================================
     LOAD
  ======================================================= */

  const load = useCallback(
    async () => {

      try {

        setLoading(true);

        await loadReferenceData();

        await loadTopic();

      } catch (e) {

        console.error(e);

        alert(
          "Error loading topic."
        );

      } finally {

        setLoading(false);

      }

    },
    [topicId]
  );

  useEffect(() => {

    load();

  }, [load]);

  /* =======================================================
     PAYLOAD
  ======================================================= */

  function getPayload() {

    return {

      label:
        topic.label,

      description:
        topic.description || null,

      seo_title:
        topic.seo_title || null,

      seo_description:
        topic.seo_description || null,

      universe_ids:
        topic.universes,

    };

  }

  /* =======================================================
     CREATE
  ======================================================= */

  async function handleCreate(): Promise<string> {

    const res =
      await api.post(
        "/topic/create",
        getPayload()
      );

    if (!res.id_topic) {

      throw new Error(
        "Missing topic id."
      );

    }

    return res.id_topic;

  }

  /* =======================================================
     UPDATE
  ======================================================= */

  async function handleUpdate() {

    if (!topicId) {
      return;
    }

    await api.put(

      `/topic/update/${topicId}`,

      getPayload(),

    );

    await loadTopic();

  }

  /* =======================================================
     SAVE
  ======================================================= */

  async function handleSave() {

    if (!topic.label.trim()) {

      alert(
        "Label required."
      );

      return;

    }

    if (
      topic.universes.length === 0
    ) {

      alert(
        "Select at least one universe."
      );

      return;

    }

    try {

      setSaving(true);

      if (isCreate) {

        const newId =
          await handleCreate();

        setTopicId(
          newId
        );

        await load();

      } else {

        await handleUpdate();

      }

    } catch (e) {

      console.error(e);

      alert(
        "Error saving topic."
      );

    } finally {

      setSaving(false);

    }

  }

  /* =======================================================
     VISUAL UPDATED
  ======================================================= */

  async function handleVisualUpdated() {

    await loadTopic();

  }

  /* =======================================================
     RENDER
  ======================================================= */

  if (loading) {

    return (
      <div className="text-gray-500">
        Loading...
      </div>
    );

  }

  return (

    <div className="space-y-10">

      <TopicIdentity

        label={topic.label}

        setLabel={(label) =>
          setTopic((prev) => ({
            ...prev,
            label,
          }))
        }

        universes={
          availableUniverses
        }

        selectedUniverses={
          topic.universes
        }

        setSelectedUniverses={(
          universes
        ) =>
          setTopic((prev) => ({
            ...prev,
            universes,
          }))
        }

      />

      <TopicKnowledge

        description={
          topic.description
        }

        setDescription={(
          description
        ) =>
          setTopic((prev) => ({
            ...prev,
            description,
          }))
        }

        seoTitle={
          topic.seo_title
        }

        setSeoTitle={(
          seo_title
        ) =>
          setTopic((prev) => ({
            ...prev,
            seo_title,
          }))
        }

        seoDescription={
          topic.seo_description
        }

        setSeoDescription={(
          seo_description
        ) =>
          setTopic((prev) => ({
            ...prev,
            seo_description,
          }))
        }

      />

      <TopicVisuals

        topicId={topicId}

        squareFilename={
          squareFilename
        }

        rectangleFilename={
          rectangleFilename
        }

        onUpdated={
          handleVisualUpdated
        }

      />

      <div className="flex justify-end pt-8 border-t">

        <button

          onClick={handleSave}

          disabled={saving}

          className="
            bg-ratecard-blue
            text-white
            px-6
            py-3
            rounded
            disabled:opacity-50
          "

        >

          {saving
            ? "Saving..."
            : isCreate
              ? "Create topic"
              : "Save changes"}

        </button>

      </div>

    </div>

  );

}
