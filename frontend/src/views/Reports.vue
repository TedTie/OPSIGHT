<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">日报管理</h1>
      <p class="page-description">查看和管理您的日报</p>
    </div>
    
    <el-card class="content-card">
      <template #header>
        <div class="card-header">
          <span>日报列表</span>
          <el-button 
            v-can="'reports:create'"
            type="primary" 
            :icon="Plus" 
            @click="openCreateDialog"
          >
            写日报
          </el-button>
        </div>
      </template>
      
      <div class="table-toolbar">
        <div class="table-filters">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
          
          <el-input
            v-model="filters.search"
            placeholder="搜索日报..."
            :prefix-icon="Search"
            clearable
          />

          <!-- 管理员：本组用户筛选 -->
          <el-select
            v-if="isAdmin"
            v-model="selectedUserId"
            placeholder="筛选本组用户"
            clearable
            @change="fetchReports"
          >
            <el-option
              v-for="user in userOptions"
              :key="user.id"
              :label="user.username"
              :value="user.id"
            />
          </el-select>

          <!-- 超级管理员：身份/组别/用户筛选（层级顺序：Identity -> Group -> User） -->
          <el-select
            v-if="isSuperAdmin"
            v-model="selectedRoleType"
            placeholder="选择身份"
            clearable
            @change="onIdentityChange"
          >
            <el-option label="全部" :value="null" />
            <el-option label="CC(顾问)" value="cc" />
            <el-option label="SS(班主任)" value="ss" />
            <el-option label="LP(英文辅导)" value="lp" />
          </el-select>

          <el-select
            v-if="isSuperAdmin"
            v-model="selectedGroupId"
            placeholder="选择组别"
            clearable
            @change="onGroupChange"
          >
            <el-option label="全部" :value="null" />
            <el-option
              v-for="group in filteredGroupOptions"
              :key="group.id"
              :label="group.name"
              :value="group.id"
            />
          </el-select>

          <el-select
            v-if="isSuperAdmin"
            v-model="selectedUserId"
            placeholder="选择用户"
            clearable
            @change="fetchReports"
          >
            <el-option label="全部" :value="null" />
            <el-option
              v-for="user in filteredUserOptions"
              :key="user.id"
              :label="user.username"
              :value="user.id"
            />
          </el-select>
        </div>
        
        <div class="table-actions">
          <el-button :icon="Refresh" @click="fetchReports">刷新</el-button>
          <el-button 
            v-can="'reports:auto_generate'"
            type="info" 
            @click="autoGenerateReport"
            :loading="autoGenerating"
          >
            自动生成今日日报
          </el-button>
        </div>
      </div>
      
      <el-table
        v-loading="loading"
        :data="reports"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="report_date" label="日期" width="120">
          <template #default="{ row }">
            {{ formatDate(row.report_date) }}
          </template>
        </el-table-column>
        <el-table-column label="提交人" width="150">
          <template #default="{ row }">
            <div v-if="row.submitter" style="display: flex; align-items: center; gap: 8px;">
              <el-avatar :size="32" :src="row.submitter.avatar_url">
                {{ row.submitter.username?.[0] || '?' }}
              </el-avatar>
              <span>{{ row.submitter.username || 'Unknown' }}</span>
            </div>
            <span v-else style="color: #999;">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="summary" label="摘要" min-width="300" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button 
              v-can:report.view="row"
              type="primary" 
              size="small" 
              @click="viewReport(row)"
            >
              查看
            </el-button>
            <el-button 
              v-can:report.edit="row"
              type="warning" 
              size="small" 
              @click="editReport(row)"
            >
              编辑
            </el-button>
            <el-button 
              v-can:report.delete="row"
              type="danger" 
              size="small" 
              @click="deleteReport(row)"
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
          @size-change="fetchReports"
          @current-change="fetchReports"
        />
      </div>
    </el-card>
    
    <!-- 创建/编辑日报对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑日报' : '写日报'"
      width="800px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="reportForm"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="日报日期" prop="report_date">
          <el-date-picker
            v-model="reportForm.report_date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :disabled="isEdit"
          />
        </el-form-item>
        
        <el-form-item label="工作摘要" prop="summary">
          <el-input
            v-model="reportForm.summary"
            type="textarea"
            :rows="3"
            placeholder="请简要描述今日工作内容"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="完成任务" prop="completed_tasks">
          <div class="completed-tasks-section">
            <!-- 自动加载提示与超管筛选控件 -->
            <el-alert 
              title="已自动加载：当日到期（已/未完成） + 正在进行未完成 + 逾期（今日完成/未完成）"
              type="info" 
              :closable="false"
              style="margin-bottom: 10px;"
            />

            <!-- 超级管理员范围筛选（联动自动刷新） -->
            <div v-if="isSuperAdmin" class="summary-scope-controls">
              <el-radio-group v-model="summaryScope" size="small" @change="autoLoadTaskSummary">
                <el-radio-button label="all">全部</el-radio-button>
                <el-radio-button label="user">个人</el-radio-button>
                <el-radio-button label="group">组别</el-radio-button>
                <el-radio-button label="identity">角色</el-radio-button>
              </el-radio-group>
              <template v-if="summaryScope === 'user'">
                <el-select v-model="summaryScopeUserId" placeholder="选择用户" filterable style="width: 220px;" @change="autoLoadTaskSummary">
                  <el-option v-for="u in userOptions" :key="u.id" :label="u.username" :value="u.id" />
                </el-select>
              </template>
              <template v-if="summaryScope === 'group'">
                <el-select v-model="summaryScopeGroupId" placeholder="选择组别" filterable style="width: 220px;" @change="autoLoadTaskSummary">
                  <el-option v-for="g in groupOptions" :key="g.id" :label="g.name" :value="g.id" />
                </el-select>
              </template>
              <template v-if="summaryScope === 'identity'">
                <el-select v-model="summaryScopeIdentity" placeholder="选择角色" filterable style="width: 220px;" @change="autoLoadTaskSummary">
                  <el-option v-for="role in identityOptions" :key="role.value" :label="role.label" :value="role.value" />
                </el-select>
              </template>
            </div>

            <!-- 文本输入栏已移除，改用分层卡片展示；提交时仍使用系统自动生成的汇总文本 -->

            <!-- 分层任务展示（卡片样式） -->
            <div class="task-hierarchy-section">
              <h4 class="hierarchy-title">今日完成</h4>
              <template v-if="groupedTasks.completedToday.length > 0">
                <el-row :gutter="12">
                  <el-col :xs="24" :sm="12" :md="12" :lg="8" v-for="task in groupedTasks.completedToday" :key="`completed-${task.id}`">
                    <el-card class="task-card" shadow="always">
                      <div class="task-card-header">
                        <span class="task-title">{{ task.title }}</span>
                        <el-tag :type="getStatusType(task.status)" size="small">{{ getTaskStatusText(task.status) }}</el-tag>
                      </div>
                      <div class="task-card-body">
                        <div class="task-meta">
                          <div class="meta-row">
                            <el-icon class="meta-icon"><component :is="getAssignmentIcon(task.assignment_type)" /></el-icon>
                            <span class="meta-label">分配：</span>
                            <span class="meta-value">{{ getAssignmentTypeText(task.assignment_type) }} · {{ getAssignmentTarget(task) }}</span>
                          </div>
                          <div class="meta-row">
                            <el-icon class="meta-icon"><Calendar /></el-icon>
                            <span class="meta-label">截止：</span>
                            <span class="meta-value">{{ task.due_date ? formatDate(task.due_date) : '无' }}</span>
                          </div>
                        </div>
                        <div class="task-progress">
                          <span class="progress-label">{{ getTaskProgressText(task) }}</span>
                          <el-progress :percentage="getTaskProgressPercent(task)" :stroke-width="10" :color="getProgressColor(getTaskProgressRatio(task))" :show-text="false" />
                          <span class="percent-text">{{ getTaskProgressPercent(task) }}%</span>
                        </div>
                      </div>
                      <div class="task-card-footer">
                        <el-button type="primary" size="small" @click="goToTaskDetail(task)">编辑记录</el-button>
                      </div>
                    </el-card>
                  </el-col>
                </el-row>
              </template>
              <el-empty v-else description="无" />

              <h4 class="hierarchy-title">今日到期</h4>
              <template v-if="groupedTasks.dueToday.length > 0">
                <el-row :gutter="12">
                  <el-col :xs="24" :sm="12" :md="12" :lg="8" v-for="task in groupedTasks.dueToday" :key="`due-${task.id}`">
                    <el-card class="task-card" shadow="always">
                      <div class="task-card-header">
                        <span class="task-title">{{ task.title }}</span>
                        <el-tag :type="getStatusType(task.status)" size="small">{{ getTaskStatusText(task.status) }}</el-tag>
                      </div>
                      <div class="task-card-body">
                        <div class="task-meta">
                          <div class="meta-row">
                            <el-icon class="meta-icon"><component :is="getAssignmentIcon(task.assignment_type)" /></el-icon>
                            <span class="meta-label">分配：</span>
                            <span class="meta-value">{{ getAssignmentTypeText(task.assignment_type) }} · {{ getAssignmentTarget(task) }}</span>
                          </div>
                          <div class="meta-row">
                            <el-icon class="meta-icon"><Calendar /></el-icon>
                            <span class="meta-label">截止：</span>
                            <span class="meta-value">{{ task.due_date ? formatDate(task.due_date) : '无' }}</span>
                          </div>
                        </div>
                        <div class="task-progress">
                          <span class="progress-label">{{ getTaskProgressText(task) }}</span>
                          <el-progress :percentage="getTaskProgressPercent(task)" :stroke-width="10" :color="getProgressColor(getTaskProgressRatio(task))" :show-text="false" />
                          <span class="percent-text">{{ getTaskProgressPercent(task) }}%</span>
                        </div>
                      </div>
                      <div class="task-card-footer">
                        <el-button type="primary" size="small" @click="goToTaskDetail(task)">编辑记录</el-button>
                      </div>
                    </el-card>
                  </el-col>
                </el-row>
              </template>
              <el-empty v-else description="无" />

              <h4 class="hierarchy-title">正在进行（未到期/无截止）</h4>
              <template v-if="groupedTasks.ongoing.length > 0">
                <el-row :gutter="12">
                  <el-col :xs="24" :sm="12" :md="12" :lg="8" v-for="task in groupedTasks.ongoing" :key="`ongoing-${task.id}`">
                    <el-card class="task-card" shadow="always">
                      <div class="task-card-header">
                        <span class="task-title">{{ task.title }}</span>
                        <el-tag :type="getStatusType(task.status)" size="small">{{ getTaskStatusText(task.status) }}</el-tag>
                      </div>
                      <div class="task-card-body">
                        <div class="task-meta">
                          <div class="meta-row">
                            <el-icon class="meta-icon"><component :is="getAssignmentIcon(task.assignment_type)" /></el-icon>
                            <span class="meta-label">分配：</span>
                            <span class="meta-value">{{ getAssignmentTypeText(task.assignment_type) }} · {{ getAssignmentTarget(task) }}</span>
                          </div>
                          <div class="meta-row">
                            <el-icon class="meta-icon"><Calendar /></el-icon>
                            <span class="meta-label">截止：</span>
                            <span class="meta-value">{{ task.due_date ? formatDate(task.due_date) : '无' }}</span>
                          </div>
                        </div>
                        <div class="task-progress">
                          <span class="progress-label">{{ getTaskProgressText(task) }}</span>
                          <el-progress :percentage="getTaskProgressPercent(task)" :stroke-width="10" :color="getProgressColor(getTaskProgressRatio(task))" :show-text="false" />
                          <span class="percent-text">{{ getTaskProgressPercent(task) }}%</span>
                        </div>
                      </div>
                      <div class="task-card-footer">
                        <el-button type="primary" size="small" @click="goToTaskDetail(task)">编辑记录</el-button>
                      </div>
                    </el-card>
                  </el-col>
                </el-row>
              </template>
              <el-empty v-else description="无" />

              <h4 class="hierarchy-title">逾期（未完成）</h4>
              <template v-if="groupedTasks.overdue.length > 0">
                <el-row :gutter="12">
                  <el-col :xs="24" :sm="12" :md="12" :lg="8" v-for="task in groupedTasks.overdue" :key="`overdue-${task.id}`">
                    <el-card class="task-card" shadow="always">
                      <div class="task-card-header">
                        <span class="task-title">{{ task.title }}</span>
                        <el-tag :type="getStatusType(task.status)" size="small">{{ getTaskStatusText(task.status) }}</el-tag>
                      </div>
                      <div class="task-card-body">
                        <div class="task-meta">
                          <div class="meta-row">
                            <el-icon class="meta-icon"><component :is="getAssignmentIcon(task.assignment_type)" /></el-icon>
                            <span class="meta-label">分配：</span>
                            <span class="meta-value">{{ getAssignmentTypeText(task.assignment_type) }} · {{ getAssignmentTarget(task) }}</span>
                          </div>
                          <div class="meta-row">
                            <el-icon class="meta-icon"><Calendar /></el-icon>
                            <span class="meta-label">截止：</span>
                            <span class="meta-value">{{ task.due_date ? formatDate(task.due_date) : '无' }}</span>
                          </div>
                        </div>
                        <div class="task-progress">
                          <span class="progress-label">{{ getTaskProgressText(task) }}</span>
                          <el-progress :percentage="getTaskProgressPercent(task)" :stroke-width="10" :color="getProgressColor(getTaskProgressRatio(task))" :show-text="false" />
                          <span class="percent-text">{{ getTaskProgressPercent(task) }}%</span>
                        </div>
                      </div>
                      <div class="task-card-footer">
                        <el-button type="primary" size="small" @click="goToTaskDetail(task)">编辑记录</el-button>
                      </div>
                    </el-card>
                  </el-col>
                </el-row>
              </template>
              <el-empty v-else description="无" />
            </div>
          </div>
        </el-form-item>
        
        <el-form-item label="遇到问题" prop="issues_encountered">
          <el-input
            v-model="reportForm.issues_encountered"
            type="textarea"
            :rows="3"
            placeholder="描述工作中遇到的问题和困难"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="明日计划" prop="next_day_plan">
          <el-input
            v-model="reportForm.next_day_plan"
            type="textarea"
            :rows="3"
            placeholder="描述明日的工作计划"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
        
        
        
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="KPI 通次" prop="call_count">
            <el-input-number
              v-model="reportForm.call_count"
              :min="0"
              :step="1"
              placeholder="今日拨打次数"
            />
          </el-form-item>
        </el-col>
        
        <el-col :span="12">
          <el-form-item label="KPI 通时" prop="call_duration">
            <el-input-number
              v-model="reportForm.call_duration"
              :min="0"
              :step="1"
              placeholder="拨打总时长（分钟）"
            />
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <template v-if="String(authStore.user?.identity_type || '').toLowerCase() === 'cc'">
          <el-col :span="12">
            <el-form-item label="当日实收金额" prop="actual_amount">
              <el-input-number v-model="reportForm.actual_amount" :min="0" :step="0.01" controls-position="right" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="新签金额" prop="new_sign_amount">
              <el-input-number v-model="reportForm.new_sign_amount" :min="0" :step="0.01" controls-position="right" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="转介绍金额" prop="referral_amount">
              <el-input-number v-model="reportForm.referral_amount" :min="0" :step="0.01" controls-position="right" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="转介绍单量" prop="referral_count">
              <el-input-number v-model="reportForm.referral_count" :min="0" :step="1" controls-position="right" />
            </el-form-item>
          </el-col>
        </template>
        <template v-else-if="String(authStore.user?.identity_type || '').toLowerCase() === 'ss'">
          <el-col :span="12">
            <el-form-item label="续费金额" prop="renewal_amount">
              <el-input-number v-model="reportForm.renewal_amount" :min="0" :step="0.01" controls-position="right" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="升级金额" prop="upgrade_amount">
              <el-input-number v-model="reportForm.upgrade_amount" :min="0" :step="0.01" controls-position="right" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="续费单量" prop="renewal_count">
              <el-input-number v-model="reportForm.renewal_count" :min="0" :step="1" controls-position="right" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="升级单量" prop="upgrade_count">
              <el-input-number v-model="reportForm.upgrade_count" :min="0" :step="1" controls-position="right" />
            </el-form-item>
          </el-col>
        </template>
      </el-row>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitReport" :loading="submitting">
            {{ isEdit ? '更新' : '提交' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 查看日报对话框 -->
    <el-dialog
      v-model="viewDialogVisible"
      title="查看日报"
      width="800px"
    >
      <div v-if="currentReport" class="report-detail">
        <div class="report-header">
          <h3>{{ formatDate(currentReport.report_date) }} 日报</h3>
          <div class="report-meta">
            <el-tag v-if="currentReport.call_count !== undefined && currentReport.call_duration !== undefined" type="success">
              KPI 通次/通时: {{ currentReport.call_count }}/{{ currentReport.call_duration }}
            </el-tag>
            <el-tag v-if="(currentReport.actual_amount||currentReport.new_sign_amount||currentReport.referral_amount||currentReport.referral_count)" type="warning" style="margin-left:8px;">
              CC 金额/单量: {{ currentReport.actual_amount }} / 新签 {{ currentReport.new_sign_amount }} / 转介 {{ currentReport.referral_amount }} / 转介单量 {{ currentReport.referral_count }}
            </el-tag>
            <el-tag v-if="(currentReport.renewal_amount||currentReport.upgrade_amount||currentReport.renewal_count||currentReport.upgrade_count)" type="info" style="margin-left:8px;">
              SS 金额/单量: 续费 {{ currentReport.renewal_amount }} / 升级 {{ currentReport.upgrade_amount }} / 续费单量 {{ currentReport.renewal_count }} / 升级单量 {{ currentReport.upgrade_count }}
            </el-tag>
          </div>
        </div>
        
        <div class="report-section">
          <h4>工作摘要</h4>
          <p>{{ currentReport.summary }}</p>
        </div>
        
        <div class="report-section">
          <h4>完成任务</h4>
          <template v-if="hasSnapshot">
            <div class="task-hierarchy-section">
              <h4 class="hierarchy-title">今日完成</h4>
              <template v-if="viewGroupedTasks.completedToday.length > 0">
                <el-row :gutter="12">
                  <el-col :xs="24" :sm="12" :md="12" :lg="8" v-for="task in viewGroupedTasks.completedToday" :key="`view-completed-${task.id}`">
                    <el-card class="task-card" shadow="always">
                      <div class="task-card-header">
                        <span class="task-title">{{ task.title }}</span>
                        <el-tag :type="getStatusType(task.status)" size="small">{{ getTaskStatusText(task.status) }}</el-tag>
                      </div>
                      <div class="task-card-body">
                        <div class="task-meta">
                          <div class="meta-row">
                            <el-icon class="meta-icon"><component :is="getAssignmentIcon(task.assignment_type)" /></el-icon>
                            <span class="meta-label">分配：</span>
                            <span class="meta-value">{{ getAssignmentTypeText(task.assignment_type) }} · {{ getAssignmentTarget(task) }}</span>
                          </div>
                          <div class="meta-row">
                            <el-icon class="meta-icon"><Calendar /></el-icon>
                            <span class="meta-label">截止：</span>
                            <span class="meta-value">{{ task.due_date ? formatDate(task.due_date) : '无' }}</span>
                          </div>
                        </div>
                        <div class="task-progress">
                          <span class="progress-label">{{ getTaskProgressText(task) }}</span>
                          <el-progress :percentage="getTaskProgressPercent(task)" :stroke-width="10" :color="getProgressColor(getTaskProgressRatio(task))" :show-text="false" />
                          <span class="percent-text">{{ getTaskProgressPercent(task) }}%</span>
                        </div>
                      </div>
                    </el-card>
                  </el-col>
                </el-row>
              </template>
              <el-empty v-else description="无" />

              <h4 class="hierarchy-title">今日到期</h4>
              <template v-if="viewGroupedTasks.dueToday.length > 0">
                <el-row :gutter="12">
                  <el-col :xs="24" :sm="12" :md="12" :lg="8" v-for="task in viewGroupedTasks.dueToday" :key="`view-due-${task.id}`">
                    <el-card class="task-card" shadow="always">
                      <div class="task-card-header">
                        <span class="task-title">{{ task.title }}</span>
                        <el-tag :type="getStatusType(task.status)" size="small">{{ getTaskStatusText(task.status) }}</el-tag>
                      </div>
                      <div class="task-card-body">
                        <div class="task-meta">
                          <div class="meta-row">
                            <el-icon class="meta-icon"><component :is="getAssignmentIcon(task.assignment_type)" /></el-icon>
                            <span class="meta-label">分配：</span>
                            <span class="meta-value">{{ getAssignmentTypeText(task.assignment_type) }} · {{ getAssignmentTarget(task) }}</span>
                          </div>
                          <div class="meta-row">
                            <el-icon class="meta-icon"><Calendar /></el-icon>
                            <span class="meta-label">截止：</span>
                            <span class="meta-value">{{ task.due_date ? formatDate(task.due_date) : '无' }}</span>
                          </div>
                        </div>
                        <div class="task-progress">
                          <span class="progress-label">{{ getTaskProgressText(task) }}</span>
                          <el-progress :percentage="getTaskProgressPercent(task)" :stroke-width="10" :color="getProgressColor(getTaskProgressRatio(task))" :show-text="false" />
                          <span class="percent-text">{{ getTaskProgressPercent(task) }}%</span>
                        </div>
                      </div>
                    </el-card>
                  </el-col>
                </el-row>
              </template>
              <el-empty v-else description="无" />

              <h4 class="hierarchy-title">正在进行（未到期/无截止）</h4>
              <template v-if="viewGroupedTasks.ongoing.length > 0">
                <el-row :gutter="12">
                  <el-col :xs="24" :sm="12" :md="12" :lg="8" v-for="task in viewGroupedTasks.ongoing" :key="`view-ongoing-${task.id}`">
                    <el-card class="task-card" shadow="always">
                      <div class="task-card-header">
                        <span class="task-title">{{ task.title }}</span>
                        <el-tag :type="getStatusType(task.status)" size="small">{{ getTaskStatusText(task.status) }}</el-tag>
                      </div>
                      <div class="task-card-body">
                        <div class="task-meta">
                          <div class="meta-row">
                            <el-icon class="meta-icon"><component :is="getAssignmentIcon(task.assignment_type)" /></el-icon>
                            <span class="meta-label">分配：</span>
                            <span class="meta-value">{{ getAssignmentTypeText(task.assignment_type) }} · {{ getAssignmentTarget(task) }}</span>
                          </div>
                          <div class="meta-row">
                            <el-icon class="meta-icon"><Calendar /></el-icon>
                            <span class="meta-label">截止：</span>
                            <span class="meta-value">{{ task.due_date ? formatDate(task.due_date) : '无' }}</span>
                          </div>
                        </div>
                        <div class="task-progress">
                          <span class="progress-label">{{ getTaskProgressText(task) }}</span>
                          <el-progress :percentage="getTaskProgressPercent(task)" :stroke-width="10" :color="getProgressColor(getTaskProgressRatio(task))" :show-text="false" />
                          <span class="percent-text">{{ getTaskProgressPercent(task) }}%</span>
                        </div>
                      </div>
                    </el-card>
                  </el-col>
                </el-row>
              </template>
              <el-empty v-else description="无" />
            </div>
          </template>
          <p v-else>{{ currentReport.completed_tasks }}</p>
        </div>
        
        <div v-if="currentReport.issues_encountered" class="report-section">
          <h4>遇到问题</h4>
          <p>{{ currentReport.issues_encountered }}</p>
        </div>
        
        <div class="report-section">
          <h4>明日计划</h4>
          <p>{{ currentReport.next_day_plan }}</p>
        </div>
        
        
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import Plus from '~icons/tabler/plus'
import Search from '~icons/tabler/search'
import Refresh from '~icons/tabler/refresh'
import User from '~icons/tabler/user'
import OfficeBuilding from '~icons/tabler/building'
import Calendar from '~icons/tabler/calendar'
import { formatDate, formatDateTime } from '@/utils/date'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import api from '@/utils/api'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

// ... existing code ...

// Initialize on mount
onMounted(async () => {
  if (isSuperAdmin.value) {
    await fetchGroups()
    await refreshUserOptions()
  } else if (isAdmin.value) {
    await fetchAdminGroupMembers()
  }
  await fetchReports()
})

// 数据
const loading = ref(false)
const reports = ref([])

// 过滤器
const filters = reactive({
  dateRange: [],
  search: ''
})

// 角色与筛选
const authStore = useAuthStore()
const isAdmin = computed(() => !!authStore.user?.is_admin && !authStore.user?.is_super_admin)
const isSuperAdmin = computed(() => !!authStore.user?.is_super_admin)
const selectedGroupId = ref(null)
const selectedUserId = ref(null)
const selectedRoleType = ref(null)
const groupOptions = ref([])
const userOptions = ref([])
// Filtered options for hierarchical filtering
const filteredGroupOptions = computed(() => {
  if (!selectedRoleType.value) return groupOptions.value
  // Filter groups that have users of selected identity
  const identityUsers = userOptions.value.filter(u => 
    String(u.identity_type || '').toLowerCase() === selectedRoleType.value.toLowerCase()
  )
  const groupIds = new Set(identityUsers.map(u => u.group_id).filter(Boolean))
  return groupOptions.value.filter(g => groupIds.has(g.id))
})
const filteredUserOptions = computed(() => {
  let users = userOptions.value
  if (selectedRoleType.value) {
    users = users.filter(u => 
      String(u.identity_type || '').toLowerCase() === selectedRoleType.value.toLowerCase()
    )
  }
  if (selectedGroupId.value) {
    users = users.filter(u => u.group_id === selectedGroupId.value)
  }
  return users
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 对话框
const dialogVisible = ref(false)
const viewDialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref()
const currentReport = ref(null)
// 查看详情用的分层任务（来自 ai_analysis.tasks_snapshot）
const viewGroupedTasks = reactive({
  completedToday: [],
  dueToday: [],
  ongoing: [],
  overdue: []
})
const hasSnapshot = computed(() => {
  const snap = currentReport.value?.ai_analysis?.tasks_snapshot
  return !!(
    snap && (
      snap.completed_today?.length ||
      snap.completedToday?.length ||
      snap.due_today?.length ||
      snap.dueToday?.length ||
      snap.ongoing?.length ||
      snap.ongoing_uncompleted?.length ||
      snap.overdue_uncompleted?.length
    )
  )
})

// 日报表单
const reportForm = reactive({
  report_date: '',
  summary: '',
  completed_tasks: '',
  issues_encountered: '',
  next_day_plan: '',
  call_count: 0,
  call_duration: 0,
  actual_amount: 0,
  new_sign_amount: 0,
  referral_amount: 0,
  referral_count: 0,
  renewal_amount: 0,
  upgrade_amount: 0,
  renewal_count: 0,
  upgrade_count: 0
})

// 任务相关数据（旧选择器不再使用，保留变量避免报错）
const availableTasks = ref([])
const selectedTaskIds = ref([])
const tasksLoading = ref(false)
const loadingSummary = ref(false)
const autoGenerating = ref(false)
// 分层任务集合（用于卡片展示）
const groupedTasks = reactive({
  completedToday: [],
  dueToday: [],
  ongoing: [],
  overdue: []
})

const router = useRouter()

// 自动汇总范围（默认：超管=全部；管理员=本组；普通用户=我的）
const summaryScope = ref('all')
const summaryScopeUserId = ref(null)
const summaryScopeGroupId = ref(null)
const summaryScopeIdentity = ref(null)
const identityOptions = ref([
  { label: 'CC(顾问)', value: 'cc' },
  { label: 'SS(班主任)', value: 'ss' },
  { label: 'LP(英文辅导)', value: 'lp' }
])

// 表单验证规则
const formRules = {
  report_date: [
    { required: true, message: '请选择日报日期', trigger: 'change' }
  ],
  summary: [
    { required: true, message: '请输入工作摘要', trigger: 'blur' },
    { min: 10, max: 500, message: '摘要长度在 10 到 500 个字符', trigger: 'blur' }
  ],
  // 完成任务改为自动汇总卡片展示，不做必填校验
  completed_tasks: [],
  next_day_plan: [
    { required: true, message: '请输入明日计划', trigger: 'blur' }
  ]
}

// 获取任务状态文本
const getTaskStatusText = (status) => {
  const statusMap = {
    'pending': '待处理',
    'processing': '进行中',
    'done': '已完成'
  }
  return statusMap[status] || status
}

// 标签样式类型
const getStatusType = (status) => {
  const s = String(status || '').toLowerCase()
  const norm = (s.match(/(pending|processing|done)/) || [])[1] || s
  const map = { pending: 'info', processing: 'warning', done: 'success' }
  return map[norm] || 'info'
}

// 分配类型文本
const getAssignmentTypeText = (assignmentType) => {
  const typeMap = {
    'user': '指定用户',
    'group': '指定组',
    'identity': '指定身份',
    'all': '所有人'
  }
  const s = String(assignmentType || '').toLowerCase()
  const norm = (s.match(/(user|group|identity|all)/) || [])[1] || s
  return typeMap[norm] || norm
}

// 分配目标文本
const getAssignmentTarget = (task) => {
  switch (task.assignment_type) {
    case 'user':
      // 优先后端给的用户名；其次使用本地索引；如是本人则直接使用用户名
      if (task.assigned_to_username) return task.assigned_to_username
      if (task.assigned_to && authStore.user?.id === task.assigned_to) {
        return authStore.user?.username || ''
      }
      if (task.assigned_to) {
        const u = (userOptions.value || []).find(x => x.id === task.assigned_to)
        return u?.username || '未知用户'
      }
      return '未知用户'
    case 'group':
      // 优先后端给的组名；其次使用本地索引；不再使用“本组”等字样
      if (task.target_group_name) return task.target_group_name
      if (task.target_group_id != null) {
        const gid = Number(task.target_group_id)
        const g = (groupOptions.value || []).find(x => Number(x.id) === gid)
        // 若列表未命中但当前用户属于该组，回退用用户的 group_name
        if (g?.name) return g.name
        if (authStore.user?.group_id === gid && authStore.user?.group_name) return authStore.user.group_name
        return '未知组'
      }
      return '未知组'
    case 'identity':
      return task.target_identity || '-'
    case 'all':
      return '所有人'
    default:
      return '-'
  }
}

// 分配类型对应图标
const getAssignmentIcon = (assignmentType) => {
  const s = String(assignmentType || '').toLowerCase()
  const norm = (s.match(/(user|group|identity|all)/) || [])[1] || s
  const map = { user: User, group: OfficeBuilding, identity: User, all: User }
  return map[norm] || User
}

// 跳转到任务详情并打开记录编辑视角（默认“我的”）
const goToTaskDetail = (task) => {
  if (!task?.id) return
  router.push({ path: '/tasks', query: { openTaskId: task.id } })
}

// —— 进度计算与展示工具 ——
const coalesce = (...vals) => {
  for (const v of vals) {
    if (v !== undefined && v !== null) return v
  }
  return 0
}

const safeDiv = (a, b) => {
  const n1 = Number(a) || 0
  const n2 = Number(b)
  if (!n2 || n2 <= 0) return 0
  return n1 / n2
}

const getTaskProgressRatio = (task) => {
  if (!task) return 0
  let ratio = 0
  switch (task.task_type) {
    case 'amount':
      ratio = safeDiv(task.current_amount, task.target_amount)
      break
    case 'quantity':
      ratio = safeDiv(task.current_quantity, task.target_quantity)
      break
    case 'jielong': {
      const cur = coalesce(task.personal_jielong_current_count, task.jielong_current_count, 0)
      const tar = coalesce(task.personal_jielong_target_count, task.jielong_target_count, 0)
      ratio = safeDiv(cur, tar)
      break
    }
    case 'checkbox':
      ratio = task.is_completed ? 1 : 0
      break
    default:
      ratio = task.status === 'done' ? 1 : 0
  }
  if (!isFinite(ratio)) ratio = 0
  return Math.max(0, Math.min(1, ratio))
}

const getTaskProgressPercent = (task) => Math.round(getTaskProgressRatio(task) * 100)

const getTaskProgressText = (task) => {
  if (!task) return '-'
  switch (task.task_type) {
    case 'amount':
      return `${task.current_amount || 0} / ${task.target_amount || 0}`
    case 'quantity':
      return `${task.current_quantity || 0} / ${task.target_quantity || 0}`
    case 'jielong': {
      const cur = coalesce(task.personal_jielong_current_count, task.jielong_current_count, 0)
      const tar = coalesce(task.personal_jielong_target_count, task.jielong_target_count, 0)
      return `${cur} / ${tar}`
    }
    case 'checkbox':
      return task.is_completed ? '已完成' : '未完成'
    default:
      return '-'
  }
}

const getProgressColor = (ratio) => {
  // 根据比例选择颜色：高=绿，中=橙，低=红
  if (ratio >= 0.8) return '#67C23A'
  if (ratio >= 0.3) return '#E6A23C'
  return '#F56C6C'
}

// —— 构建任务卡片快照（用于持久化到日报 ai_analysis） ——
const mapTaskForSnapshot = (t) => ({
  id: t.id,
  title: t.title,
  task_type: t.task_type,
  assignment_type: t.assignment_type,
  assigned_to: t.assigned_to,
  target_group_id: t.target_group_id,
  target_identity: t.target_identity,
  assigned_to_username: t.assigned_to_username,
  target_group_name: t.target_group_name,
  status: t.status,
  is_completed: t.is_completed,
  due_date: t.due_date,
  updated_at: t.updated_at,
  target_amount: t.target_amount,
  current_amount: t.current_amount,
  target_quantity: t.target_quantity,
  current_quantity: t.current_quantity,
  personal_jielong_target_count: t.personal_jielong_target_count,
  personal_jielong_current_count: t.personal_jielong_current_count,
  jielong_target_count: t.jielong_target_count,
  jielong_current_count: t.jielong_current_count
})

const buildTasksSnapshot = () => ({
  completed_today: (groupedTasks.completedToday || []).map(mapTaskForSnapshot),
  due_today: (groupedTasks.dueToday || []).map(mapTaskForSnapshot),
  ongoing: (groupedTasks.ongoing || []).map(mapTaskForSnapshot),
  overdue_uncompleted: (groupedTasks.overdue || []).map(mapTaskForSnapshot)
})

const fetchTasksForScope = async () => {
  tasksLoading.value = true
  try {
    // 后端已按可见性统一过滤（USER/ALL/GROUP/IDENTITY），这里不再用仅限“我的任务”的参数，避免漏数
    const params = { page: 1, size: 100 }

    // 超管按个人筛选：后端支持 assigned_to
    if (isSuperAdmin.value && summaryScope.value === 'user' && summaryScopeUserId.value) {
      params.assigned_to = summaryScopeUserId.value
    }

    // 普通用户：不附加“assigned_to_me”，统一由后端做可见性过滤，再在前端做细分（与查看端一致）

    const response = await api.get('/tasks', { params })
    let list = Array.isArray(response.data) ? response.data : (response.data?.items || response.data || [])

    const normType = (val) => {
      const s = String(val || '').toLowerCase()
      const m = s.match(/(user|group|identity|all)/)
      return m ? m[1] : s
    }

    // 普通用户：前端再细分一次，仅保留与本人相关的任务（个人/所在组/身份/全员），与查看端可见性一致

    // 管理员默认本组范围；普通用户默认我的
    if (isAdmin.value && summaryScope.value === 'group') {
      const gid = summaryScopeGroupId.value || authStore.user?.group_id
      if (gid) {
        const groupMemberIds = (userOptions.value || []).map(u => u.id)
        list = list.filter(t => {
          const type = normType(t.assignment_type)
          return (
            (type === 'group' && t.target_group_id === gid) ||
            (type === 'user' && groupMemberIds.includes(t.assigned_to)) ||
            (type === 'all')
          )
        })
      }
    } else if (!isAdmin.value && !isSuperAdmin.value) {
      // 普通用户：尽量只保留与本人相关任务
      const uid = authStore.user?.id
      const gid = authStore.user?.group_id
      const ident = String(authStore.user?.identity_type || '').toLowerCase()
      list = list.filter(t => {
        const type = normType(t.assignment_type)
        return (
          (type === 'user' && t.assigned_to === uid) ||
          (type === 'group' && t.target_group_id === gid) ||
          (type === 'identity' && String(t.target_identity || '').toLowerCase() === ident) ||
          (type === 'all')
        )
      })
    } else if (isSuperAdmin.value) {
      // 超管其它范围前端细分
      if (summaryScope.value === 'group' && summaryScopeGroupId.value) {
        const gid = summaryScopeGroupId.value
        const memberIds = (userOptions.value || []).filter(u => u.group_id === gid).map(u => u.id)
        list = list.filter(t => {
          const type = normType(t.assignment_type)
          return (
            (type === 'group' && t.target_group_id === gid) ||
            (type === 'user' && memberIds.includes(t.assigned_to)) ||
            (type === 'all')
          )
        })
      }
      if (summaryScope.value === 'identity' && summaryScopeIdentity.value) {
        const ident = String(summaryScopeIdentity.value || '').toLowerCase()
        list = list.filter(t => {
          const type = normType(t.assignment_type)
          return (type === 'identity' && String(t.target_identity || '').toLowerCase() === ident)
        })
      }
    }

    return list
  } catch (error) {
    ElMessage.error('获取任务用于汇总失败')
    return []
  } finally {
    tasksLoading.value = false
  }
}

// 工具：日期同一天判断
const isSameDay = (d1, d2) => {
  if (!d1 || !d2) return false
  const a = new Date(d1)
  const b = new Date(d2)
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()
}

// 自动生成完成任务汇总文本
const autoLoadTaskSummary = async () => {
  loadingSummary.value = true
  try {
    const targetDate = reportForm.report_date || formatDate(new Date())
    const dayStart = new Date(targetDate + 'T00:00:00')

    const tasks = await fetchTasksForScope()
    const dueTodayDone = []
    const dueTodayUndone = []
    const completedToday = []
    const ongoingUncompleted = []
    const overdueUncompleted = []

    tasks.forEach(t => {
      const s = String(t.status || '').toLowerCase()
      const status = (s.match(/(pending|processing|done)/) || [])[1] || s
      const isDone = status === 'done' || t.is_completed === true
      const due = t.due_date ? new Date(t.due_date.replace(' ', 'T')) : null
      const updated = t.updated_at ? new Date(String(t.updated_at).replace(' ', 'T')) : null

      const dueIsToday = !!(due && isSameDay(due, dayStart))
      const dueBeforeToday = !!(due && due < dayStart)

      // “今日完成”：任意任务只要今天变为完成（以 updated_at 作为代理）
      if (isDone && updated && isSameDay(updated, dayStart)) {
        completedToday.push(t)
      }

      if (dueIsToday) {
        if (isDone) {
          dueTodayDone.push(t)
        } else {
          dueTodayUndone.push(t)
        }
      } else if (!due || (due && due > dayStart)) {
        if (!isDone) ongoingUncompleted.push(t)
      } else {
        // 逾期但未完成：单独分组展示，确保写日报时与查看记录一致
        if (!isDone && dueBeforeToday) overdueUncompleted.push(t)
      }
    })

    const lines = []
    if (completedToday.length) {
      lines.push('【今日完成】\n' + completedToday.map(t => `• ${t.title}`).join('\n'))
    }

    const todaySection = []
    if (dueTodayDone.length) todaySection.push(...dueTodayDone.map(t => `• ${t.title}（已完成）`))
    if (dueTodayUndone.length) todaySection.push(...dueTodayUndone.map(t => `• ${t.title}（未完成）`))
    if (todaySection.length) lines.push('【今日到期】\n' + todaySection.join('\n'))

    if (ongoingUncompleted.length) {
      lines.push('【正在进行（未到期/无截止）】\n' + ongoingUncompleted.map(t => `• ${t.title}`).join('\n'))
    }

    if (overdueUncompleted.length) {
      lines.push('【逾期未完成】\n' + overdueUncompleted.map(t => `• ${t.title}`).join('\n'))
    }

    reportForm.completed_tasks = lines.length ? lines.join('\n\n') : '【今日完成】\n无\n\n【今日到期】\n无\n\n【正在进行（未到期/无截止）】\n无'

    // 写入分层卡片数据
    groupedTasks.completedToday = completedToday
    groupedTasks.dueToday = [...dueTodayDone, ...dueTodayUndone]
    groupedTasks.ongoing = ongoingUncompleted
    groupedTasks.overdue = overdueUncompleted
  } catch (error) {
    ElMessage.error('自动加载任务汇总失败')
  } finally {
    loadingSummary.value = false
  }
}

// 初始化 summaryScope 默认值
if (isSuperAdmin.value) {
  summaryScope.value = 'all'
} else if (isAdmin.value) {
  summaryScope.value = 'group'
  summaryScopeGroupId.value = authStore.user?.group_id || null
} else {
  summaryScope.value = 'user'
  summaryScopeUserId.value = authStore.user?.id || null
}

// 打开对话框时自动加载汇总；日期变化时刷新
watch(() => dialogVisible.value, (v) => { if (v) autoLoadTaskSummary() })
watch(() => reportForm.report_date, () => { if (dialogVisible.value) autoLoadTaskSummary() })

// 获取日报列表
const fetchReports = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      search: filters.search
    }
    
    if (filters.dateRange && filters.dateRange.length === 2) {
      params.start_date = filters.dateRange[0]
      params.end_date = filters.dateRange[1]
    }

    // 角色默认视角与筛选
    if (isSuperAdmin.value) {
      if (selectedRoleType.value) params.identity_type = selectedRoleType.value
      if (selectedGroupId.value) params.group_id = selectedGroupId.value
      if (selectedUserId.value) params.user_id = selectedUserId.value
    } else if (isAdmin.value) {
      if (authStore.user?.group_id) params.group_id = authStore.user.group_id
      if (selectedUserId.value) params.user_id = selectedUserId.value
    } else {
      // 普通用户：仅查看自己
      if (authStore.user?.id) params.user_id = authStore.user.id
    }
    
    const response = await api.get('/reports', { params })
    // 兼容后端返回的两种结构：
    // 1) 直接数组 [ {...}, {...} ]
    // 2) 分页对象 { items: [...], total: N }
    const data = response.data
    // 映射后端 DailyReportResponse -> 前端展示字段
    const mapReportToUI = (r) => ({
      id: r.id,
      report_date: r.work_date,
      // 优先展示 work_summary，其次使用 title 兜底
      summary: r.work_summary ?? r.title ?? '',
      // 完成任务文本用于详情展示与一致性分析
      completed_tasks: r.task_progress ?? '',
      issues_encountered: r.challenges ?? '',
      next_day_plan: r.tomorrow_plan ?? '',
      call_count: r.call_count ?? 0,
      call_duration: r.call_duration ?? 0,
      actual_amount: r.actual_amount ?? 0,
      new_sign_amount: r.new_sign_amount ?? 0,
      referral_amount: r.referral_amount ?? 0,
      referral_count: r.referral_count ?? 0,
      renewal_amount: r.renewal_amount ?? 0,
      upgrade_amount: r.upgrade_amount ?? 0,
      renewal_count: r.renewal_count ?? 0,
      upgrade_count: r.upgrade_count ?? 0,
      ai_analysis: r.ai_analysis || {},
      submitter: r.submitter || null,
      created_at: r.created_at,
      updated_at: r.updated_at
    })

    if (Array.isArray(data)) {
      reports.value = data.map(mapReportToUI)
      // 如果是数组，无法获知总数，使用当前长度作为展示用途
      pagination.total = data.length || 0
    } else if (data && typeof data === 'object') {
      const items = data.items || []
      reports.value = items.map(mapReportToUI)
      pagination.total = (typeof data.total === 'number' ? data.total : (data.items?.length || 0))
    } else {
      reports.value = []
      pagination.total = 0
    }
  } catch (error) {
    ElMessage.error('获取日报列表失败')
  } finally {
    loading.value = false
  }
}

// 获取组和用户选项
const fetchGroups = async () => {
  try {
    const res = await api.get('/groups', { params: { page: 1, size: 100 } })
    groupOptions.value = res.data.items || []
  } catch (e) {
    // 忽略错误，保持空列表
  }
}

const fetchAdminGroupMembers = async () => {
  if (!authStore.user?.group_id) {
    userOptions.value = []
    return
  }
  try {
    const res = await api.get(`/groups/${authStore.user.group_id}/members`)
    userOptions.value = res.data || []
  } catch (e) {
    userOptions.value = []
  }
}

const refreshUserOptions = async () => {
  if (!isSuperAdmin.value) return
  try {
    const params = { page: 1, size: 500 }
    const res = await api.get('/users', { params })
    userOptions.value = res.data.items || []
  } catch (e) {
    userOptions.value = []
  }
}

// Hierarchical filter change handlers
const onIdentityChange = () => {
  selectedGroupId.value = null
  selectedUserId.value = null
  fetchReports()
}

const onGroupChange = () => {
  selectedUserId.value = null
  fetchReports()
}

const goToTaskDetail = (task) => {
  router.push(`/tasks/${task.id}`)
}

const refreshUserOptionsAndReports = async () => {
  await refreshUserOptions()
  await fetchReports()
}

// 打开创建对话框
const openCreateDialog = () => {
  isEdit.value = false
  reportForm.report_date = new Date().toISOString().split('T')[0]
  dialogVisible.value = true
  autoLoadTaskSummary() // 自动生成任务完成汇总
}

// 查看日报
const buildingSnapshot = ref(false)
const ensureSnapshotForReport = async (report) => {
  // 若已有快照则不再补录
  const snap = report?.ai_analysis?.tasks_snapshot
  const exists = !!(
    snap && (
      snap.completed_today?.length ||
      snap.completedToday?.length ||
      snap.due_today?.length ||
      snap.dueToday?.length ||
      snap.ongoing?.length ||
      snap.ongoing_uncompleted?.length
    )
  )
  if (exists) return

  buildingSnapshot.value = true
  try {
    const resp = await api.post(`/reports/${parseInt(report.id)}/build-snapshot`)
    const ai = resp.data?.ai_analysis || {}
    // 更新当前报告的 AI 分析（含 tasks_snapshot）
    if (currentReport.value) {
      currentReport.value.ai_analysis = ai
    }
    const s2 = ai?.tasks_snapshot || null
    if (s2) {
      viewGroupedTasks.completedToday = s2.completed_today || s2.completedToday || []
      viewGroupedTasks.dueToday = s2.due_today || s2.dueToday || []
      viewGroupedTasks.ongoing = s2.ongoing || s2.ongoing_uncompleted || s2.ongoingUncompleted || []
      viewGroupedTasks.overdue = s2.overdue_uncompleted || []
    }
  } catch (e) {
    // 权限不足时保持文本回退，不打断查看
    if (e?.response?.status !== 403) {
      console.error('[Reports] build-snapshot failed', e)
      ElMessage.error('构建任务卡片快照失败')
    }
  } finally {
    buildingSnapshot.value = false
  }
}

const viewReport = async (report) => {
  currentReport.value = report
  // 从快照填充查看用的分层任务
  const snap = report?.ai_analysis?.tasks_snapshot || null
  if (snap) {
    // 兼容不同命名
    viewGroupedTasks.completedToday = snap.completed_today || snap.completedToday || []
    viewGroupedTasks.dueToday = snap.due_today || snap.dueToday || []
    viewGroupedTasks.ongoing = snap.ongoing || snap.ongoing_uncompleted || snap.ongoingUncompleted || []
    viewGroupedTasks.overdue = snap.overdue_uncompleted || []
  } else {
    viewGroupedTasks.completedToday = []
    viewGroupedTasks.dueToday = []
    viewGroupedTasks.ongoing = []
    viewGroupedTasks.overdue = []
  }
  viewDialogVisible.value = true
  // 若无快照则自动向后端补录并刷新展示
  await ensureSnapshotForReport(report)
}

// 编辑日报
const editReport = (report) => {
  isEdit.value = true
  Object.assign(reportForm, {
    id: parseInt(report.id), // 确保ID是数字类型
    report_date: report.report_date,
    summary: report.summary,
    // 旧数据中的手动输入不再保留，进入编辑后触发自动汇总覆盖
    completed_tasks: '',
    issues_encountered: report.issues_encountered || '',
    next_day_plan: report.next_day_plan,
    call_count: report.call_count || 0,
    call_duration: report.call_duration || 0
  })
  dialogVisible.value = true
  // 立即根据卡片数据刷新“完成任务”汇总，避免沿用历史手动输入
  autoLoadTaskSummary()
}

// 重置表单
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  Object.assign(reportForm, {
    report_date: '',
    summary: '',
    completed_tasks: '',
    issues_encountered: '',
    next_day_plan: '',
    call_count: 0,
    call_duration: 0,
    actual_amount: 0,
    new_sign_amount: 0,
    referral_amount: 0,
    referral_count: 0,
    renewal_amount: 0,
    upgrade_amount: 0,
    renewal_count: 0,
    upgrade_count: 0
  })
  selectedTaskIds.value = []
}

// 提交日报
const submitReport = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    // 提交前强制刷新“完成任务”卡片汇总，清除并替换手动输入
    await autoLoadTaskSummary()
    
    // 计算效率分（1-10），根据分层任务平均进度，若无数据则给 7
    const allTasks = [...(groupedTasks.completedToday || []), ...(groupedTasks.dueToday || []), ...(groupedTasks.ongoing || [])]
    const ratios = allTasks.map(t => getTaskProgressRatio(t)).filter(x => Number.isFinite(x))
    const avg = ratios.length ? (ratios.reduce((a,b)=>a+b,0) / ratios.length) : 0.7
    const efficiencyScore = Math.max(1, Math.min(10, Math.round(avg * 10)))

    // 统一内容：保持原封不动拼接多段文本用于 content
    const contentSections = [
      `【工作摘要】\n${reportForm.summary || ''}`,
      // 始终使用自动汇总后的卡片文本
      `【完成任务】\n${reportForm.completed_tasks || ''}`,
      `【遇到问题】\n${reportForm.issues_encountered || ''}`,
      `【明日计划】\n${reportForm.next_day_plan || ''}`
    ]
    const unifiedContent = contentSections.join('\n\n')

    if (isEdit.value) {
      // 更新：使用后端字段名
      const updatePayload = {
        work_summary: reportForm.summary || undefined,
        // 始终用系统自动生成的卡片汇总，清除手动输入
        task_progress: reportForm.completed_tasks || undefined,
        challenges: reportForm.issues_encountered || undefined,
        tomorrow_plan: reportForm.next_day_plan || undefined,
        call_count: Number.isFinite(Number(reportForm.call_count)) ? Number(reportForm.call_count) : undefined,
        call_duration: Number.isFinite(Number(reportForm.call_duration)) ? Number(reportForm.call_duration) : undefined,
        content: unifiedContent || undefined,
        title: (reportForm.summary || `日报 ${reportForm.report_date || ''}`).slice(0, 200),
        // 结构化快照用于后端持久化（ai_analysis.tasks_snapshot）
        tasks_snapshot: buildTasksSnapshot(),
        actual_amount: Number(reportForm.actual_amount) || 0,
        new_sign_amount: Number(reportForm.new_sign_amount) || 0,
        referral_amount: Number(reportForm.referral_amount) || 0,
        referral_count: Number(reportForm.referral_count) || 0,
        renewal_amount: Number(reportForm.renewal_amount) || 0,
        upgrade_amount: Number(reportForm.upgrade_amount) || 0,
        renewal_count: Number(reportForm.renewal_count) || 0,
        upgrade_count: Number(reportForm.upgrade_count) || 0
      }
      await api.put(`/reports/${reportForm.id}`, updatePayload)
      ElMessage.success('日报更新成功')
    } else {
      // 创建：映射到 DailyReportCreateRequest
      const todayStr = formatDate(new Date())
      const workDate = reportForm.report_date || todayStr
      const createPayload = {
        work_date: workDate,
        title: (reportForm.summary || `日报 ${workDate}`).slice(0, 200),
        content: unifiedContent,
        work_hours: 0.0,
        // 始终用系统自动生成的卡片汇总，清除手动输入
        task_progress: reportForm.completed_tasks || '',
        work_summary: reportForm.summary || '',
        mood_score: 0,
        efficiency_score: efficiencyScore,
        call_count: Number.isFinite(Number(reportForm.call_count)) ? Number(reportForm.call_count) : 0,
        call_duration: Number.isFinite(Number(reportForm.call_duration)) ? Number(reportForm.call_duration) : 0,
        achievements: undefined,
    challenges: reportForm.issues_encountered || undefined,
    tomorrow_plan: reportForm.next_day_plan || undefined,
        // 结构化快照用于后端持久化（ai_analysis.tasks_snapshot）
        tasks_snapshot: buildTasksSnapshot(),
        created_by: authStore.user?.id || undefined,
        actual_amount: Number(reportForm.actual_amount) || 0,
        new_sign_amount: Number(reportForm.new_sign_amount) || 0,
        referral_amount: Number(reportForm.referral_amount) || 0,
        referral_count: Number(reportForm.referral_count) || 0,
        renewal_amount: Number(reportForm.renewal_amount) || 0,
        upgrade_amount: Number(reportForm.upgrade_amount) || 0,
        renewal_count: Number(reportForm.renewal_count) || 0,
        upgrade_count: Number(reportForm.upgrade_count) || 0
      }
      // 输出调试信息，便于定位服务端500问题
      console.debug('[Reports] POST /reports payload', createPayload)
      await api.post('/reports', createPayload)
      ElMessage.success('日报提交成功')
    }
    
    dialogVisible.value = false
    fetchReports()
  } catch (error) {
    // 更详细的错误提示与日志输出
    const status = error?.response?.status
    const data = error?.response?.data
    if (data?.detail) {
      ElMessage.error(data.detail)
    } else if (status) {
      if (status === 500) {
        ElMessage.error('服务器内部错误：请稍后重试或联系管理员')
      } else if (status === 422) {
        const msg = Array.isArray(data?.detail) ? data.detail.map(d => d.msg).join('; ') : '请求参数不合法'
        ElMessage.error(`提交失败：${msg}`)
      } else {
        ElMessage.error(`提交失败（HTTP ${status}）`)
      }
    } else {
      ElMessage.error(isEdit.value ? '更新失败' : '提交失败')
    }
    // 控制台输出完整上下文
    console.error('[Reports] Submit error', {
      isEdit: isEdit.value,
      reportForm: { ...reportForm },
      status,
      data
    })
  } finally {
    submitting.value = false
  }
}

// 删除日报
const deleteReport = async (report) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除${formatDate(report.report_date)}的日报吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.delete(`/reports/${parseInt(report.id)}`)
    ElMessage.success('删除成功')
    fetchReports()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}


// 加载任务完成汇总
const loadTaskSummary = async () => {
  if (!reportForm.report_date) {
    ElMessage.warning('请先选择日报日期')
    return
  }
  
  loadingSummary.value = true
  try {
    const response = await api.get('/task-sync/daily-task-summary', {
      params: {
        date: reportForm.report_date
      }
    })
    
    if (response.data && response.data.length > 0) {
      // 自动填充完成的任务
      const taskSummary = response.data.map(task => 
        `${task.title}: ${task.completion_data || '已完成'}`
      ).join('\n')
      
      reportForm.completed_tasks = taskSummary
      ElMessage.success(`已加载${response.data.length}个任务完成记录`)
    } else {
      ElMessage.info('该日期没有任务完成记录')
    }
  } catch (error) {
    console.error('加载任务汇总失败:', error)
    ElMessage.error('加载任务汇总失败')
  } finally {
    loadingSummary.value = false
  }
}

// 自动生成今日日报
const autoGenerateReport = async () => {
  autoGenerating.value = true
  try {
    const today = new Date().toISOString().split('T')[0]
    const response = await api.post('/task-sync/auto-generate-daily-report', {
      date: today
    })
    
    if (response.data.success) {
      ElMessage.success('自动生成日报成功')
      fetchReports() // 刷新日报列表
    } else {
      ElMessage.warning(response.data.message || '自动生成日报失败')
    }
  } catch (error) {
    console.error('自动生成日报失败:', error)
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('自动生成日报失败')
    }
  } finally {
    autoGenerating.value = false
  }
}

// 初始化
onMounted(async () => {
  // 始终加载组列表，确保任何角色都能正确显示组名
  await fetchGroups()
  // 初始化筛选选项
  if (isSuperAdmin.value) {
    await fetchAllUsersForSuperAdmin()
  } else if (isAdmin.value) {
    await fetchAdminGroupMembers()
  }
  await fetchReports()
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

.text-muted {
  color: #909399;
}

.report-detail {
  padding: 20px 0;
}

.report-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.report-header h3 {
  margin: 0 0 12px 0;
  color: #303133;
}

.report-meta {
  display: flex;
  align-items: center;
  gap: 16px;
}

.report-section {
  margin-bottom: 24px;
}

.report-section h4 {
  margin: 0 0 12px 0;
  color: #606266;
  font-size: 16px;
  font-weight: 600;
}

.report-section p {
  margin: 0;
  color: #303133;
  line-height: 1.6;
  white-space: pre-wrap;
}


.completed-tasks-section {
  width: 100%;
}

.task-selector {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.task-selector .el-select {
  flex: 1;
}

@media (max-width: 768px) {
  .table-filters {
    flex-direction: column;
  }
  
  .report-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}

/* —— 任务分层卡片样式优化 —— */
.task-hierarchy-section {
  display: block;
}

.hierarchy-title {
  margin: 14px 0 10px 0;
  font-size: 15px;
  color: #606266;
}

.task-card {
  margin-bottom: 12px;
  border-radius: 8px;
}

.task-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  border-bottom: 1px dashed #ebeef5;
  padding-bottom: 6px;
}

.task-title {
  font-weight: 600;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-card-body {
  display: grid;
  grid-template-columns: 1fr;
  row-gap: 8px;
}

.task-meta {
  display: grid;
  grid-template-columns: 1fr;
  row-gap: 6px;
  color: #606266;
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.meta-icon {
  color: #909399;
}

.meta-label {
  color: #909399;
}

.meta-value {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-progress {
  display: flex;
  align-items: center;
  gap: 10px;
}

.progress-label {
  min-width: 90px;
  color: #606266;
}

.percent-text {
  color: #606266;
  font-variant-numeric: tabular-nums;
}

.task-card-footer {
  margin-top: 8px;
}
</style>