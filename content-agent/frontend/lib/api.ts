import { Task, RagDocument } from './types'
import { createClient } from './supabase-client'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function getAuthHeader(): Promise<string> {
  const supabase = createClient()
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  if (!token) throw new Error('Brak sesji — zaloguj się ponownie')
  return `Bearer ${token}`
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const auth = await getAuthHeader()
  const res = await fetch(`${API_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': auth,
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
    upload: async (file: File, doc_type: string) => {
      const auth = await getAuthHeader()
      const form = new FormData()
      form.append('file', file)
      form.append('doc_type', doc_type)
      const res = await fetch(`${API_URL}/api/rag/documents/upload`, {
        method: 'POST',
        headers: { 'Authorization': auth },
        body: form,
      })
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(error.detail || 'Upload error')
      }
      return res.json() as Promise<{ message: string }>
    },
    delete: (id: string) =>
      apiFetch<{ message: string }>(`/api/rag/documents/${id}`, {
        method: 'DELETE',
      }),
  },
  admin: {
    listUsers: () => apiFetch<{ id: string; email: string; role: string; created_at: string }[]>('/api/admin/users'),
    createUser: (email: string, password: string) =>
      apiFetch<{ id: string; email: string }>('/api/admin/users', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),
    deleteUser: (userId: string) =>
      apiFetch<{ message: string }>(`/api/admin/users/${userId}`, {
        method: 'DELETE',
      }),
  },
}
