"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";

import ProfileIdentityCard from "./ProfileIdentityCard";
import ProfileAccountCard from "./ProfileAccountCard";
import ProfileSecurityCard from "./ProfileSecurityCard";
import ProfileExpertsCard from "./ProfileExpertsCard";
import ProfilePreferencesViewer from "./ProfilePreferencesViewer";
import ProfileKeywordsEditor from "./ProfileKeywordsEditor";
import ProfileGeographyEditor from "./ProfileGeographyEditor";
import ProfileAIEditor from "./ProfileAIEditor";

import FormActions from "@/components/ui/FormActions";

/* ========================================================= */

type Props = {
  mode: "create" | "edit";
  userId?: string;
};

/* ========================================================= */

export default function ProfileEditor({
  mode,
  userId,
}: Props) {

  const router = useRouter();

  const [loading, setLoading] =
    useState(mode === "edit");

  const [saving, setSaving] =
    useState(false);

  const [email, setEmail] =
  useState("");

  const [password, setPassword] =
    useState("");

  const [displayName, setDisplayName] =
    useState("");

  const [name, setName] =
    useState("");

  const [company, setCompany] =
    useState("");

  const [description, setDescription] =
    useState("");

  const [profileType, setProfileType] =
    useState<"USER" | "EXPERT">("USER");

  const [role, setRole] =
    useState("user");

  const [language, setLanguage] =
    useState("fr");

  const [frequency, setFrequency] =
    useState("WEEKLY");

  const [isActive, setIsActive] =
    useState(true);

  /* =====================================================
     LOAD
  ===================================================== */

  useEffect(() => {

    if (
      mode !== "edit" ||
      !userId
    ) {
      return;
    }

    async function load() {

      try {

        setLoading(true);

        const res =
          await api.get(
            `/user/${userId}`,
          );

        const user = res.user;

        setEmail(user.EMAIL ?? "");
        setPassword("");

        setDisplayName(
          user.DISPLAY_NAME ?? "",
        );

        setName(user.NAME ?? "");

        setCompany(
          user.COMPANY ?? "",
        );

        setDescription(
          user.DESCRIPTION ?? "",
        );

        setProfileType(
          (user.PROFILE_TYPE ?? "USER") as
            "USER" | "EXPERT",
        );

        setRole(user.ROLE ?? "user");

        setLanguage(
          user.LANGUAGE ?? "fr",
        );

        setFrequency(
          user.FREQUENCY ?? "WEEKLY",
        );

        setIsActive(
          user.IS_ACTIVE ?? true,
        );

      } catch (e) {

        console.error(e);

      } finally {

        setLoading(false);

      }

    }

    load();

  }, [mode, userId]);

  /* =====================================================
     SAVE
  ===================================================== */

  async function save() {

    try {

      setSaving(true);

      if (mode === "create") {

        await api.post(
          "/user/create",
          user,
        );

      } else {

        await api.post(
          "/user/update",
          {
            user_id: userId,
            ...user,
          },
        );

      }

      router.push(
        "/admin/users",
      );

    } catch (e) {

      console.error(e);

      alert(
        "Unable to save profile."
      );

    } finally {

      setSaving(false);

    }

  }

  /* ===================================================== */

  if (loading) {

    return (
      <div className="p-8">
        Loading...
      </div>
    );

  }

  return (

    <div className="space-y-6">

      <ProfileIdentityCard
        values={user}
        onChange={updateField}
        disabled={mode === "edit"}
      />

      <ProfileAccountCard
        values={user}
        onChange={updateField}
      />

      <ProfileSecurityCard
        values={user}
        onChange={updateField}
      />

      <FormActions
        saving={saving}
        saveLabel={
          mode === "create"
            ? "Create Profile"
            : "Save Changes"
        }
        onSave={save}
        onCancel={() =>
          router.push("/admin/users")
        }
      />

      {mode === "edit" &&
        userId && (
          <>
            {user.profile_type ===
              "USER" && (
              <ProfileExpertsCard
                userId={userId}
              />
            )}

            <ProfilePreferencesViewer
              userId={userId}
            />

            <ProfileKeywordsEditor
              userId={userId}
            />

            <ProfileGeographyEditor
              userId={userId}
            />

            <ProfileAIEditor
              userId={userId}
            />
          </>
      )}

    </div>

  );

}
