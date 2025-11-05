import { NextResponse } from "next/server";

const DEFAULT_DATA_COLLECTOR_URL =
  process.env.DATA_COLLECTOR_URL ||
  process.env.NEXT_PUBLIC_DATA_COLLECTOR_URL ||
  "http://localhost:8005";

const DEFAULT_CUSTOMER_ID =
  process.env.DEFAULT_CUSTOMER_ID ||
  process.env.NEXT_PUBLIC_DEFAULT_CUSTOMER_ID ||
  "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11";

const jsonHeaders = { "Content-Type": "application/json" };

function buildCollectorUrl(path: string) {
  return new URL(path, DEFAULT_DATA_COLLECTOR_URL);
}

export async function GET(request: Request) {
  const requestUrl = new URL(request.url);
  const customerId = requestUrl.searchParams.get("customer_id") || DEFAULT_CUSTOMER_ID;

  try {
    const statusUrl = buildCollectorUrl("/api/v1/collectors/status");
    if (customerId) {
      statusUrl.searchParams.set("customer_id", customerId);
    }

    const response = await fetch(statusUrl.toString(), {
      cache: "no-store",
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        {
          success: false,
          error: data?.detail || "Failed to retrieve collector status.",
        },
        { status: response.status },
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Failed to reach data-collector service:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Unable to contact data-collector service.",
      },
      { status: 502 },
    );
  }
}

export async function POST(request: Request) {
  try {
    const payload = await request.json();

    const response = await fetch(buildCollectorUrl("/api/v1/credentials").toString(), {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    });

    // Some FastAPI errors return plain text, handle gracefully.
    let data: unknown;
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      data = await response.json();
    } else {
      data = { message: await response.text() };
    }

    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error("Failed to configure provider credentials:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Unable to configure provider credentials.",
      },
      { status: 502 },
    );
  }
}
