import Link from 'next/link'
import { Task } from '@/lib/types'
import { StatusBadge } from './StatusBadge'

const platformLabel: Record<string, string> = {
  wordpress: 'WordPress',
  linkedin: 'LinkedIn',
  twitter: 'Twitter/X',
}

const postTypeLabel: Record<string, string> = {
  article: 'Artykuł',
  short_post: 'Krótki post',
  newsletter: 'Newsletter',
}

export function TaskCard({ task }: { task: Task }) {
  return (
    <Link href={`/task/${task.id}`} className="block">
      <div className="bg-white border border-gray-200 rounded-lg p-4 hover:border-gray-300 hover:shadow-sm transition-all">
        <div className="flex items-start justify-between gap-2">
          <p className="font-medium text-gray-900 text-sm line-clamp-2">{task.topic}</p>
          <StatusBadge status={task.status} />
        </div>
        <div className="mt-2 flex items-center gap-2 text-xs text-gray-500">
          <span className="bg-gray-100 px-2 py-0.5 rounded">{platformLabel[task.platform]}</span>
          <span className="bg-gray-100 px-2 py-0.5 rounded">{postTypeLabel[task.post_type]}</span>
          {task.iteration > 1 && (
            <span className="bg-orange-50 text-orange-700 px-2 py-0.5 rounded">
              iteracja {task.iteration}
            </span>
          )}
        </div>
        <p className="mt-2 text-xs text-gray-400">
          {new Date(task.created_at).toLocaleString('pl-PL')}
        </p>
      </div>
    </Link>
  )
}
