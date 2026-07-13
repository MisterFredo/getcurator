"use client";

import Link from "next/link";

import TopicForm from "@/components/admin/topic/TopicForm";

/* ========================================================= */

export default function CreateTopicPage() {

  return (

    <div className="space-y-10">

      <div className="flex items-center justify-between">

        <div>

          <h1 className="text-3xl font-semibold">
            Create topic
          </h1>

          <p className="text-sm text-gray-500 mt-1">
            Create a new topic and configure its knowledge base.
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
        mode="create"
      />

    </div>

  );

}
