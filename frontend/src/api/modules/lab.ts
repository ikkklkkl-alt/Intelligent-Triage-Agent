import request from '../request'

export interface LabOrderItem {
  id: number
  encounter_id: number
  patient_name: string
  item_name: string
  fee: number
  status: 'pending_payment' | 'paid' | 'reported'
  created_at: string
}

export interface LabReport {
  id: number
  lab_order_id: number
  item_name: string | null
  raw_text: string
  items_json: Record<string, unknown>[] | Record<string, unknown> | null
  ai_status: string
  ai_summary: string
  ai_degraded: boolean
}

export function getLabOrdersApi() {
  return request.get<any, LabOrderItem[]>('/lab/orders')
}

export function submitLabResultApi(orderId: number, data: { raw_text: string }) {
  return request.post<any, LabReport>(`/lab/orders/${orderId}/report`, data)
}

export function getLabReportApi(reportId: number) {
  return request.get<any, LabReport>(`/reports/${reportId}`)
}

export function getMyReportsApi() { return request.get<any, LabReport[]>('/patient/reports') }
