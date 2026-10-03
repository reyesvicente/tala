export function formatClock(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  const mm = String(m).padStart(h ? 2 : 1, "0");
  const ss = String(sec).padStart(2, "0");
  return h ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function timeUntil(iso: string): string {
  const hours = Math.round((new Date(iso).getTime() - Date.now()) / 3_600_000);
  if (hours <= 1) return "within the hour";
  if (hours < 48) return `in ${hours} hours`;
  return `in ${Math.round(hours / 24)} days`;
}

export function formatDuration(seconds: number): string {
  const minutes = Math.round(seconds / 60);
  if (minutes < 1) return "less than a minute";
  if (minutes === 1) return "about a minute";
  if (minutes < 60) return `about ${minutes} minutes`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return `about ${hours}h ${String(rest).padStart(2, "0")}m`;
}
