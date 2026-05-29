import { Activity } from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { PageHeading } from "@/components/page-heading";

export default function SystemHealthPage() {
  return (
    <div className="space-y-4">
      <PageHeading title="System Health" subtitle="Forward-tested evidence — does the ranking work?" />
      <EmptyState
        icon={Activity}
        title="No evidence yet"
        description="Walk-forward forward returns by score bucket, setup and regime, excess vs SPY/QQQ/sector, and random same-sector control groups (with sample sizes and honest limitations) appear here once the forward-testing engine lands (iter-6)."
      />
    </div>
  );
}
