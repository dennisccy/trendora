import { LayoutDashboard } from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { PageHeading } from "@/components/page-heading";

export default function DashboardPage() {
  return (
    <div className="space-y-4">
      <PageHeading title="Dashboard" subtitle="The daily snapshot at a glance" />
      <EmptyState
        icon={LayoutDashboard}
        title="No scan yet"
        description="Market regime, top sectors and themes, candidate counts and market breadth will appear here once the scanner runs (arriving in iter-2+). The backend is up and serving the committed offline seed today."
      />
    </div>
  );
}
