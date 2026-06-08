'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase-client'

const links = [
  { href: '/',     label: 'Dashboard' },
  { href: '/new',  label: 'Nowe zadanie' },
  { href: '/rag',  label: 'Baza wiedzy' },
]

export function Navbar() {
  const pathname = usePathname()
  const router = useRouter()

  const handleLogout = async () => {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push('/login')
    router.refresh()
  }

  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="max-w-6xl mx-auto px-4 flex items-center h-14 gap-6">
        <span className="font-bold text-gray-900 text-lg tracking-tight">ContentAgent</span>
        <div className="flex gap-1 flex-1">
          {links.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                pathname === href
                  ? 'bg-gray-100 text-gray-900'
                  : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              {label}
            </Link>
          ))}
        </div>
        <button
          onClick={handleLogout}
          className="text-sm text-gray-500 hover:text-gray-900 transition-colors"
        >
          Wyloguj
        </button>
      </div>
    </nav>
  )
}
