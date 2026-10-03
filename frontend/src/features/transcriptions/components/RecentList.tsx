import { Card, CardEyebrow } from "ice-ds";
import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

import { timeUntil } from "@/lib/format";

import { useRecentStore } from "../store";

export function RecentList() {
  const items = useRecentStore((state) => state.items);
  if (!items.length) return null;

  return (
    <Card elevation="md" className="bg-white">
      <CardEyebrow className="mb-3">Made in this browser</CardEyebrow>
      <ul className="divide-y-2 divide-neo-black">
        {items.map((item) => (
          <li key={item.slug}>
            <Link
              to={`/t/${item.slug}`}
              className="flex items-center justify-between gap-4 py-3 hover:bg-neo-yellow/40"
            >
              <span className="min-w-0">
                <span className="block truncate font-bold">{item.filename}</span>
                <span className="text-sm">expires {timeUntil(item.expiresAt)}</span>
              </span>
              <ArrowRight className="h-5 w-5 shrink-0" />
            </Link>
          </li>
        ))}
      </ul>
    </Card>
  );
}
