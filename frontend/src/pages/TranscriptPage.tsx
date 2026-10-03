import { Alert, Button, Skeleton } from "ice-ds";
import { useEffect } from "react";
import { Link, useParams } from "react-router-dom";

import { useTranscription } from "@/features/transcriptions/api";
import { JobStatus } from "@/features/transcriptions/components/JobStatus";
import { TranscriptView } from "@/features/transcriptions/components/TranscriptView";
import { useRecentStore } from "@/features/transcriptions/store";
import { ApiError, isTransient } from "@/lib/api";

export default function TranscriptPage() {
  const { slug = "" } = useParams();
  const { data: job, error, isPending } = useTranscription(slug);
  const removeRecent = useRecentStore((state) => state.remove);
  const notFound = error instanceof ApiError && error.status === 404;

  useEffect(() => {
    if (notFound) removeRecent(slug);
  }, [notFound, removeRecent, slug]);

  if (isPending) return <Skeleton className="h-64 w-full" />;

  const inProgress = job && (job.status === "pending" || job.status === "processing");
  if (error && inProgress && isTransient(error)) {
    // The server is probably restarting (e.g. a deploy). The job is safe on disk and resumes.
    return (
      <div className="space-y-4">
        <Alert intent="warning" title="Reconnecting…">
          The server is restarting. Your file is safe and transcription will continue. This page updates by itself.
        </Alert>
        <JobStatus job={job} />
      </div>
    );
  }

  if (error && (!job || notFound)) {
    return (
      <div className="space-y-6">
        <Alert intent={notFound ? "warning" : "error"} title={error.message} />
        <Link to="/">
          <Button type="button">Transcribe something</Button>
        </Link>
      </div>
    );
  }

  if (job.status === "failed") {
    return (
      <div className="space-y-6">
        <Alert intent="error" title="That one didn't work">
          {job.error}
        </Alert>
        <Link to="/">
          <Button type="button">Try another file</Button>
        </Link>
      </div>
    );
  }

  return job.status === "done" ? <TranscriptView job={job} /> : <JobStatus job={job} />;
}
