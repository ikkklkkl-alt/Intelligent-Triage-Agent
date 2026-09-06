import request from '../request'

export interface BillingItem {
  id: number
  patient_name: string
  kind: 'prescription' | 'lab'
  ref_id: number
  amount: number
  status: 'pending' | 'paid' | 'cancelled'
  created_at: string
}

export function getPendingBillingApi() {
  return request.get<any, BillingItem[]>('/billing/pending')
}

export function confirmPaymentApi(billingId: number) {
  return request.post<any, BillingItem>(`/billing/${billingId}/pay`)
}

export function getMyPaymentsApi() {
  return request.get<any, BillingItem[]>('/billing/mine')
}
