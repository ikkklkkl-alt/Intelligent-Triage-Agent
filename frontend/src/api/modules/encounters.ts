import request from '../request'

export interface Encounter {
  id: number
  patient_id: number
  patient_name: string
  appointment_id: number
  status: 'open' | 'closed'
  chief_complaint: string | null
  diagnosis: string | null
  plan: string | null
  created_at: string
}

export interface MedicalRecord {
  id: number
  appointment_id: number
  chief_complaint: string
  diagnosis: string | null
  plan: string | null
  prescriptions: Prescription[]
  lab_orders: LabOrder[]
}

export interface Prescription {
  id: number
  total_fee: number
  items: Array<{ drug_name: string; spec: string | null; quantity: number; price: number; usage: string | null }>
}

export interface LabOrder {
  id: number
  item_name: string
  fee: number
  status: string
}

export interface WorklistAppointment { id: number; patient_name: string; department_name: string; work_date: string; slot: string; status: string }

export function getWorklistApi() {
  return request.get<any, WorklistAppointment[]>('/doctor/worklist')
}

export function startEncounterApi(appointmentId: number) {
  return request.post<any, Encounter>('/encounters', { appointment_id: appointmentId })
}

export function getEncounterDetailApi(encounterId: number) {
  return request.get<any, Encounter>(`/encounters/${encounterId}`)
}

export function getEncounterOrdersApi(encounterId: number) {
  return request.get<any, { prescriptions: Prescription[]; lab_orders: LabOrder[] }>(`/encounters/${encounterId}/orders`)
}

export function saveEncounterApi(encounterId: number, data: Partial<MedicalRecord>) {
  return request.put<any, Encounter>(`/encounters/${encounterId}`, data)
}

export function completeEncounterApi(encounterId: number) {
  return request.put<any, Encounter>(`/encounters/${encounterId}`, { close: true })
}

export function createPrescriptionApi(encounterId: number, data: { drug_name: string; spec?: string; quantity: number; price: number; usage?: string }) {
  return request.post<any, Prescription>(`/encounters/${encounterId}/prescriptions`, { items: [data] })
}

export function createLabOrderApi(encounterId: number, data: { item_name: string; fee: number }) {
  return request.post<any, LabOrder>(`/encounters/${encounterId}/lab-orders`, data)
}

export function getEncounterHistoryApi() {
  return request.get<any, Encounter[]>('/patient/encounters')
}
