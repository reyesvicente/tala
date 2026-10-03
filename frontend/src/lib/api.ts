export interface Envelope<T> {
  data: T | null;
  message: string;
  errors: unknown;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly errors: unknown = null,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function parse<T>(res: Response): Promise<T> {
  let body: Envelope<T> | null = null;
  try {
    body = (await res.json()) as Envelope<T>;
  } catch {
    // non-JSON (e.g. proxy error page)
  }
  if (!res.ok) {
    throw new ApiError(body?.message || `Request failed (${res.status})`, res.status, body?.errors);
  }
  return body?.data as T;
}

export const api = {
  get: async <T>(path: string) => parse<T>(await fetch(`/api${path}`)),
  delete: async <T>(path: string) => parse<T>(await fetch(`/api${path}`, { method: "DELETE" })),
  postForm: async <T>(path: string, form: FormData) =>
    parse<T>(await fetch(`/api${path}`, { method: "POST", body: form })),
};

export const exportUrl = (slug: string, format: "txt" | "srt" | "vtt") =>
  `/api/transcriptions/${encodeURIComponent(slug)}/export/${format}`;
