import type { LucideIcon } from "lucide-react";

export function AlertBanner({
  icon: Icon,
  title,
  detail,
}: {
  icon: LucideIcon;
  title: string;
  detail?: string;
}) {
  return (
    <div
      role="status"
      className="flex items-start gap-4 rounded-2xl border-2 border-accent/50 bg-accent/15 p-4"
    >
      <Icon aria-hidden="true" className="size-7 text-accent-foreground shrink-0 mt-0.5" />
      <div>
        <p className="font-bold text-lg leading-tight">{title}</p>
        {detail ? <p className="text-base text-foreground/80 mt-1">{detail}</p> : null}
      </div>
    </div>
  );
}
