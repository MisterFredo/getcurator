"use client";

import { useDrawer } from "@/contexts/DrawerContext";

import AnalysisDrawerAdmin from "@/components/drawers/AnalysisDrawerAdmin";
import DigestPreviewDrawer from "@/components/drawers/DigestPreviewDrawer";

/* ========================================================= */

export default function DrawerHost() {

  const {
    rightDrawer,
    closeRightDrawer,
  } = useDrawer();

  return (
    <>
      {rightDrawer.type === "analysis" &&
        rightDrawer.id && (
          <AnalysisDrawerAdmin
            contentId={rightDrawer.id}
            onClose={closeRightDrawer}
          />
      )}

      {rightDrawer.type === "digest-preview" &&
        rightDrawer.id && (
          <DigestPreviewDrawer
            digestId={rightDrawer.id}
            onClose={closeRightDrawer}
          />
      )}
    </>
  );

}
