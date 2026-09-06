<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { getKnowledgeBaseApi, createKBArticleApi, updateKBArticleApi, deleteKBArticleApi, type KnowledgeBaseItem } from '@/api/modules/kb'
import { ElMessage, ElMessageBox } from 'element-plus'

const articles = ref<KnowledgeBaseItem[]>([])
const loading = ref(false)
const showDialog = ref(false)
const isEdit = ref(false)
const editId = ref(0)

const form = reactive({
  title: '',
  content: '',
  category: ''
})

const categories = ref<string[]>(['疾病知识', '用药指南', '就诊流程', '常见问题'])
const filterCategory = ref('')

async function fetchArticles() {
  loading.value = true
  try {
    articles.value = await getKnowledgeBaseApi(filterCategory.value ? { category: filterCategory.value } : undefined)
  } catch {
    ElMessage.error('获取知识库失败')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  isEdit.value = false
  form.title = ''
  form.content = ''
  form.category = ''
  showDialog.value = true
}

function openEdit(item: KnowledgeBaseItem) {
  isEdit.value = true
  editId.value = item.id
  form.title = item.title
  form.content = item.content || ''
  form.category = item.category || item.source || ''
  showDialog.value = true
}

async function handleSave() {
  if (!form.title || !form.content) {
    ElMessage.warning('请填写标题和内容')
    return
  }
  try {
    if (isEdit.value) {
      await updateKBArticleApi(editId.value, { ...form })
      ElMessage.success('更新成功')
    } else {
      await createKBArticleApi({ ...form })
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    fetchArticles()
  } catch {
    ElMessage.error('操作失败')
  }
}

async function handleDelete(item: KnowledgeBaseItem) {
  try {
    await ElMessageBox.confirm(`确定删除「${item.title}」？`, '提示', { type: 'warning' })
    await deleteKBArticleApi(item.id)
    ElMessage.success('已删除')
    fetchArticles()
  } catch {
    // user cancelled
  }
}

onMounted(fetchArticles)
</script>

<template>
  <div style="background: #fff; border-radius: 8px; padding: 20px">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px">
      <div style="display: flex; gap: 12px; align-items: center">
        <h3>知识库管理</h3>
        <el-select v-model="filterCategory" placeholder="按分类筛选" clearable style="width: 150px" @change="fetchArticles">
          <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
        </el-select>
      </div>
      <el-button type="primary" @click="openCreate">新建文章</el-button>
    </div>

    <el-table :data="articles" v-loading="loading" stripe>
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="category" label="分类" width="120" />
      <el-table-column prop="updated_at" label="更新时间" width="180" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button type="primary" size="small" link @click="openEdit(row)">编辑</el-button>
          <el-button type="danger" size="small" link @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showDialog" :title="isEdit ? '编辑文章' : '新建文章'" width="600px">
      <el-form label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category" placeholder="选择分类" style="width: 100%">
            <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="form.content" type="textarea" :rows="10" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
