'use client'

import { useState } from 'react'
import { RagDocument, DocType } from '@/lib/types'
import { api } from '@/lib/api'

const docTypeLabels: Record<DocType, string> = {
  brand_voice: 'Brand Voice',
  example_post: 'Przykładowy post',
  company_info: 'O firmie',
  keywords: 'Słowa kluczowe',
}

interface Props {
  initialDocs: RagDocument[]
}

export function RagManager({ initialDocs }: Props) {
  const [docs, setDocs] = useState(initialDocs)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [form, setForm] = useState({ name: '', content: '', doc_type: 'brand_voice' as DocType })
  const [file, setFile] = useState<File | null>(null)
  const [tab, setTab] = useState<'text' | 'file'>('text')

  const refresh = async () => {
    const updated = await api.rag.list()
    setDocs(updated)
  }

  const showSuccess = (msg: string) => {
    setSuccess(msg)
    setTimeout(() => setSuccess(''), 3000)
  }

  const handleAddText = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const res = await api.rag.add(form)
      showSuccess(res.message)
      setForm({ name: '', content: '', doc_type: 'brand_voice' })
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Błąd dodawania dokumentu')
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return
    setLoading(true)
    setError('')
    try {
      const res = await api.rag.upload(file, form.doc_type)
      showSuccess(res.message)
      setFile(null)
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Błąd uploadu')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Usunąć dokument?')) return
    try {
      await api.rag.delete(id)
      setDocs(d => d.filter(doc => doc.id !== id))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Błąd usuwania')
    }
  }

  return (
    <div className="space-y-8">
      <div className="bg-white border border-gray-200 rounded-lg p-5">
        <div className="flex gap-2 mb-5">
          {(['text', 'file'] as const).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                tab === t ? 'bg-gray-900 text-white' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {t === 'text' ? 'Tekst' : 'Plik PDF/TXT'}
            </button>
          ))}
        </div>

        {tab === 'text' ? (
          <form onSubmit={handleAddText} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nazwa</label>
                <input
                  value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  placeholder="Np. Brand voice 2025"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Typ</label>
                <select
                  value={form.doc_type}
                  onChange={e => setForm(f => ({ ...f, doc_type: e.target.value as DocType }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {Object.entries(docTypeLabels).map(([v, l]) => (
                    <option key={v} value={v}>{l}</option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Treść</label>
              <textarea
                value={form.content}
                onChange={e => setForm(f => ({ ...f, content: e.target.value }))}
                rows={5}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 text-white py-2 px-4 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Dodawanie...' : 'Dodaj dokument'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleUpload} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Plik</label>
                <input
                  type="file"
                  accept=".pdf,.txt"
                  onChange={e => setFile(e.target.files?.[0] || null)}
                  className="w-full text-sm text-gray-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:bg-gray-100 file:text-gray-700 file:text-sm"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Typ</label>
                <select
                  value={form.doc_type}
                  onChange={e => setForm(f => ({ ...f, doc_type: e.target.value as DocType }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {Object.entries(docTypeLabels).map(([v, l]) => (
                    <option key={v} value={v}>{l}</option>
                  ))}
                </select>
              </div>
            </div>
            <button
              type="submit"
              disabled={loading || !file}
              className="bg-blue-600 text-white py-2 px-4 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Wgrywanie...' : 'Wgraj plik'}
            </button>
          </form>
        )}

        {error && <p className="mt-3 text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>}
        {success && <p className="mt-3 text-sm text-green-700 bg-green-50 rounded-lg px-3 py-2">{success}</p>}
      </div>

      <div>
        <h2 className="text-sm font-semibold text-gray-700 mb-3">
          Dokumenty w bazie ({docs.length})
        </h2>
        {docs.length === 0 ? (
          <p className="text-sm text-gray-400">Brak dokumentów. Dodaj pierwszý dokument powyżej.</p>
        ) : (
          <div className="space-y-2">
            {docs.map(doc => (
              <div key={doc.id} className="flex items-center justify-between bg-white border border-gray-200 rounded-lg px-4 py-3">
                <div>
                  <p className="text-sm font-medium text-gray-900">{doc.name}</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {docTypeLabels[doc.doc_type]} · {doc.chunk_count} chunków ·{' '}
                    {new Date(doc.created_at).toLocaleDateString('pl-PL')}
                  </p>
                </div>
                <button
                  onClick={() => handleDelete(doc.id)}
                  className="text-xs text-red-500 hover:text-red-700 transition-colors"
                >
                  Usuń
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
