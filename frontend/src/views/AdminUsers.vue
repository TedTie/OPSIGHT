<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">用户管理</h1>
      <p class="page-description">管理系统用户和权限</p>
    </div>
    
    <el-card class="content-card">
      <template #header>
        <div class="card-header">
          <span>用户列表</span>
          <el-button type="primary" :icon="Plus" @click="showCreateDialog">
            新增用户
          </el-button>
        </div>
      </template>
      
      <div class="table-toolbar">
        <div class="table-filters">
          <el-input
            v-model="filters.search"
            placeholder="搜索用户..."
            :prefix-icon="Search"
            clearable
          />
          
          <el-select
            v-model="filters.role"
            placeholder="角色筛选"
            clearable
          >
            <el-option label="普通用户" value="user" />
            <el-option label="管理员" value="admin" />
            <el-option label="超级管理员" value="super_admin" />
          </el-select>
          
          <el-select
            v-model="filters.is_active"
            placeholder="状态筛选"
            clearable
          >
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </div>
        
        <div class="table-actions">
          <el-button :icon="Refresh" @click="fetchUsers">刷新</el-button>
        </div>
      </div>
      
      <el-table
        v-loading="loading"
        :data="users"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="organization" label="组织" min-width="180" />
        <el-table-column label="权限" width="100">
          <template #default="{ row }">
            <el-tag :type="getUserRoleColor(row.role)" size="small">
              {{ formatUserRole(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="身份" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.identity_type" type="info" size="small">
              {{ formatIdentityType(row.identity_type) }}
            </el-tag>
            <span v-else class="text-gray-400">-</span>
          </template>
        </el-table-column>
        <el-table-column label="组别" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.group_name" type="primary" size="small">
              {{ row.group_name }}
            </el-tag>
            <span v-else class="text-gray-400">-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="text" size="small" @click="editUser(row)">
              编辑
            </el-button>
            <el-button 
              type="text" 
              size="small" 
              @click="toggleUserStatus(row)"
              :disabled="row.role === 'super_admin'"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button 
              type="text" 
              size="small" 
              @click="deleteUser(row)"
              :disabled="row.role === 'super_admin'"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchUsers"
          @current-change="fetchUsers"
        />
      </div>
    </el-card>
    
    <!-- 创建/编辑用户对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑用户' : '新增用户'"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="isEdit" />
        </el-form-item>
        
        <el-form-item label="组织" prop="organization">
          <el-input v-model="form.organization" placeholder="请输入组织名称" />
        </el-form-item>
        
        <el-form-item label="权限" prop="role">
          <el-select v-model="form.role" style="width: 100%">
            <el-option label="普通用户" value="user" />
            <el-option label="管理员" value="admin" />
            <el-option label="超级管理员" value="super_admin" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="身份" prop="identity_type">
          <el-select v-model="form.identity_type" style="width: 100%" clearable>
            <el-option label="CC(顾问)" value="cc" />
            <el-option label="SS(班主任)" value="ss" />
            <el-option label="LP(英文辅导)" value="lp" />
            <el-option label="SA(超级分析师)" value="sa" />
          </el-select>
        </el-form-item>

        <!-- 创建时必须填写初始密码与确认密码 -->
        <el-form-item v-if="!isEdit" label="初始密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入至少6位密码" show-password />
        </el-form-item>
        <el-form-item v-if="!isEdit" label="确认密码" prop="confirm_password">
          <el-input v-model="form.confirm_password" type="password" placeholder="请再次输入" show-password />
        </el-form-item>

        <!-- 编辑时支持修改密码（留空不改） -->
        <el-form-item v-if="isEdit" label="新密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="留空则不修改" show-password />
        </el-form-item>
        <el-form-item v-if="isEdit" label="确认密码" prop="confirm_password">
          <el-input v-model="form.confirm_password" type="password" placeholder="请再次输入" show-password />
        </el-form-item>

        <el-form-item label="组别" prop="group_id">
          <el-select v-model="form.group_id" style="width: 100%" clearable placeholder="请选择组别">
            <el-option 
              v-for="group in groups" 
              :key="group.id" 
              :label="group.name" 
              :value="group.id" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import Plus from '~icons/tabler/plus'
import Search from '~icons/tabler/search'
import Refresh from '~icons/tabler/refresh'
import { formatDateTime } from '@/utils/date'
import { formatUserRole, getUserRoleColor } from '@/utils/auth'
import api from '@/utils/api'

// 格式化身份类型显示
const formatIdentityType = (identityType) => {
  const identityNames = {
    'cc': 'CC(顾问)',
    'ss': 'SS(班主任)',
    'lp': 'LP(英文辅导)',
    'sa': 'SA(超级分析师)'
  }
  return identityNames[identityType] || identityType
}

// 数据
const loading = ref(false)
const submitting = ref(false)
const users = ref([])
const groups = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()

// 过滤器
const filters = reactive({
  search: '',
  role: '',
  is_active: ''
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 表单数据
const form = reactive({
  username: '',
  organization: '',
  role: 'user',
  identity_type: null,
  group_id: null,
  is_active: true,
  password: '',
  confirm_password: ''
})

// 表单验证规则
const formRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择权限', trigger: 'change' }
  ],
  password: [
    {
      validator: (rule, value, callback) => {
        // 创建时必填且至少6位；编辑时可选，填写则至少6位
        if (!isEdit.value) {
          if (!value || String(value).length < 6) return callback(new Error('密码至少6位'))
          return callback()
        }
        if (!value) return callback()
        if (String(value).length < 6) return callback(new Error('密码至少6位'))
        return callback()
      },
      trigger: 'blur'
    }
  ],
  confirm_password: [
    {
      validator: (rule, value, callback) => {
        // 创建时必须与密码一致；编辑时仅在填写密码时需要一致
        if (!isEdit.value) {
          if (!value) return callback(new Error('请再次输入密码'))
          if (value !== form.password) return callback(new Error('两次输入的密码不一致'))
          return callback()
        }
        if (!form.password) return callback()
        if (value !== form.password) return callback(new Error('两次输入的密码不一致'))
        return callback()
      },
      trigger: 'blur'
    }
  ]
}

// 获取用户列表
const fetchUsers = async () => {
  loading.value = true
  try {
    // 过滤掉空值
    const filteredParams = Object.fromEntries(
      Object.entries(filters).filter(([key, value]) => value !== '' && value != null)
    )
    
    const params = {
      page: pagination.page,
      size: pagination.size,
      ...filteredParams
    }
    
    const response = await api.get('/users', { params })
    users.value = response.data.items || []
    pagination.total = response.data.total || 0
  } catch (error) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

// 获取组别列表
const fetchGroups = async () => {
  try {
    const response = await api.get('/groups')
    groups.value = response.data.items || []
  } catch (error) {
    console.error('获取组别列表失败:', error)
  }
}

// 显示创建对话框
const showCreateDialog = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

// 编辑用户
const editUser = (user) => {
  isEdit.value = true
  Object.assign(form, {
    id: parseInt(user.id), // 确保ID是数字类型
    username: user.username,
    organization: user.organization || '',
    role: user.role || 'user',
    identity_type: user.identity_type || null,
    group_id: user.group_id || null,
    is_active: user.is_active,
    password: '',
    confirm_password: ''
  })
  dialogVisible.value = true
}

// 重置表单
const resetForm = () => {
  Object.assign(form, {
    id: '',
    username: '',
    organization: '',
    role: 'user',
    identity_type: null,
    group_id: null,
    is_active: true,
    password: '',
    confirm_password: ''
  })
  formRef.value?.clearValidate()
}

// 提交表单
const submitForm = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true
    
    if (isEdit.value) {
      // 仅在填写新密码时提交密码；不提交确认字段
      const payload = { ...form }
      if (!payload.password) delete payload.password
      delete payload.confirm_password
      await api.put(`/users/${form.id}`, payload)
      ElMessage.success('更新成功')
    } else {
      // 创建时后端不接收 confirm_password 字段，避免422
      const payload = { ...form }
      delete payload.confirm_password
      await api.post('/users', payload)
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    fetchUsers()
  } catch (error) {
    if (error.response?.status === 422) {
      ElMessage.error('数据验证失败，请检查输入')
    } else {
      ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
    }
  } finally {
    submitting.value = false
  }
}

// 切换用户状态
const toggleUserStatus = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要${user.is_active ? '禁用' : '启用'}用户 ${user.username} 吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.put(`/users/${parseInt(user.id)}`, {
      ...user,
      is_active: !user.is_active
    })
    
    ElMessage.success('操作成功')
    fetchUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

// 删除用户
const deleteUser = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 ${user.username} 吗？此操作不可恢复！`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.delete(`/users/${user.id}`)
    ElMessage.success('删除成功')
    fetchUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 初始化
onMounted(() => {
  fetchUsers()
  fetchGroups()
})
</script>

<style scoped>
.table-toolbar {
  margin-bottom: 16px;
}

.table-filters {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

@media (max-width: 768px) {
  .table-filters {
    flex-direction: column;
  }
}
</style>