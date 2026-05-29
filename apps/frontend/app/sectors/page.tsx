import { Grid2x2 } from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { PageHeading } from "@/components/page-heading";

export default function SectorsPage() {
  return (
    <div className="space-y-4">
      <PageHeading title="Sectors" subtitle="Sector / industry Leaderboard — ranked by Sector Score" />
      <EmptyState
        icon={Grid2x2}
        title="No ranked sectors yet"
        description="Sector and industry ETFs will be ranked by Sector Score, each with RS-vs-SPY, distance from 52-week high and a trend label once scoring lands (iter-2)."
      />
    </div>
  );
}
