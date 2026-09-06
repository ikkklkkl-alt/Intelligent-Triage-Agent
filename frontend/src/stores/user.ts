import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type UserRole = 'patient' | 'doctor' | 'lab' | 'cashier' | 'pharmacist' | 'admin'

export interface UserInfo {
  id: number
  username: string
  name: string
  role: UserRole
}

const STORAGE_KEY = 'imcs-user'
const stored = typeof localStorage === 'undefined' ? null : localStorage.getItem(STORAGE_KEY)
const initial = stored ? JSON.parse(stored) as { token: string; userInfo: UserInfo } : null
let _token = initial?.token || ''
let _userInfo: UserInfo | null = initial?.userInfo || null

export function getToken(): string {
  return _token
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(_token)
  const userInfo = ref<UserInfo | null>(_userInfo)

  const isLoggedIn = computed(() => !!token.value)
  const userRole = computed(() => userInfo.value?.role || null)

  function setToken(t: string) {
    token.value = t
    _token = t
  }

  function setUserInfo(info: UserInfo) {
    userInfo.value = info
    _userInfo = info
  }

  function persist() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ token: _token, userInfo: _userInfo }))
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    _token = ''
    _userInfo = null
    localStorage.removeItem(STORAGE_KEY)
  }

  return { token, userInfo, isLoggedIn, userRole, setToken, setUserInfo, persist, logout }
})
