import type { LucideIcon } from "lucide-react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function EmptyState({
  title,
  description,
  icon: Icon,
  className,
}: {
  title: string;
  description: string;
  icon?: LucideIcon;
  className?: string;
}) {
  return (
    <Card
      className={cn(
        "flex flex-col items-center justify-center gap-3 border-dashed border-border-strong bg-surface py-16 text-center",
        className,
      )}
    >
      {Icon ? <Icon className="h-8 w-8 text-text-faint" aria-hidden /> : null}
      <div className="space-y-1">
        <h3 className="text-sm font-medium text-text">{title}</h3>
        <p className="mx-auto max-w-md text-sm text-text-muted">{description}</p>
      </div>
    </Card>
  );
}
