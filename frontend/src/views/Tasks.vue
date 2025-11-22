<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">任务管理</h1>
      <p class="page-description">管理和跟踪您的任务</p>
    </div>
    
    <el-card class="content-card">
      <template #header>
        <div class="card-header">
          <span>任务列表</span>
          <!-- 只有管理员和超级管理员可以创建任务 -->
          <el-button 
            v-can="'tasks:create'"
            type="primary" 
            :icon="Plus" 
            @click="openCreateDialog"
          >
            创建任务
          </el-button>
        </div>
      </template>
      
      <div class="toolbar-container">
        <div class="filter-group">
          <el-input
            v-model="filters.search"
            placeholder="搜索任务..."
            :prefix-icon="Search"
            clearable
            class="search-input"
          />
          
          <el-select v-model="filters.status" placeholder="状态" clearable class="filter-select">
            <el-option label="待处理" value="pending" />
            <el-option label="进行中" value="processing" />
            <el-option label="已完成" value="done" />
          </el-select>
          
          <el-select v-model="filters.priority" placeholder="优先级" clearable class="filter-select">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="紧急" value="urgent" />
          </el-select>

          <el-select v-model="filters.task_type" placeholder="任务类型" clearable class="filter-select">
            <el-option label="金额" value="amount" />
            <el-option label="数量" value="quantity" />
            <el-option label="接龙" value="jielong" />
            <el-option label="勾选" value="checkbox" />
          </el-select>
        </div>
        
        <div class="action-group">
          <!-- 管理员专用功能 -->
          <template v-if="authStore.isAdmin || authStore.isSuperAdmin">
            <el-button type="info" plain @click="showTaskStats">
              任务统计
            </el-button>
            <el-button 
              v-can="'tasks:assign'"
              type="warning" 
              plain
              @click="showBatchAssign"
              :disabled="selectedTasks.length === 0"
            >
              批量分配 ({{ selectedTasks.length }})
            </el-button>
          </template>
          
          <el-button :icon="Refresh" circle @click="fetchTasks" />
        </div>
      </div>
      
      <el-table
        v-loading="loading"
        :data="tasks"
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <!-- 管理员可以选择任务进行批量操作 -->
        <el-table-column 
          v-can="'tasks:assign'"
          type="selection" 
          width="55"
        />
        
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="description" label="描述" min-width="300" />
        
        <el-table-column label="任务类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTaskTypeColor(row.task_type)">
              {{ getTaskTypeText(row.task_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="进度" width="150">
          <template #default="{ row }">
            <div v-if="row.task_type === 'amount'">
              {{ row.current_amount || 0 }} / {{ row.target_amount || 0 }}
            </div>
            <div v-else-if="row.task_type === 'quantity'">
              {{ row.current_quantity || 0 }} / {{ row.target_quantity || 0 }}
            </div>
            <div v-else-if="row.task_type === 'jielong'">
              {{ (row.personal_jielong_current_count !== undefined && row.personal_jielong_current_count !== null) ? row.personal_jielong_current_count : (row.jielong_current_count || 0) }}
              /
              {{ (row.personal_jielong_target_count !== undefined && row.personal_jielong_target_count !== null) ? row.personal_jielong_target_count : (row.jielong_target_count || 0) }}
            </div>
            <div v-else-if="row.task_type === 'checkbox'">
              <el-icon v-if="row.is_completed" color="green"><Check /></el-icon>
              <el-icon v-else color="gray"><Close /></el-icon>
            </div>
            <div v-else>-</div>
          </template>
        </el-table-column>

        <el-table-column label="标签" width="150">
          <template #default="{ row }">
            <el-tag v-for="tag in (row.tags || [])" :key="tag" size="small" style="margin-right: 4px;">
              {{ tag }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="100">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)">
              {{ getPriorityText(row.priority) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="350" fixed="right">
          <template #default="{ row }">
            <!-- 查看详情：所有用户都可以查看 -->
            <el-button type="info" size="small" @click="viewTaskDetails(row)">
              详情
            </el-button>
            
            <!-- 快速操作按钮 -->
            <template v-if="row.task_type === 'checkbox'">
              <!-- 勾选任务快速完成 -->
              <el-button 
                v-can:task.complete="row"
                :type="row.is_completed ? 'success' : 'warning'"
                size="small" 
                @click="quickToggleCheckbox(row)"
                :disabled="row.status === 'done'"
              >
                {{ row.is_completed ? '已完成' : '完成' }}
              </el-button>
            </template>
            
            <template v-else-if="row.task_type === 'amount'">
              <!-- 金额任务快速参与 -->
              <el-button 
                v-can:task.participate="row"
                type="success" 
                size="small" 
                @click="quickParticipateAmount(row)"
                :disabled="row.status === 'done'"
              >
                参与
              </el-button>
            </template>
            
            <template v-else-if="row.task_type === 'quantity'">
              <!-- 数量任务快速参与 -->
              <el-button 
                v-can:task.participate="row"
                type="success" 
                size="small" 
                @click="quickParticipateQuantity(row)"
                :disabled="row.status === 'done'"
              >
                参与
              </el-button>
            </template>
            
            <template v-else-if="row.task_type === 'jielong'">
              <!-- 接龙任务快速参与 -->
              <el-button 
                v-can:task.participate="row"
                type="success" 
                size="small" 
                @click="quickParticipateJielong(row)"
                :disabled="row.status === 'done'"
              >
                接龙
              </el-button>
            </template>
            
            <!-- 编辑任务：只有创建者或管理员可以编辑 -->
            <el-button 
              v-can:task.edit="row"
              type="primary" 
              size="small" 
              @click="editTask(row)"
            >
              编辑
            </el-button>
            
            <!-- 删除任务：只有创建者或管理员可以删除 -->
            <el-button 
              v-can:task.delete="row"
              type="danger" 
              size="small" 
              @click="deleteTask(row)"
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
          @size-change="fetchTasks"
          @current-change="fetchTasks"
        />
      </div>
    </el-card>
    
    <!-- 创建/编辑任务对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑任务' : '创建任务'"
      width="700px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="taskForm"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="任务标题" prop="title">
          <el-input v-model="taskForm.title" placeholder="请输入任务标题" />
        </el-form-item>
        
        <el-form-item label="任务描述" prop="description">
          <el-input
            v-model="taskForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入任务描述"
          />
        </el-form-item>

        <el-form-item label="任务标签" prop="tags">
          <el-select
            v-model="taskForm.tags"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="请输入或选择标签"
            style="width: 100%"
          >
            <el-option
              v-for="tag in commonTags"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="任务类型" prop="task_type">
          <el-select v-model="taskForm.task_type" placeholder="请选择任务类型" @change="onTaskTypeChange">
            <el-option label="金额任务" value="amount" />
            <el-option label="数量任务" value="quantity" />
            <el-option label="接龙任务" value="jielong" />
            <el-option label="勾选任务" value="checkbox" />
          </el-select>
        </el-form-item>

        <!-- 金额任务特定字段 -->
        <template v-if="taskForm.task_type === 'amount'">
          <el-form-item label="目标金额" prop="target_amount">
            <el-input-number
              v-model="taskForm.target_amount"
              :min="0"
              :precision="2"
              placeholder="请输入目标金额"
              style="width: 100%"
            />
          </el-form-item>
        </template>

        <!-- 数量任务特定字段 -->
        <template v-if="taskForm.task_type === 'quantity'">
          <el-form-item label="目标数量" prop="target_quantity">
            <el-input-number
              v-model="taskForm.target_quantity"
              :min="1"
              placeholder="请输入目标数量"
              style="width: 100%"
            />
          </el-form-item>
        </template>

        <!-- 接龙任务特定字段 -->
        <template v-if="taskForm.task_type === 'jielong'">
          <el-form-item label="目标接龙数量" prop="jielong_target_count">
            <el-input-number
              v-model="taskForm.jielong_target_count"
              :min="1"
              placeholder="请输入目标接龙数量"
              style="width: 100%"
            />
          </el-form-item>
          
          <el-form-item label="接龙配置">
            <el-card class="jielong-config-card">
              <el-checkbox v-model="jielongConfig.id_enabled" label="ID字段" />
              <el-checkbox v-model="jielongConfig.remark_enabled" label="备注字段" />
              <el-checkbox v-model="jielongConfig.intention_enabled" label="意向字段" />
              
              <div v-if="jielongConfig.custom_field_enabled" style="margin-top: 10px;">
                <el-form-item label="自定义字段名称" style="margin-bottom: 10px;">
                  <el-input v-model="jielongConfig.custom_field_name" placeholder="请输入自定义字段名称" />
                </el-form-item>
                <el-form-item label="自定义字段类型" style="margin-bottom: 10px;">
                  <el-select v-model="jielongConfig.custom_field_type" placeholder="请选择字段类型">
                    <el-option label="文本" value="text" />
                    <el-option label="数值" value="number" />
                  </el-select>
                </el-form-item>
              </div>
              
              <el-checkbox v-model="jielongConfig.custom_field_enabled" label="启用自定义字段" />
            </el-card>
          </el-form-item>
        </template>
        
        <el-form-item label="优先级" prop="priority">
          <el-select v-model="taskForm.priority" placeholder="请选择优先级">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="紧急" value="urgent" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="分配类型" prop="assignment_type">
          <el-select v-model="taskForm.assignment_type" placeholder="请选择分配类型">
            <el-option label="指定用户" value="user" />
            <el-option label="指定组" value="group" />
            <el-option label="指定身份" value="identity" />
            <el-option label="所有人" value="all" />
          </el-select>
        </el-form-item>
        
        <el-form-item
          v-if="taskForm.assignment_type === 'user'"
          label="分配用户"
          prop="assigned_to"
        >
          <el-select v-model="taskForm.assigned_to" placeholder="请选择用户">
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="user.username"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item
          v-if="taskForm.assignment_type === 'group'"
          label="分配组"
          prop="target_group_id"
        >
          <el-select v-model="taskForm.target_group_id" placeholder="请选择组">
            <el-option
              v-for="group in groups"
              :key="group.id"
              :label="group.name"
              :value="group.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item
          v-if="taskForm.assignment_type === 'identity'"
          label="目标身份"
          prop="target_identity"
        >
          <el-select v-model="taskForm.target_identity" placeholder="请选择目标身份">
            <el-option label="CC(顾问)" value="cc" />
            <el-option label="SS(班主任)" value="ss" />
            <el-option label="LP(英文辅导)" value="lp" />
            <el-option label="SA(超级分析师)" value="sa" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="截止日期" prop="due_date">
          <el-date-picker
            v-model="taskForm.due_date"
            type="datetime"
            placeholder="选择截止日期"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitTask" :loading="submitting">
            {{ isEdit ? '更新' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 任务详情对话框 -->
    <el-dialog
      v-model="taskDetailVisible"
      title="任务详情"
      width="800px"
    >
      <div v-if="currentTask" class="task-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务标题">
            {{ currentTask.title }}
          </el-descriptions-item>
          <el-descriptions-item label="任务类型">
            <el-tag :type="getTaskTypeColor(currentTask.task_type)">
              {{ getTaskTypeText(currentTask.task_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="任务描述" :span="2">
            {{ currentTask.description }}
          </el-descriptions-item>
          <el-descriptions-item label="标签" :span="2">
            <el-tag v-for="tag in (currentTask.tags || [])" :key="tag" size="small" style="margin-right: 4px;">
              {{ tag }}
            </el-tag>
          </el-descriptions-item>
          <!-- 详情视角切换（我的/全部），管理员/超管可在此筛选指定用户 -->
          <el-descriptions-item label="视角" :span="2">
            <div style="display: flex; gap: 12px; align-items: center;">
              <template v-if="currentTask.task_type === 'jielong'">
                <el-radio-group v-model="jielongEntriesScope" size="small" @change="onEntriesScopeChange">
                  <el-radio-button label="mine">我的</el-radio-button>
                  <el-radio-button label="all">全部</el-radio-button>
                </el-radio-group>
              </template>
              <template v-else-if="currentTask.task_type === 'amount'">
                <el-radio-group v-model="amountRecordsScope" size="small" @change="onAmountScopeChange">
                  <el-radio-button label="mine">我的</el-radio-button>
                  <el-radio-button label="all">全部</el-radio-button>
                </el-radio-group>
              </template>
              <template v-else-if="currentTask.task_type === 'quantity'">
                <el-radio-group v-model="quantityRecordsScope" size="small" @change="onQuantityScopeChange">
                  <el-radio-button label="mine">我的</el-radio-button>
                  <el-radio-button label="all">全部</el-radio-button>
                </el-radio-group>
              </template>
              <template v-else-if="currentTask.task_type === 'checkbox'">
                <el-radio-group v-model="checkboxCompletionsScope" size="small" @change="onCompletionsScopeChange">
                  <el-radio-button label="mine">我的</el-radio-button>
                  <el-radio-button label="all">全部</el-radio-button>
                </el-radio-group>
              </template>
              <template v-if="authStore.isAdmin || authStore.isSuperAdmin">
                <el-select
                  v-model="selectedUserId"
                  placeholder="筛选用户"
                  filterable
                  clearable
                  size="small"
                  style="width: 220px;"
                  @change="onSelectedUserChange"
                >
                  <el-option
                    v-for="u in availableUsers"
                    :key="u.id"
                    :label="u.username"
                    :value="u.id"
                  />
                </el-select>
                <el-tag v-if="authStore.isAdmin && !authStore.isSuperAdmin" type="warning" size="small">
                  仅显示本组成员
                </el-tag>
              </template>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentTask.status)">
              {{ getStatusText(currentTask.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="优先级">
            <el-tag :type="getPriorityType(currentTask.priority)">
              {{ getPriorityText(currentTask.priority) }}
            </el-tag>
          </el-descriptions-item>
          
          <!-- 任务类型特定信息 -->
          <template v-if="currentTask.task_type === 'amount'">
            <!-- 我的 / 指定用户 视角：显示个人目标/当前与个人进度 -->
            <template v-if="amountRecordsScope === 'mine' || selectedUserId">
              <el-descriptions-item label="目标金额">
                {{ coalesce(currentTask.personal_target_amount, currentTask.target_amount, 0) }}
              </el-descriptions-item>
              <el-descriptions-item label="当前金额">
                {{ coalesce(currentTask.personal_current_amount, currentTask.current_amount, 0) }}
              </el-descriptions-item>
              <el-descriptions-item label="完成进度" :span="2">
                <el-progress 
                  :percentage="Math.round(ratio(coalesce(currentTask.personal_current_amount, currentTask.current_amount, 0), coalesce(currentTask.personal_target_amount, currentTask.target_amount, 1)) * 100)"
                  :color="getProgressColor(ratio(coalesce(currentTask.personal_current_amount, currentTask.current_amount, 0), coalesce(currentTask.personal_target_amount, currentTask.target_amount, 1)))"
                />
              </el-descriptions-item>
            </template>
            <!-- 全部视角：显示汇总目标/当前与汇总进度 -->
            <template v-else>
              <el-descriptions-item label="目标金额">
                {{ coalesce(currentTask.aggregate_target_amount, ((currentTask.target_amount || 0) * coalesce(currentTask.participant_count, 1)), (currentTask.target_amount || 0)) }}
              </el-descriptions-item>
              <el-descriptions-item label="当前金额">
                {{ coalesce(currentTask.aggregate_current_amount, currentTask.current_amount, 0) }}
              </el-descriptions-item>
              <el-descriptions-item label="完成进度" :span="2">
                <el-progress 
                  :percentage="Math.round(ratio(coalesce(currentTask.aggregate_current_amount, currentTask.current_amount, 0), coalesce(currentTask.aggregate_target_amount, ((currentTask.target_amount || 1) * coalesce(currentTask.participant_count, 1)), (currentTask.target_amount || 1))) * 100)"
                  :color="getProgressColor(ratio(coalesce(currentTask.aggregate_current_amount, currentTask.current_amount, 0), coalesce(currentTask.aggregate_target_amount, ((currentTask.target_amount || 1) * coalesce(currentTask.participant_count, 1)), (currentTask.target_amount || 1))))"
                />
              </el-descriptions-item>
            </template>
          </template>
          
          <template v-if="currentTask.task_type === 'quantity'">
            <!-- 我的 / 指定用户 视角：显示个人目标/当前与个人进度 -->
            <template v-if="quantityRecordsScope === 'mine' || selectedUserId">
              <el-descriptions-item label="目标数量">
                {{ coalesce(currentTask.personal_target_quantity, currentTask.target_quantity, 0) }}
              </el-descriptions-item>
              <el-descriptions-item label="当前数量">
                {{ coalesce(currentTask.personal_current_quantity, currentTask.current_quantity, 0) }}
              </el-descriptions-item>
              <el-descriptions-item label="完成进度" :span="2">
                <el-progress 
                  :percentage="Math.round(ratio(coalesce(currentTask.personal_current_quantity, currentTask.current_quantity, 0), coalesce(currentTask.personal_target_quantity, currentTask.target_quantity, 1)) * 100)"
                  :color="getProgressColor(ratio(coalesce(currentTask.personal_current_quantity, currentTask.current_quantity, 0), coalesce(currentTask.personal_target_quantity, currentTask.target_quantity, 1)))"
                />
              </el-descriptions-item>
            </template>
            <!-- 全部视角：显示汇总目标/当前与汇总进度 -->
            <template v-else>
              <el-descriptions-item label="目标数量">
                {{ coalesce(currentTask.aggregate_target_quantity, ((currentTask.target_quantity || 0) * coalesce(currentTask.participant_count, 1)), (currentTask.target_quantity || 0)) }}
              </el-descriptions-item>
              <el-descriptions-item label="当前数量">
                {{ coalesce(currentTask.aggregate_current_quantity, currentTask.current_quantity, 0) }}
              </el-descriptions-item>
              <el-descriptions-item label="完成进度" :span="2">
                <el-progress 
                  :percentage="Math.round(ratio(coalesce(currentTask.aggregate_current_quantity, currentTask.current_quantity, 0), coalesce(currentTask.aggregate_target_quantity, ((currentTask.target_quantity || 1) * coalesce(currentTask.participant_count, 1)), (currentTask.target_quantity || 1))) * 100)"
                  :color="getProgressColor(ratio(coalesce(currentTask.aggregate_current_quantity, currentTask.current_quantity, 0), coalesce(currentTask.aggregate_target_quantity, ((currentTask.target_quantity || 1) * coalesce(currentTask.participant_count, 1)), (currentTask.target_quantity || 1))))"
                />
              </el-descriptions-item>
            </template>
          </template>
          
          <template v-if="currentTask.task_type === 'jielong'">
            <!-- 我的 / 指定用户 视角：显示个人目标/当前与个人进度 -->
            <template v-if="jielongEntriesScope === 'mine' || selectedUserId">
              <el-descriptions-item label="目标接龙数量">
                {{ coalesce(currentTask.personal_jielong_target_count, currentTask.jielong_target_count, 0) }}
              </el-descriptions-item>
              <el-descriptions-item label="当前接龙数量">
                {{ coalesce(currentTask.personal_jielong_current_count, currentTask.jielong_current_count, 0) }}
              </el-descriptions-item>
              <el-descriptions-item label="接龙进度" :span="2">
                <el-progress 
                  :percentage="Math.round(coalesce(currentTask.personal_jielong_progress, ratio(coalesce(currentTask.personal_jielong_current_count, currentTask.jielong_current_count, 0), coalesce(currentTask.personal_jielong_target_count, currentTask.jielong_target_count, 1))) * 100)"
                  :color="getProgressColor(coalesce(currentTask.personal_jielong_progress, ratio(coalesce(currentTask.personal_jielong_current_count, currentTask.jielong_current_count, 0), coalesce(currentTask.personal_jielong_target_count, currentTask.jielong_target_count, 1))))"
                />
              </el-descriptions-item>
            </template>
            <!-- 全部视角：显示汇总当前/目标与汇总进度 -->
            <template v-else>
              <el-descriptions-item label="目标接龙数量">
                {{ coalesce(currentTask.aggregate_jielong_target_count, ((currentTask.jielong_target_count || 0) * coalesce(currentTask.participant_count, 1)), (currentTask.jielong_target_count || 0)) }}
              </el-descriptions-item>
              <el-descriptions-item label="当前接龙数量">
                {{ currentTask.jielong_current_count || 0 }}
              </el-descriptions-item>
              <el-descriptions-item label="接龙进度" :span="2">
                <el-progress 
                  :percentage="Math.round(coalesce(currentTask.aggregate_jielong_progress, ratio((currentTask.jielong_current_count || 0), coalesce(currentTask.aggregate_jielong_target_count, ((currentTask.jielong_target_count || 1) * coalesce(currentTask.participant_count, 1)), (currentTask.jielong_target_count || 1)))) * 100)"
                  :color="getProgressColor(coalesce(currentTask.aggregate_jielong_progress, ratio((currentTask.jielong_current_count || 0), coalesce(currentTask.aggregate_jielong_target_count, ((currentTask.jielong_target_count || 1) * coalesce(currentTask.participant_count, 1)), (currentTask.jielong_target_count || 1)))))"
                />
              </el-descriptions-item>
            </template>

            <!-- 接龙配置信息 -->
            <el-descriptions-item label="接龙配置" :span="2">
              <div class="jielong-config-info">
                <el-tag v-if="currentTask.jielong_config?.id_enabled" size="small" type="info">ID字段</el-tag>
                <el-tag v-if="currentTask.jielong_config?.remark_enabled" size="small" type="info">备注字段</el-tag>
                <el-tag v-if="currentTask.jielong_config?.intention_enabled" size="small" type="info">意向字段</el-tag>
                <el-tag v-if="currentTask.jielong_config?.custom_field_enabled" size="small" type="info">
                  {{ currentTask.jielong_config?.custom_field_name || '自定义字段' }}
                </el-tag>
              </div>
            </el-descriptions-item>
          </template>
          
          <template v-if="currentTask.task_type === 'checkbox'">
            <!-- 个人/指定用户视角下显示完成状态；全部视角下显示汇总进度 -->
            <template v-if="checkboxCompletionsScope === 'mine' || selectedUserId">
              <el-descriptions-item label="完成状态" :span="2">
                <template v-if="(currentTask.personal_is_completed !== undefined && currentTask.personal_is_completed !== null) ? currentTask.personal_is_completed : currentTask.is_completed">
                  <el-icon color="green"><Check /></el-icon>
                  <span style="color: green; margin-left: 4px;">已完成</span>
                </template>
                <template v-else>
                  <el-icon color="gray"><Close /></el-icon>
                  <span style="color: gray; margin-left: 4px;">未完成</span>
                </template>
              </el-descriptions-item>
            </template>
            <template v-else>
              <el-descriptions-item label="完成人数">
                {{ currentTask.completed_count || 0 }} / {{ currentTask.participant_count || 0 }}
              </el-descriptions-item>
              <el-descriptions-item label="完成进度" :span="2">
                <el-progress
                  :percentage="Math.round(((currentTask.aggregate_checkbox_progress || 0) * 100))"
                  :color="getProgressColor(currentTask.aggregate_checkbox_progress || 0)"
                />
              </el-descriptions-item>
            </template>
          </template>
          
          <!-- 分配信息 -->
          <el-descriptions-item label="分配类型">
            {{ getAssignmentTypeText(currentTask.assignment_type) }}
          </el-descriptions-item>
          <el-descriptions-item label="分配对象">
            {{ getAssignmentTarget(currentTask) }}
          </el-descriptions-item>
          
          <el-descriptions-item label="截止日期">
            {{ currentTask.due_date ? formatDateTime(currentTask.due_date) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDateTime(currentTask.created_at) }}
          </el-descriptions-item>
          
          <el-descriptions-item label="更新时间">
            {{ currentTask.updated_at ? formatDateTime(currentTask.updated_at) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建者">
            {{ currentTask.created_by_username || '-' }}
          </el-descriptions-item>
        </el-descriptions>
        
        <!-- 任务参与记录（只读显示） -->
        <div v-if="currentTask.task_type !== 'checkbox'" class="participation-records">
          <h4>参与记录</h4>
          <el-alert 
            title="提示" 
            type="info" 
            :closable="false"
            style="margin-bottom: 16px;"
          >
            要参与任务，请在任务列表中点击对应的快速操作按钮
          </el-alert>
          
          <!-- 这里可以显示参与记录的只读信息 -->
          <div v-if="currentTask.task_type === 'amount'" class="amount-records">
            <div style="margin-bottom: 8px; display: flex; gap: 12px; align-items: center;">
              <el-radio-group v-model="amountRecordsScope" size="small" @change="onAmountScopeChange">
                <el-radio-button label="mine">我的</el-radio-button>
                <el-radio-button label="all">全部</el-radio-button>
              </el-radio-group>
              <el-tag type="info" size="small">
                {{ amountRecordsScope === 'mine' ? '按当前用户筛选' : '显示全部记录' }}
              </el-tag>
              <template v-if="authStore.isAdmin || authStore.isSuperAdmin">
                <el-select
                  v-model="selectedUserId"
                  placeholder="筛选用户"
                  filterable
                  clearable
                  size="small"
                  style="width: 220px;"
                  @change="onSelectedUserChange"
                >
                  <el-option
                    v-for="u in availableUsers"
                    :key="u.id"
                    :label="u.username"
                    :value="u.id"
                  />
                </el-select>
                <el-tag v-if="authStore.isAdmin && !authStore.isSuperAdmin" type="warning" size="small">
                  仅显示本组成员
                </el-tag>
              </template>
            </div>
            <el-table 
              :data="amountRecords" 
              size="small"
              v-loading="loadingAmountRecords"
            >
              <el-table-column prop="sequence" label="序号" width="60" />
              <el-table-column prop="user_username" label="用户" width="120" />
              <el-table-column prop="value" label="金额/值" width="120" />
              <el-table-column prop="created_at" label="参与时间" width="160">
                <template #default="{ row }">
                  {{ formatDateTime(row.created_at) }}
                </template>
              </el-table-column>
            </el-table>
          </div>

          <div v-if="currentTask.task_type === 'quantity'" class="quantity-records">
            <div style="margin-bottom: 8px; display: flex; gap: 12px; align-items: center;">
              <el-radio-group v-model="quantityRecordsScope" size="small" @change="onQuantityScopeChange">
                <el-radio-button label="mine">我的</el-radio-button>
                <el-radio-button label="all">全部</el-radio-button>
              </el-radio-group>
              <el-tag type="info" size="small">
                {{ quantityRecordsScope === 'mine' ? '按当前用户筛选' : '显示全部记录' }}
              </el-tag>
              <template v-if="authStore.isAdmin || authStore.isSuperAdmin">
                <el-select
                  v-model="selectedUserId"
                  placeholder="筛选用户"
                  filterable
                  clearable
                  size="small"
                  style="width: 220px;"
                  @change="onSelectedUserChange"
                >
                  <el-option
                    v-for="u in availableUsers"
                    :key="u.id"
                    :label="u.username"
                    :value="u.id"
                  />
                </el-select>
                <el-tag v-if="authStore.isAdmin && !authStore.isSuperAdmin" type="warning" size="small">
                  仅显示本组成员
                </el-tag>
              </template>
            </div>
            <el-table 
              :data="quantityRecords" 
              size="small"
              v-loading="loadingQuantityRecords"
            >
              <el-table-column prop="sequence" label="序号" width="60" />
              <el-table-column prop="user_username" label="用户" width="120" />
              <el-table-column prop="value" label="数量/值" width="120" />
              <el-table-column prop="created_at" label="参与时间" width="160">
                <template #default="{ row }">
                  {{ formatDateTime(row.created_at) }}
                </template>
              </el-table-column>
            </el-table>
          </div>
          <div v-if="currentTask.task_type === 'jielong'" class="jielong-entries">
            <div style="margin-bottom: 8px; display: flex; gap: 12px; align-items: center;">
              <el-radio-group v-model="jielongEntriesScope" size="small" @change="onEntriesScopeChange">
                <el-radio-button label="mine">我的</el-radio-button>
                <el-radio-button label="all">全部</el-radio-button>
              </el-radio-group>
              <el-tag type="info" size="small">
                {{ jielongEntriesScope === 'mine' ? '按当前用户筛选' : '显示全部记录' }}
              </el-tag>
              <template v-if="authStore.isAdmin || authStore.isSuperAdmin">
                <el-select
                  v-model="selectedUserId"
                  placeholder="筛选用户"
                  filterable
                  clearable
                  size="small"
                  style="width: 220px;"
                  @change="onSelectedUserChange"
                >
                  <el-option
                    v-for="u in availableUsers"
                    :key="u.id"
                    :label="u.username"
                    :value="u.id"
                  />
                </el-select>
                <el-tag v-if="authStore.isAdmin && !authStore.isSuperAdmin" type="warning" size="small">
                  仅显示本组成员
                </el-tag>
              </template>
            </div>
            <el-table 
              :data="jielongEntries" 
              size="small"
              v-loading="loadingEntries"
            >
              <el-table-column prop="sequence" label="序号" width="60" />
              <el-table-column prop="user_username" label="用户" width="100" />
              <el-table-column prop="id" label="ID" width="120" />
              <el-table-column prop="remark" label="备注" />
              <el-table-column prop="created_at" label="参与时间" width="160">
                <template #default="{ row }">
                  {{ formatDateTime(row.created_at) }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <!-- 勾选任务完成记录 -->
        <div v-if="currentTask.task_type === 'checkbox'" class="participation-records">
          <h4>完成记录</h4>
          <div style="margin-bottom: 8px; display: flex; gap: 12px; align-items: center;">
            <el-radio-group v-model="checkboxCompletionsScope" size="small" @change="onCompletionsScopeChange">
              <el-radio-button label="mine">我的</el-radio-button>
              <el-radio-button label="all">全部</el-radio-button>
            </el-radio-group>
            <el-tag type="info" size="small">
              {{ checkboxCompletionsScope === 'mine' ? '按当前用户筛选' : '显示全部记录' }}
            </el-tag>
            <template v-if="authStore.isAdmin || authStore.isSuperAdmin">
              <el-select
                v-model="selectedUserId"
                placeholder="筛选用户"
                filterable
                clearable
                size="small"
                style="width: 220px;"
                @change="onSelectedUserChange"
              >
                <el-option
                  v-for="u in availableUsers"
                  :key="u.id"
                  :label="u.username"
                  :value="u.id"
                />
              </el-select>
              <el-tag v-if="authStore.isAdmin && !authStore.isSuperAdmin" type="warning" size="small">
                仅显示本组成员
              </el-tag>
            </template>
          </div>
          <el-table 
            :data="checkboxCompletions" 
            size="small"
            v-loading="loadingCompletions"
          >
            <el-table-column prop="sequence" label="序号" width="60" />
            <el-table-column prop="user_username" label="用户" width="120" />
            <el-table-column prop="completion_value" label="完成值" width="120" />
            <el-table-column prop="completed_at" label="完成时间" width="160">
              <template #default="{ row }">
                {{ formatDateTime(row.completed_at) }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>

    <!-- 任务完成对话框 -->
    <el-dialog
      v-model="completeDialogVisible"
      title="完成任务"
      width="500px"
      @close="resetCompleteForm"
    >
      <el-form :model="completeForm" label-width="100px">
        <el-form-item label="任务标题">
          <span>{{ completeForm.title }}</span>
        </el-form-item>
        
        <el-form-item label="完成备注">
          <el-input
            v-model="completeForm.completion_note"
            type="textarea"
            :rows="4"
            placeholder="请输入完成备注（可选）"
          />
        </el-form-item>
        
        <template v-if="completeForm.task_type === 'amount'">
          <el-form-item label="完成数量" required>
            <el-input-number
              v-model="completeForm.completed_amount"
              :min="0"
              :max="completeForm.target_amount"
              placeholder="请输入完成数量"
            />
            <span style="margin-left: 8px;">/ {{ completeForm.target_amount }}</span>
          </el-form-item>
        </template>
        
        <template v-if="completeForm.task_type === 'quantity'">
          <el-form-item label="完成数量" required>
            <el-input-number
              v-model="completeForm.completed_quantity"
              :min="0"
              :max="completeForm.target_quantity"
              placeholder="请输入完成数量"
            />
            <span style="margin-left: 8px;">/ {{ completeForm.target_quantity }}</span>
          </el-form-item>
        </template>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="completeDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitTaskCompletion">确认完成</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import Plus from '~icons/tabler/plus'
import Search from '~icons/tabler/search'
import Refresh from '~icons/tabler/refresh'
import Check from '~icons/tabler/check'
import Close from '~icons/tabler/x'
import { formatDateTime } from '@/utils/date'
import api from '@/utils/api'

import { useAuthStore } from '@/stores/auth'

// 认证store
const authStore = useAuthStore()

// 路由
const router = useRouter()
const route = useRoute()

// 数据
const loading = ref(false)
const tasks = ref([])
const users = ref([])
const groups = ref([])
const selectedTasks = ref([])

// 过滤器
const filters = reactive({
  status: '',
  priority: '',
  task_type: '',
  search: ''
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 对话框
const dialogVisible = ref(false)
const taskDetailVisible = ref(false)
const completeDialogVisible = ref(false)
const activeTab = ref('basic')
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref()

// 常用标签
const commonTags = ref(['重要', '紧急', '日常', '项目', '会议', '学习', '沟通'])

// 任务表单
const taskForm = reactive({
  title: '',
  description: '',
  tags: [],
  task_type: 'checkbox',
  priority: 'medium',
  assignment_type: 'user',
  assigned_to: null,
  target_group_id: null,
  target_identity: '',
  due_date: '',
  // 任务类型特定字段
  target_amount: null,
  target_quantity: null,
  jielong_target_count: null,
  jielong_config: {}
})

// 接龙配置
const jielongConfig = reactive({
  id_enabled: true,
  remark_enabled: true,
  intention_enabled: false,
  custom_field_enabled: false,
  custom_field_name: '',
  custom_field_type: 'text'
})

// 当前查看的任务详情
const currentTask = ref(null)

// 接龙相关数据
const jielongEntries = ref([])
const loadingEntries = ref(false)
const jielongEntriesScope = ref('mine')
// 管理员/超级管理员用户筛选
const availableUsers = ref([])
const selectedUserId = ref(null)

// 金额/数量记录与勾选完成记录
const amountRecords = ref([])
const quantityRecords = ref([])
const checkboxCompletions = ref([])
const loadingAmountRecords = ref(false)
const loadingQuantityRecords = ref(false)
const loadingCompletions = ref(false)
const amountRecordsScope = ref('mine')
const quantityRecordsScope = ref('mine')
const checkboxCompletionsScope = ref('mine')

// 详情视角（mine/all）统一绑定，按任务类型映射到对应 scope
const detailScope = computed({
  get() {
    const type = currentTask.value?.task_type
    if (type === 'jielong') return jielongEntriesScope.value
    if (type === 'amount') return amountRecordsScope.value
    if (type === 'quantity') return quantityRecordsScope.value
    if (type === 'checkbox') return checkboxCompletionsScope.value
    return 'mine'
  },
  set(val) {
    const type = currentTask.value?.task_type
    if (type === 'jielong') {
      jielongEntriesScope.value = val
      onEntriesScopeChange()
    } else if (type === 'amount') {
      amountRecordsScope.value = val
      onAmountScopeChange()
    } else if (type === 'quantity') {
      quantityRecordsScope.value = val
      onQuantityScopeChange()
    } else if (type === 'checkbox') {
      checkboxCompletionsScope.value = val
      onCompletionsScopeChange()
    }
  }
})

const loadAvailableUsers = async () => {
  // 仅管理员或超级管理员加载用户列表
  if (!(authStore.isAdmin || authStore.isSuperAdmin)) {
    availableUsers.value = []
    selectedUserId.value = null
    return
  }
  try {
    // 后端会根据权限返回可见用户：
    // - 超级管理员：所有用户
    // - 管理员：仅本组用户
    const resp = await api.get('/users', { params: { page: 1, size: 200 } })
    const items = resp.data.items || resp.data || []
    availableUsers.value = items.map(u => ({ id: u.id, username: u.username }))
  } catch (e) {
    console.error('加载用户列表失败:', e)
    availableUsers.value = []
  }
}

const onSelectedUserChange = () => {
  if (currentTask.value?.id) {
    // 选择用户后刷新参与记录与个人统计
    if (currentTask.value.task_type === 'jielong') {
      fetchJielongEntries(currentTask.value.id)
    } else if (currentTask.value.task_type === 'amount') {
      fetchAmountRecords(currentTask.value.id)
    } else if (currentTask.value.task_type === 'quantity') {
      fetchQuantityRecords(currentTask.value.id)
    } else if (currentTask.value.task_type === 'checkbox') {
      fetchCheckboxCompletions(currentTask.value.id)
    }
    refreshTaskDetail()
  }
}

// 任务完成表单
const completeForm = reactive({
  id: null,
  title: '',
  task_type: '',
  target_amount: null,
  target_quantity: null,
  completion_note: '',
  completed_amount: null,
  completed_quantity: null
})

// 表单验证规则
const formRules = {
  title: [
    { required: true, message: '请输入任务标题', trigger: 'blur' },
    { min: 2, max: 100, message: '标题长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入任务描述', trigger: 'blur' }
  ],
  task_type: [
    { required: true, message: '请选择任务类型', trigger: 'change' }
  ],
  priority: [
    { required: true, message: '请选择优先级', trigger: 'change' }
  ],
  assignment_type: [
    { required: true, message: '请选择分配类型', trigger: 'change' }
  ],
  target_amount: [
    { required: true, message: '请输入目标金额', trigger: 'blur' }
  ],
  target_quantity: [
    { required: true, message: '请输入目标数量', trigger: 'blur' }
  ],
  jielong_target_count: [
    { required: true, message: '请输入目标接龙数量', trigger: 'blur' }
  ]
}

// 获取状态类型
const getStatusType = (status) => {
  const statusMap = {
    'pending': 'warning',
    'processing': 'primary',
    'done': 'success'
  }
  return statusMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    'pending': '待处理',
    'processing': '进行中',
    'done': '已完成'
  }
  return statusMap[status] || status
}

// 获取优先级类型
const getPriorityType = (priority) => {
  const priorityMap = {
    'low': 'info',
    'medium': 'warning',
    'high': 'danger',
    'urgent': 'danger',
    // 兼容旧数据
    1: 'info',
    2: 'warning',
    3: 'danger',
    4: 'danger'
  }
  return priorityMap[priority] || 'info'
}

// 获取优先级文本
const getPriorityText = (priority) => {
  const priorityMap = {
    'low': '低',
    'medium': '中',
    'high': '高',
    'urgent': '紧急',
    // 兼容旧数据
    1: '低',
    2: '中',
    3: '高',
    4: '紧急'
  }
  return priorityMap[priority] || priority
}

// 获取任务类型颜色
const getTaskTypeColor = (taskType) => {
  const typeMap = {
    'amount': 'success',
    'quantity': 'primary',
    'jielong': 'warning',
    'checkbox': 'info'
  }
  return typeMap[taskType] || 'info'
}

// 获取任务类型文本
const getTaskTypeText = (taskType) => {
  const typeMap = {
    'amount': '金额',
    'quantity': '数量',
    'jielong': '接龙',
    'checkbox': '勾选'
  }
  return typeMap[taskType] || taskType
}

// 任务类型变化处理
const onTaskTypeChange = (taskType) => {
  // 清空其他类型的字段
  taskForm.target_amount = null
  taskForm.target_quantity = null
  taskForm.jielong_target_count = null
  taskForm.jielong_config = {}
  
  // 重置接龙配置
  Object.assign(jielongConfig, {
    id_enabled: true,
    remark_enabled: true,
    intention_enabled: false,
    custom_field_enabled: false,
    custom_field_name: '',
    custom_field_type: 'text'
  })
}

// 获取任务列表
const fetchTasks = async () => {
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
    
    const response = await api.get('/tasks', { params })
    // 兼容两种返回结构：{ items: [...], total } 或直接数组 [...]
    const list = coalesce(response.data?.items, response.data, [])
    tasks.value = Array.isArray(list) ? list : []
    // 优先使用后端提供的 total；否则退化为当前列表长度
    const total = response.data?.total
    pagination.total = typeof total === 'number' ? total : (Array.isArray(list) ? list.length : 0)
  } catch (error) {
    ElMessage.error('获取任务列表失败')
  } finally {
    loading.value = false
  }
}

// 获取用户列表
const fetchUsers = async () => {
  try {
    const response = await api.get('/users')
    users.value = response.data.items || response.data || []
  } catch (error) {
    console.error('获取用户列表失败:', error)
  }
}

// 获取组列表
const fetchGroups = async () => {
  try {
    const response = await api.get('/groups')
    const allGroups = response.data.items || response.data || []
    
    // 权限控制：管理员只能选择自己所在的组别，超级管理员可以选择任意组别
    if (authStore.isSuperAdmin) {
      groups.value = allGroups
    } else if (authStore.isAdmin && authStore.user?.group_id) {
      // 管理员只能看到自己所在的组别
      groups.value = allGroups.filter(group => group.id === authStore.user.group_id)
    } else {
      groups.value = []
    }
  } catch (error) {
    console.error('获取组列表失败:', error)
  }
}

// 打开创建对话框
const openCreateDialog = () => {
  isEdit.value = false
  dialogVisible.value = true
}

// 编辑任务
const editTask = (task) => {
  isEdit.value = true
  Object.assign(taskForm, {
    id: parseInt(task.id),
    title: task.title,
    description: task.description,
    tags: task.tags || [],
    task_type: task.task_type || 'checkbox',
    priority: task.priority,
    assignment_type: task.assignment_type,
    assigned_to: task.assigned_to,
    target_group_id: task.target_group_id,
    target_identity: task.target_identity,
    due_date: task.due_date,
    target_amount: task.target_amount,
    target_quantity: task.target_quantity,
    jielong_target_count: task.jielong_target_count,
    jielong_config: task.jielong_config || {}
  })
  
  // 如果是接龙任务，设置接龙配置
  if (task.task_type === 'jielong' && task.jielong_config) {
    Object.assign(jielongConfig, task.jielong_config)
  }
  
  dialogVisible.value = true
}

// 查看任务详情 - 已移动到 script setup 底部

// 刷新任务详情
const refreshTaskDetail = async () => {
  if (!currentTask.value) return
  
  try {
    const params = {}
    // 如果管理员/超管选择了特定用户，则请求该用户的个人统计
    if ((authStore.isAdmin || authStore.isSuperAdmin) && selectedUserId.value) {
      params.view_user_id = selectedUserId.value
    }
    // 详情视图范围（我的/全部），按任务类型选择对应 scope
    if (currentTask.value.task_type === 'jielong') {
      params.scope = jielongEntriesScope.value
    } else if (currentTask.value.task_type === 'amount') {
      params.scope = amountRecordsScope.value
    } else if (currentTask.value.task_type === 'quantity') {
      params.scope = quantityRecordsScope.value
    } else if (currentTask.value.task_type === 'checkbox') {
      params.scope = checkboxCompletionsScope.value
    }
    const response = await api.get(`/tasks/${currentTask.value.id}`, { params })
    currentTask.value = response.data
    // 同时刷新任务列表
    fetchTasks()
  } catch (error) {
    ElMessage.error('刷新任务详情失败')
  }
}

// 重置表单
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  Object.assign(taskForm, {
    title: '',
    description: '',
    tags: [],
    task_type: 'checkbox',
    priority: 'medium',
    assignment_type: 'user',
    assigned_to: null,
    target_group_id: null,
    target_identity: '',
    due_date: '',
    target_amount: null,
    target_quantity: null,
    jielong_target_count: null,
    jielong_config: {}
  })
  
  // 重置接龙配置
  Object.assign(jielongConfig, {
    id_enabled: true,
    remark_enabled: true,
    intention_enabled: false,
    custom_field_enabled: false,
    custom_field_name: '',
    custom_field_type: 'text'
  })
}

// 提交任务
const submitTask = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    // 准备提交数据
    const submitData = { ...taskForm }
    
    // 如果是接龙任务，设置接龙配置
    if (taskForm.task_type === 'jielong') {
      submitData.jielong_config = { ...jielongConfig }
    }
    
    // 处理组分配：将target_group_id转换为assigned_group_ids数组
    if (taskForm.assignment_type === 'group' && taskForm.target_group_id) {
      submitData.assigned_group_ids = [taskForm.target_group_id]
    } else {
      submitData.assigned_group_ids = []
    }

    // 处理用户分配：将 assigned_to 转换为 assigned_user_ids 数组
    if (taskForm.assignment_type === 'user' && taskForm.assigned_to) {
      submitData.assigned_user_ids = [parseInt(taskForm.assigned_to)]
    } else {
      submitData.assigned_user_ids = []
    }
    
    // 清理不需要的字段
    delete submitData.target_group_id  // 删除前端使用的字段
    delete submitData.assigned_to      // 避免发送未使用的字段
    if (taskForm.task_type !== 'amount') {
      delete submitData.target_amount
    }
    if (taskForm.task_type !== 'quantity') {
      delete submitData.target_quantity
    }
    if (taskForm.task_type !== 'jielong') {
      delete submitData.jielong_target_count
      delete submitData.jielong_config
    }
    
    if (isEdit.value) {
      await api.put(`/tasks/${taskForm.id}`, submitData)
      ElMessage.success('任务更新成功')
    } else {
      await api.post('/tasks', submitData)
      ElMessage.success('任务创建成功')
    }
    
    dialogVisible.value = false
    fetchTasks()
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
    }
  } finally {
    submitting.value = false
  }
}

// 删除任务
const deleteTask = async (task) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除任务"${task.title}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.delete(`/tasks/${parseInt(task.id)}`)
    ElMessage.success('删除成功')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 权限检查函数
const canEditTask = (task) => {
  // 管理员和超级管理员可以编辑所有任务
  if (authStore.isAdmin || authStore.isSuperAdmin) {
    return true
  }
  // 任务创建者可以编辑自己的任务
  return task.created_by === authStore.user?.id
}

const canDeleteTask = (task) => {
  // 管理员和超级管理员可以删除所有任务
  if (authStore.isAdmin || authStore.isSuperAdmin) {
    return true
  }
  // 任务创建者可以删除自己的任务
  return task.created_by === authStore.user?.id
}

const canCompleteTask = (task) => {
  // 已完成的任务不能再完成
  if (task.status === 'completed') {
    return false
  }
  
  // 检查任务是否分配给当前用户
  const currentUserId = authStore.user?.id
  
  // 如果任务分配给所有人
  if (task.assignment_type === 'all') {
    return true
  }
  
  // 如果任务分配给特定身份类型（大小写统一）
  if (task.assignment_type === 'identity') {
    const ti = String(task.target_identity || '').toLowerCase()
    const ui = String(authStore.user?.identity_type || '').toLowerCase()
    if (ti === ui) {
      return true
    }
  }
  
  // 如果任务分配给用户组，检查当前用户是否在该组中
  if (task.assignment_type === 'group' && task.target_group_id) {
    // 这里需要检查用户是否在目标组中，暂时简化处理
    return authStore.user?.groups?.some(group => group.id === task.target_group_id)
  }
  
  return false
}

// 完成任务
const completeTask = (task) => {
  // 填充完成表单
  completeForm.id = task.id
  completeForm.title = task.title
  completeForm.task_type = task.task_type
  completeForm.target_amount = task.target_amount
  completeForm.target_quantity = task.target_quantity
  completeForm.completion_note = ''
  completeForm.completed_amount = task.task_type === 'amount' ? task.target_amount : null
  completeForm.completed_quantity = task.task_type === 'quantity' ? task.target_quantity : null
  
  // 打开完成对话框
  completeDialogVisible.value = true
}

// 重置完成表单
const resetCompleteForm = () => {
  completeForm.id = null
  completeForm.title = ''
  completeForm.task_type = ''
  completeForm.target_amount = null
  completeForm.target_quantity = null
  completeForm.completion_note = ''
  completeForm.completed_amount = null
  completeForm.completed_quantity = null
}

// 提交任务完成
const submitTaskCompletion = async () => {
  try {
    const completionData = {
      status: 'completed',
      completion_note: completeForm.completion_note
    }
    
    // 根据任务类型添加完成数据
    if (completeForm.task_type === 'amount' && completeForm.completed_amount !== null) {
      completionData.completed_amount = completeForm.completed_amount
    }
    
    if (completeForm.task_type === 'quantity' && completeForm.completed_quantity !== null) {
      completionData.completed_quantity = completeForm.completed_quantity
    }
    
    await api.put(`/tasks/${parseInt(completeForm.id)}/status`, completionData)
    
    ElMessage.success('任务已完成')
    completeDialogVisible.value = false
    fetchTasks()
  } catch (error) {
    ElMessage.error('完成任务失败')
  }
}

// 处理表格选择变化
const handleSelectionChange = (selection) => {
  selectedTasks.value = selection
}

// 显示任务统计
const showTaskStats = async () => {
  try {
    const response = await api.get('/tasks/stats')
    const stats = response.data
    
    await ElMessageBox.alert(
      `
      <div style="text-align: left;">
        <p><strong>任务总数：</strong>${stats.total || 0}</p>
        <p><strong>待处理：</strong>${stats.pending || 0}</p>
        <p><strong>进行中：</strong>${stats.processing || 0}</p>
        <p><strong>已完成：</strong>${stats.completed || 0}</p>
        <p><strong>高优先级：</strong>${stats.high_priority || 0}</p>
        <p><strong>紧急任务：</strong>${stats.urgent || 0}</p>
      </div>
      `,
      '任务统计',
      {
        dangerouslyUseHTMLString: true,
        confirmButtonText: '确定'
      }
    )
  } catch (error) {
    ElMessage.error('获取任务统计失败')
  }
}

// 显示批量分配对话框
const showBatchAssign = () => {
  if (selectedTasks.value.length === 0) {
    ElMessage.warning('请先选择要分配的任务')
    return
  }
  
  ElMessageBox.prompt(
    `确定要批量分配这 ${selectedTasks.value.length} 个任务吗？请输入目标用户ID：`,
    '批量分配任务',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /^\d+$/,
      inputErrorMessage: '请输入有效的用户ID'
    }
  ).then(async ({ value }) => {
    try {
      const taskIds = selectedTasks.value.map(task => task.id)
      await api.put('/tasks/batch-assign', {
        task_ids: taskIds,
        assigned_to: parseInt(value)
      })
      
      ElMessage.success('批量分配成功')
      selectedTasks.value = []
      fetchTasks()
    } catch (error) {
      ElMessage.error('批量分配失败')
    }
  }).catch(() => {
    // 用户取消
  })
}

// 快速参与金额任务
const quickParticipateAmount = async (task) => {
  try {
    const { value } = await ElMessageBox.prompt(
      `请输入参与金额（目标：${task.target_amount}，当前：${task.current_amount || 0}）：`,
      '参与金额任务',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPattern: /^\d+(\.\d{1,2})?$/,
        inputErrorMessage: '请输入有效的金额',
        inputType: 'number'
      }
    )
    
    const amount = parseFloat(value)
    if (amount <= 0) {
      ElMessage.error('金额必须大于0')
      return
    }
    
    await api.post(`/task-sync/sync-task-to-report`, {
      task_id: task.id,
      amount: amount,
      remark: ''
    })
    
    ElMessage.success('参与成功')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('参与失败')
    }
  }
}

// 快速参与数量任务
const quickParticipateQuantity = async (task) => {
  try {
    const { value } = await ElMessageBox.prompt(
      `请输入参与数量（目标：${task.target_quantity}，当前：${task.current_quantity || 0}）：`,
      '参与数量任务',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPattern: /^\d+$/,
        inputErrorMessage: '请输入有效的数量',
        inputType: 'number'
      }
    )
    
    const quantity = parseInt(value)
    if (quantity <= 0) {
      ElMessage.error('数量必须大于0')
      return
    }
    
    await api.post(`/task-sync/sync-task-to-report`, {
      task_id: task.id,
      quantity: quantity,
      remark: ''
    })
    
    ElMessage.success('参与成功')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('参与失败')
    }
  }
}

// 快速参与接龙任务
const quickParticipateJielong = async (task) => {
  try {
    // 构建接龙表单
    const fields = []
    const config = task.jielong_config || {}
    
    if (config.id_enabled) {
      fields.push({ label: 'ID', key: 'id', required: true })
    }
    if (config.remark_enabled) {
      fields.push({ label: '备注', key: 'remark', required: false })
    }
    if (config.intention_enabled) {
      fields.push({ label: '意向', key: 'intention', required: false })
    }
    if (config.custom_field_enabled && config.custom_field_name) {
      fields.push({ 
        label: config.custom_field_name, 
        key: 'custom_field', 
        required: false,
        type: config.custom_field_type || 'text'
      })
    }
    
    // 简化版接龙参与 - 只收集ID和备注
    const personalCurrent = (task.personal_jielong_current_count !== undefined && task.personal_jielong_current_count !== null) ? task.personal_jielong_current_count : (task.jielong_current_count || 0)
    const personalTarget = (task.personal_jielong_target_count !== undefined && task.personal_jielong_target_count !== null) ? task.personal_jielong_target_count : (task.jielong_target_count || 0)
    const { value: id } = await ElMessageBox.prompt(
      `请输入您的ID（当前接龙：${personalCurrent}/${personalTarget}）：`,
      '参与接龙',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValidator: (value) => {
          if (!value || value.trim() === '') {
            return 'ID不能为空'
          }
          return true
        }
      }
    )
    
    const { value: remark } = await ElMessageBox.prompt(
      '请输入备注（可选）：',
      '参与接龙',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputType: 'textarea'
      }
    ).catch(() => ({ value: '' }))
    
    const jielongData = {
      id: id.trim(),
      remark: remark || '',
      intention: '',
      custom_field: ''
    }
    
    await api.post(`/tasks/${task.id}/jielong`, jielongData)
    
    ElMessage.success('接龙成功')
    fetchTasks()
    if (currentTask.value?.id === task.id) {
      // 参与成功后刷新详情和参与记录
      refreshTaskDetail()
      fetchJielongEntries(task.id)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('接龙失败')
    }
  }
}

// 快速切换勾选任务状态
const quickToggleCheckbox = async (task) => {
  try {
    const newStatus = !task.is_completed
    await api.put(`/task-sync/sync-task-to-report/${task.id}`, {
      is_completed: newStatus
    })
    
    ElMessage.success(newStatus ? '任务已完成' : '任务已取消完成')
    fetchTasks()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 监听接龙配置变化
watch(jielongConfig, (newConfig) => {
  if (taskForm.task_type === 'jielong') {
    taskForm.jielong_config = { ...newConfig }
  }
}, { deep: true })

// 获取进度颜色
const getProgressColor = (percentage) => {
  if (percentage < 0.3) return '#f56c6c'
  if (percentage < 0.7) return '#e6a23c'
  return '#67c23a'
}
const coalesce = (...values) => {
  for (const v of values) {
    if (v !== undefined && v !== null) return v
  }
  return undefined
}
const ratio = (numerator, denominator) => {
  const n = Number(numerator) || 0
  const d = Number(denominator)
  if (!d || d <= 0) return 0
  return n / d
}

// 获取接龙记录
const fetchJielongEntries = async (taskId) => {
  if (!taskId) return
  
  loadingEntries.value = true
  try {
    const params = {}
    // 优先使用管理员/超管选择的用户
    if ((authStore.isAdmin || authStore.isSuperAdmin) && selectedUserId.value) {
      params.user_id = selectedUserId.value
    } else if (jielongEntriesScope.value === 'mine' && authStore.user?.id) {
      // 非管理员或未选择用户时，“我的”筛选按当前登录用户
      params.user_id = authStore.user.id
    }
    const response = await api.get(`/tasks/${taskId}/jielong`, { params })
    jielongEntries.value = response.data.items || response.data || []
  } catch (error) {
    console.error('获取接龙记录失败:', error)
    jielongEntries.value = []
  } finally {
    loadingEntries.value = false
  }
}

const onEntriesScopeChange = () => {
  if (currentTask.value?.id) {
    fetchJielongEntries(currentTask.value.id)
    refreshTaskDetail()
  }
}

// 获取金额记录
const fetchAmountRecords = async (taskId) => {
  if (!taskId) return
  loadingAmountRecords.value = true
  try {
    const params = {}
    if ((authStore.isAdmin || authStore.isSuperAdmin) && selectedUserId.value) {
      params.user_id = selectedUserId.value
    } else if (amountRecordsScope.value === 'mine' && authStore.user?.id) {
      params.user_id = authStore.user.id
    }
    const response = await api.get(`/tasks/${taskId}/records`, { params })
    amountRecords.value = response.data.items || response.data || []
  } catch (e) {
    console.error('获取金额记录失败:', e)
    amountRecords.value = []
  } finally {
    loadingAmountRecords.value = false
  }
}

const onAmountScopeChange = () => {
  if (currentTask.value?.id) {
    fetchAmountRecords(currentTask.value.id)
    refreshTaskDetail()
  }
}

// 获取数量记录
const fetchQuantityRecords = async (taskId) => {
  if (!taskId) return
  loadingQuantityRecords.value = true
  try {
    const params = {}
    if ((authStore.isAdmin || authStore.isSuperAdmin) && selectedUserId.value) {
      params.user_id = selectedUserId.value
    } else if (quantityRecordsScope.value === 'mine' && authStore.user?.id) {
      params.user_id = authStore.user.id
    }
    const response = await api.get(`/tasks/${taskId}/records`, { params })
    quantityRecords.value = response.data.items || response.data || []
  } catch (e) {
    console.error('获取数量记录失败:', e)
    quantityRecords.value = []
  } finally {
    loadingQuantityRecords.value = false
  }
}

const onQuantityScopeChange = () => {
  if (currentTask.value?.id) {
    fetchQuantityRecords(currentTask.value.id)
    refreshTaskDetail()
  }
}

// 获取勾选完成记录
const fetchCheckboxCompletions = async (taskId) => {
  if (!taskId) return
  loadingCompletions.value = true
  try {
    const params = {}
    if ((authStore.isAdmin || authStore.isSuperAdmin) && selectedUserId.value) {
      params.user_id = selectedUserId.value
    } else if (checkboxCompletionsScope.value === 'mine' && authStore.user?.id) {
      params.user_id = authStore.user.id
    }
    const response = await api.get(`/tasks/${taskId}/completions`, { params })
    checkboxCompletions.value = response.data.items || response.data || []
  } catch (e) {
    console.error('获取完成记录失败:', e)
    checkboxCompletions.value = []
  } finally {
    loadingCompletions.value = false
  }
}

const onCompletionsScopeChange = () => {
  if (currentTask.value?.id) {
    fetchCheckboxCompletions(currentTask.value.id)
    refreshTaskDetail()
  }
}

// 查看任务详情时获取接龙记录
const viewTaskDetails = (task) => {
  currentTask.value = task
  activeTab.value = 'basic'
  taskDetailVisible.value = true
  
  // 打开详情时加载可选用户列表（仅管理员/超管可见）
  loadAvailableUsers()
  // 各类型默认 scope 为“我的”，并加载记录
  if (task.task_type === 'jielong') {
    jielongEntriesScope.value = 'mine'
    fetchJielongEntries(task.id)
  } else if (task.task_type === 'amount') {
    amountRecordsScope.value = 'mine'
    fetchAmountRecords(task.id)
  } else if (task.task_type === 'quantity') {
    quantityRecordsScope.value = 'mine'
    fetchQuantityRecords(task.id)
  } else if (task.task_type === 'checkbox') {
    checkboxCompletionsScope.value = 'mine'
    fetchCheckboxCompletions(task.id)
  }
  // 打开详情后刷新一次，从后端获取个人/全部统计字段
  refreshTaskDetail()
}

// 通过任务ID打开详情（供从日报跳转使用）
const openTaskDetailById = async (taskId) => {
  if (!taskId) return
  try {
    const response = await api.get(`/tasks/${taskId}`, { params: { scope: 'mine' } })
    const task = response.data || response.data?.item || response.data
    if (task && task.id) {
      viewTaskDetails(task)
    } else {
      ElMessage.error('未找到任务详情')
    }
  } catch (e) {
    ElMessage.error('打开任务详情失败')
  }
}

onMounted(() => {
  // 首次加载任务列表
  fetchTasks()
  // 如果存在 openTaskId 查询参数，自动打开详情（“我的”视角）
  const openId = Number(route.query.openTaskId)
  if (openId) {
    openTaskDetailById(openId)
  }
})

// 获取分配类型文本
const getAssignmentTypeText = (assignmentType) => {
  const typeMap = {
    'user': '指定用户',
    'group': '指定组',
    'identity': '指定身份',
    'all': '所有人'
  }
  return typeMap[assignmentType] || assignmentType
}

// 获取分配目标
const getAssignmentTarget = (task) => {
  switch (task.assignment_type) {
    case 'user':
      return task.assigned_to_username || `用户ID: ${task.assigned_to}`
    case 'group':
      return task.target_group_name || `组ID: ${task.target_group_id}`
    case 'identity':
      return task.target_identity || '-'
    case 'all':
      return '所有人'
    default:
      return '-'
  }
}



// 监听过滤器变化
watch(filters, () => {
  pagination.page = 1
  fetchTasks()
}, { deep: true })

// 初始化
onMounted(() => {
  fetchTasks()
  // 仅管理员或超级管理员需要用户列表（用于分配/创建任务）
  if (authStore.isAdmin || authStore.isSuperAdmin) {
    fetchUsers()
  }
  fetchGroups()
})
</script>

<style scoped>
.table-toolbar {
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-filters {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.admin-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

.jielong-config-card {
  margin-top: 10px;
}

.jielong-config-card .el-checkbox {
  margin-right: 16px;
  margin-bottom: 8px;
}

.task-detail {
  padding: 16px 0;
}

.task-detail .el-descriptions {
  margin-top: 16px;
}

@media (max-width: 768px) {
  .table-filters {
    flex-direction: column;
  }
  
  .table-toolbar {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
}
</style>