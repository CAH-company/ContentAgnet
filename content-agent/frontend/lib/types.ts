export type Platform = 'blog' | 'linkedin' | 'twitter' | 'facebook' | 'instagram'
export type PostType = 'article' | 'short_post' | 'newsletter' | 'carousel'
export type TaskStatus = 'pending' | 'running' | 'review' | 'approved' | 'published' | 'failed'
export type DocType = 'brand_voice' | 'example_post' | 'company_info' | 'keywords'

export interface Task {
  id: string
  created_at: string
  updated_at: string
  topic: string
  platform: Platform
  post_type: PostType
  status: TaskStatus
  result: string | null
  user_comment: string | null
  error_message: string | null
  token_input: number
  token_output: number
  iteration: number
  ready_to_publish: boolean
}

export interface RagDocument {
  id: string
  created_at: string
  name: string
  content: string
  doc_type: DocType
  chunk_count: number
}
