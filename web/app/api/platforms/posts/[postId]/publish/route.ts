import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

type PostParams = { postId: string }

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<PostParams> }
) {
  try {
    const { postId } = await params
    const response = await fetch(`${BACKEND_URL}/api/platforms/posts/${postId}/publish`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: { message: error.message } },
      { status: 500 }
    );
  }
}
