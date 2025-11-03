<template>
  <div class="permission-test">
    <v-container>
      <v-row>
        <v-col cols="12">
          <v-card>
            <v-card-title>
              <v-icon left>mdi-shield-check</v-icon>
              权限系统测试页面
            </v-card-title>
            
            <v-card-text>
              <!-- 当前用户信息 -->
              <v-alert type="info" class="mb-4">
                <h4>当前用户信息</h4>
                <p><strong>用户名:</strong> {{ currentUser?.username || '未登录' }}</p>
                <p><strong>角色:</strong> {{ formatUserRole(currentUser) }}</p>
                <p><strong>是否管理员:</strong> {{ currentUser?.is_admin ? '是' : '否' }}</p>
                <p><strong>是否超级管理员:</strong> {{ currentUser?.is_super_admin ? '是' : '否' }}</p>
                <p><strong>身份类型:</strong> {{ currentUser?.identity_type || '未知' }}</p>
                <p><strong>所属组:</strong> {{ currentUser?.group_name || '未知' }}</p>
              </v-alert>

              <!-- 权限测试区域 -->
              <v-row>
                <!-- 超级管理员权限测试 -->
                <v-col cols="12" md="4">
                  <v-card outlined>
                    <v-card-title class="text-h6">
                      <v-icon left color="red">mdi-crown</v-icon>
                      超级管理员功能
                    </v-card-title>
                    <v-card-text>
                      <div v-if="currentUser?.is_super_admin">
                        <v-chip color="success" small class="mb-2">✓ 用户管理</v-chip><br>
                        <v-chip color="success" small class="mb-2">✓ 组管理</v-chip><br>
                        <v-chip color="success" small class="mb-2">✓ AI配置</v-chip><br>
                        <v-chip color="success" small class="mb-2">✓ 系统设置</v-chip><br>
                        <v-chip color="success" small class="mb-2">✓ 所有数据访问</v-chip>
                      </div>
                      <div v-else>
                        <v-chip color="error" small class="mb-2">✗ 权限不足</v-chip>
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>

                <!-- 管理员权限测试 -->
                <v-col cols="12" md="4">
                  <v-card outlined>
                    <v-card-title class="text-h6">
                      <v-icon left color="orange">mdi-account-supervisor</v-icon>
                      管理员功能
                    </v-card-title>
                    <v-card-text>
                      <div v-if="currentUser?.is_admin">
                        <v-chip color="success" small class="mb-2">✓ 组内任务管理</v-chip><br>
                        <v-chip color="success" small class="mb-2">✓ 组内用户查看</v-chip><br>
                        <v-chip color="success" small class="mb-2">✓ 组分析数据</v-chip><br>
                        <v-chip color="success" small class="mb-2">✓ 组报告查看</v-chip>
                      </div>
                      <div v-else>
                        <v-chip color="error" small class="mb-2">✗ 权限不足</v-chip>
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>

                <!-- 普通用户权限测试 -->
                <v-col cols="12" md="4">
                  <v-card outlined>
                    <v-card-title class="text-h6">
                      <v-icon left color="blue">mdi-account</v-icon>
                      普通用户功能
                    </v-card-title>
                    <v-card-text>
                      <div v-if="currentUser">
                        <v-chip color="success" small class="mb-2">✓ 个人任务</v-chip><br>
                        <v-chip color="success" small class="mb-2">✓ 个人日报</v-chip><br>
                        <v-chip color="success" small class="mb-2">✓ 个人分析</v-chip><br>
                        <v-chip color="success" small class="mb-2">✓ 基础功能</v-chip>
                      </div>
                      <div v-else>
                        <v-chip color="error" small class="mb-2">✗ 未登录</v-chip>
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>

              <!-- 权限函数测试 -->
              <v-card outlined class="mt-4">
                <v-card-title class="text-h6">
                  <v-icon left>mdi-function</v-icon>
                  权限函数测试
                </v-card-title>
                <v-card-text>
                  <v-row>
                    <v-col cols="12" md="6">
                      <h4>hasPermission 函数测试</h4>
                      <p>用户管理权限: <v-chip :color="hasPermission(currentUser, 'user_management') ? 'success' : 'error'" small>
                        {{ hasPermission(currentUser, 'user_management') ? '有权限' : '无权限' }}
                      </v-chip></p>
                      <p>AI配置权限: <v-chip :color="hasPermission(currentUser, 'ai_config') ? 'success' : 'error'" small>
                        {{ hasPermission(currentUser, 'ai_config') ? '有权限' : '无权限' }}
                      </v-chip></p>
                    </v-col>
                    <v-col cols="12" md="6">
                      <h4>canAccessUser 函数测试</h4>
                      <p>访问自己: <v-chip :color="canAccessUser(currentUser, currentUser) ? 'success' : 'error'" small>
                        {{ canAccessUser(currentUser, currentUser) ? '可访问' : '不可访问' }}
                      </v-chip></p>
                      <p>canManageGroup: <v-chip :color="canManageGroup(currentUser, currentUser?.group_id) ? 'success' : 'error'" small>
                        {{ canManageGroup(currentUser, currentUser?.group_id) ? '可管理' : '不可管理' }}
                      </v-chip></p>
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>

              <!-- 页面访问测试 -->
              <v-card outlined class="mt-4">
                <v-card-title class="text-h6">
                  <v-icon left>mdi-web</v-icon>
                  页面访问权限测试
                </v-card-title>
                <v-card-text>
                  <v-row>
                    <v-col cols="12" md="3">
                      <v-btn 
                        :disabled="!currentUser?.is_admin" 
                        color="primary" 
                        block
                        @click="$router.push('/admin/users')"
                      >
                        用户管理
                        <v-icon right>{{ currentUser?.is_admin ? 'mdi-check' : 'mdi-lock' }}</v-icon>
                      </v-btn>
                    </v-col>
                    <v-col cols="12" md="3">
                      <v-btn 
                        :disabled="!currentUser?.is_super_admin" 
                        color="primary" 
                        block
                        @click="$router.push('/admin/ai')"
                      >
                        AI配置
                        <v-icon right>{{ currentUser?.is_super_admin ? 'mdi-check' : 'mdi-lock' }}</v-icon>
                      </v-btn>
                    </v-col>
                    <v-col cols="12" md="3">
                      <v-btn 
                        :disabled="!(currentUser?.is_admin || currentUser?.is_super_admin)" 
                        color="primary" 
                        block
                        @click="$router.push('/analytics')"
                      >
                        分析中心
                        <v-icon right>{{ (currentUser?.is_admin || currentUser?.is_super_admin) ? 'mdi-check' : 'mdi-lock' }}</v-icon>
                      </v-btn>
                    </v-col>
                    <v-col cols="12" md="3">
                      <v-btn 
                        color="primary" 
                        block
                        @click="$router.push('/dashboard')"
                      >
                        个人面板
                        <v-icon right>mdi-check</v-icon>
                      </v-btn>
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script>
import { useAuthStore } from '@/stores/auth'
import { hasPermission, canAccessUser, canManageGroup, formatUserRole } from '@/utils/auth'

export default {
  name: 'PermissionTest',
  setup() {
    const authStore = useAuthStore()
    
    return {
      currentUser: authStore.user,
      hasPermission,
      canAccessUser,
      canManageGroup,
      formatUserRole
    }
  }
}
</script>

<style scoped>
.permission-test {
  padding: 20px;
}
</style>