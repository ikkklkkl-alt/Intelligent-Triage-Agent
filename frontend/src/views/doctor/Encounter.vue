<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getEncounterDetailApi,
  getEncounterOrdersApi,
  saveEncounterApi,
  completeEncounterApi,
  createPrescriptionApi,
  createLabOrderApi,
  type MedicalRecord,
  type Prescription,
  type LabOrder
} from '@/api/modules/encounters'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const encounterId = Number(route.params.id)
interface EncounterRecord extends MedicalRecord {
  patient_name: string
  status: string
}
const record = ref<EncounterRecord | null>(null)
const loading = ref(false)
const activeTab = ref('record')

const recordForm = reactive({
  chief_complaint: '',
  diagnosis: '',
  plan: ''
})

const prescriptionForm = reactive({
  drug_name: '',
  spec: '',
  quantity: 1,
  price: 0,
  usage: ''
})
const showPrescriptionDialog = ref(false)

const labOrderForm = reactive({
  item_name: '',
  fee: 0
})
const showLabOrderDialog = ref(false)

async function fetchRecord() {
  loading.value = true
  try {
    const enc = await getEncounterDetailApi(encounterId)
    const orders = await getEncounterOrdersApi(encounterId)
    record.value = {
      id: enc.id,
      appointment_id: enc.appointment_id,
      patient_name: enc.patient_name,
      status: enc.status,
      chief_complaint: enc.chief_complaint || '',
      diagnosis: enc.diagnosis,
      plan: enc.plan,
      prescriptions: orders.prescriptions || [],
      lab_orders: orders.lab_orders || []
    } as EncounterRecord
    recordForm.chief_complaint = enc.chief_complaint || ''
    recordForm.diagnosis = enc.diagnosis || ''
    recordForm.plan = enc.plan || ''
  } catch {
    ElMessage.error('获取病历失败')
  } finally {
    loading.value = false
  }
}

async function handleSaveRecord() {
  try {
    await saveEncounterApi(encounterId, { ...recordForm })
    ElMessage.success('病历已保存')
  } catch {
    ElMessage.error('保存失败')
  }
}

async function handleComplete() {
  try {
    await ElMessageBox.confirm('确定完成本次接诊吗？', '提示', { type: 'warning' })
    await completeEncounterApi(encounterId)
    ElMessage.success('接诊已完成')
    router.push('/doctor/worklist')
  } catch {
    // user cancelled or error
  }
}

async function handleAddPrescription() {
  if (!prescriptionForm.drug_name) {
    ElMessage.warning('请输入药品名称')
    return
  }
  try {
    const newRx = await createPrescriptionApi(encounterId, { ...prescriptionForm })
    if (record.value) {
      record.value.prescriptions.push(newRx)
    }
    ElMessage.success('处方已添加')
    showPrescriptionDialog.value = false
    Object.assign(prescriptionForm, { drug_name: '', spec: '', quantity: 1, price: 0, usage: '' })
  } catch {
    ElMessage.error('添加处方失败')
  }
}

async function handleAddLabOrder() {
  if (!labOrderForm.item_name) {
    ElMessage.warning('请输入检验项目')
    return
  }
  try {
    const newOrder = await createLabOrderApi(encounterId, { ...labOrderForm })
    if (record.value) {
      record.value.lab_orders.push(newOrder)
    }
    ElMessage.success('检验单已开具')
    showLabOrderDialog.value = false
    Object.assign(labOrderForm, { item_name: '', fee: 0 })
  } catch {
    ElMessage.error('开具检验单失败')
  }
}

onMounted(fetchRecord)
</script>

<template>
  <div style="background: #fff; border-radius: 8px; padding: 20px" v-loading="loading">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px">
      <h3>接诊 - {{ record?.patient_name || '加载中...' }}</h3>
      <div style="display: flex; gap: 8px">
        <el-button @click="router.push('/doctor/worklist')">返回</el-button>
        <el-button type="primary" @click="handleSaveRecord">保存病历</el-button>
        <el-button type="success" @click="handleComplete">完成接诊</el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="病历" name="record">
        <el-form label-width="100px" style="max-width: 700px">
          <el-form-item label="主诉">
            <el-input v-model="recordForm.chief_complaint" type="textarea" :rows="2" />
          </el-form-item>
          <el-form-item label="诊断">
            <el-input v-model="recordForm.diagnosis" type="textarea" :rows="2" />
          </el-form-item>
          <el-form-item label="诊疗计划">
            <el-input v-model="recordForm.plan" type="textarea" :rows="3" />
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="处方" name="prescriptions">
        <el-button type="primary" style="margin-bottom: 12px" @click="showPrescriptionDialog = true">开处方</el-button>
        <el-table :data="record?.prescriptions || []" stripe>
          <el-table-column label="药品"><template #default="{ row }">{{ row.items.map((i: any) => i.drug_name).join('、') }}</template></el-table-column>
          <el-table-column prop="total_fee" label="金额" width="120" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="检验" name="lab-orders">
        <el-button type="primary" style="margin-bottom: 12px" @click="showLabOrderDialog = true">开检验单</el-button>
        <el-table :data="record?.lab_orders || []" stripe>
          <el-table-column prop="item_name" label="检验项目" />
          <el-table-column prop="fee" label="金额" />
          <el-table-column prop="status" label="状态" width="120" />
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="showPrescriptionDialog" title="开处方" width="500px">
      <el-form label-width="80px">
        <el-form-item label="药品"><el-input v-model="prescriptionForm.drug_name" /></el-form-item>
        <el-form-item label="规格"><el-input v-model="prescriptionForm.spec" /></el-form-item>
        <el-form-item label="数量"><el-input-number v-model="prescriptionForm.quantity" :min="1" /></el-form-item>
        <el-form-item label="单价"><el-input-number v-model="prescriptionForm.price" :min="0" :precision="2" /></el-form-item>
        <el-form-item label="用法"><el-input v-model="prescriptionForm.usage" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPrescriptionDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddPrescription">确认</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showLabOrderDialog" title="开检验单" width="500px">
      <el-form label-width="80px">
        <el-form-item label="项目"><el-input v-model="labOrderForm.item_name" /></el-form-item>
        <el-form-item label="费用"><el-input-number v-model="labOrderForm.fee" :min="0" :precision="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showLabOrderDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddLabOrder">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>
