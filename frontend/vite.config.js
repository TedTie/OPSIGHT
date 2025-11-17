import { defineConfig, loadEnv } from 'vite'
import path from 'path'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import Icons from 'unplugin-icons/vite'
import IconsResolver from 'unplugin-icons/resolver'

function devMockPlugin() {
  return {
    name: 'dev-mock-plugin',
    apply: 'serve',
    configureServer(server) {
      // 简易内存存储：个人月度目标
      const personalGoalsStore = {}
      // 设置页本地存储（AI 与系统设置）
      const defaultAISettings = {
        provider: 'openrouter',
        api_key: '',
        base_url: 'https://openrouter.ai/api/v1',
        model_name: 'openai/gpt-5',
        max_tokens: 2000,
        temperature: 0.7
      }
      const defaultSystemSettings = {
        system_name: 'KillerApp',
        timezone: 'Asia/Shanghai',
        language: 'zh-CN',
        auto_analysis: true,
        data_retention_days: 90
      }
      const aiSettingsStore = { ...defaultAISettings }
      const systemSettingsStore = { ...defaultSystemSettings }
      // 简易用户与组数据（用于本地联调）
      const mockUsers = [
        { id: 101, username: 'alice', identity_type: 'CC', group_id: 1, group_name: '销售一组' },
        { id: 102, username: 'bob', identity_type: 'CC', group_id: 1, group_name: '销售一组' },
        { id: 201, username: 'charlie', identity_type: 'SS', group_id: 2, group_name: '教务一组' },
        { id: 202, username: 'diana', identity_type: 'SS', group_id: 2, group_name: '教务一组' },
        { id: 301, username: 'eve', identity_type: 'LP', group_id: 3, group_name: '产品一组' }
      ]
      server.middlewares.use((req, res, next) => {
        const url = req.url || ''

        // Analytics summary (identity-based monthly aggregation)
        if (req.method === 'GET' && url.startsWith('/api/v1/analytics/summary')) {
          res.setHeader('Content-Type', 'application/json')
          const u = new URL(url, 'http://localhost')
          const idt = (u.searchParams.get('identity_type') || '').toUpperCase()
          if (idt === 'CC') {
            res.end(JSON.stringify({
              month: {
                actual_amount: 250000,
                new_sign_amount: 215000,
                referral_amount: 35000,
                referral_count: 12
              },
              progress_display: {
                amount_rate: 0.8,
                new_sign_achievement_rate: 0.72,
                referral_achievement_rate: 0.35
              }
            }))
            return
          }
          if (idt === 'SS') {
            res.end(JSON.stringify({
              month: {
                actual_amount: 200000,
                renewal_amount: 120000,
                upgrade_amount: 80000,
                renewal_count: 24,
                upgrade_count: 9
              },
              progress_display: {
                total_renewal_achievement_rate: 0.6
              }
            }))
            return
          }
          // default fallback
          res.end(JSON.stringify({ month: { actual_amount: 0 } }))
          return
        }

        // Analytics trend (provide detailed metric fields for compatibility)
        if (req.method === 'GET' && url.startsWith('/api/v1/analytics/trend')) {
          res.setHeader('Content-Type', 'application/json')
          const now = new Date()
          const series = []
          for (let i = 9; i >= 0; i--) {
            const d = new Date(now)
            d.setDate(now.getDate() - i)
            const day = d.toISOString().slice(0, 10)
            const ns = Math.round(60000 + Math.random() * 40000)
            const rf = Math.round(15000 + Math.random() * 20000)
            const rn = Math.round(50000 + Math.random() * 40000)
            const ug = Math.round(20000 + Math.random() * 30000)
            series.push({
              date: day,
              new_sign_amount: ns,
              referral_amount: rf,
              renewal_amount: rn,
              upgrade_amount: ug,
              referral_count: Math.floor(1 + Math.random() * 5),
              renewal_count: Math.floor(3 + Math.random() * 8),
              upgrade_count: Math.floor(1 + Math.random() * 4)
            })
          }
          res.end(JSON.stringify({ series }))
          return
        }

        // Analytics data (unified metrics across scopes)
        if (req.method === 'GET' && url.startsWith('/api/v1/analytics/data')) {
          res.setHeader('Content-Type', 'application/json')
          const metrics = {
            task_completion_rate: 0.82,
            report_submission_rate: 0.93,
            call_count: 180,
            new_leads_count: 45,
            conversion_rate: 0.23,
            active_students: 620,
            refund_rate: 0.015,
            course_completion_rate: 0.71
          }
          res.end(JSON.stringify({ metrics }))
          return
        }

        // Analytics AI insight (legacy)
        if (req.method === 'POST' && url.startsWith('/api/v1/analytics/ai-insight')) {
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ insight: '这是基于模拟原始数据的AI洞察示例：销售额波动主要受周末促销影响，建议在周中增加转介绍活动以平滑趋势。' }))
          return
        }
        // Analytics AI insight summary (current)
        if (req.method === 'POST' && url.startsWith('/api/v1/analytics/ai-insight-summary')) {
          res.setHeader('Content-Type', 'application/json')
          let body = ''
          req.on('data', chunk => { body += chunk })
          req.on('end', () => {
            res.end(JSON.stringify({ insight: 'AI洞察：当前期间销售节奏稳定，升级贡献占比较高。建议优化转介绍活动以提升转化率。' }))
          })
          return
        }

        // Monthly goals
        if (req.method === 'GET' && url.startsWith('/api/v1/goals/monthly')) {
          const u = new URL(url, 'http://localhost')
          const year = Number(u.searchParams.get('year') || new Date().getFullYear())
          const month = Number(u.searchParams.get('month') || (new Date().getMonth() + 1))
          res.setHeader('Content-Type', 'application/json')
          const cc_new = 300000
          const cc_ref = 100000
          const ss_total = 120000
          const goals = [
            {
              id: 1,
              identity_type: 'CC',
              scope: 'global',
              year,
              month,
              amount_target: cc_new + cc_ref,
              new_sign_target_amount: cc_new,
              referral_target_amount: cc_ref,
              renewal_total_target_amount: 0,
              upgrade_target_count: 8,
              renewal_target_count: 0,
              notes: null,
              created_at: null,
              updated_at: null
            },
            {
              id: 2,
              identity_type: 'SS',
              scope: 'global',
              year,
              month,
              amount_target: ss_total,
              new_sign_target_amount: 0,
              referral_target_amount: 0,
              renewal_total_target_amount: ss_total,
              upgrade_target_count: 12,
              renewal_target_count: 0,
              notes: null,
              created_at: null,
              updated_at: null
            }
          ]
          res.end(JSON.stringify(goals))
          return
        }

        if (req.method === 'POST' && url.startsWith('/api/v1/goals/monthly')) {
          let body = ''
          req.on('data', chunk => { body += chunk })
          req.on('end', () => {
            try {
              const payload = JSON.parse(body || '{}')
              res.setHeader('Content-Type', 'application/json')
              res.end(JSON.stringify({ id: Math.floor(Math.random() * 10000), ...payload }))
            } catch (e) {
              res.statusCode = 400
              res.end(JSON.stringify({ error: 'Invalid JSON' }))
            }
          })
          return
        }

        // Personal monthly goals (batch)
        if (req.method === 'GET' && url.startsWith('/api/v1/goals/monthly/personal')) {
          const u = new URL(url, 'http://localhost')
          const identity_type = (u.searchParams.get('identity_type') || '').toUpperCase()
          const group_id = u.searchParams.get('group_id') || ''
          const year = u.searchParams.get('year') || ''
          const month = u.searchParams.get('month') || ''
          const user_id = u.searchParams.get('user_id') || null
          const key = `${identity_type}|${group_id}|${year}|${month}`
          const bucket = personalGoalsStore[key] || {}
          let items = Object.values(bucket)
          if (user_id) items = items.filter(it => String(it.user_id) === String(user_id))
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ items }))
          return
        }
        if (req.method === 'POST' && url.startsWith('/api/v1/goals/monthly/personal')) {
          let body = ''
          req.on('data', chunk => { body += chunk })
          req.on('end', () => {
            try {
              const payload = JSON.parse(body || '[]')
              const arr = Array.isArray(payload) ? payload : (payload.items || [])
              // 每条记录：identity_type, group_id, user_id, year, month, ...fields
              for (const it of arr) {
                const identity_type = String(it.identity_type || '').toUpperCase()
                const group_id = it.group_id ?? ''
                const year = it.year ?? ''
                const month = it.month ?? ''
                const key = `${identity_type}|${group_id}|${year}|${month}`
                if (!personalGoalsStore[key]) personalGoalsStore[key] = {}
                const userKey = String(it.user_id)
                personalGoalsStore[key][userKey] = {
                  identity_type,
                  group_id,
                  user_id: it.user_id,
                  year,
                  month,
                  new_sign_target_amount: Number(it.new_sign_target_amount || 0),
                  referral_target_amount: Number(it.referral_target_amount || 0),
                  renewal_total_target_amount: Number(it.renewal_total_target_amount || 0),
                  upgrade_target_count: Number(it.upgrade_target_count || 0)
                }
              }
              res.setHeader('Content-Type', 'application/json')
              res.end(JSON.stringify({ success: true, saved: arr.length }))
            } catch (e) {
              res.statusCode = 400
              res.end(JSON.stringify({ error: 'Invalid JSON' }))
            }
          })
          return
        }

        // Users (mock)
        if (req.method === 'GET' && url.startsWith('/api/v1/users')) {
          const u = new URL(url, 'http://localhost')
          const page = Number(u.searchParams.get('page') || '1')
          const size = Number(u.searchParams.get('size') || '10')
          const start = (page - 1) * size
          const items = mockUsers.slice(start, start + size)
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ items, total: mockUsers.length, page, size }))
          return
        }

        // Groups (mock, derived from users)
        if (req.method === 'GET' && url.startsWith('/api/v1/groups')) {
          const uniq = new Map()
          for (const u of mockUsers) {
            if (u.group_id != null) {
              const gid = String(u.group_id)
              if (!uniq.has(gid)) uniq.set(gid, { id: u.group_id, name: u.group_name, description: '', member_count: 0 })
            }
          }
          const items = Array.from(uniq.values())
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ items, total: items.length, page: 1, size: items.length }))
          return
        }

        // Group members (mock): /api/v1/groups/:id/members
        if (req.method === 'GET' && url.startsWith('/api/v1/groups/') && url.includes('/members')) {
          const u = new URL(url, 'http://localhost')
          const pathname = u.pathname || ''
          const parts = pathname.split('/')
          // ['', 'api', 'v1', 'groups', ':id', 'members']
          const gid = parts[4]
          const items = mockUsers.filter(m => String(m.group_id) === String(gid)).map(m => ({
            id: m.id,
            username: m.username,
            identity_type: m.identity_type,
            group_id: m.group_id,
            group_name: m.group_name
          }))
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ items, total: items.length, page: 1, size: items.length }))
          return
        }

        // Admin metrics
        if (req.method === 'GET' && url.startsWith('/api/v1/admin/metrics')) {
          res.setHeader('Content-Type', 'application/json')
          const items = [
            { id: 1, key: 'period_sales_amount', name: '期间销售总额', is_active: true, default_roles: ['CC', 'SS'] },
            { id: 2, key: 'task_completion_rate', name: '任务完成率', is_active: true, default_roles: ['CC', 'SS', 'LP'] },
            { id: 3, key: 'report_submission_rate', name: '日报提交率', is_active: true, default_roles: ['CC', 'SS', 'LP'] }
          ]
          res.end(JSON.stringify(items))
          return
        }

        if (req.method === 'PUT' && url.startsWith('/api/v1/admin/metrics/')) {
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ success: true }))
          return
        }

        // Auth mocks (to avoid 401 during preview)
        if (req.method === 'POST' && url.startsWith('/api/v1/auth/login')) {
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ user: { id: 1, username: 'demo', role: 'super_admin' } }))
          return
        }

        if (req.method === 'POST' && url.startsWith('/api/v1/auth/logout')) {
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ success: true }))
          return
        }

        if (req.method === 'GET' && url.startsWith('/api/v1/auth/me')) {
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ id: 1, username: 'demo', role: 'super_admin' }))
          return
        }

        // AI system knowledge
        if (req.method === 'GET' && url.startsWith('/api/v1/ai/system-knowledge')) {
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({
            welcome: '你好！我是系统向导，帮你快速找到功能入口。',
            recommended: [
              '如何查看我的任务进度？',
              '如何提交当天的日报？',
              '哪里可以设置月度目标？'
            ]
          }))
          return
        }

        // AI chat
        if (req.method === 'POST' && url.startsWith('/api/v1/ai/chat')) {
          res.setHeader('Content-Type', 'application/json')
          let body = ''
          req.on('data', chunk => { body += chunk })
          req.on('end', () => {
            try {
              const payload = JSON.parse(body || '{}')
              const q = String(payload.question || '')
              // 简单规则：根据关键词给出指引
              let answer = '这是 AI 向导的示例回答：请在系统中查找对应功能入口。'
              if (/任务|进度/.test(q)) {
                answer = '任务进度可在“任务管理”与“仪表盘”查看。'
              } else if (/日报|提交/.test(q)) {
                answer = '提交日报请进入“日报”页面，点击新建后填写并提交。'
              } else if (/目标|月度/.test(q)) {
                answer = '月度目标可在“分析/目标管理”页进行设置与查看。'
              }
              res.end(JSON.stringify({ answer }))
            } catch (e) {
              res.statusCode = 400
              res.end(JSON.stringify({ error: 'Invalid JSON' }))
            }
          })
          return
        }

        // Settings: 获取AI设置
        if (req.method === 'GET' && url.startsWith('/api/v1/settings/ai')) {
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify(aiSettingsStore))
          return
        }

        // Settings: 保存AI设置
        if (req.method === 'PUT' && url.startsWith('/api/v1/settings/ai')) {
          res.setHeader('Content-Type', 'application/json')
          let body = ''
          req.on('data', chunk => { body += chunk })
          req.on('end', () => {
            try {
              const payload = JSON.parse(body || '{}')
              // 映射字段并保存
              aiSettingsStore.provider = payload.provider ?? aiSettingsStore.provider
              aiSettingsStore.api_key = payload.api_key ?? aiSettingsStore.api_key
              aiSettingsStore.base_url = payload.base_url ?? aiSettingsStore.base_url
              aiSettingsStore.model_name = payload.model_name ?? aiSettingsStore.model_name
              aiSettingsStore.max_tokens = Number(payload.max_tokens ?? aiSettingsStore.max_tokens)
              aiSettingsStore.temperature = Number(payload.temperature ?? aiSettingsStore.temperature)
              res.end(JSON.stringify({ success: true }))
            } catch (e) {
              res.statusCode = 400
              res.end(JSON.stringify({ error: 'Invalid JSON' }))
            }
          })
          return
        }

        // Settings: 获取系统设置
        if (req.method === 'GET' && url.startsWith('/api/v1/settings/system')) {
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify(systemSettingsStore))
          return
        }

        // Settings: 保存系统设置
        if (req.method === 'PUT' && url.startsWith('/api/v1/settings/system')) {
          res.setHeader('Content-Type', 'application/json')
          let body = ''
          req.on('data', chunk => { body += chunk })
          req.on('end', () => {
            try {
              const payload = JSON.parse(body || '{}')
              systemSettingsStore.system_name = payload.system_name ?? systemSettingsStore.system_name
              systemSettingsStore.timezone = payload.timezone ?? systemSettingsStore.timezone
              systemSettingsStore.language = payload.language ?? systemSettingsStore.language
              systemSettingsStore.auto_analysis = payload.auto_analysis ?? systemSettingsStore.auto_analysis
              systemSettingsStore.data_retention_days = Number(payload.data_retention_days ?? systemSettingsStore.data_retention_days)
              res.end(JSON.stringify({ success: true }))
            } catch (e) {
              res.statusCode = 400
              res.end(JSON.stringify({ error: 'Invalid JSON' }))
            }
          })
          return
        }

        // Settings: 测试AI连接
        if (req.method === 'POST' && url.startsWith('/api/v1/settings/ai/test')) {
          res.setHeader('Content-Type', 'application/json')
          let body = ''
          req.on('data', chunk => { body += chunk })
          req.on('end', () => {
            try {
              const payload = JSON.parse(body || '{}')
              const hasKey = !!(payload.api_key || aiSettingsStore.api_key)
              const provider = (payload.provider || aiSettingsStore.provider || '').toLowerCase()
              const okProviders = ['openrouter', 'openai', 'claude']
              const success = hasKey && okProviders.includes(provider)
              const responseText = success ? '服务可用，认证通过' : '缺少有效密钥或不支持的提供商'
              res.end(JSON.stringify({ success, response: responseText, message: success ? 'OK' : 'Failed' }))
            } catch (e) {
              res.statusCode = 400
              res.end(JSON.stringify({ success: false, message: 'Invalid JSON' }))
            }
          })
          return
        }

        // Settings: 导出数据
        if (req.method === 'GET' && url.startsWith('/api/v1/settings/export')) {
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ message: '数据导出完成（模拟）' }))
          return
        }

        // Settings: 清理缓存
        if (req.method === 'POST' && url.startsWith('/api/v1/settings/clear-cache')) {
          res.setHeader('Content-Type', 'application/json')
          // 简单模拟：不做实际清理
          res.end(JSON.stringify({ success: true }))
          return
        }

        // Settings: 重置设置
        if (req.method === 'POST' && url.startsWith('/api/v1/settings/reset')) {
          res.setHeader('Content-Type', 'application/json')
          Object.assign(aiSettingsStore, defaultAISettings)
          Object.assign(systemSettingsStore, defaultSystemSettings)
          res.end(JSON.stringify({ success: true }))
          return
        }

        return next()
      })
    }
  }
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const useMock = env.VITE_USE_MOCK === 'true' || env.USE_MOCK === 'true'
  return {
    plugins: useMock
      ? [
          vue(),
          devMockPlugin(),
          Components({
            resolvers: [IconsResolver({ componentPrefix: 'i' })]
          }),
          Icons({ compiler: 'vue3' })
        ]
      : [
          vue(),
          Components({
            resolvers: [IconsResolver({ componentPrefix: 'i' })]
          }),
          Icons({ compiler: 'vue3' })
        ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src')
      }
    },
    server: {
      port: 3001,
      proxy: useMock ? {} : {
        '/api/v1': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true
        }
      }
    }
  }
})