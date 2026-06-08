import { api } from '@/lib/api'
import { RagDocument } from '@/lib/types'
import { RagManager } from '@/components/RagManager'

export const revalidate = 0

export default async function RagPage() {
  let docs: RagDocument[] = []
  try {
    docs = await api.rag.list()
  } catch {
    // backend may not be running during build
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Baza wiedzy</h1>
        <p className="text-sm text-gray-500 mt-1">
          Dokumenty które agenci czytają podczas pisania: brand voice, przykłady postów, opis firmy, słowa kluczowe.
        </p>
      </div>
      <RagManager initialDocs={docs} />
    </div>
  )
}
