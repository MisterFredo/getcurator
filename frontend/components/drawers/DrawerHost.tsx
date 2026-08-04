// frontend/components/drawers/DrawerHost.tsx

"use client";

import { useDrawer } from "@/contexts/DrawerContext";

import AnalysisDrawerAdmin from "@/components/drawers/AnalysisDrawerAdmin";
import DigestPreviewDrawer from "@/components/drawers/DigestPreviewDrawer";
import KnowledgeDrawer from "@/components/knowledge/KnowledgeDrawer";

/* ========================================================= */

export default function DrawerHost() {

  const {

    rightDrawer,

    closeRightDrawer,

  } = useDrawer();

  return (

    <>

      {/* =================================================== */}
      {/* ANALYSIS */}
      {/* =================================================== */}

      {

        rightDrawer.type === "analysis" &&
        rightDrawer.id && (

          <AnalysisDrawerAdmin

            contentId={rightDrawer.id}

            onClose={closeRightDrawer}

          />

        )

      }

      {/* =================================================== */}
      {/* DIGEST */}
      {/* =================================================== */}

      {

        rightDrawer.type === "digest-preview" &&
        rightDrawer.id && (

          <DigestPreviewDrawer

            digestId={rightDrawer.id}

            onClose={closeRightDrawer}

          />

        )

      }

      {/* =================================================== */}
      {/* KNOWLEDGE */}
      {/* =================================================== */}

      {

        rightDrawer.type === "knowledge" &&
        rightDrawer.id &&
        rightDrawer.entityType && (

          <KnowledgeDrawer

            entityId={rightDrawer.id}

            entityType={rightDrawer.entityType}

            onClose={closeRightDrawer}

          />

        )

      }

    </>

  );

}
