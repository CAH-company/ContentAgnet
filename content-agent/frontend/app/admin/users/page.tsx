'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'

interface UserProfile {
  id: string
  email: string
  role: string
  created_at: string
}

export default function AdminUsersPage() {
  const router = useRouter()
  const [users, setUsers] = useState<UserProfile[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [newEmail, setNewEmail] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState('')
  const [createSuccess, setCreateSuccess] = useState('')

  useEffect(() => {
    loadUsers()
  }, [])

  async function loadUsers() {
    try {
      const data = await api.admin.listUsers()
      setUsers(data)
    } catch (err: any) {
      if (err.message?.includes('403') || err.message?.includes('administrator')) {
        setError('Brak dostępu — tylko administrator może wyświetlić tę stronę.')
      } else {
        setError(err.message || 'Błąd ładowania użytkowników')
      }
    } finally {
      setLoading(false)
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setCreating(true)
    setCreateError('')
    setCreateSuccess('')
    try {
      await api.admin.createUser(newEmail, newPassword)
      setCreateSuccess(`Utworzono konto dla ${newEmail}`)
      setNewEmail('')
      setNewPassword('')
      loadUsers()
    } catch (err: any) {
      setCreateError(err.message || 'Błąd tworzenia użytkownika')
    } finally {
      setCreating(false)
    }
  }

  async function handleDelete(userId: string, email: string) {
    if (!confirm(`Usunąć użytkownika ${email}? Tej operacji nie można cofnąć.`)) return
    try {
      await api.admin.deleteUser(userId)
      setUsers(prev => prev.filter(u => u.id !== userId))
    } catch (err: any) {
      alert(err.message || 'Błąd usuwania użytkownika')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-xl py-16">
        <p className="text-red-600 text-sm">{error}</p>
        <button onClick={() => router.push('/')} className="mt-4 text-sm text-blue-600 hover:underline">
          Wróć do dashboardu
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-2xl space-y-8">
      <div>
        <button onClick={() => router.push('/')} className="text-sm text-gray-500 hover:text-gray-900 mb-4 block">
          ← Dashboard
        </button>
        <h1 className="text-xl font-bold text-gray-900">Zarządzanie użytkownikami</h1>
        <p className="text-sm text-gray-500 mt-1">Panel administratora</p>
      </div>

      {/* Formularz tworzenia użytkownika */}
      <div className="border border-gray-200 rounded-xl p-6 space-y-4">
        <h2 className="text-sm font-semibold text-gray-900">Nowy użytkownik</h2>
        <form onSubmit={handleCreate} className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={newEmail}
              onChange={e => setNewEmail(e.target.value)}
              required
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="user@example.com"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Hasło</label>
            <input
              type="password"
              value={newPassword}
              onChange={e => setNewPassword(e.target.value)}
              required
              minLength={8}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Min. 8 znaków"
            />
          </div>
          {createError && (
            <p className="text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">{createError}</p>
          )}
          {createSuccess && (
            <p className="text-xs text-green-700 bg-green-50 rounded-lg px-3 py-2">{createSuccess}</p>
          )}
          <button
            type="submit"
            disabled={creating}
            className="bg-blue-600 text-white py-2 px-4 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {creating ? 'Tworzenie...' : 'Utwórz użytkownika'}
          </button>
        </form>
      </div>

      {/* Lista użytkowników */}
      <div className="border border-gray-200 rounded-xl overflow-hidden">
        <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
          <h2 className="text-sm font-semibold text-gray-900">
            Użytkownicy ({users.length})
          </h2>
        </div>
        {users.length === 0 ? (
          <p className="text-sm text-gray-500 p-4">Brak użytkowników</p>
        ) : (
          <ul className="divide-y divide-gray-100">
            {users.map(user => (
              <li key={user.id} className="flex items-center justify-between px-4 py-3">
                <div>
                  <p className="text-sm font-medium text-gray-900">{user.email}</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {user.role === 'admin' ? (
                      <span className="text-blue-600 font-medium">Admin</span>
                    ) : (
                      'Użytkownik'
                    )}
                    {' · '}
                    {new Date(user.created_at).toLocaleDateString('pl-PL')}
                  </p>
                </div>
                {user.role !== 'admin' && (
                  <button
                    onClick={() => handleDelete(user.id, user.email)}
                    className="text-xs text-red-600 hover:text-red-800 hover:bg-red-50 px-2 py-1 rounded transition-colors"
                  >
                    Usuń
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
