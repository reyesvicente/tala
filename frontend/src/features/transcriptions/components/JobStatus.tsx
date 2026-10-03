import { Card, CardEyebrow, CardTitle, Progress, Spinner } from "ice-ds";

import { formatDuration } from "@/lib/format";

import type { Transcription } from "../types";

function secondsLeft(job: Transcription): number | null {
  // Wait for a few percent so the estimate isn't wildly off.
  if (!job.started_at || job.progress < 0.03) return null;
  const elapsed = (Date.now() - new Date(job.started_at).getTime()) / 1000;
  return (elapsed / job.progress) * (1 - job.progress);
}

export function JobStatus({ job }: { job: Transcription }) {
  const pending = job.status === "pending";
  const preparing = !pending && job.progress === 0;
  const percent = Math.round(job.progress * 100);
  const remaining = secondsLeft(job);

  const eyebrow = pending ? "In line" : preparing ? "Preparing audio" : "Listening…";
  const message = pending
    ? "Waiting for the transcriber. It works on one file at a time, right here on this server."
    : preparing
      ? "Decoding the audio and finding the parts with speech. Long recordings take a minute here."
      : remaining != null
        ? `${formatDuration(remaining)} left. You can close this tab and come back to this link later.`
        : "Working through your audio. You can close this tab and come back to this link later.";

  return (
    <Card variant="info" elevation="lg" className="space-y-5">
      <div className="flex items-center gap-4">
        <Spinner size="lg" />
        <div className="min-w-0">
          <CardEyebrow>{eyebrow}</CardEyebrow>
          <CardTitle className="break-all">{job.original_filename}</CardTitle>
        </div>
      </div>
      <Progress value={percent} striped showValue={!pending && !preparing} label="Transcribing" />
      <p className="text-sm">{message}</p>
    </Card>
  );
}
