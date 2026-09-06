import { createRouter, createWebHashHistory, type RouteRecordRaw } from 'vue-router'
import { useUserStore, type UserRole } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      // Patient
      { path: '', redirect: '/patient/guide' },
      { path: 'patient/guide', name: 'PatientGuide', component: () => import('@/views/patient/PatientGuide.vue'), meta: { role: 'patient' } },
      { path: 'patient/triage', name: 'Triage', component: () => import('@/views/patient/Triage.vue'), meta: { role: 'patient' } },
      { path: 'patient/book', name: 'BookAppointment', component: () => import('@/views/patient/BookAppointment.vue'), meta: { role: 'patient' } },
      { path: 'patient/reports', name: 'MyReports', component: () => import('@/views/patient/MyReports.vue'), meta: { role: 'patient' } },
      { path: 'patient/payments', name: 'MyPayments', component: () => import('@/views/patient/MyPayments.vue'), meta: { role: 'patient' } },
      // Doctor
      { path: 'doctor/worklist', name: 'Worklist', component: () => import('@/views/doctor/Worklist.vue'), meta: { role: 'doctor' } },
      { path: 'doctor/encounter/:id', name: 'Encounter', component: () => import('@/views/doctor/Encounter.vue'), meta: { role: 'doctor' } },
      // Lab
      { path: 'lab/orders', name: 'LabOrders', component: () => import('@/views/lab/LabOrders.vue'), meta: { role: 'lab' } },
      // Cashier
      { path: 'billing/pending', name: 'Billing', component: () => import('@/views/cashier/Billing.vue'), meta: { role: 'cashier' } },
      // Pharmacist
      { path: 'pharmacy/pending', name: 'Pharmacy', component: () => import('@/views/pharmacy/Pharmacy.vue'), meta: { role: 'pharmacist' } },
      // Admin
      { path: 'admin/stats', name: 'Dashboard', component: () => import('@/views/admin/Dashboard.vue'), meta: { role: 'admin' } },
      { path: 'admin/kb', name: 'KnowledgeBase', component: () => import('@/views/admin/KnowledgeBase.vue'), meta: { role: 'admin' } },
      { path: 'admin/llm-logs', name: 'LlmLogs', component: () => import('@/views/admin/LlmLogs.vue'), meta: { role: 'admin' } }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/login' }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

const roleDefaultPages: Record<UserRole, string> = {
  patient: '/patient/guide',
  doctor: '/doctor/worklist',
  lab: '/lab/orders',
  cashier: '/billing/pending',
  pharmacist: '/pharmacy/pending',
  admin: '/admin/stats'
}

router.beforeEach((to, _from, next) => {
  const userStore = useUserStore()
  if (to.meta.requiresAuth === false) {
    if (userStore.isLoggedIn && to.name === 'Login') {
      const role = userStore.userRole
      next(role ? roleDefaultPages[role] : '/')
    } else {
      next()
    }
    return
  }
  if (!userStore.isLoggedIn) {
    next('/login')
    return
  }
  const requiredRole = to.meta.role as UserRole | undefined
  if (requiredRole && userStore.userRole !== requiredRole) {
    const role = userStore.userRole
    next(role ? roleDefaultPages[role] : '/')
    return
  }
  next()
})

export default router
