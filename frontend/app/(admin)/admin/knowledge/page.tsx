// frontend/app/(admin)/admin/knowledge/page.tsx

"use client";

import {
  useEffect,
  useState,
} from "react";

import KnowledgeHeader from "@/components/knowledge/KnowledgeHeader";
import KnowledgeDashboard from "@/components/knowledge/KnowledgeDashboard";
import KnowledgeToolbar from "@/components/knowledge/KnowledgeToolbar";
import KnowledgeExplorer from "@/components/knowledge/KnowledgeExplorer";

import {
  getKnowledgeDashboard,
  getKnowledgeExplorer,
} from "@/lib/knowledge";

import type {
  KnowledgeDashboard as Dashboard,
  KnowledgeExplorer as Explorer,
} from "@/types/knowledge";

/* ========================================================= */

export default function KnowledgePage() {

  const [
    dashboard,
    setDashboard,
  ] =
    useState<Dashboard | null>(
      null,
    );

  const [
    explorer,
    setExplorer,
  ] =
    useState<Explorer | null>(
      null,
    );

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  /* =======================================================
     LOAD
  ======================================================= */

  useEffect(() => {

    async function load() {

      try {

        const [

          dashboard,

          explorer,

        ] = await Promise.all([

          getKnowledgeDashboard(),

          getKnowledgeExplorer(),

        ]);

        setDashboard(
          dashboard,
        );

        setExplorer(
          explorer,
        );

      } catch (e) {

        console.error(e);

        alert(
          "Unable to load Knowledge Cockpit.",
        );

      } finally {

        setLoading(
          false,
        );

      }

    }

    load();

  }, []);

  /* =======================================================
     RENDER
  ======================================================= */

  if (loading) {

    return (
      <div>
        Loading...
      </div>
    );

  }

  return (

    <div className="space-y-8">

      <KnowledgeHeader />

      {

        dashboard && (

          <KnowledgeDashboard

            dashboard={dashboard}

          />

        )

      }

      <KnowledgeToolbar />

      {

        explorer && (

          <KnowledgeExplorer

            entities={
              explorer.entities
            }

          />

        )

      }

    </div>

  );

}
