import { NextResponse, type NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  if (pathname.startsWith('/login')) {
    return NextResponse.next()
  }

  // Sprawdź czy cookie sesji Supabase istnieje
  const hasSession = request.cookies.getAll().some(c => c.name.includes('auth-token'))

  if (!hasSession) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
