"use client";

import { useParams } from "next/navigation";

import ProfileEditor from "@/components/admin/users/ProfileEditor";

export default function EditProfilePage() {

  const params =
    useParams();

  return (

    <div className="max-w-6xl mx-auto space-y-6">

      <h1 className="text-2xl font-semibold">
        Edit Profile
      </h1>

      <ProfileEditor
        mode="edit"
        userId={params.id as string}
      />

    </div>

  );

}
