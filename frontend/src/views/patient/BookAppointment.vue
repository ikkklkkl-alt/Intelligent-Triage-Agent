<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getDoctorsApi, getDoctorSchedulesApi, createAppointmentApi, getMyAppointmentsApi, cancelAppointmentApi, type Doctor, type Appointment, type Schedule } from '@/api/modules/appointments'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const activeTab = ref('book')
const department = ref((route.query.department as string) || '')
const doctors = ref<Doctor[]>([])
const appointments = ref<Appointment[]>([])
const loading = ref(false)
const selectedDoctor = ref<Doctor | null>(null)
const schedules = ref<Schedule[]>([])
const selectedScheduleId = ref<number | null>(null)
const showBookingDialog = ref(false)
const today = ref('')

async function fetchServerDate() {
  try {
    const res = await fetch('/api/health')
    const data = await res.json()
    today.value = data.today
  } catch {
    today.value = new Date().toISOString().slice(0, 10)
  }
}

async function fetchDoctors() {
  loading.value = true
  try {
    const all = await getDoctorsApi()
    doctors.value = department.value ? all.filter(d => d.department_name.includes(department.value)) : all
  } catch {
    ElMessage.error('获取医生列表失败')
  } finally {
    loading.value = false
  }
}

async function fetchAppointments() {
  try {
    appointments.value = await getMyAppointmentsApi()
  } catch {
    ElMessage.error('获取预约列表失败')
  }
}

async function openBooking(doctor: Doctor) {
  selectedDoctor.value = doctor
  selectedScheduleId.value = null
  try { schedules.value = await getDoctorSchedulesApi(doctor.id) } catch { ElMessage.error('获取医生排班失败'); return }
  showBookingDialog.value = true
}

async function handleBook() {
  if (!selectedDoctor.value || !selectedScheduleId.value) {
    ElMessage.warning('请选择可预约时段')
    return
  }
  try {
    await createAppointmentApi({
      schedule_id: selectedScheduleId.value
    })
    const selected = schedules.value.find(s => s.id === selectedScheduleId.value)
    if (selected && selected.work_date === today.value) {
      ElMessage.success('预约成功！今天可直接就诊，请前往诊室等候')
    } else {
      ElMessage.success(`预约成功！请于 ${selected?.work_date} 前往就诊`)
    }
    showBookingDialog.value = false
    fetchAppointments()
  } catch {
    ElMessage.error('预约失败')
  }
}

async function handleCancel(appointment: Appointment) {
  try {
    await ElMessageBox.confirm('确定取消该预约吗？', '提示', { type: 'warning' })
    await cancelAppointmentApi(appointment.id)
    ElMessage.success('已取消预约')
    fetchAppointments()
  } catch {
    // cancelled by user or API error
  }
}

function statusType(status: string) {
  const map: Record<string, string> = { booked: 'success', cancelled: 'info', completed: '' }
  return map[status] || 'info'
}

function statusLabel(status: string) {
  const map: Record<string, string> = { booked: '已预约', cancelled: '已取消', completed: '已完成' }
  return map[status] || status
}

onMounted(() => {
  fetchServerDate()
  fetchDoctors()
  fetchAppointments()
})
</script>

<template>
  <div style="background: #fff; border-radius: 8px; padding: 20px">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="预约挂号" name="book">
        <div style="margin-bottom: 16px; display: flex; gap: 12px">
          <el-input v-model="department" placeholder="按科室筛选" clearable style="width: 200px" />
          <el-button type="primary" @click="fetchDoctors">搜索</el-button>
        </div>
        <el-table :data="doctors" v-loading="loading" stripe>
          <el-table-column prop="full_name" label="医生姓名" width="120" />
          <el-table-column prop="department_name" label="科室" width="150" />
          <el-table-column prop="title" label="职称" width="120" />
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="openBooking(row)">预约</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="我的预约" name="mine">
        <el-table :data="appointments" stripe>
          <el-table-column prop="doctor_name" label="医生" width="120" />
          <el-table-column prop="department_name" label="科室" width="150" />
          <el-table-column label="预约时间" width="200"><template #default="{ row }">{{ row.work_date }} {{ row.slot === 'am' ? '上午' : '下午' }}</template></el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="statusType(row.status) as any">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
          <el-button v-if="row.status === 'booked'" type="danger" size="small" link @click="handleCancel(row)">取消</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="showBookingDialog" title="确认预约" width="400px">
      <div v-if="selectedDoctor" style="margin-bottom: 16px">
        <p><strong>医生：</strong>{{ selectedDoctor.full_name }} ({{ selectedDoctor.title }})</p>
        <p><strong>科室：</strong>{{ selectedDoctor.department_name }}</p>
      </div>
      <el-form-item label="可预约时段">
        <el-select v-model="selectedScheduleId" placeholder="选择时段" style="width: 100%">
          <el-option v-for="schedule in schedules" :key="schedule.id" :disabled="schedule.booked >= schedule.capacity" :value="schedule.id" :label="`${schedule.work_date} ${schedule.slot === 'am' ? '上午' : '下午'}（剩余 ${schedule.capacity - schedule.booked} 个号）${schedule.work_date === today ? ' ⭐ 今天可就诊' : ''}`" />
        </el-select>
      </el-form-item>
      <template #footer>
        <el-button @click="showBookingDialog = false">取消</el-button>
        <el-button type="primary" @click="handleBook">确认预约</el-button>
      </template>
    </el-dialog>
  </div>
</template>
