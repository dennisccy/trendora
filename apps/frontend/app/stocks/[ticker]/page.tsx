import { LineChart } from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { PageHeading } from "@/components/page-heading";

// Detail-route stub so the route resolves. Reached from a leaderboard row (which does not
// exist yet) — intentionally NOT linked from the sidebar nav.
export default async function StockDetailPage({
  params,
}: {
  params: Promise<{ ticker: string }>;
}) {
  const { ticker } = await params;
  return (
    <div className="space-y-4">
      <PageHeading title={ticker.toUpperCase()} subtitle="Stock detail" />
      <EmptyState
        icon={LineChart}
        title="Detail not available yet"
        description="A price + moving-average chart, the three explainable score breakdowns, theme membership, setup status, reason and invalidation note will appear here once scoring and the scanner land."
      />
    </div>
  );
}
