import { useCallback, useEffect, useRef, useState } from "react";

type RecorderState = "idle" | "recording" | "unsupported";

const MIN_SECONDS = 1.5;
const MIN_BYTES = 2048;

const MIME_CANDIDATES = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg;codecs=opus"];

function pickMimeType(): string | undefined {
  if (typeof MediaRecorder === "undefined") return undefined;
  return MIME_CANDIDATES.find((type) => MediaRecorder.isTypeSupported(type));
}

function extensionFor(mime: string): string {
  if (mime.includes("mp4")) return "m4a";
  if (mime.includes("ogg")) return "ogg";
  return "webm";
}

/** Records from the microphone and hands back a File ready to upload. */
export function useRecorder(onRecorded: (file: File) => void) {
  const supported = typeof navigator !== "undefined" && !!navigator.mediaDevices?.getUserMedia && !!pickMimeType();
  const [state, setState] = useState<RecorderState>(supported ? "idle" : "unsupported");
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<number | null>(null);
  const onRecordedRef = useRef(onRecorded);
  onRecordedRef.current = onRecorded;

  const cleanup = useCallback(() => {
    if (timerRef.current) window.clearInterval(timerRef.current);
    timerRef.current = null;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }, []);

  useEffect(() => cleanup, [cleanup]);

  const start = useCallback(async () => {
    setError(null);
    const mimeType = pickMimeType();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      const chunks: Blob[] = [];
      recorder.ondataavailable = (event) => event.data.size && chunks.push(event.data);
      recorder.onstop = () => {
        cleanup();
        setState("idle");
        const seconds = (Date.now() - startedAt) / 1000;
        const size = chunks.reduce((total, chunk) => total + chunk.size, 0);
        if (seconds < MIN_SECONDS || size < MIN_BYTES) {
          setError("That recording was too short or empty. Record for at least a couple of seconds.");
          return;
        }
        const type = recorder.mimeType || mimeType || "audio/webm";
        const stamp = new Date().toISOString().slice(0, 16).replace(/[:T]/g, "-");
        const file = new File(chunks, `recording-${stamp}.${extensionFor(type)}`, { type: type.split(";")[0] });
        onRecordedRef.current(file);
      };
      recorderRef.current = recorder;
      const startedAt = Date.now();
      recorder.start(1000);
      setElapsed(0);
      timerRef.current = window.setInterval(() => setElapsed((Date.now() - startedAt) / 1000), 250);
      setState("recording");
    } catch (err) {
      cleanup();
      setError(
        err instanceof DOMException && err.name === "NotAllowedError"
          ? "Microphone access was blocked. Allow it in your browser's site settings and try again."
          : "Couldn't start the microphone.",
      );
    }
  }, [cleanup]);

  const stop = useCallback(() => {
    if (recorderRef.current?.state === "recording") recorderRef.current.stop();
  }, []);

  return { state, elapsed, error, start, stop };
}
