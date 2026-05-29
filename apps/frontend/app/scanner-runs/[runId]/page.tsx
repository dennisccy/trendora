import { History } from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { PageHeading } from "@/components/page-heading";

// Detail-route stub so the route resolves. Reached from a run row (which does not exist
// yet) — intentionally NOT linked from the sidebar nav.
export default async function RunDetailPage({
  params,
}: {
  params: Promise<{ runId: string }>;
}) {
  const { runId } = await params;
  return (
    <div className="space-y-4">
      <PageHeading title={`Run #${runId}`} subtitle="Immutable as-of snapshot" />
      <EmptyState
        icon={History}
        title="Run detail not available yet"
        description="This will show the exact, immutable as-of view for the run — its regime, ranked stocks and their stored scores — once the scanner and snapshot tables land (iter-5)."
      />
    </div>
  );
}
