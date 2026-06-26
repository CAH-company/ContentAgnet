'use client'

import { useState } from 'react'
import { Task } from '@/lib/types'
import { api } from '@/lib/api'
import { StatusBadge } from './StatusBadge'

// Claude Sonnet 4-5 pricing (USD per million tokens)
const INPUT_COST_PER_MTK = 3.00
const OUTPUT_COST_PER_MTK = 15.00

function calcCost(inputTokens: number, outputTokens: number): string {
  const cost = (inputTokens / 1_000_000) * INPUT_COST_PER_MTK
             + (outputTokens / 1_000_000) * OUTPUT_COST_PER_MTK
  if (cost < 0.001) return '~$0.00'
  if (cost < 0.01) return `~$${cost.toFixed(4)}`
  return `~$${cost.toFixed(3)}`
}

interface Props {
  task: Task
  onUpdate: (task: Task) => void
}

export function ApprovalView({ task, onUpdate }: Props) {
  const [comment, setComment] = useState('')
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  const handleApprove = async () => {
    setLoading(true)
    try {
      await api.tasks.approve(task.id)
      onUpdate({ ...task, status: 'published', ready_to_publish: true })
    } finally {
      setLoading(false)
    }
  }

  const handleRevise = async () => {
    if (!comment.trim()) return
    setLoading(true)
    try {
      await api.tasks.revise(task.id, comment)
      onUpdate({ ...task, status: 'pending', iteration: task.iteration + 1 })
    } finally {
      setLoading(false)
      setComment('')
    }
  }

  const handleCopy = () => {
    if (task.result) {
      navigator.clipboard.writeText(task.result)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <StatusBadge status={task.status} />
        {task.iteration > 1 && (
          <span className="text-xs text-gray-500">iteracja {task.iteration}</span>
        )}
        {task.token_input > 0 && (
          <span className="text-xs text-gray-400 ml-auto" title={`In: ${task.token_input.toLocaleString()} | Out: ${task.token_output.toLocaleString()}`}>
            {(task.token_input + task.token_output).toLocaleString()} tokenów
            {' · '}
            {calcCost(task.token_input, task.token_output)}
          </span>
        )}
      </div>

      {task.result && (
        <div className="relative">
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <pre className="text-sm text-gray-800 whitespace-pre-wrap font-sans leading-relaxed">
              {task.result}
            </pre>
          </div>
          <button
            onClick={handleCopy}
            className="absolute top-3 right-3 text-xs text-gray-500 hover:text-gray-900 bg-white border border-gray-200 rounded px-2 py-1 transition-colors"
          >
            {copied ? 'Skopiowano!' : 'Kopiuj'}
          </button>
        </div>
      )}

      {task.error_message && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-700 font-medium">Błąd agenta</p>
          <p className="text-xs text-red-600 mt-1 font-mono">{task.error_message}</p>
        </div>
      )}

      {task.status === 'review' && (
        <div className="border-t border-gray-200 pt-5 space-y-3">
          <div className="flex gap-3">
            <button
              onClick={handleApprove}
              disabled={loading}
              className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              Zatwierdź i opublikuj
            </button>
          </div>
          <div className="space-y-2">
            <textarea
              value={comment}
              onChange={e => setComment(e.target.value)}
              rows={2}
              placeholder="Co poprawić? Np. Dodaj więcej konkretnych przykładów..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400 resize-none"
            />
            <button
              onClick={handleRevise}
              disabled={loading || !comment.trim()}
              className="w-full bg-orange-500 text-white py-2 px-4 rounded-lg text-sm font-medium hover:bg-orange-600 disabled:opacity-50 transition-colors"
            >
              Wyślij do poprawki
            </button>
          </div>
        </div>
      )}

      {(task.status === 'running' || task.status === 'pending') && (
        <div className="flex items-center gap-3 text-sm text-gray-500 py-4">
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          Agenci pracują nad postem...
        </div>
      )}
    </div>
  )
}
