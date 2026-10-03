import {
  Badge,
  Button,
  buttonVariants,
  Card,
  CardEyebrow,
  CardTitle,
  Modal,
  ModalClose,
  ModalContent,
  ModalDescription,
  ModalFooter,
  ModalHeader,
  ModalTitle,
  ModalTrigger,
  Switch,
} from "ice-ds";
import { Check, Copy, Download, Trash2 } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { exportUrl } from "@/lib/api";
import { formatClock, timeUntil } from "@/lib/format";

import { useDeleteTranscription, useServiceInfo } from "../api";
import { useRecentStore } from "../store";
import type { Transcription } from "../types";

const FORMATS = [
  { format: "txt", label: "Text" },
  { format: "srt", label: "SRT subtitles" },
  { format: "vtt", label: "WebVTT" },
] as const;

export function TranscriptView({ job }: { job: Transcription }) {
  const navigate = useNavigate();
  const removeRecent = useRecentStore((state) => state.remove);
  const { data: info } = useServiceInfo();
  const deleteTranscription = useDeleteTranscription();
  const [showTimestamps, setShowTimestamps] = useState(false);
  const [copied, setCopied] = useState(false);

  const languageName = job.detected_language
    ? (info?.languages[job.detected_language] ?? job.detected_language.toUpperCase())
    : null;

  const copy = async () => {
    await navigator.clipboard.writeText(job.text ?? "");
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  };

  const remove = () =>
    deleteTranscription.mutate(job.slug, {
      onSuccess: () => {
        removeRecent(job.slug);
        navigate("/");
      },
    });

  return (
    <div className="space-y-6">
      <Card variant="success" elevation="lg" className="space-y-4">
        <div>
          <CardEyebrow>Done</CardEyebrow>
          <CardTitle className="break-all">{job.original_filename}</CardTitle>
        </div>
        <div className="flex flex-wrap gap-2">
          {languageName && <Badge>{languageName}</Badge>}
          {job.task === "translate" && <Badge variant="premium">Translated to English</Badge>}
          {job.duration_seconds != null && <Badge variant="info">{formatClock(job.duration_seconds)} long</Badge>}
          {job.model_name && <Badge variant="new">whisper-{job.model_name}</Badge>}
        </div>
        <p className="text-sm">
          Anyone with this link can read it. It deletes itself {timeUntil(job.expires_at)}; the audio is already gone.
        </p>
      </Card>

      <div className="flex flex-wrap items-center gap-3">
        <Button type="button" onClick={copy} disabled={!job.text}>
          {copied ? <Check className="mr-2 h-4 w-4" /> : <Copy className="mr-2 h-4 w-4" />}
          {copied ? "Copied!" : "Copy text"}
        </Button>
        {FORMATS.map(({ format, label }) => (
          <a key={format} href={exportUrl(job.slug, format)} className={buttonVariants({ variant: "secondary" })}>
            <Download className="mr-2 h-4 w-4" /> {label}
          </a>
        ))}
        <Modal>
          <ModalTrigger asChild>
            <Button type="button" variant="ghost" className="ml-auto">
              <Trash2 className="mr-2 h-4 w-4" /> Delete now
            </Button>
          </ModalTrigger>
          <ModalContent>
            <ModalHeader>
              <ModalTitle>Delete this transcript?</ModalTitle>
              <ModalDescription>The link stops working for everyone. This can't be undone.</ModalDescription>
            </ModalHeader>
            <ModalFooter>
              <ModalClose asChild>
                <Button type="button" variant="secondary">
                  Keep it
                </Button>
              </ModalClose>
              <Button type="button" variant="destructive" loading={deleteTranscription.isPending} onClick={remove}>
                Delete
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </div>

      <Card elevation="md" className="min-w-0 bg-white">
        <div className="mb-4 flex items-center justify-between gap-4 border-b-[3px] border-neo-black pb-4">
          <h2 className="text-2xl">Transcript</h2>
          <Switch label="Timestamps" checked={showTimestamps} onCheckedChange={setShowTimestamps} />
        </div>
        {!job.text ? (
          <p className="italic">No speech found in this audio.</p>
        ) : showTimestamps ? (
          <ol className="space-y-2">
            {job.segments?.map((segment, index) => (
              <li key={index} className="grid grid-cols-[4.5rem_1fr] gap-3">
                <span className="font-mono text-sm leading-7 text-neo-black/60">{formatClock(segment.start)}</span>
                <span className="min-w-0 text-lg leading-7 [overflow-wrap:anywhere]">{segment.text}</span>
              </li>
            ))}
          </ol>
        ) : (
          <div className="whitespace-pre-wrap text-lg leading-8 [overflow-wrap:anywhere]">{job.text}</div>
        )}
      </Card>
    </div>
  );
}
