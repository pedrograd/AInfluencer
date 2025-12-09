import { NextRequest, NextResponse } from 'next/server'

const COMFYUI_URL = process.env.COMFYUI_URL || 'http://localhost:8188'

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const filename = searchParams.get('filename')
  const subfolder = searchParams.get('subfolder') || ''
  const type = searchParams.get('type') || 'output'

  if (!filename) {
    return NextResponse.json({ error: 'Filename is required' }, { status: 400 })
  }

  try {
    const url = `${COMFYUI_URL}/view?filename=${encodeURIComponent(filename)}&subfolder=${encodeURIComponent(subfolder)}&type=${encodeURIComponent(type)}`
    
    const response = await fetch(url, {
      method: 'GET',
    })

    if (!response.ok) {
      throw new Error(`ComfyUI API error: ${response.statusText}`)
    }

    const blob = await response.blob()
    return new NextResponse(blob, {
      headers: {
        'Content-Type': response.headers.get('Content-Type') || 'image/png',
      },
    })
  } catch (error: any) {
    console.error('ComfyUI image proxy error:', error)
    return NextResponse.json(
      { error: error.message || 'Failed to fetch image' },
      { status: 500 }
    )
  }
}
