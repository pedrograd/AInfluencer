import { NextRequest, NextResponse } from 'next/server'

const COMFYUI_URL = process.env.COMFYUI_URL || 'http://localhost:8188'

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const path = searchParams.get('path') || 'system_stats'
  
  try {
    const response = await fetch(`${COMFYUI_URL}/${path}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      cache: 'no-store',
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`ComfyUI API error: ${response.status} ${errorText}`)
    }

    const data = await response.json()
    return NextResponse.json(data, {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      },
    })
  } catch (error: any) {
    console.error('ComfyUI proxy error:', error)
    return NextResponse.json(
      { error: error.message || 'Failed to connect to ComfyUI', details: error.toString() },
      { 
        status: 500,
        headers: {
          'Access-Control-Allow-Origin': '*',
        },
      }
    )
  }
}

export async function POST(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const path = searchParams.get('path') || 'prompt'
  
  try {
    const body = await request.json()
    
    // Validate request body for prompt endpoint
    if (path === 'prompt' && !body.prompt) {
      return NextResponse.json(
        { error: 'Missing prompt in request body' },
        { status: 400 }
      )
    }

    const url = `${COMFYUI_URL}/${path}`
    console.log(`[ComfyUI Proxy] POST ${url}`, path === 'prompt' ? { ...body, prompt: '...' } : body)
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      cache: 'no-store',
    })

    if (!response.ok) {
      let errorText = ''
      let errorData: any = null
      try {
        errorText = await response.text()
        try {
          errorData = JSON.parse(errorText)
        } catch (e) {
          // Not JSON, use as text
        }
      } catch (e) {
        errorText = `HTTP ${response.status} ${response.statusText}`
      }
      
      console.error(`[ComfyUI Proxy] Error ${response.status}:`, errorText)
      
      // Extract helpful information from ComfyUI errors
      let helpfulMessage = errorText
      if (errorData?.node_errors) {
        const nodeErrors = Object.values(errorData.node_errors) as any[]
        for (const nodeError of nodeErrors) {
          if (nodeError.errors) {
            for (const err of nodeError.errors) {
              if (err.type === 'value_not_in_list' && err.extra_info?.input_config) {
                const availableValues = err.extra_info.input_config[0]
                helpfulMessage = `${err.message}: ${err.details}\n\nAvailable options: ${availableValues.join(', ')}`
              }
            }
          }
        }
      }
      
      throw new Error(`ComfyUI API error: ${response.status} ${helpfulMessage}`)
    }

    let data
    try {
      data = await response.json()
    } catch (e) {
      // Some endpoints might return empty response
      data = { success: true }
    }

    return NextResponse.json(data, {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      },
    })
  } catch (error: any) {
    console.error('[ComfyUI Proxy] Error:', error)
    const errorMessage = error.message || 'Failed to connect to ComfyUI'
    const errorDetails = error.cause ? error.cause.toString() : error.toString()
    
    return NextResponse.json(
      { 
        error: errorMessage,
        details: errorDetails,
        hint: path === 'prompt' ? 'Check that ComfyUI is running and the workflow structure is valid' : 'Check that ComfyUI is running on ' + COMFYUI_URL
      },
      { 
        status: 500,
        headers: {
          'Access-Control-Allow-Origin': '*',
        },
      }
    )
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  })
}
