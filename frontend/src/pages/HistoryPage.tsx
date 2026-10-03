import { Badge, Button, Card, EmptyState, Input, Skeleton } from "ice-ds";
import { ArrowRight, FileAudio } from "lucide-react";
import { useDeferredValue, useState } from "react";
import { Link } from "react-router-dom";

import { useHistory, useServiceInfo } from "@/features/transcriptions/api";
import type { TranscriptionStatus } from "@/features/transcriptions/types";
import { formatClock, timeUntil } from "@/lib/format";

const STATUS_BADGE: Record<TranscriptionStatus, { label: string; variant: "success" | "info" | "warning" | "error" }> = {
  done: { label: "Done", variant: "success" },
  processing: { label: "Working", variant: "info" },
  pending: { label: "In line", variant: "warning" },
  failed: { label: "Failed", variant: "error" },
};

export default function HistoryPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const query = useDeferredValue(search.trim());
  const { data, isPending, isError, error } = useHistory(page, query);
  const { data: info } = useServiceInfo();
  const days = info ? Math.round(info.retention_hours / 24) : 3;
  const pages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-4xl sm:text-5xl">My transcripts</h1>
        <p>Transcripts made while you were logged in. Each one still deletes itself after {days} days.</p>
      </header>

      <Input
        type="search"
        placeholder="Search by file name…"
        value={search}
        onChange={(event) => {
          setSearch(event.target.value);
          setPage(1);
        }}
        aria-label="Search transcripts"
      />

      {isPending ? (
        <Skeleton className="h-48 w-full" />
      ) : isError ? (
        <p role="alert">{error.message}</p>
      ) : data.items.length === 0 ? (
        <EmptyState
          icon={<FileAudio className="h-10 w-10" />}
          title={query ? "No matches" : "Nothing here yet"}
          description={query ? "Try a different file name." : "Transcribe something and it shows up here."}
          action={
            <Link to="/">
              <Button type="button">Transcribe a file</Button>
            </Link>
          }
        />
      ) : (
        <Card elevation="md" className="bg-white">
          <ul className="divide-y-2 divide-neo-black">
            {data.items.map((item) => {
              const badge = STATUS_BADGE[item.status];
              return (
                <li key={item.slug}>
                  <Link to={`/t/${item.slug}`} className="flex items-center gap-4 py-3 hover:bg-neo-yellow/40">
                    <span className="min-w-0 flex-1">
                      <span className="block truncate font-bold">{item.original_filename}</span>
                      <span className="text-sm">
                        {new Date(item.created_at).toLocaleString()}
                        {item.duration_seconds != null && ` · ${formatClock(item.duration_seconds)}`} · expires{" "}
                        {timeUntil(item.expires_at)}
                      </span>
                    </span>
                    <Badge variant={badge.variant}>{badge.label}</Badge>
                    <ArrowRight className="h-5 w-5 shrink-0" />
                  </Link>
                </li>
              );
            })}
          </ul>
        </Card>
      )}

      {data && pages > 1 && (
        <div className="flex items-center justify-between">
          <Button type="button" variant="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>
            Previous
          </Button>
          <span className="text-sm">
            Page {page} of {pages}
          </span>
          <Button type="button" variant="secondary" disabled={page >= pages} onClick={() => setPage(page + 1)}>
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
