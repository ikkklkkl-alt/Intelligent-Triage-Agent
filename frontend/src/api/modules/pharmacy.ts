import request from '../request'

export interface PharmacyItem {
  id: number
  encounter_id: number
  patient_name: string
  status: 'paid' | 'dispensed'
  total_fee: number
  items: Array<{ id: number; drug_name: string; spec: string | null; quantity: number; price: number; usage: string | null }>
  created_at: string
}

export function getPendingPrescriptionsApi() {
  return request.get<any, PharmacyItem[]>('/pharmacy/pending')
}

export function dispensePrescriptionApi(id: number) {
  return request.post<any, PharmacyItem>(`/pharmacy/${id}/dispense`)
}
