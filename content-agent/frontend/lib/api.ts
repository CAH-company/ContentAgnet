import { Task, RagDocument } from './types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const API_KEY = process.env.NEXT_PUBLIC_API_SECRET_KEY || ''

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
    },
    ...options,
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail || 'API error')
  }
  return res.json()
}

export const api = {
  tasks: {
    list: () => apiFetch<Task[]>('/api/tasks'),
    get: (id: string) => apiFetch<Task>(`/api/tasks/${id}`),
    create: (data: { topic: string; platform: string; post_type: string }) =>
      apiFetch<{ task_id: string; status: string }>('/api/tasks', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    approve: (id: string) =>
      apiFetch<{ status: string; message: string }>(`/api/tasks/${id}/approve`, {
        method: 'POST',
      }),
    revise: (id: string, comment: string) =>
      apiFetch<{ status: string; message: string }>(`/api/tasks/${id}/revise`, {
        method: 'POST',
        body: JSON.stringify({ comment }),
      }),
  },
  rag: {
    list: () => apiFetch<RagDocument[]>('/api/rag/documents'),
    add: (data: { name: string; content: string; doc_type: string }) =>
      apiFetch<{ message: string }>('/api/rag/documents', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    upload: (file: File, doc_type: string) => {
      const form = new FormData()
      form.append('file', file)
      form.append('doc_type', doc_type)
      return fetch(`${API_URL}/api/rag/documents/upload`, {
        method: 'POST',
        headers: { 'X-API-Key': API_KEY },
        body: form,
      }).then(r => r.json()) as Promise<{ message: string }>
    },
    delete: (id: string) =>
      apiFetch<{ message: string }>(`/api/rag/documents/${id}`, {
        method: 'DELETE',
      }),
  },
}
