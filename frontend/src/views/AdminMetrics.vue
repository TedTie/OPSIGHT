<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">指标管理</h1>
      <p class="page-description">月度目标与指标库管理</p>
    </div>

  <el-tabs v-model="activeTab">
      <!-- 月度目标设置 -->
      <el-tab-pane label="月度目标设置" name="goals">
        <el-card class="content-card">
          <template #header>
            <div class="card-header">
              <span>月度目标设置（含细分目标）</span>
              <div class="header-actions">
                <el-select v-model="targetYear" placeholder="年份" style="width: 120px" @change="loadMonthlyGoal">
                  <el-option v-for="y in yearOptions" :key="y" :label="String(y)" :value="y" />
                </el-select>
                <el-select v-model="targetMonth" placeholder="月份" style="width: 120px" @change="loadMonthlyGoal">
                  <el-option v-for="m in monthOptions" :key="m" :label="String(m)" :value="m" />
                </el-select>
                <el-button type="primary" :loading="savingGoal" @click="saveMonthlyGoal">保存</el-button>
              </div>
            </div>
          </template>
  <div class="goal-form">
    <el-form label-width="160px">
      <el-form-item label="新单目标金额 (USD)">
        <el-input v-model="newSignTargetAmount" placeholder="请输入本月新单目标金额" />
      </el-form-item>
      <el-form-item label="转介绍目标金额 (USD)">
        <el-input v-model="referralTargetAmount" placeholder="请输入本月转介绍目标金额" />
      </el-form-item>
      <el-form-item label="总续费目标金额 (USD)">
        <el-input v-model="renewalTotalTargetAmount" placeholder="请输入本月总续费目标金额（含续费+升舱金额）" />
      </el-form-item>
      <el-form-item label="升舱人数目标 (人)">
        <el-input v-model="upgradeTargetCount" placeholder="请输入本月升舱人数目标" />
      </el-form-item>
      <el-form-item label="销售总目标 (自动汇总)">
        <el-input :model-value="salesTotalTarget" disabled />
      </el-form-item>
    </el-form>
  </div>
        </el-card>
      </el-tab-pane>

      <!-- 指标库管理 -->
      <el-tab-pane label="指标库管理" name="library">
        <el-card class="content-card">
          <template #header>
            <div class="card-header">
              <span>系统指标库</span>
              <div class="header-actions">
                <el-button @click="fetchMetricDefs">刷新</el-button>
              </div>
            </div>
          </template>

          <div class="filters-bar">
            <el-input v-model="metricSearch" placeholder="搜索名称或Key" clearable style="width: 240px" />
          </div>

          <el-table :data="filteredMetrics" border stripe style="width: 100%" v-loading="loading">
            <el-table-column prop="name" label="名称" min-width="200" />
            <el-table-column prop="key" label="Key" min-width="220" />
            <el-table-column label="启用" width="140">
              <template #default="scope">
                <el-switch
                  v-model="scope.row.is_active"
                  :loading="scope.row.__saving"
                  @change="onToggleActive(scope.row)"
                />
              </template>
            </el-table-column>
            <el-table-column prop="default_roles" label="默认角色" min-width="160">
              <template #default="scope">
                <el-tag v-for="r in (scope.row.default_roles || [])" :key="r" size="small" style="margin-right:6px">{{ r }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 个人目标设置 -->
      <el-tab-pane label="个人目标设置" name="personal">
        <el-card class="content-card">
          <template #header>
            <div class="card-header">
              <span>个人目标设置（按身份→组织→年月）</span>
              <div class="header-actions">
                <el-select v-model="personalIdentity" placeholder="身份" style="width: 140px" @change="refreshGroupsForIdentity">
                  <el-option label="CC(顾问)" value="CC" />
                  <el-option label="SS(班主任)" value="SS" />
                </el-select>
                <el-select v-model="personalGroupId" placeholder="组织" style="width: 160px" @change="reloadPersonalRows">
                  <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
                </el-select>
                <el-select v-model="personalYear" placeholder="年份" style="width: 110px" @change="reloadPersonalRows">
                  <el-option v-for="y in yearOptions" :key="y" :label="String(y)" :value="y" />
                </el-select>
                <el-select v-model="personalMonth" placeholder="月份" style="width: 110px" @change="reloadPersonalRows">
                  <el-option v-for="m in monthOptions" :key="m" :label="String(m)" :value="m" />
                </el-select>
                <el-button type="primary" :loading="savingPersonal" @click="savePersonalGoals">批量保存</el-button>
              </div>
            </div>
          </template>
          <div>
            <el-table :data="personalRows" border stripe style="width: 100%" v-loading="loadingPersonal">
              <el-table-column prop="username" label="用户" min-width="160" />
              <el-table-column v-if="personalIdentity === 'CC'" label="新单目标金额(USD)" min-width="180">
                <template #default="{ row }">
                  <el-input v-model="row.new_sign_target_amount" placeholder="输入金额" />
                </template>
              </el-table-column>
              <el-table-column v-if="personalIdentity === 'CC'" label="转介绍目标金额(USD)" min-width="180">
                <template #default="{ row }">
                  <el-input v-model="row.referral_target_amount" placeholder="输入金额" />
                </template>
              </el-table-column>
              <el-table-column v-if="personalIdentity === 'CC'" label="销售总目标(自动)" width="160">
                <template #default="{ row }">
                  <el-input :model-value="computeCcSalesTarget(row)" disabled />
                </template>
              </el-table-column>

              <el-table-column v-if="personalIdentity === 'SS'" label="总续费目标金额(USD)" min-width="190">
                <template #default="{ row }">
                  <el-input v-model="row.renewal_total_target_amount" placeholder="输入金额" />
                </template>
              </el-table-column>
              <el-table-column v-if="personalIdentity === 'SS'" label="升舱人数目标(人)" width="160">
                <template #default="{ row }">
                  <el-input v-model="row.upgrade_target_count" placeholder="输入人数" />
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

// Tabs
const activeTab = ref('goals')

// 年月选择
const now = new Date()
const currentYear = now.getFullYear()
const currentMonth = now.getMonth() + 1
const yearOptions = computed(() => [currentYear - 1, currentYear, currentYear + 1])
const monthOptions = computed(() => Array.from({ length: 12 }, (_, i) => i + 1))
const targetYear = ref(currentYear)
const targetMonth = ref(currentMonth)

// 月度目标字段
const newSignTargetAmount = ref('')
const referralTargetAmount = ref('')
const renewalTotalTargetAmount = ref('')
const savingGoal = ref(false)
const upgradeTargetCount = ref('')

// 自动汇总的销售总目标展示
const salesTotalTarget = computed(() => {
  const cc = Number(newSignTargetAmount.value || 0) + Number(referralTargetAmount.value || 0)
  const ss = Number(renewalTotalTargetAmount.value || 0)
  return (cc + ss).toFixed(0)
})

// 指标库
const loading = ref(false)
const metrics = ref([])
const metricSearch = ref('')

const filteredMetrics = computed(() => {
  let list = metrics.value || []
  if (metricSearch.value) {
    const q = metricSearch.value.toLowerCase()
    list = list.filter(m => (m.name || '').toLowerCase().includes(q) || (m.key || '').toLowerCase().includes(q))
  }
  return list
})

onMounted(() => {
  loadMonthlyGoal()
  fetchMetricDefs()
  refreshGroupsForIdentity()
})

// 读取月度目标
async function loadMonthlyGoal() {
  try {
    const { data } = await api.get('/goals/monthly', { params: { year: targetYear.value, month: targetMonth.value, scope: 'global' } })
    const list = Array.isArray(data) ? data : (data?.items || [])
    const cc = list.find(g => String(g.identity_type || '').toUpperCase() === 'CC' && String(g.scope || '').toLowerCase() === 'global')
    const ss = list.find(g => String(g.identity_type || '').toUpperCase() === 'SS' && String(g.scope || '').toLowerCase() === 'global')
    newSignTargetAmount.value = cc?.new_sign_target_amount ?? ''
    referralTargetAmount.value = cc?.referral_target_amount ?? ''
    renewalTotalTargetAmount.value = ss?.renewal_total_target_amount ?? ''
    upgradeTargetCount.value = ss?.upgrade_target_count ?? ''
  } catch (err) {
    newSignTargetAmount.value = ''
    referralTargetAmount.value = ''
    renewalTotalTargetAmount.value = ''
    upgradeTargetCount.value = ''
  }
}

// 保存月度目标
async function saveMonthlyGoal() {
  savingGoal.value = true
  try {
    const year = targetYear.value
    const month = targetMonth.value
    // CC 视角：新单+转介绍
    const payloadCC = {
      identity_type: 'CC',
      scope: 'global',
      year,
      month,
      amount_target: Number(newSignTargetAmount.value || 0) + Number(referralTargetAmount.value || 0),
      new_sign_target_amount: Number(newSignTargetAmount.value || 0),
      referral_target_amount: Number(referralTargetAmount.value || 0)
    }
    await api.post('/goals/monthly', payloadCC)

    // SS 视角：总续费（续费+升舱）
    const payloadSS = {
      identity_type: 'SS',
      scope: 'global',
      year,
      month,
      amount_target: Number(renewalTotalTargetAmount.value || 0),
      renewal_total_target_amount: Number(renewalTotalTargetAmount.value || 0),
      upgrade_target_count: Number(upgradeTargetCount.value || 0)
    }
    await api.post('/goals/monthly', payloadSS)

    ElMessage.success('月度目标已保存')
  } catch (err) {
    ElMessage.error('保存月度目标失败')
  } finally {
    savingGoal.value = false
  }
}

// 获取指标库定义
async function fetchMetricDefs() {
  loading.value = true
  try {
    const { data } = await api.get('/admin/metrics')
    metrics.value = Array.isArray(data) ? data : (data?.items || [])
  } catch (err) {
    ElMessage.error('获取指标库失败')
  } finally {
    loading.value = false
  }
}

// -------------------- 个人目标设置 --------------------
const personalIdentity = ref('CC')
const personalYear = ref(currentYear)
const personalMonth = ref(currentMonth)
const personalGroupId = ref(null)
const groups = ref([])
const loadingPersonal = ref(false)
const savingPersonal = ref(false)
const personalRows = ref([])

async function refreshGroupsForIdentity() {
  try {
    const { data } = await api.get('/users', { params: { page: 1, size: 500 }, suppressErrorMessage: true })
    const allUsers = Array.isArray(data?.items) ? data.items : []
    const idt = String(personalIdentity.value || '').toUpperCase()
    let filtered = allUsers.filter(u => String(u.identity_type || '').toUpperCase() === idt && u.group_id != null)

    // 如果 /users 为空或没有匹配身份，尝试通过 /groups + /groups/:id/members 推断
    if (!filtered.length) {
      const gRes = await api.get('/groups', { suppressErrorMessage: true })
      const gItems = Array.isArray(gRes?.data?.items) ? gRes.data.items : (Array.isArray(gRes?.data) ? gRes.data : [])
      const candidate = []
      for (const g of gItems) {
        try {
          const mRes = await api.get(`/groups/${g.id}/members`, { suppressErrorMessage: true })
          const mItems = Array.isArray(mRes?.data?.items) ? mRes.data.items : (Array.isArray(mRes?.data) ? mRes.data : [])
          const hasIdt = mItems.some(m => String(m.identity_type || '').toUpperCase() === idt)
          if (hasIdt) candidate.push({ id: g.id, name: g.name || `组${g.id}` })
        } catch {}
      }
      groups.value = candidate
    } else {
      const uniq = new Map()
      for (const u of filtered) {
        const gid = String(u.group_id)
        if (!uniq.has(gid)) uniq.set(gid, { id: u.group_id, name: u.group_name || `组${gid}` })
      }
      groups.value = Array.from(uniq.values())
    }

    personalGroupId.value = groups.value.length ? groups.value[0].id : null
    await reloadPersonalRows()
  } catch {
    // 当 /users 请求失败（如权限403）时，走 /groups + /groups/:id/members 推断
    try {
      const idt = String(personalIdentity.value || '').toUpperCase()
      const gRes = await api.get('/groups', { suppressErrorMessage: true })
      const gItems = Array.isArray(gRes?.data?.items) ? gRes.data.items : (Array.isArray(gRes?.data) ? gRes.data : [])
      const candidate = []
      for (const g of gItems) {
        try {
          const mRes = await api.get(`/groups/${g.id}/members`, { suppressErrorMessage: true })
          const mItems = Array.isArray(mRes?.data?.items) ? mRes.data.items : (Array.isArray(mRes?.data) ? mRes.data : [])
          const hasIdt = mItems.some(m => String(m.identity_type || '').toUpperCase() === idt)
          if (hasIdt) candidate.push({ id: g.id, name: g.name || `组${g.id}` })
        } catch {}
      }
      groups.value = candidate
      personalGroupId.value = groups.value.length ? groups.value[0].id : null
      await reloadPersonalRows()
    } catch {
      groups.value = []
      personalGroupId.value = null
      personalRows.value = []
    }
  }
}

function computeCcSalesTarget(row) {
  const a = Number(row.new_sign_target_amount || 0)
  const b = Number(row.referral_target_amount || 0)
  return (a + b).toFixed(0)
}

async function reloadPersonalRows() {
  loadingPersonal.value = true
  try {
    const gid = personalGroupId.value
    if (!gid) { personalRows.value = []; return }
    // 拉取组内用户（不再按身份过滤，确保看到该组织内所有用户）
    let members = []
    try {
      const mRes = await api.get(`/groups/${gid}/members`) // 不抑制错误，若权限不足会提示
      const mItems = Array.isArray(mRes?.data?.items) ? mRes.data.items : (Array.isArray(mRes?.data) ? mRes.data : [])
      members = mItems
    } catch (err) {
      // 如果因为权限不足导致无法读取成员，给出明确提示，再降级尝试 /users
      const status = err?.response?.status
      if (status === 403) {
        ElMessage.warning('权限不足：无法查看该组织成员（需要管理员或超级管理员）')
      }
      try {
        const uRes = await api.get('/users', { params: { page: 1, size: 500 }, suppressErrorMessage: true })
        const allUsers = Array.isArray(uRes?.data?.items) ? uRes.data.items : []
        members = allUsers.filter(u => String(u.group_id) === String(gid))
      } catch {}
    }

    // 拉取已保存的个人目标
    const gRes = await api.get('/goals/monthly', {
      params: { identity_type: personalIdentity.value, scope: 'user', group_id: gid, year: personalYear.value, month: personalMonth.value },
      suppressErrorMessage: true
    })
    const saved = Array.isArray(gRes?.data) ? gRes.data : (Array.isArray(gRes?.data?.items) ? gRes.data.items : [])
    const savedMap = new Map(saved.map(it => [String(it.user_id), it]))

    personalRows.value = members.map(m => {
      const userId = m.id ?? m.user_id
      const s = savedMap.get(String(userId)) || {}
      return {
        user_id: userId,
        username: m.username || m.name || m.email || `用户${userId}`,
        new_sign_target_amount: s.new_sign_target_amount ?? '',
        referral_target_amount: s.referral_target_amount ?? '',
        renewal_total_target_amount: s.renewal_total_target_amount ?? '',
        upgrade_target_count: s.upgrade_target_count ?? ''
      }
    })
  } catch {
    personalRows.value = []
  } finally {
    loadingPersonal.value = false
  }
}

async function savePersonalGoals() {
  savingPersonal.value = true
  try {
    const payloads = personalRows.value.map(r => ({
      identity_type: personalIdentity.value,
      scope: 'user',
      group_id: personalGroupId.value,
      user_id: r.user_id,
      year: personalYear.value,
      month: personalMonth.value,
      new_sign_target_amount: Number(r.new_sign_target_amount || 0),
      referral_target_amount: Number(r.referral_target_amount || 0),
      renewal_total_target_amount: Number(r.renewal_total_target_amount || 0),
      upgrade_target_count: Number(r.upgrade_target_count || 0)
    }))
    await Promise.all(payloads.map(p => api.post('/goals/monthly', p)))
    ElMessage.success('个人目标已批量保存')
    reloadPersonalRows()
  } catch (err) {
    const status = err?.response?.status
    if (status === 403) {
      ElMessage.error('保存失败：需要管理员或超级管理员权限')
    } else {
      ElMessage.error('保存个人目标失败')
    }
  } finally {
    savingPersonal.value = false
  }
}

// 切换启用状态
async function onToggleActive(row) {
  const prev = !!row.is_active
  row.__saving = true
  try {
    if (!row.id) throw new Error('缺少指标ID')
    await api.put(`/admin/metrics/${row.id}`, { is_active: row.is_active })
    ElMessage.success('已更新启用状态')
  } catch (err) {
    row.is_active = prev
    ElMessage.error('更新启用状态失败')
  } finally {
    row.__saving = false
  }
}
</script>

<style scoped>
.page-container { padding: 24px; }
.page-header { margin-bottom: 16px; }
.page-title { font-size: 22px; font-weight: 600; margin: 0 0 6px; }
.page-description { color: #909399; margin: 0; }

.content-card { margin-bottom: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.filters-bar { display: flex; gap: 12px; align-items: center; margin-bottom: 12px; }

.goal-form { padding: 8px 0; }
</style>