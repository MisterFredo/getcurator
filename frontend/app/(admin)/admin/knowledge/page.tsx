"use client";

import { useState } from "react";

import KnowledgeHeader from "@/components/knowledge/KnowledgeHeader";
import KnowledgeDashboard from "@/components/knowledge/KnowledgeDashboard";
import KnowledgeToolbar from "@/components/knowledge/KnowledgeToolbar";
import KnowledgeExplorer from "@/components/knowledge/KnowledgeExplorer";
import KnowledgeDrawer from "@/components/knowledge/KnowledgeDrawer";

export default function KnowledgePage() {

  const [
    dashboard,
    setDashboard,
  ] = useState<KnowledgeDashboard | null>(
    null,
  );
  
  const [
    explorer,
    setExplorer,
  ] = useState<KnowledgeExplorer | null>(
    null,
  );
  
  const [
    loading,
    setLoading,
  ] = useState(true);
  
  const [
    selectedEntity,
    setSelectedEntity,
  ] =
    useState<KnowledgeEntitySummary | null>(
      null,
    );
  
  const [
    drawerOpen,
    setDrawerOpen,
  ] =
    useState(false);

  return (

    <div className="space-y-8">

      <KnowledgeHeader />

      <KnowledgeDashboard />

      <KnowledgeToolbar />

      <KnowledgeExplorer

        onOpen={(entity) => {

          setSelectedEntity(
            entity,
          );

          setDrawerOpen(
            true,
          );

        }}

      />

      <KnowledgeDrawer

        open={drawerOpen}

        entity={selectedEntity}

        onClose={() =>
          setDrawerOpen(false)
        }

      />

    </div>

  );

}
