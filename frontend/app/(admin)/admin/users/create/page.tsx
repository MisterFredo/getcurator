"use client";

import ProfileEditor from "@/components/admin/users/ProfileEditor";

export default function CreateProfilePage() {

  return (

    <div className="max-w-6xl mx-auto space-y-6">

      <h1 className="text-2xl font-semibold">
        Create Profile
      </h1>

      <ProfileEditor
        mode="create"
      />

    </div>

  );

}
