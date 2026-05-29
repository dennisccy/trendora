import { TrendingUp } from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { PageHeading } from "@/components/page-heading";

export default function StocksPage() {
  return (
    <div className="space-y-4">
      <PageHeading title="Stocks" subtitle="Stock Leaderboard — ranked, filterable" />
      <EmptyState
        icon={TrendingUp}
        title="No ranked stocks yet"
        description="The leaderboard will list each stock's Leadership, Entry Quality and Risk scores (A–E bucket + number), setup status and reason once scoring lands. Rows will open a stock's detail page."
      />
    </div>
  );
}
