import { TaskStatus } from '@/lib/types'

const config: Record<TaskStatus, { label: string; className: string }> = {
  pending:   { label: 'Oczekuje',    className: 'bg-yellow-100 text-yellow-800' },
  running:   { label: 'Generuje...',  className: 'bg-blue-100 text-blue-800 animate-pulse' },
  review:    { label: 'Do akceptacji', className: 'bg-purple-100 text-purple-800' },
  approved:  { label: 'Zatwierdzono', className: 'bg-green-100 text-green-800' },
  published: { label: 'Opublikowano', className: 'bg-green-200 text-green-900' },
  failed:    { label: 'Błąd',         className: 'bg-red-100 text-red-800' },
}

export function StatusBadge({ status }: { status: TaskStatus }) {
  const { label, className } = config[status]
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${className}`}>
      {label}
    </span>
  )
}
