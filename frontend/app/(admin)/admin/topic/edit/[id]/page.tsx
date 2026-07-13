"use client";

import Link from "next/link";

import { useParams } from "next/navigation";

import TopicForm from "@/components/admin/topic/TopicForm";

/* ========================================================= */

export default function EditTopicPage() {

  const params =
    useParams();

  const topicId =
    params.id as string;

  return (

    <div className="space-y-10">

      <div className="flex items-center justify-between">

        <div>

          <h1 className="text-3xl font-semibold">
            Edit topic
          </h1>

          <p className="text-sm text-gray-500 mt-1">
            Update the topic information and associated visuals.
          </p>

        </div>

        <Link
          href="/admin/topic"
          className="underline"
        >
          ← Back
        </Link>

      </div>

      <TopicForm
        mode="edit"
        topicId={topicId}
      />

    </div>

  );

}
