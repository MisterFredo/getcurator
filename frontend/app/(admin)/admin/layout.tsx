import AdminShell from "./AdminShell";

import {
  DrawerProvider,
} from "@/contexts/DrawerContext";

import DrawerHost from "@/components/drawers/DrawerHost";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <DrawerProvider>

      <AdminShell>
        {children}
      </AdminShell>

      <DrawerHost />

    </DrawerProvider>
  );
}
