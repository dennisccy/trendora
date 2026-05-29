import { Star } from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { PageHeading } from "@/components/page-heading";

export default function WatchlistPage() {
  return (
    <div className="space-y-4">
      <PageHeading title="Watchlist" subtitle="Your saved stocks — persisted across restarts" />
      <EmptyState
        icon={Star}
        title="Your watchlist is empty"
        description="Saved stocks will show date added, your reason, their current Leadership / Entry / Risk and setup, price-since-added and an invalidation level — and persist across a backend restart. Adding lands in iter-7."
      />
    </div>
  );
}
