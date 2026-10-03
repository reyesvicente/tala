import { Alert, Button } from "ice-ds";
import { Mic, Square } from "lucide-react";

import { formatClock } from "@/lib/format";

import { useRecorder } from "../hooks/useRecorder";

interface RecorderPanelProps {
  file: File | null;
  onRecorded: (file: File) => void;
}

export function RecorderPanel({ file, onRecorded }: RecorderPanelProps) {
  const { state, elapsed, error, start, stop } = useRecorder(onRecorded);

  if (state === "unsupported") {
    return <Alert intent="warning" title="Recording isn't supported in this browser. Upload a file instead." />;
  }

  const recording = state === "recording";

  return (
    <div className="flex flex-col items-center gap-4 border-[3px] border-neo-black bg-white px-6 py-8 text-center">
      <div
        className={`font-mono text-5xl font-bold tabular-nums ${recording ? "text-neo-red" : ""}`}
        aria-live="polite"
      >
        {formatClock(elapsed)}
      </div>
      {recording ? (
        <Button type="button" variant="destructive" size="lg" onClick={stop}>
          <Square className="mr-2 h-5 w-5" fill="currentColor" /> Stop recording
        </Button>
      ) : (
        <Button type="button" variant="accent" size="lg" onClick={start}>
          <Mic className="mr-2 h-5 w-5" /> {file ? "Record again" : "Start recording"}
        </Button>
      )}
      {file && !recording && (
        <p className="text-sm">
          Ready: <span className="font-bold">{file.name}</span>
        </p>
      )}
      {error && <Alert intent="error" title={error} />}
    </div>
  );
}
