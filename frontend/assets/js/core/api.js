import { API_BASE_URL } from "./config.js";
import { clearSession, getSession } from "./storage.js";

export class ApiError extends Error {
  constructor(status, message, payload = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

function extractErrorMessage(payload) {
  if (!payload) return "Request failed";

  if (payload.error && payload.error.message) return payload.error.message;
  if (typeof payload.detail === "string") return payload.detail;
  if (Array.isArray(payload.detail) && payload.detail.length) {
    return payload.detail[0].msg || "Validation failed";
  }
  return payload.message || "Request failed";
}

export async function apiRequest(path, options = {}) {
  const {
    method = "GET",
    body,
    form = false,
    auth = true,
    headers = {},
    tokenOverride,
  } = options;

  const finalHeaders = { ...headers };
  let payload;

  if (body !== undefined) {
    if (form) {
      payload = new URLSearchParams(body).toString();
      finalHeaders["Content-Type"] = "application/x-www-form-urlencoded";
    } else {
      payload = JSON.stringify(body);
      finalHeaders["Content-Type"] = "application/json";
    }
  }

  if (auth) {
    const session = getSession();
    const token = tokenOverride || session?.token;
    if (!token) {
      throw new ApiError(401, "Not authenticated");
    }
    finalHeaders.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: finalHeaders,
    body: payload,
  });

  let responsePayload = null;
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    responsePayload = await response.json();
  } else {
    const text = await response.text();
    responsePayload = text ? { message: text } : null;
  }

  if (!response.ok) {
    if (response.status === 401 && auth) {
      clearSession();
    }
    throw new ApiError(response.status, extractErrorMessage(responsePayload), responsePayload);
  }

  return responsePayload;
}
