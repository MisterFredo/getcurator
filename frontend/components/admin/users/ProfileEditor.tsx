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
import ProfileProfileEditor from "./ProfileProfileEditor";

import FormActions from "@/components/ui/FormActions";

/* ========================================================= */

type Props = {
  mode: "create" | "edit";
  userId?: string;
};

type ProfileType =
  | "USER"
  | "EXPERT";

/* ========================================================= */

export default function ProfileEditor({
  mode,
  userId,
}: Props) {

  const router =
    useRouter();

  const [loading, setLoading] =
    useState(
      mode === "edit"
    );

  const [saving, setSaving] =
    useState(false);

  /* =========================================================
     IDENTITY
  ========================================================= */

  const [email, setEmail] =
    useState("");

  const [
    displayName,
    setDisplayName,
  ] = useState("");

  const [name, setName] =
    useState("");

  const [company, setCompany] =
    useState("");

  const [
    description,
    setDescription,
  ] = useState("");

  /* =========================================================
     ACCOUNT
  ========================================================= */

  const [
    profileType,
    setProfileType,
  ] =
    useState<ProfileType>(
      "USER",
    );

  const [role, setRole] =
    useState("user");

  const [
    language,
    setLanguage,
  ] = useState("en");

  const [
    frequency,
    setFrequency,
  ] = useState("WEEKLY");

  const [
    isActive,
    setIsActive,
  ] = useState(true);

  /* =========================================================
     SECURITY
  ========================================================= */

  const [
    password,
    setPassword,
  ] = useState("");

  /* =========================================================
     LOAD
  ========================================================= */

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

        const user =
          res.user;

        setEmail(
          user.email ?? "",
        );

        setDisplayName(
          user.display_name ?? "",
        );

        setName(
          user.name ?? "",
        );

        setCompany(
          user.company ?? "",
        );

        setDescription(
          user.description ?? "",
        );

        setProfileType(
          user.profile_type ??
            "USER",
        );

        setRole(
          user.role ??
            "user",
        );

        setLanguage(
          user.language ??
            "en",
        );

        setFrequency(
          user.frequency ??
            "WEEKLY",
        );

        setIsActive(
          user.is_active ??
            true,
        );

      } finally {

        setLoading(false);

      }

    }

    load();

  }, [
    mode,
    userId,
  ]);

  /* =========================================================
     SAVE
  ========================================================= */

  async function save() {

    try {

      setSaving(true);

      const payload = {

        email,

        display_name:
          displayName,

        name,

        company,

        description,

        profile_type:
          profileType,

        role,

        language,

        frequency,

        is_active:
          isActive,

        password,
      };

      if (
        mode === "create"
      ) {

        await api.post(
          "/user/create",
          payload,
        );

      } else {

        await api.post(
          "/user/update",
          {
            user_id: userId,
            ...payload,
          },
        );

      }

      router.push(
        "/admin/users",
      );

    } catch (error) {

      console.error(error);

      alert(
        "Unable to save profile.",
      );

    } finally {

      setSaving(false);

    }

  }

  /* ========================================================= */

  if (loading) {

    return (
      <div>
        Loading...
      </div>
    );

  }

  return (

    <div className="space-y-6">

      <ProfileIdentityCard
        email={email}
        setEmail={setEmail}
        displayName={displayName}
        setDisplayName={setDisplayName}
        name={name}
        setName={setName}
        company={company}
        setCompany={setCompany}
        description={description}
        setDescription={setDescription}
        emailDisabled={
          mode === "edit"
        }
      />

      <ProfileAccountCard
        profileType={profileType}
        setProfileType={setProfileType}
        role={role}
        setRole={setRole}
        language={language}
        setLanguage={setLanguage}
        frequency={frequency}
        setFrequency={setFrequency}
        isActive={isActive}
        setIsActive={setIsActive}
      />

      <ProfileSecurityCard
        password={password}
        setPassword={setPassword}
      />

      {mode === "edit" &&
        profileType ===
          "USER" &&
        userId && (

          <ProfileExpertsCard
            userId={userId}
          />

      )}

      {mode === "edit" &&
        userId && (

        <>
          <ProfilePreferencesViewer
            userId={userId}
          />

          <ProfileKeywordsEditor
            userId={userId}
          />

          <ProfileGeographyEditor
            userId={userId}
          />

          <ProfileProfileEditor
            userId={userId}
          />
        </>

      )}

      <FormActions
        saving={saving}
        saveLabel={
          mode === "create"
            ? "Create Profile"
            : "Save Changes"
        }
        onSave={save}
        onCancel={() =>
          router.back()
        }
      />

    </div>

  );

}
