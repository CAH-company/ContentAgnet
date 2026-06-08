import { TaskForm } from '@/components/TaskForm'

export default function NewTaskPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Nowe zadanie</h1>
        <p className="text-sm text-gray-500 mt-1">
          Opisz temat a agenci AI napiszą post dostosowany do platformy i brand voice firmy.
        </p>
      </div>
      <TaskForm />
    </div>
  )
}
