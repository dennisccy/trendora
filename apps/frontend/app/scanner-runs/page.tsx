import { History } from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { PageHeading } from "@/components/page-heading";

export default function ScannerRunsPage() {
  return (
    <div className="space-y-4">
      <PageHeading title="Scanner Runs" subtitle="History of immutable scan snapshots" />
      <EmptyState
        icon={History}
        title="No scanner runs yet"
        description="Each daily scan is saved as an immutable, dated snapshot you can open to see exactly what the scanner said on that date. Runs appear here once the scanner lands (iter-5)."
      />
    </div>
  );
}
