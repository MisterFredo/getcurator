"use client";

import { useDrawer } from "@/contexts/DrawerContext";

// DRAWERS
import AnalysisDrawerAdmin from "@/components/drawers/AnalysisDrawerAdmin";

/* =========================================================
   HOST — RENDU CENTRALISÉ DES DRAWERS
========================================================= */

export default function DrawerHost() {
  const {
    leftDrawer,
    rightDrawer,
    closeLeftDrawer,
    closeRightDrawer,
  } = useDrawer();

  return (
    <>
      
      {/* =========================================
          DRAWER DROITE — ANALYSIS (ADMIN)
      ========================================= */}
      {rightDrawer.type === "analysis" && rightDrawer.id && (
        <AnalysisDrawerAdmin
          contentId={rightDrawer.id}
          onClose={closeRightDrawer}
        />
      )}
    </>
  );
}
