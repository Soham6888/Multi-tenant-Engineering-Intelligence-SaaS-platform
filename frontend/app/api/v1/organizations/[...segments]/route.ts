import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
type Context = { params: Promise<{ segments: string[] }> };

function failure(status: number, code: string, message: string) {
  const id = `req_${crypto.randomUUID().replaceAll("-", "")}`;
  return NextResponse.json(
    { error: { code, message, request_id: id } },
    { status, headers: { "Cache-Control": "no-store", "X-Request-ID": id } },
  );
}

function allowed(segments: string[], method: string) {
  const uuid = /^[0-9a-f-]{36}$/i;
  if (segments.length === 0) return ["GET", "POST"].includes(method);
  if (segments.join("/") === "invitations/accept") return method === "POST";
  if (!uuid.test(segments[0])) return false;
  if (segments.length === 1) return method === "GET";
  if (segments.length === 2 && segments[1] === "members")
    return method === "GET";
  if (segments.length === 2 && segments[1] === "invitations")
    return method === "POST";
  return (
    segments.length === 3 &&
    segments[1] === "members" &&
    uuid.test(segments[2]) &&
    ["PATCH", "DELETE"].includes(method)
  );
}

async function proxy(request: NextRequest, context: Context) {
  const { segments } = await context.params;
  const method = request.method;
  if (!allowed(segments, method))
    return failure(404, "RESOURCE_NOT_FOUND", "Route not found");
  const headers = new Headers();
  for (const name of [
    "origin",
    "content-type",
    "x-eip-request",
    "x-csrf-token",
  ]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  const cookies = request.cookies
    .getAll()
    .filter((cookie) =>
      ["eip_session", "__Host-eip_session"].includes(cookie.name),
    );
  if (cookies.length)
    headers.set(
      "cookie",
      cookies.map((cookie) => `${cookie.name}=${cookie.value}`).join("; "),
    );
  let body: Uint8Array | undefined;
  if (request.body) {
    const reader = request.body.getReader();
    const chunks: Uint8Array[] = [];
    let total = 0;
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      total += value.byteLength;
      if (total > 16384) {
        await reader.cancel();
        return failure(413, "PAYLOAD_TOO_LARGE", "Request is too large");
      }
      chunks.push(value);
    }
    body = new Uint8Array(total);
    let offset = 0;
    for (const chunk of chunks) {
      body.set(chunk, offset);
      offset += chunk.byteLength;
    }
  }
  try {
    const path = segments.map(encodeURIComponent).join("/");
    const upstream = await fetch(
      `${process.env.EIP_API_URL || "http://127.0.0.1:8000"}/api/v1/organizations${path ? `/${path}` : ""}`,
      {
        method,
        headers,
        body: body as BodyInit | undefined,
        cache: "no-store",
        redirect: "error",
        signal: AbortSignal.timeout(10000),
      },
    );
    const outputHeaders = new Headers({ "Cache-Control": "no-store" });
    for (const name of ["content-type", "x-request-id", "retry-after"]) {
      const value = upstream.headers.get(name);
      if (value) outputHeaders.set(name, value);
    }
    return new Response(
      upstream.status === 204 ? null : await upstream.text(),
      { status: upstream.status, headers: outputHeaders },
    );
  } catch {
    return failure(
      503,
      "DEPENDENCY_UNAVAILABLE",
      "Organization service is unavailable.",
    );
  }
}

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
