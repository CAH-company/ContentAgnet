'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'

const PLATFORMS = [
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'blog', label: 'Blog' },
  { value: 'facebook', label: 'Facebook' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'twitter', label: 'Twitter/X' },
]

const PLATFORM_POST_TYPES: Record<string, { value: string; label: string }[]> = {
  blog: [
    { value: 'article', label: 'Artykuł' },
    { value: 'newsletter', label: 'Newsletter' },
  ],
  linkedin: [
    { value: 'short_post', label: 'Krótki post' },
    { value: 'article', label: 'Artykuł' },
    { value: 'newsletter', label: 'Newsletter' },
    { value: 'carousel', label: 'Karuzela' },
  ],
  twitter: [
    { value: 'short_post', label: 'Krótki post' },
  ],
  facebook: [
    { value: 'short_post', label: 'Krótki post' },
    { value: 'article', label: 'Artykuł' },
  ],
  instagram: [
    { value: 'short_post', label: 'Podpis (caption)' },
    { value: 'carousel', label: 'Karuzela' },
  ],
}

export function TaskForm() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState({
    topic: '',
    platform: 'linkedin',
    post_type: 'short_post',
  })

  const handlePlatformChange = (platform: string) => {
    const firstType = PLATFORM_POST_TYPES[platform][0].value
    setForm(f => ({ ...f, platform, post_type: firstType }))
  }

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

  const postTypes = PLATFORM_POST_TYPES[form.platform] ?? []

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
            onChange={e => handlePlatformChange(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {PLATFORMS.map(p => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Typ contentu</label>
          <select
            value={form.post_type}
            onChange={e => setForm(f => ({ ...f, post_type: e.target.value }))}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {postTypes.map(t => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
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
