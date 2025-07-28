import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const url = request.nextUrl.clone()
  
  if (url.pathname.startsWith('/api/')) {
    url.host = 'localhost:8000'
    url.port = '8000'
    url.protocol = 'http:'
    return NextResponse.rewrite(url)
  }
}

export const config = {
  matcher: '/api/:path*',
}
