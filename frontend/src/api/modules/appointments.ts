import request from '../request'

export interface Appointment {
  id: number
  patient_name: string
  doctor_name: string
  department_name: string
  work_date: string
  slot: string
  status: 'booked' | 'cancelled' | 'completed'
}

export interface Doctor {
  id: number
  full_name: string
  department_id: number
  department_name: string
  title: string
}

export interface Schedule { id: number; work_date: string; slot: string; capacity: number; booked: number }

export function getDoctorsApi() {
  return request.get<any, Doctor[]>('/doctors')
}

export function getDoctorSchedulesApi(doctorId: number) { return request.get<any, Schedule[]>(`/doctors/${doctorId}/schedules`) }

export function createAppointmentApi(data: { schedule_id: number; triage_session_id?: number }) {
  return request.post<any, Appointment>('/appointments', data)
}

export function getMyAppointmentsApi() {
  return request.get<any, Appointment[]>('/appointments')
}

export function cancelAppointmentApi(id: number) {
  return request.post<any, Appointment>(`/appointments/${id}/cancel`)
}
