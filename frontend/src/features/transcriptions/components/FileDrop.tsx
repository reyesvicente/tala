import { cn } from "ice-ds";
import { FileAudio, Upload } from "lucide-react";
import { useRef, useState, type DragEvent } from "react";

import { formatBytes } from "@/lib/format";

interface FileDropProps {
  file: File | null;
  onFile: (file: File) => void;
  maxMb?: number;
}

export function FileDrop({ file, onFile, maxMb }: FileDropProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const handleDrop = (event: DragEvent<HTMLButtonElement>) => {
    event.preventDefault();
    setDragging(false);
    const dropped = event.dataTransfer.files[0];
    if (dropped) onFile(dropped);
  };

  return (
    <>
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        className={cn(
          "flex w-full flex-col items-center justify-center gap-3 border-[3px] border-dashed border-neo-black px-6 py-10 text-center transition-colors",
          dragging ? "bg-neo-yellow" : file ? "bg-neo-green/30" : "bg-white hover:bg-neo-yellow/40",
        )}
      >
        {file ? <FileAudio className="h-10 w-10" strokeWidth={2.5} /> : <Upload className="h-10 w-10" strokeWidth={2.5} />}
        {file ? (
          <span>
            <span className="block break-all font-display text-lg font-bold">{file.name}</span>
            <span className="text-sm">{formatBytes(file.size)} · click to swap</span>
          </span>
        ) : (
          <span>
            <span className="block font-display text-lg font-bold">Drop audio or video here</span>
            <span className="text-sm">
              or click to browse · mp3, m4a, wav, ogg, webm, mp4…{maxMb ? ` up to ${maxMb} MB` : ""}
            </span>
          </span>
        )}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="audio/*,video/*"
        className="hidden"
        onChange={(event) => {
          const picked = event.target.files?.[0];
          if (picked) onFile(picked);
          event.target.value = "";
        }}
      />
    </>
  );
}
