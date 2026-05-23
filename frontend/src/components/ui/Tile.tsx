import * as React from "react";
import { Link } from "@tanstack/react-router";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

type TileProps = {
  to: string;
  label: string;
  icon: LucideIcon;
  description?: string;
  tone?: "primary" | "accent" | "info" | "success";
};

const toneClasses: Record<NonNullable<TileProps["tone"]>, string> = {
  primary: "bg-primary text-primary-foreground",
  accent: "bg-accent text-accent-foreground",
  info: "bg-info text-info-foreground",
  success: "bg-success text-success-foreground",
};

export function Tile({ to, label, icon: Icon, description, tone = "primary" }: TileProps) {
  return (
    <Link
      to={to}
      aria-label={label}
      className={cn(
        "group relative flex flex-col justify-between rounded-3xl p-6 min-h-36 shadow-sm hover:shadow-md transition",
        toneClasses[tone],
      )}
    >
      <Icon aria-hidden="true" className="size-10" strokeWidth={2.25} />
      <div>
        <p className="text-xl font-bold leading-tight">{label}</p>
        {description ? (
          <p className="text-sm opacity-90 mt-1">{description}</p>
        ) : null}
      </div>
    </Link>
  );
}
