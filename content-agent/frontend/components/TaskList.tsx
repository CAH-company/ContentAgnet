'use client'

import { Task } from '@/lib/types'
import { TaskCard } from './TaskCard'

export function TaskList({ tasks }: { tasks: Task[] }) {
  if (tasks.length === 0) {
    return (
      <div className="text-center py-16 text-gray-400">
        <p className="text-lg">Brak zadań</p>
        <p className="text-sm mt-1">Utwórz pierwsze zadanie klikając &quot;Nowe zadanie&quot;</p>
      </div>
    )
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {tasks.map(task => (
        <TaskCard key={task.id} task={task} />
      ))}
    </div>
  )
}
