const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function fetchJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });

  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const message =
      typeof payload === "object" && payload !== null && "detail" in payload
        ? String((payload as { detail?: string }).detail)
        : "Request failed";

    throw new Error(message);
  }

  return payload as T;
}

export function getBackendHealth() {
  return fetchJson<{ message: string }>("/");
}

export function loginUser(email: string, password: string) {
  return fetchJson<{ access_token: string; token_type: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function registerUser(name: string, email: string, password: string) {
  return fetchJson<{ id: string; name: string; email: string; is_active: boolean; created_at: string }>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ name, email, password }),
  });
}
