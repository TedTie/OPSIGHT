<template>
  <div class="task-participation">
    <!-- 金额任务参与 -->
    <div v-if="task.task_type === 'amount'" class="amount-task">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>金额任务参与</span>
            <el-progress 
              :percentage="getAmountProgress()" 
              :status="task.status === 'done' ? 'success' : ''"
            />
          </div>
        </template>
        
        <div class="task-info">
          <p><strong>目标金额：</strong>{{ task.target_amount || 0 }}</p>
          <p><strong>当前金额：</strong>{{ task.current_amount || 0 }}</p>
          <p><strong>剩余金额：</strong>{{ (task.target_amount || 0) - (task.current_amount || 0) }}</p>
        </div>
        
        <el-form v-if="task.status !== 'done'" @submit.prevent="submitAmount">
          <el-form-item label="参与金额">
            <el-input-number
              v-model="amountForm.amount"
              :min="0.01"
              :precision="2"
              placeholder="请输入参与金额"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="备注">
            <el-input
              v-model="amountForm.remark"
              type="textarea"
              :rows="2"
              placeholder="请输入备注（可选）"
            />
          </el-form-item>
          <el-form-item>
            <el-button 
              v-can:task.participate="task"
              type="primary" 
              @click="submitAmount" 
              :loading="submitting"
            >
              提交参与
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- 数量任务参与 -->
    <div v-if="task.task_type === 'quantity'" class="quantity-task">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>数量任务参与</span>
            <el-progress 
              :percentage="getQuantityProgress()" 
              :status="task.status === 'done' ? 'success' : ''"
            />
          </div>
        </template>
        
        <div class="task-info">
          <p><strong>目标数量：</strong>{{ task.target_quantity || 0 }}</p>
          <p><strong>当前数量：</strong>{{ task.current_quantity || 0 }}</p>
          <p><strong>剩余数量：</strong>{{ (task.target_quantity || 0) - (task.current_quantity || 0) }}</p>
        </div>
        
        <el-form v-if="task.status !== 'done'" @submit.prevent="submitQuantity">
          <el-form-item label="参与数量">
            <el-input-number
              v-model="quantityForm.quantity"
              :min="1"
              placeholder="请输入参与数量"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="备注">
            <el-input
              v-model="quantityForm.remark"
              type="textarea"
              :rows="2"
              placeholder="请输入备注（可选）"
            />
          </el-form-item>
          <el-form-item>
            <el-button 
              v-can:task.participate="task"
              type="primary" 
              @click="submitQuantity" 
              :loading="submitting"
            >
              提交参与
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- 接龙任务参与 -->
    <div v-if="task.task_type === 'jielong'" class="jielong-task">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>接龙任务参与</span>
            <el-progress 
              :percentage="getJielongProgress()" 
              :status="task.status === 'done' ? 'success' : ''"
            />
          </div>
        </template>
        
        <div class="task-info">
          <p><strong>目标接龙数量：</strong>{{ task.jielong_target_count || 0 }}</p>
          <p><strong>当前接龙数量：</strong>{{ task.jielong_current_count || 0 }}</p>
          <p><strong>剩余名额：</strong>{{ (task.jielong_target_count || 0) - (task.jielong_current_count || 0) }}</p>
        </div>
        
        <el-form v-if="task.status !== 'done' && !hasParticipated" @submit.prevent="submitJielong">
          <el-form-item v-if="jielongConfig.id_enabled" label="ID">
            <el-input v-model="jielongForm.id" placeholder="请输入ID" />
          </el-form-item>
          <el-form-item v-if="jielongConfig.remark_enabled" label="备注">
            <el-input
              v-model="jielongForm.remark"
              type="textarea"
              :rows="2"
              placeholder="请输入备注"
            />
          </el-form-item>
          <el-form-item v-if="jielongConfig.intention_enabled" label="意向">
            <el-select v-model="jielongForm.intention" placeholder="请选择意向">
              <el-option label="强烈意向" value="strong" />
              <el-option label="一般意向" value="medium" />
              <el-option label="了解一下" value="weak" />
            </el-select>
          </el-form-item>
          <el-form-item 
            v-if="jielongConfig.custom_field_enabled && jielongConfig.custom_field_name" 
            :label="jielongConfig.custom_field_name"
          >
            <el-input
              v-if="jielongConfig.custom_field_type === 'text'"
              v-model="jielongForm.custom_field"
              :placeholder="`请输入${jielongConfig.custom_field_name}`"
            />
            <el-input-number
              v-else
              v-model="jielongForm.custom_field"
              :placeholder="`请输入${jielongConfig.custom_field_name}`"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item>
            <el-button 
              v-can:task.participate="task"
              type="primary" 
              @click="submitJielong" 
              :loading="submitting"
            >
              参与接龙
            </el-button>
          </el-form-item>
        </el-form>
        
        <div v-if="hasParticipated" class="participated-notice">
          <el-alert
            title="您已参与此接龙任务"
            type="success"
            :closable="false"
          />
        </div>
      </el-card>

      <!-- 接龙参与列表 -->
      <el-card style="margin-top: 16px;">
        <template #header>
          <span>参与列表</span>
        </template>
        <el-table :data="jielongEntries" stripe>
          <el-table-column prop="entry_order" label="序号" width="80" />
          <el-table-column prop="user.username" label="用户" width="120" />
          <el-table-column v-if="jielongConfig.id_enabled" prop="entry_data.id" label="ID" width="120" />
          <el-table-column v-if="jielongConfig.remark_enabled" prop="entry_data.remark" label="备注" />
          <el-table-column v-if="jielongConfig.intention_enabled" prop="entry_data.intention" label="意向" width="100" />
          <el-table-column 
            v-if="jielongConfig.custom_field_enabled && jielongConfig.custom_field_name" 
            :prop="`entry_data.custom_field`" 
            :label="jielongConfig.custom_field_name" 
            width="120" 
          />
          <el-table-column prop="created_at" label="参与时间" width="180">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 勾选任务参与 -->
    <div v-if="task.task_type === 'checkbox'" class="checkbox-task">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>勾选任务</span>
            <el-tag :type="task.is_completed ? 'success' : 'info'">
              {{ task.is_completed ? '已完成' : '未完成' }}
            </el-tag>
          </div>
        </template>
        
        <div class="checkbox-content">
          <el-checkbox 
            v-can:task.participate="task"
            v-model="checkboxCompleted" 
            @change="toggleCheckbox"
            :disabled="submitting"
            size="large"
          >
            {{ task.is_completed ? '任务已完成' : '标记为完成' }}
          </el-checkbox>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { formatDateTime } from '@/utils/date'
import api from '@/utils/api'

const props = defineProps({
  task: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['refresh'])

// 数据
const submitting = ref(false)
const jielongEntries = ref([])
const hasParticipated = ref(false)

// 表单数据
const amountForm = reactive({
  amount: null,
  remark: ''
})

const quantityForm = reactive({
  quantity: null,
  remark: ''
})

const jielongForm = reactive({
  id: '',
  remark: '',
  intention: '',
  custom_field: ''
})

const checkboxCompleted = ref(false)

// 接龙配置
const jielongConfig = computed(() => {
  return props.task.jielong_config || {}
})

// 计算进度
const getAmountProgress = () => {
  if (!props.task.target_amount) return 0
  return Math.min(100, (props.task.current_amount || 0) / props.task.target_amount * 100)
}

const getQuantityProgress = () => {
  if (!props.task.target_quantity) return 0
  return Math.min(100, (props.task.current_quantity || 0) / props.task.target_quantity * 100)
}

const getJielongProgress = () => {
  if (!props.task.jielong_target_count) return 0
  return Math.min(100, (props.task.jielong_current_count || 0) / props.task.jielong_target_count * 100)
}

// 提交金额任务
const submitAmount = async () => {
  if (!amountForm.amount) {
    ElMessage.error('请输入参与金额')
    return
  }
  
  submitting.value = true
  try {
    // 调用新的任务同步API
    const response = await api.post(`/task-sync/sync-task-to-report/${props.task.id}`, {
      task_id: props.task.id,
      completion_value: amountForm.amount,
      completion_data: {
        remark: amountForm.remark
      },
      is_completed: false
    })
    
    ElMessage.success('参与成功，已同步到日报')
    if (response.data.task_achievement) {
      ElMessage.info(`成就记录：${response.data.task_achievement}`)
    }
    
    amountForm.amount = null
    amountForm.remark = ''
    emit('refresh')
  } catch (error) {
    ElMessage.error('参与失败')
  } finally {
    submitting.value = false
  }
}

// 提交数量任务
const submitQuantity = async () => {
  if (!quantityForm.quantity) {
    ElMessage.error('请输入参与数量')
    return
  }
  
  submitting.value = true
  try {
    // 调用新的任务同步API
    const response = await api.post(`/task-sync/sync-task-to-report/${props.task.id}`, {
      task_id: props.task.id,
      completion_value: quantityForm.quantity,
      completion_data: {
        remark: quantityForm.remark
      },
      is_completed: false
    })
    
    ElMessage.success('参与成功，已同步到日报')
    if (response.data.task_achievement) {
      ElMessage.info(`成就记录：${response.data.task_achievement}`)
    }
    
    quantityForm.quantity = null
    quantityForm.remark = ''
    emit('refresh')
  } catch (error) {
    ElMessage.error('参与失败')
  } finally {
    submitting.value = false
  }
}

// 提交接龙任务
const submitJielong = async () => {
  submitting.value = true
  try {
    const entryData = {}
    
    if (jielongConfig.value.id_enabled) {
      entryData.id = jielongForm.id
    }
    if (jielongConfig.value.remark_enabled) {
      entryData.remark = jielongForm.remark
    }
    if (jielongConfig.value.intention_enabled) {
      entryData.intention = jielongForm.intention
    }
    if (jielongConfig.value.custom_field_enabled && jielongConfig.value.custom_field_name) {
      entryData.custom_field = jielongForm.custom_field
    }
    
    await api.post(`/tasks/${props.task.id}/jielong`, {
      entry_data: entryData
    })
    
    ElMessage.success('参与接龙成功')
    Object.assign(jielongForm, {
      id: '',
      remark: '',
      intention: '',
      custom_field: ''
    })
    
    fetchJielongEntries()
    emit('refresh')
  } catch (error) {
    ElMessage.error('参与接龙失败')
  } finally {
    submitting.value = false
  }
}

// 切换勾选状态
const toggleCheckbox = async (checked) => {
  submitting.value = true
  try {
    // 调用新的任务同步API
    const response = await api.post(`/task-sync/sync-task-to-report/${props.task.id}`, {
      task_id: props.task.id,
      completion_value: null,
      completion_data: {},
      is_completed: checked
    })
    
    ElMessage.success(checked ? '任务已完成，已同步到日报' : '任务已取消完成')
    if (checked && response.data.task_achievement) {
      ElMessage.info(`成就记录：${response.data.task_achievement}`)
    }
    
    emit('refresh')
  } catch (error) {
    ElMessage.error('操作失败')
    checkboxCompleted.value = !checked // 回滚状态
  } finally {
    submitting.value = false
  }
}

// 获取接龙参与列表
const fetchJielongEntries = async () => {
  if (props.task.task_type !== 'jielong') return
  
  try {
    const response = await api.get(`/tasks/${props.task.id}/jielong`)
    jielongEntries.value = response.data || []
    
    // 检查当前用户是否已参与
    const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
    hasParticipated.value = jielongEntries.value.some(entry => entry.user_id === currentUser.id)
  } catch (error) {
    console.error('获取接龙列表失败:', error)
  }
}

// 初始化
onMounted(() => {
  if (props.task.task_type === 'checkbox') {
    checkboxCompleted.value = props.task.is_completed || false
  }
  
  if (props.task.task_type === 'jielong') {
    fetchJielongEntries()
  }
})
</script>

<style scoped>
.task-participation {
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-info {
  margin-bottom: 16px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.task-info p {
  margin: 4px 0;
}

.checkbox-content {
  text-align: center;
  padding: 20px;
}

.participated-notice {
  margin-top: 16px;
}

.el-progress {
  width: 200px;
}

@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    gap: 8px;
  }
  
  .el-progress {
    width: 100%;
  }
}
</style>