/** 统一 API 请求封装，支持 JWT Bearer token 注入和自动刷新 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "https://saizhitong-agent2.onrender.com";

function buildUrl(path: string) {
  return `${BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

export function apiUrl(path: string) {
  return buildUrl(path);
}

// Token provider — set by AuthContext
let tokenProvider: (() => string | null) | null = null;
export function setTokenProvider(provider: () => string | null) {
  tokenProvider = provider;
}

// Refresh callback — set by AuthContext
let refreshCallback: (() => Promise<string | null>) | null = null;
export function setRefreshCallback(cb: () => Promise<string | null>) {
  refreshCallback = cb;
}

export interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
  headers?: Record<string, string>;
  body?: unknown;
  timeout?: number;
}

export async function request<T = unknown>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", headers = {}, body, timeout = 120000 } = options;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);

  const doFetch = async (): Promise<Response> => {
    const authHeaders: Record<string, string> = {};
    const token = tokenProvider?.();
    if (token) {
      authHeaders["Authorization"] = `Bearer ${token}`;
    }

    return fetch(buildUrl(path), {
      method,
      headers: {
        "Content-Type": "application/json",
        ...authHeaders,
        ...headers,
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
  };

  try {
    // 记录本次请求是否携带了 token —— 未认证的 401 不应清空登录态
    let sentToken = !!tokenProvider?.();

    let response = await doFetch();

    // 仅在请求携带了 token 且收到 401 时才尝试刷新（token 可能过期）
    if (response.status === 401 && sentToken && refreshCallback) {
      const newToken = await refreshCallback();
      if (newToken) {
        sentToken = true;
        response = await doFetch();
      }
    }

    const text = await response.text();
    if (!response.ok) {
      // 仅当本次请求携带了 token 且仍返回 401 时，才认为登录态失效
      if (response.status === 401 && sentToken) {
        localStorage.removeItem("saizhitong_refresh_token");
        localStorage.removeItem("saizhitong_user");
      }
      let detail = text;
      try {
        const parsed = JSON.parse(text);
        detail = parsed.detail || text;
      } catch {
        // not JSON, use raw text
      }
      throw new Error(detail);
    }

    return text ? (JSON.parse(text) as T) : ({} as T);
  } finally {
    clearTimeout(timer);
  }
}
