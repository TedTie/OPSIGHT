<template>
  <div class="filters-bar">
    <el-radio-group v-model="local.timeRange" @change="onRangeChange">
      <el-radio-button label="today">今日</el-radio-button>
      <el-radio-button label="week">本周</el-radio-button>
      <el-radio-button label="month">本月</el-radio-button>
      <el-radio-button label="custom">自定义</el-radio-button>
    </el-radio-group>

    <el-date-picker
      v-if="local.timeRange === 'custom'"
      v-model="local.dateRange"
      type="daterange"
      range-separator="至"
      start-placeholder="开始日期"
      end-placeholder="结束日期"
      format="YYYY-MM-DD"
      value-format="YYYY-MM-DD"
      @change="emitChange"
    />

    <el-select v-model="local.role" placeholder="视角" style="width: 160px" @change="emitChange">
      <el-option label="CC(顾问)" value="CC" />
      <el-option label="SS(班主任)" value="SS" />
      <el-option label="LP(英文辅导)" value="LP" />
      <el-option label="全体" value="ALL" />
    </el-select>

    <el-select v-model="local.groupId" placeholder="组织" clearable style="width: 200px" @change="onGroupChange">
      <el-option label="全部组织" :value="null" />
      <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
    </el-select>

    <el-select v-model="local.userId" placeholder="用户" clearable filterable style="width: 220px" @change="emitChange">
      <el-option label="全部用户" :value="null" />
      <el-option v-for="u in displayedUsers" :key="u.id" :label="u.username" :value="u.id" />
    </el-select>
  </div>
</template>

<script setup>
import { reactive, watch, ref, computed, onMounted } from 'vue'
import api from '@/utils/api'
import { getWeekStartEnd, getMonthStartEnd, getTodayString } from '@/utils/date'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  modelValue: { type: Object, required: true }
})
const emit = defineEmits(['update:modelValue'])

const authStore = useAuthStore()
const local = reactive({
  timeRange: props.modelValue.timeRange || 'month',
  dateRange: props.modelValue.dateRange || [],
  groupId: props.modelValue.groupId || null,
  // 超级管理员默认“全局”，否则保持为“CC”；若父组件明确传值，则以父组件为准
  role: props.modelValue.role ?? (authStore?.isSuperAdmin ? 'ALL' : 'CC'),
  userId: props.modelValue.userId || null
})

// 选项数据
const groups = ref([])
const users = ref([])
const displayedUsers = computed(() => {
  if (!local.groupId) return users.value
  return users.value.filter(u => u.group_id === local.groupId)
})

function emitChange() {
  emit('update:modelValue', { ...local })
}

function onRangeChange() {
  if (local.timeRange === 'today') {
    const t = getTodayString()
    local.dateRange = [t, t]
  } else if (local.timeRange === 'week') {
    local.dateRange = getWeekStartEnd(new Date())
  } else if (local.timeRange === 'month') {
    local.dateRange = getMonthStartEnd(new Date())
  }
  emitChange()
}

function onGroupChange() {
  // 切换组织时，如果当前用户不在新组织内，重置为全部用户
  const inGroup = displayedUsers.value.some(u => u.id === local.userId)
  if (!inGroup) local.userId = null
  emitChange()
}

// 加载组织与用户选项（根据权限自动裁剪）
async function loadGroupsAndUsers() {
  try {
    const [{ data: gRes }, { data: uRes }] = await Promise.all([
      api.get('/groups', { params: { page: 1, size: 100 }, suppressErrorMessage: true }),
      api.get('/users', { params: { page: 1, size: 100 }, suppressErrorMessage: true })
    ])
    groups.value = Array.isArray(gRes?.items) ? gRes.items : []
    users.value = Array.isArray(uRes?.items) ? uRes.items : []
  } catch (e) {
    // 无权限或未登录时保持空列表，但不打扰用户
    groups.value = []
    users.value = []
  }
}

// 同步外部变更
watch(() => props.modelValue, (v) => {
  Object.assign(local, v || {})
})

onMounted(() => {
  // 若用户信息尚未初始化，尝试恢复
  if (!authStore.user) {
    try { authStore.initAuth() } catch {}
  }
  // 超级管理员强制默认为“全局”并同步父组件
  if (authStore.isSuperAdmin && local.role !== 'ALL') {
    local.role = 'ALL'
    emitChange()
  }
  loadGroupsAndUsers()
})
</script>

<style scoped>
.filters-bar { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
</style>