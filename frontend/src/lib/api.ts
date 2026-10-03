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

/** Server restarting/deploying or the network blipped: worth waiting and retrying. */
export function isTransient(error: unknown): boolean {
  return error instanceof ApiError && (error.status === 0 || error.status >= 500);
}

async function request(input: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(input, init);
  } catch {
    throw new ApiError("Can't reach the server. Check your connection.", 0);
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
  get: async <T>(path: string) => parse<T>(await request(`/api${path}`)),
  delete: async <T>(path: string) => parse<T>(await request(`/api${path}`, { method: "DELETE" })),
  postJson: async <T>(path: string, body?: unknown) =>
    parse<T>(
      await request(`/api${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: body === undefined ? undefined : JSON.stringify(body),
      }),
    ),
  postForm: async <T>(path: string, form: FormData) =>
    parse<T>(await request(`/api${path}`, { method: "POST", body: form })),
};

export const exportUrl = (slug: string, format: "txt" | "srt" | "vtt") =>
  `/api/transcriptions/${encodeURIComponent(slug)}/export/${format}`;
