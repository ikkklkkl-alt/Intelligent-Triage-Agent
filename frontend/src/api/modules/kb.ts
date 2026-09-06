import request from '../request'

export interface KnowledgeBaseItem {
  id: number
  title: string
  source?: string | null
  category?: string
  status?: string
  error?: string | null
  chunk_count?: number
  content?: string
  created_at: string
  updated_at: string
}

export function getKnowledgeBaseApi(params?: { category?: string; keyword?: string }) {
  return request.get<any, KnowledgeBaseItem[]>('/kb/documents', { params })
}

export function createKBArticleApi(data: { title: string; content: string; category?: string }) {
  return request.post<any, KnowledgeBaseItem>('/kb/documents', { title: data.title, source: data.category, content: data.content })
}

export function updateKBArticleApi(id: number, data: Partial<KnowledgeBaseItem>) {
  return request.post<any, KnowledgeBaseItem>(`/kb/documents/${id}/reingest`, data)
}

export function deleteKBArticleApi(id: number) {
  return request.delete<any, void>(`/kb/documents/${id}`)
}
