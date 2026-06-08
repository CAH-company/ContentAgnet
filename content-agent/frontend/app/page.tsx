import { api } from '@/lib/api'
import { TaskList } from '@/components/TaskList'
import Link from 'next/link'

export const revalidate = 0

export default async function DashboardPage() {
  let tasks = []
  try {
    tasks = await api.tasks.list()
  } catch {
    // backend may not be running during build
  }

  const counts = {
    review: tasks.filter(t => t.status === 'review').length,
    running: tasks.filter(t => t.status === 'running' || t.status === 'pending').length,
    published: tasks.filter(t => t.status === 'published').length,
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <Link
          href="/new"
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          + Nowe zadanie
        </Link>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <p className="text-2xl font-bold text-purple-600">{counts.review}</p>
          <p className="text-sm text-gray-500 mt-1">Do akceptacji</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <p className="text-2xl font-bold text-blue-600">{counts.running}</p>
          <p className="text-sm text-gray-500 mt-1">W toku</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <p className="text-2xl font-bold text-green-600">{counts.published}</p>
          <p className="text-sm text-gray-500 mt-1">Opublikowanych</p>
        </div>
      </div>

      <TaskList tasks={tasks} />
    </div>
  )
}
