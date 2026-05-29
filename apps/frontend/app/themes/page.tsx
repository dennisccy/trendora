import { Layers } from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { PageHeading } from "@/components/page-heading";

export default function ThemesPage() {
  return (
    <div className="space-y-4">
      <PageHeading title="Themes" subtitle="Theme Leaderboard — ranked by Theme Score" />
      <EmptyState
        icon={Layers}
        title="No ranked themes yet"
        description="Themes will be ranked by a price-confirmed Theme Score, each showing its member stocks, 1-month and 3-month basket return, breadth and trend label once scoring lands."
      />
    </div>
  );
}
