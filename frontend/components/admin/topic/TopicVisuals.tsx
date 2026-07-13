// components/admin/topic/TopicVisuals.tsx

"use client";

import VisualSection from "@/components/visuals/VisualSection";

/* ========================================================= */

const GCS_BASE_URL =
  process.env.NEXT_PUBLIC_GCS_BASE_URL!;

const TOPIC_MEDIA_PATH =
  "topics";

/* ========================================================= */

type Props = {
  topicId: string | null;

  squareFilename: string | null;

  rectangleFilename: string | null;

  onUpdated: () => Promise<void>;
};

/* ========================================================= */

export default function TopicVisuals({

  topicId,

  squareFilename,

  rectangleFilename,

  onUpdated,

}: Props) {

  if (!topicId) {

    return (

      <section className="space-y-4">

        <div>

          <h2 className="text-lg font-semibold">
            Visuals
          </h2>

          <p className="text-sm text-gray-500">
            Save the topic before uploading visuals.
          </p>

        </div>

      </section>

    );

  }

  const squareUrl =
    squareFilename
      ? `${GCS_BASE_URL}/${TOPIC_MEDIA_PATH}/${squareFilename}`
      : null;

  const rectUrl =
    rectangleFilename
      ? `${GCS_BASE_URL}/${TOPIC_MEDIA_PATH}/${rectangleFilename}`
      : null;

  return (

    <section className="space-y-6">

      <div>

        <h2 className="text-lg font-semibold">
          Visuals
        </h2>

        <p className="text-sm text-gray-500">
          Upload the assets associated with this topic.
        </p>

      </div>

      <VisualSection
        entityId={topicId}
        entityType="topic"
        squareUrl={squareUrl}
        rectUrl={rectUrl}
        onUpdated={onUpdated}
      />

    </section>

  );

}
