"use client";

import { useState } from "react";

import KnowledgeHeader from "@/components/knowledge/KnowledgeHeader";
import KnowledgeDashboard from "@/components/knowledge/KnowledgeDashboard";
import KnowledgeToolbar from "@/components/knowledge/KnowledgeToolbar";
import KnowledgeExplorer from "@/components/knowledge/KnowledgeExplorer";
import KnowledgeDrawer from "@/components/knowledge/KnowledgeDrawer";

export default function KnowledgePage() {

  const [
    selectedEntity,
    setSelectedEntity,
  ] = useState(null);

  const [
    drawerOpen,
    setDrawerOpen,
  ] = useState(false);

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
