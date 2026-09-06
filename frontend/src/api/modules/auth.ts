import request from '../request'

export interface LoginParams {
  username: string
  password: string
}

export interface LoginResult {
  access_token: string
  token_type: string
}

export interface UserProfile { id: number; username: string; full_name: string; role: string }

export function loginApi(data: LoginParams) {
  const form = new URLSearchParams()
  form.set('username', data.username)
  form.set('password', data.password)
  return request.post<any, LoginResult>('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })
}

export function getProfileApi() {
  return request.get<any, UserProfile>('/auth/me')
}
