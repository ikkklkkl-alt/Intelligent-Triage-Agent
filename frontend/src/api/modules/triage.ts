import request from '../request'
import { getToken } from '@/stores/user'

export interface TriageChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface TriageResult {
  department: string
  urgency: 'emergency' | 'high' | 'medium' | 'low'
  advice: string
  degraded: boolean
}

export interface TriageSession { id: number; status: string; result_json: TriageResult | null; created_at: string }

export function createTriageSession() {
  return request.post<any, TriageSession>('/triage/sessions')
}

export function getTriageSessionsApi() {
  return request.get<any, TriageSession[]>('/triage/sessions')
}

export function getTriageMessagesApi(sessionId: number) {
  return request.get<any, TriageChatMessage[]>(`/triage/sessions/${sessionId}/messages`)
}

export function sendTriageMessage(sessionId: number, content: string) {
  return fetch(`/api/v1/triage/sessions/${sessionId}/messages`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getToken()}`
    },
    body: JSON.stringify({ content })
  })
}

export function getTriageResultApi(sessionId: number) {
  return request.get<any, TriageSession>(`/triage/sessions/${sessionId}`)
}
