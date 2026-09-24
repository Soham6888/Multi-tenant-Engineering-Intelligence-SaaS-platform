import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
type Context = { params: Promise<{ action: string }> };

function failure(status: number, code: string, message: string) {
  const id = `req_${crypto.randomUUID().replaceAll("-", "")}`;
  return NextResponse.json(
    { error: { code, message, request_id: id } },
    {
      status,
      headers: { "Cache-Control": "no-store", "X-Request-ID": id },
    },
  );
}

async function proxy(request: NextRequest, context: Context) {
  const { action } = await context.params;
  const method = action === "me" ? "GET" : "POST";
  if (!["register", "login", "logout", "me"].includes(action))
    return failure(404, "RESOURCE_NOT_FOUND", "Route not found");
  if (request.method !== method)
    return failure(405, "METHOD_NOT_ALLOWED", "Method not allowed");
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
    .filter((c) => ["eip_session", "__Host-eip_session"].includes(c.name));
  if (cookies.length)
    headers.set(
      "cookie",
      cookies.map((c) => `${c.name}=${c.value}`).join("; "),
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
    const upstream = await fetch(
      `${process.env.EIP_API_URL || "http://127.0.0.1:8000"}/api/v1/auth/${action}`,
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
    for (const cookie of upstream.headers.getSetCookie())
      outputHeaders.append("set-cookie", cookie);
    return new Response(
      upstream.status === 204 ? null : await upstream.text(),
      { status: upstream.status, headers: outputHeaders },
    );
  } catch {
    return failure(
      503,
      "DEPENDENCY_UNAVAILABLE",
      "Sign-in is temporarily unavailable. Please try again.",
    );
  }
}

export const GET = proxy;
export const POST = proxy;
