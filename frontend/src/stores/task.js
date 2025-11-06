import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

export const useTaskStore = defineStore('task', {
  state: () => ({
    tasks: [],
    loading: false,
    pagination: {
      page: 1,
      size: 10,
      total: 0
    }
  }),

  getters: {
    // 获取任务总数
    totalTasks: (state) => state.tasks.length,
    
    // 按状态筛选任务
    tasksByStatus: (state) => (status) => {
      return state.tasks.filter(task => task.status === status)
    },
    
    // 按类型筛选任务
    tasksByType: (state) => (type) => {
      return state.tasks.filter(task => task.type === type)
    }
  },

  actions: {
    // 获取任务列表
    async fetchTasks(params = {}) {
      this.loading = true
      try {
        // 过滤掉空值
        const filteredParams = Object.fromEntries(
          Object.entries(params).filter(([key, value]) => value !== '' && value != null)
        )
        
        const requestParams = {
          page: this.pagination.page,
          size: this.pagination.size,
          ...filteredParams
        }
        
        const response = await api.get('/tasks', { params: requestParams })
        const data = response.data

        // 兼容后端返回数组或带分页对象两种格式
        if (Array.isArray(data)) {
          this.tasks = data
          this.pagination.total = data.length
        } else {
          this.tasks = data.items || data.data || []
          this.pagination.total = data.total || (this.tasks.length || 0)
        }

        return response.data
      } catch (error) {
        console.error('获取任务列表失败:', error)
        ElMessage.error('获取任务列表失败')
        throw error
      } finally {
        this.loading = false
      }
    },

    // 更新任务进度
    async updateTaskProgress(taskId, progressData) {
      try {
        // 1. 调用 API，现在它会返回更新后的完整任务
        const response = await api.put(`/tasks/${taskId}/progress`, progressData)
        const updatedTask = response.data
        
        // 2. 在本地 state.tasks 数组中找到这个任务的索引
        const index = this.tasks.findIndex(t => t.id === taskId)
        
        // 3. 如果找到了，就用新数据替换它，而不是重新 fetch 所有数据
        if (index !== -1) {
          this.tasks[index] = updatedTask
        } else {
          // 如果没找到（不太可能发生），作为备用方案可以重新 fetch
          await this.fetchTasks()
        }
        
        ElMessage.success('任务进度更新成功')
        return updatedTask
      } catch (error) {
        console.error('更新任务进度失败:', error)
        ElMessage.error('更新任务进度失败')
        throw error
      }
    },

    // 参与接龙任务
    async participateInJielong(taskId, participationData) {
      try {
        const response = await api.post(`/tasks/${taskId}/participate`, participationData)
        
        // 更新本地任务状态
        const taskIndex = this.tasks.findIndex(task => task.id === taskId)
        if (taskIndex !== -1) {
          this.tasks[taskIndex] = { ...this.tasks[taskIndex], ...response.data }
        }
        
        ElMessage.success('参与接龙成功')
        return response.data
      } catch (error) {
        console.error('参与接龙失败:', error)
        ElMessage.error('参与接龙失败')
        throw error
      }
    },

    // 设置分页参数
    setPagination(page, size) {
      this.pagination.page = page
      this.pagination.size = size
    },

    // 重置状态
    resetState() {
      this.tasks = []
      this.loading = false
      this.pagination = {
        page: 1,
        size: 10,
        total: 0
      }
    }
  }
})