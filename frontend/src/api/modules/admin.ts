import request from '../request'

export interface DashboardStats {
  total_calls: number
  ok_calls: number
  error_calls: number
  fallback_calls: number
  total_tokens: number
  avg_latency_ms: number
  today_calls: number
  scene_breakdown: Record<string, number>
}

export interface LlmLog {
  id: number
  scene: string
  model: string
  prompt_tokens: number
  completion_tokens: number
  latency_ms: number
  status: string
  created_at: string
}

export function getDashboardStatsApi() {
  return request.get<any, DashboardStats>('/admin/stats')
}

export function getLlmLogsApi(params?: { limit?: number; scene?: string }) {
  return request.get<any, LlmLog[]>('/admin/llm-logs', { params })
}
