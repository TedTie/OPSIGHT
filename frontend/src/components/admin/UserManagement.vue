<template>
  <div class="user-management">
    <div class="page-header">
      <h2>用户管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        创建用户
      </el-button>
    </div>

    <!-- 用户列表 -->
    <el-card class="user-list-card">
      <el-table :data="users" v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="identity_type" label="身份">
          <template #default="{ row }">
            <el-tag :type="getIdentityTagType(row.identity_type)">
              {{ getIdentityLabel(row.identity_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="organization" label="组织" />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '活跃' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button type="primary" link @click="editUser(row)">编辑</el-button>
            <el-button
              type="danger"
              link
              @click="deleteUser(row)"
              :disabled="row.id === currentUserId"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建用户对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建用户"
      width="500px"
    >
      <el-form :model="createForm" :rules="rules" ref="createFormRef" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="createForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="身份" prop="identity_type">
          <el-select v-model="createForm.identity_type" placeholder="请选择身份">
            <el-option label="普通用户" value="user" />
            <el-option label="管理员" value="admin" />
            <el-option label="超级管理员" value="super_admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="组织" prop="organization">
          <el-input v-model="createForm.organization" placeholder="请输入组织名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createUser" :loading="creating">创建</el-button>
      </template>
    </el-dialog>

    <!-- 编辑用户对话框 -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑用户"
      width="500px"
    >
      <el-form :model="editForm" :rules="rules" ref="editFormRef" label-width="80px">
        <el-form-item label="身份" prop="identity_type">
          <el-select v-model="editForm.identity_type" placeholder="请选择身份">
            <el-option label="普通用户" value="user" />
            <el-option label="管理员" value="admin" />
            <el-option label="超级管理员" value="super_admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="组织" prop="organization">
          <el-input v-model="editForm.organization" placeholder="请输入组织名称" />
        </el-form-item>
        <el-form-item label="状态" prop="is_active">
          <el-switch
            v-model="editForm.is_active"
            active-text="活跃"
            inactive-text="禁用"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="updateUser" :loading="updating">更新</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import Plus from '~icons/tabler/plus'
import { useAuthStore } from '@/stores/auth'
import api from '@/utils/api'

const authStore = useAuthStore()

// 状态
const loading = ref(false)
const creating = ref(false)
const updating = ref(false)
const users = ref([])
const showCreateDialog = ref(false)
const showEditDialog = ref(false)

// 当前用户ID
const currentUserId = computed(() => authStore.user?.id)

// 表单引用
const createFormRef = ref()
const editFormRef = ref()

// 表单数据
const createForm = reactive({
  username: '',
  identity_type: 'user',
  organization: ''
})

const editForm = reactive({
  id: null,
  identity_type: 'user',
  organization: '',
  is_active: true
})

// 表单验证规则
const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  identity: [
    { required: true, message: '请选择身份', trigger: 'change' }
  ],
  organization: [
    { required: true, message: '请输入组织名称', trigger: 'blur' }
  ]
}

// 获取用户列表
const fetchUsers = async () => {
  loading.value = true
  try {
    const response = await api.get('/users')
    users.value = response.data
  } catch (error) {
    ElMessage.error('获取用户列表失败')
    console.error('Fetch users error:', error)
  } finally {
    loading.value = false
  }
}

// 创建用户
const createUser = async () => {
  if (!createFormRef.value) return

  try {
    await createFormRef.value.validate()
    creating.value = true

    await api.post('/users', createForm)
    ElMessage.success('用户创建成功')
    showCreateDialog.value = false
    resetCreateForm()
    await fetchUsers()
  } catch (error) {
    if (error?.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    }
  } finally {
    creating.value = false
  }
}

// 编辑用户
const editUser = (user) => {
  editForm.id = user.id
  editForm.identity_type = user.identity_type
  editForm.organization = user.organization
  editForm.is_active = user.is_active
  showEditDialog.value = true
}

// 更新用户
const updateUser = async () => {
  if (!editFormRef.value) return

  try {
    await editFormRef.value.validate()
    updating.value = true

    await api.put(`/users/${editForm.id}`, editForm)
    ElMessage.success('用户更新成功')
    showEditDialog.value = false
    await fetchUsers()
  } catch (error) {
    if (error?.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    }
  } finally {
    updating.value = false
  }
}

// 删除用户
const deleteUser = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await api.delete(`/users/${user.id}`)
    ElMessage.success('用户删除成功')
    await fetchUsers()
  } catch (error) {
    if (error !== 'cancel') {
      if (error?.response?.data?.detail) {
        ElMessage.error(error.response.data.detail)
      } else {
        ElMessage.error('删除用户失败')
      }
    }
  }
}

// 重置创建表单
const resetCreateForm = () => {
  createForm.username = ''
  createForm.identity_type = 'user'
  createForm.organization = ''
  if (createFormRef.value) {
    createFormRef.value.resetFields()
  }
}

// 身份标签样式
const getIdentityTagType = (identity) => {
  const types = {
    'super_admin': 'danger',
    'admin': 'warning',
    'user': 'info'
  }
  return types[identity] || 'info'
}

const getIdentityLabel = (identity) => {
  const labels = {
    'super_admin': '超级管理员',
    'admin': '管理员',
    'user': '普通用户'
  }
  return labels[identity] || '未知'
}

// 初始化
onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.user-management {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #2c3e50;
}

.user-list-card {
  margin-top: 20px;
}
</style>