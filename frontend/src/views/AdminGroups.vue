<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">组织管理</h1>
      <p class="page-description">管理组织架构和成员</p>
    </div>
    
    <el-card class="content-card">
      <template #header>
        <div class="card-header">
          <span>组织列表</span>
          <el-button 
            v-if="authStore.isSuperAdmin" 
            type="primary" 
            :icon="Plus" 
            @click="showCreateDialog"
          >
            新增组织
          </el-button>
        </div>
      </template>
      
      <div class="table-toolbar">
        <div class="table-filters">
          <el-input
            v-model="filters.search"
            placeholder="搜索组织..."
            :prefix-icon="Search"
            clearable
          />
        </div>
        
        <div class="table-actions">
          <el-button :icon="Refresh" @click="fetchGroups">刷新</el-button>
        </div>
      </div>
      
      <el-table
        v-loading="loading"
        :data="groups"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="name" label="组织名称" min-width="200" />
        <el-table-column prop="description" label="描述" min-width="300" />
        <el-table-column label="成员数量" width="120">
          <template #default="{ row }">
            {{ row.member_count || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="text" size="small" @click="viewMembers(row)">
              成员
            </el-button>
            <el-button 
              v-if="authStore.isSuperAdmin" 
              type="text" 
              size="small" 
              @click="editGroup(row)"
            >
              编辑
            </el-button>
            <el-button 
              v-if="authStore.isSuperAdmin" 
              type="text" 
              size="small" 
              @click="deleteGroup(row)"
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
          @size-change="fetchGroups"
          @current-change="fetchGroups"
        />
      </div>
    </el-card>
    
    <!-- 创建/编辑组织对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑组织' : '新增组织'"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="80px"
      >
        <el-form-item label="组织名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入组织描述"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 成员管理对话框 -->
    <el-dialog
      v-model="membersDialogVisible"
      :title="`${currentGroup?.name} - 成员管理`"
      width="800px"
    >
      <div class="members-toolbar">
        <el-button 
          v-if="authStore.isSuperAdmin" 
          type="primary" 
          :icon="Plus" 
          @click="showAddMemberDialog"
        >
          添加成员
        </el-button>
      </div>
      
      <el-table
        v-loading="membersLoading"
        :data="members"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="full_name" label="姓名" width="120" />
        <el-table-column prop="email" label="邮箱" min-width="200" />
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="getUserRoleColor(row.role)" size="small">
              {{ formatUserRole(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button 
              v-if="authStore.isSuperAdmin" 
              type="text" 
              size="small" 
              @click="removeMember(row)"
            >
              移除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
    
    <!-- 添加成员对话框 -->
    <el-dialog
      v-model="addMemberDialogVisible"
      title="添加成员"
      width="500px"
    >
      <el-form label-width="80px">
        <el-form-item label="选择用户">
          <el-select
            v-model="selectedUsers"
            multiple
            filterable
            placeholder="请选择用户"
            style="width: 100%"
          >
            <el-option
              v-for="user in availableUsers"
              :key="user.id"
              :label="`${user.username} (${user.full_name})`"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="addMemberDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="addMembers" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/date'
import { formatUserRole, getUserRoleColor } from '@/utils/auth'
import { useAuthStore } from '@/stores/auth'
import api from '@/utils/api'

// 权限控制
const authStore = useAuthStore()

// 数据
const loading = ref(false)
const membersLoading = ref(false)
const submitting = ref(false)
const groups = ref([])
const members = ref([])
const availableUsers = ref([])
const dialogVisible = ref(false)
const membersDialogVisible = ref(false)
const addMemberDialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()
const currentGroup = ref(null)
const selectedUsers = ref([])

// 过滤器
const filters = reactive({
  search: ''
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 表单数据
const form = reactive({
  name: '',
  description: ''
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入组织名称', trigger: 'blur' },
    { min: 2, max: 100, message: '组织名称长度在 2 到 100 个字符', trigger: 'blur' }
  ]
}

// 获取组织列表
const fetchGroups = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      search: filters.search
    }
    
    const response = await api.get('/groups', { params })
    const data = response.data || []
    // 兼容后端两种返回格式：分页对象或纯数组
    groups.value = (data.items && Array.isArray(data.items)) ? data.items : (Array.isArray(data) ? data : [])
    pagination.total = (typeof data.total === 'number') ? data.total : (Array.isArray(data) ? data.length : 0)
  } catch (error) {
    ElMessage.error('获取组织列表失败')
  } finally {
    loading.value = false
  }
}

// 显示创建对话框
const showCreateDialog = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

// 编辑组织
const editGroup = (group) => {
  isEdit.value = true
  Object.assign(form, {
    id: parseInt(group.id), // 确保ID是数字类型
    name: group.name,
    description: group.description
  })
  dialogVisible.value = true
}

// 重置表单
const resetForm = () => {
  Object.assign(form, {
    id: '',
    name: '',
    description: ''
  })
  formRef.value?.clearValidate()
}

// 提交表单
const submitForm = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true
    
    if (isEdit.value) {
      await api.put(`/groups/${form.id}`, form)
      ElMessage.success('更新成功')
    } else {
      await api.post('/groups', form)
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    fetchGroups()
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

// 删除组织
const deleteGroup = async (group) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除组织 ${group.name} 吗？此操作不可恢复！`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.delete(`/groups/${parseInt(group.id)}`)
    ElMessage.success('删除成功')
    fetchGroups()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 查看成员
const viewMembers = async (group) => {
  currentGroup.value = group
  membersDialogVisible.value = true
  await fetchMembers(parseInt(group.id))
}

// 获取成员列表
const fetchMembers = async (groupId) => {
  membersLoading.value = true
  try {
    const response = await api.get(`/groups/${groupId}/members`)
    members.value = response.data || []
  } catch (error) {
    ElMessage.error('获取成员列表失败')
  } finally {
    membersLoading.value = false
  }
}

// 显示添加成员对话框
const showAddMemberDialog = async () => {
  try {
    // 获取可用用户列表（排除已在组织中的用户）
    const response = await api.get('/users', {
      params: { size: 1000 }
    })
    const allUsers = response.data.items || []
    const memberIds = members.value.map(m => m.id)
    availableUsers.value = allUsers.filter(user => !memberIds.includes(user.id))
    
    selectedUsers.value = []
    addMemberDialogVisible.value = true
  } catch (error) {
    ElMessage.error('获取用户列表失败')
  }
}

// 添加成员
const addMembers = async () => {
  if (selectedUsers.value.length === 0) {
    ElMessage.warning('请选择要添加的用户')
    return
  }
  
  submitting.value = true
  try {
    await api.post(`/groups/${currentGroup.value.id}/members`, {
      user_ids: selectedUsers.value
    })
    
    ElMessage.success('添加成功')
    addMemberDialogVisible.value = false
    fetchMembers(currentGroup.value.id)
  } catch (error) {
    ElMessage.error('添加失败')
  } finally {
    submitting.value = false
  }
}

// 移除成员
const removeMember = async (member) => {
  try {
    await ElMessageBox.confirm(
      `确定要将 ${member.username} 从组织中移除吗？`,
      '确认移除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.delete(`/groups/${currentGroup.value.id}/members/${member.id}`)
    ElMessage.success('移除成功')
    fetchMembers(currentGroup.value.id)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('移除失败')
    }
  }
}

// 初始化
onMounted(() => {
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

.members-toolbar {
  margin-bottom: 16px;
}

@media (max-width: 768px) {
  .table-filters {
    flex-direction: column;
  }
}
</style>