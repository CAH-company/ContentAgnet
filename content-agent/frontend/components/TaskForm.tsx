'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'

export function TaskForm() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState({
    topic: '',
    platform: 'linkedin',
    post_type: 'short_post',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.topic.trim()) return
    setLoading(true)
    setError('')
    try {
      const { task_id } = await api.tasks.create(form)
      router.push(`/task/${task_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Błąd tworzenia zadania')
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5 max-w-lg">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Temat / prompt
        </label>
        <textarea
          value={form.topic}
          onChange={e => setForm(f => ({ ...f, topic: e.target.value }))}
          rows={3}
          placeholder="Np. Jak AI zmienia content marketing w 2025 roku"
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          required
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Platforma</label>
          <select
            value={form.platform}
            onChange={e => setForm(f => ({ ...f, platform: e.target.value }))}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="linkedin">LinkedIn</option>
            <option value="wordpress">WordPress</option>
            <option value="twitter">Twitter/X</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Typ contentu</label>
          <select
            value={form.post_type}
            onChange={e => setForm(f => ({ ...f, post_type: e.target.value }))}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="short_post">Krótki post</option>
            <option value="article">Artykuł</option>
            <option value="newsletter">Newsletter</option>
          </select>
        </div>
      </div>

      {error && (
        <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? 'Tworzenie...' : 'Utwórz zadanie'}
      </button>
    </form>
  )
}
