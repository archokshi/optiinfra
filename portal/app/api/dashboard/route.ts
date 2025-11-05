import { NextRequest, NextResponse } from 'next/server';

const COST_AGENT_URL = process.env.COST_AGENT_URL || 'http://cost-agent:8001';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const provider = searchParams.get('provider') || 'runpod';
    
    const response = await fetch(`${COST_AGENT_URL}/api/v1/dashboard?provider=${provider}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: `Cost Agent returned ${response.status}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Dashboard API Error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch dashboard data' },
      { status: 500 }
    );
  }
}
