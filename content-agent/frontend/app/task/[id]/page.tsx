'use client'

import { useState, useEffect, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Task } from '@/lib/types'
import { api } from '@/lib/api'
import { ApprovalView } from '@/components/ApprovalView'

const POLL_INTERVAL = 3000

export default function TaskPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const [task, setTask] = useState<Task | null>(null)
  const [error, setError] = useState('')

  const fetchTask = useCallback(async () => {
    try {
      const data = await api.tasks.get(id)
      setTask(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Nie znaleziono zadania')
    }
  }, [id])

  useEffect(() => {
    fetchTask()
  }, [fetchTask])

  useEffect(() => {
    if (!task) return
    if (task.status === 'pending' || task.status === 'running') {
      const interval = setInterval(fetchTask, POLL_INTERVAL)
      return () => clearInterval(interval)
    }
  }, [task, fetchTask])

  if (error) {
    return (
      <div className="text-center py-16">
        <p className="text-red-600">{error}</p>
        <button onClick={() => router.push('/')} className="mt-4 text-sm text-blue-600 hover:underline">
          Wróć do dashboardu
        </button>
      </div>
    )
  }

  if (!task) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <button onClick={() => router.push('/')} className="text-sm text-gray-500 hover:text-gray-900 mb-4 block">
          ← Dashboard
        </button>
        <h1 className="text-xl font-bold text-gray-900">{task.topic}</h1>
        <p className="text-sm text-gray-500 mt-1">
          {task.platform} · {task.post_type}
        </p>
      </div>

      <ApprovalView task={task} onUpdate={setTask} />
    </div>
  )
}
