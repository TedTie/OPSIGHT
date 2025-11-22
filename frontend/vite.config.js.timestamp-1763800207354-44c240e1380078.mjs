// vite.config.js
import { defineConfig, loadEnv } from "file:///E:/51/AI/KillerApp/frontend/node_modules/vite/dist/node/index.js";
import path from "path";
import vue from "file:///E:/51/AI/KillerApp/frontend/node_modules/@vitejs/plugin-vue/dist/index.mjs";
import Components from "file:///E:/51/AI/KillerApp/frontend/node_modules/unplugin-vue-components/dist/vite.js";
import Icons from "file:///E:/51/AI/KillerApp/frontend/node_modules/unplugin-icons/dist/vite.js";
import IconsResolver from "file:///E:/51/AI/KillerApp/frontend/node_modules/unplugin-icons/dist/resolver.js";
var __vite_injected_original_dirname = "E:\\51\\AI\\KillerApp\\frontend";
function devMockPlugin() {
  return {
    name: "dev-mock-plugin",
    apply: "serve",
    configureServer(server) {
      const personalGoalsStore = {};
      const defaultAISettings = {
        provider: "openrouter",
        api_key: "",
        base_url: "https://openrouter.ai/api/v1",
        model_name: "openai/gpt-5",
        max_tokens: 2e3,
        temperature: 0.7
      };
      const defaultSystemSettings = {
        system_name: "KillerApp",
        timezone: "Asia/Shanghai",
        language: "zh-CN",
        auto_analysis: true,
        data_retention_days: 90
      };
      const aiSettingsStore = { ...defaultAISettings };
      const systemSettingsStore = { ...defaultSystemSettings };
      const mockUsers = [
        { id: 101, username: "alice", identity_type: "CC", group_id: 1, group_name: "\u9500\u552E\u4E00\u7EC4" },
        { id: 102, username: "bob", identity_type: "CC", group_id: 1, group_name: "\u9500\u552E\u4E00\u7EC4" },
        { id: 201, username: "charlie", identity_type: "SS", group_id: 2, group_name: "\u6559\u52A1\u4E00\u7EC4" },
        { id: 202, username: "diana", identity_type: "SS", group_id: 2, group_name: "\u6559\u52A1\u4E00\u7EC4" },
        { id: 301, username: "eve", identity_type: "LP", group_id: 3, group_name: "\u4EA7\u54C1\u4E00\u7EC4" }
      ];
      server.middlewares.use((req, res, next) => {
        const url = req.url || "";
        if (req.method === "GET" && url.startsWith("/api/v1/analytics/summary")) {
          res.setHeader("Content-Type", "application/json");
          const u = new URL(url, "http://localhost");
          const idt = (u.searchParams.get("identity_type") || "").toUpperCase();
          if (idt === "CC") {
            res.end(JSON.stringify({
              month: {
                actual_amount: 25e4,
                new_sign_amount: 215e3,
                referral_amount: 35e3,
                referral_count: 12
              },
              progress_display: {
                amount_rate: 0.8,
                new_sign_achievement_rate: 0.72,
                referral_achievement_rate: 0.35
              }
            }));
            return;
          }
          if (idt === "SS") {
            res.end(JSON.stringify({
              month: {
                actual_amount: 2e5,
                renewal_amount: 12e4,
                upgrade_amount: 8e4,
                renewal_count: 24,
                upgrade_count: 9
              },
              progress_display: {
                total_renewal_achievement_rate: 0.6
              }
            }));
            return;
          }
          res.end(JSON.stringify({ month: { actual_amount: 0 } }));
          return;
        }
        if (req.method === "GET" && url.startsWith("/api/v1/analytics/trend")) {
          res.setHeader("Content-Type", "application/json");
          const now = /* @__PURE__ */ new Date();
          const series = [];
          for (let i = 9; i >= 0; i--) {
            const d = new Date(now);
            d.setDate(now.getDate() - i);
            const day = d.toISOString().slice(0, 10);
            const ns = Math.round(6e4 + Math.random() * 4e4);
            const rf = Math.round(15e3 + Math.random() * 2e4);
            const rn = Math.round(5e4 + Math.random() * 4e4);
            const ug = Math.round(2e4 + Math.random() * 3e4);
            series.push({
              date: day,
              new_sign_amount: ns,
              referral_amount: rf,
              renewal_amount: rn,
              upgrade_amount: ug,
              referral_count: Math.floor(1 + Math.random() * 5),
              renewal_count: Math.floor(3 + Math.random() * 8),
              upgrade_count: Math.floor(1 + Math.random() * 4)
            });
          }
          res.end(JSON.stringify({ series }));
          return;
        }
        if (req.method === "GET" && url.startsWith("/api/v1/analytics/data")) {
          res.setHeader("Content-Type", "application/json");
          const metrics = {
            task_completion_rate: 0.82,
            report_submission_rate: 0.93,
            call_count: 180,
            new_leads_count: 45,
            conversion_rate: 0.23,
            active_students: 620,
            refund_rate: 0.015,
            course_completion_rate: 0.71
          };
          res.end(JSON.stringify({ metrics }));
          return;
        }
        if (req.method === "POST" && url.startsWith("/api/v1/analytics/ai-insight")) {
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ insight: "\u8FD9\u662F\u57FA\u4E8E\u6A21\u62DF\u539F\u59CB\u6570\u636E\u7684AI\u6D1E\u5BDF\u793A\u4F8B\uFF1A\u9500\u552E\u989D\u6CE2\u52A8\u4E3B\u8981\u53D7\u5468\u672B\u4FC3\u9500\u5F71\u54CD\uFF0C\u5EFA\u8BAE\u5728\u5468\u4E2D\u589E\u52A0\u8F6C\u4ECB\u7ECD\u6D3B\u52A8\u4EE5\u5E73\u6ED1\u8D8B\u52BF\u3002" }));
          return;
        }
        if (req.method === "POST" && url.startsWith("/api/v1/analytics/ai-insight-summary")) {
          res.setHeader("Content-Type", "application/json");
          let body = "";
          req.on("data", (chunk) => {
            body += chunk;
          });
          req.on("end", () => {
            res.end(JSON.stringify({ insight: "AI\u6D1E\u5BDF\uFF1A\u5F53\u524D\u671F\u95F4\u9500\u552E\u8282\u594F\u7A33\u5B9A\uFF0C\u5347\u7EA7\u8D21\u732E\u5360\u6BD4\u8F83\u9AD8\u3002\u5EFA\u8BAE\u4F18\u5316\u8F6C\u4ECB\u7ECD\u6D3B\u52A8\u4EE5\u63D0\u5347\u8F6C\u5316\u7387\u3002" }));
          });
          return;
        }
        if (req.method === "GET" && url.startsWith("/api/v1/goals/monthly")) {
          const u = new URL(url, "http://localhost");
          const year = Number(u.searchParams.get("year") || (/* @__PURE__ */ new Date()).getFullYear());
          const month = Number(u.searchParams.get("month") || (/* @__PURE__ */ new Date()).getMonth() + 1);
          res.setHeader("Content-Type", "application/json");
          const cc_new = 3e5;
          const cc_ref = 1e5;
          const ss_total = 12e4;
          const goals = [
            {
              id: 1,
              identity_type: "CC",
              scope: "global",
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
              identity_type: "SS",
              scope: "global",
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
          ];
          res.end(JSON.stringify(goals));
          return;
        }
        if (req.method === "POST" && url.startsWith("/api/v1/goals/monthly")) {
          let body = "";
          req.on("data", (chunk) => {
            body += chunk;
          });
          req.on("end", () => {
            try {
              const payload = JSON.parse(body || "{}");
              res.setHeader("Content-Type", "application/json");
              res.end(JSON.stringify({ id: Math.floor(Math.random() * 1e4), ...payload }));
            } catch (e) {
              res.statusCode = 400;
              res.end(JSON.stringify({ error: "Invalid JSON" }));
            }
          });
          return;
        }
        if (req.method === "GET" && url.startsWith("/api/v1/goals/monthly/personal")) {
          const u = new URL(url, "http://localhost");
          const identity_type = (u.searchParams.get("identity_type") || "").toUpperCase();
          const group_id = u.searchParams.get("group_id") || "";
          const year = u.searchParams.get("year") || "";
          const month = u.searchParams.get("month") || "";
          const user_id = u.searchParams.get("user_id") || null;
          const key = `${identity_type}|${group_id}|${year}|${month}`;
          const bucket = personalGoalsStore[key] || {};
          let items = Object.values(bucket);
          if (user_id) items = items.filter((it) => String(it.user_id) === String(user_id));
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ items }));
          return;
        }
        if (req.method === "POST" && url.startsWith("/api/v1/goals/monthly/personal")) {
          let body = "";
          req.on("data", (chunk) => {
            body += chunk;
          });
          req.on("end", () => {
            try {
              const payload = JSON.parse(body || "[]");
              const arr = Array.isArray(payload) ? payload : payload.items || [];
              for (const it of arr) {
                const identity_type = String(it.identity_type || "").toUpperCase();
                const group_id = it.group_id ?? "";
                const year = it.year ?? "";
                const month = it.month ?? "";
                const key = `${identity_type}|${group_id}|${year}|${month}`;
                if (!personalGoalsStore[key]) personalGoalsStore[key] = {};
                const userKey = String(it.user_id);
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
                };
              }
              res.setHeader("Content-Type", "application/json");
              res.end(JSON.stringify({ success: true, saved: arr.length }));
            } catch (e) {
              res.statusCode = 400;
              res.end(JSON.stringify({ error: "Invalid JSON" }));
            }
          });
          return;
        }
        if (req.method === "GET" && url.startsWith("/api/v1/users")) {
          const u = new URL(url, "http://localhost");
          const page = Number(u.searchParams.get("page") || "1");
          const size = Number(u.searchParams.get("size") || "10");
          const start = (page - 1) * size;
          const items = mockUsers.slice(start, start + size);
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ items, total: mockUsers.length, page, size }));
          return;
        }
        if (req.method === "GET" && url.startsWith("/api/v1/groups")) {
          const uniq = /* @__PURE__ */ new Map();
          for (const u of mockUsers) {
            if (u.group_id != null) {
              const gid = String(u.group_id);
              if (!uniq.has(gid)) uniq.set(gid, { id: u.group_id, name: u.group_name, description: "", member_count: 0 });
            }
          }
          const items = Array.from(uniq.values());
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ items, total: items.length, page: 1, size: items.length }));
          return;
        }
        if (req.method === "GET" && url.startsWith("/api/v1/groups/") && url.includes("/members")) {
          const u = new URL(url, "http://localhost");
          const pathname = u.pathname || "";
          const parts = pathname.split("/");
          const gid = parts[4];
          const items = mockUsers.filter((m) => String(m.group_id) === String(gid)).map((m) => ({
            id: m.id,
            username: m.username,
            identity_type: m.identity_type,
            group_id: m.group_id,
            group_name: m.group_name
          }));
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ items, total: items.length, page: 1, size: items.length }));
          return;
        }
        if (req.method === "GET" && url.startsWith("/api/v1/admin/metrics")) {
          res.setHeader("Content-Type", "application/json");
          const items = [
            { id: 1, key: "period_sales_amount", name: "\u671F\u95F4\u9500\u552E\u603B\u989D", is_active: true, default_roles: ["CC", "SS"] },
            { id: 2, key: "task_completion_rate", name: "\u4EFB\u52A1\u5B8C\u6210\u7387", is_active: true, default_roles: ["CC", "SS", "LP"] },
            { id: 3, key: "report_submission_rate", name: "\u65E5\u62A5\u63D0\u4EA4\u7387", is_active: true, default_roles: ["CC", "SS", "LP"] }
          ];
          res.end(JSON.stringify(items));
          return;
        }
        if (req.method === "PUT" && url.startsWith("/api/v1/admin/metrics/")) {
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ success: true }));
          return;
        }
        if (req.method === "POST" && url.startsWith("/api/v1/auth/login")) {
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ user: { id: 1, username: "demo", role: "super_admin" } }));
          return;
        }
        if (req.method === "POST" && url.startsWith("/api/v1/auth/logout")) {
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ success: true }));
          return;
        }
        if (req.method === "GET" && url.startsWith("/api/v1/auth/me")) {
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ id: 1, username: "demo", role: "super_admin" }));
          return;
        }
        if (req.method === "GET" && url.startsWith("/api/v1/ai/system-knowledge")) {
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({
            welcome: "\u4F60\u597D\uFF01\u6211\u662F\u7CFB\u7EDF\u5411\u5BFC\uFF0C\u5E2E\u4F60\u5FEB\u901F\u627E\u5230\u529F\u80FD\u5165\u53E3\u3002",
            recommended: [
              "\u5982\u4F55\u67E5\u770B\u6211\u7684\u4EFB\u52A1\u8FDB\u5EA6\uFF1F",
              "\u5982\u4F55\u63D0\u4EA4\u5F53\u5929\u7684\u65E5\u62A5\uFF1F",
              "\u54EA\u91CC\u53EF\u4EE5\u8BBE\u7F6E\u6708\u5EA6\u76EE\u6807\uFF1F"
            ]
          }));
          return;
        }
        if (req.method === "POST" && url.startsWith("/api/v1/ai/chat")) {
          res.setHeader("Content-Type", "application/json");
          let body = "";
          req.on("data", (chunk) => {
            body += chunk;
          });
          req.on("end", () => {
            try {
              const payload = JSON.parse(body || "{}");
              const q = String(payload.question || "");
              let answer = "\u8FD9\u662F AI \u5411\u5BFC\u7684\u793A\u4F8B\u56DE\u7B54\uFF1A\u8BF7\u5728\u7CFB\u7EDF\u4E2D\u67E5\u627E\u5BF9\u5E94\u529F\u80FD\u5165\u53E3\u3002";
              if (/任务|进度/.test(q)) {
                answer = "\u4EFB\u52A1\u8FDB\u5EA6\u53EF\u5728\u201C\u4EFB\u52A1\u7BA1\u7406\u201D\u4E0E\u201C\u4EEA\u8868\u76D8\u201D\u67E5\u770B\u3002";
              } else if (/日报|提交/.test(q)) {
                answer = "\u63D0\u4EA4\u65E5\u62A5\u8BF7\u8FDB\u5165\u201C\u65E5\u62A5\u201D\u9875\u9762\uFF0C\u70B9\u51FB\u65B0\u5EFA\u540E\u586B\u5199\u5E76\u63D0\u4EA4\u3002";
              } else if (/目标|月度/.test(q)) {
                answer = "\u6708\u5EA6\u76EE\u6807\u53EF\u5728\u201C\u5206\u6790/\u76EE\u6807\u7BA1\u7406\u201D\u9875\u8FDB\u884C\u8BBE\u7F6E\u4E0E\u67E5\u770B\u3002";
              }
              res.end(JSON.stringify({ answer }));
            } catch (e) {
              res.statusCode = 400;
              res.end(JSON.stringify({ error: "Invalid JSON" }));
            }
          });
          return;
        }
        if (req.method === "GET" && url.startsWith("/api/v1/settings/ai")) {
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify(aiSettingsStore));
          return;
        }
        if (req.method === "PUT" && url.startsWith("/api/v1/settings/ai")) {
          res.setHeader("Content-Type", "application/json");
          let body = "";
          req.on("data", (chunk) => {
            body += chunk;
          });
          req.on("end", () => {
            try {
              const payload = JSON.parse(body || "{}");
              aiSettingsStore.provider = payload.provider ?? aiSettingsStore.provider;
              aiSettingsStore.api_key = payload.api_key ?? aiSettingsStore.api_key;
              aiSettingsStore.base_url = payload.base_url ?? aiSettingsStore.base_url;
              aiSettingsStore.model_name = payload.model_name ?? aiSettingsStore.model_name;
              aiSettingsStore.max_tokens = Number(payload.max_tokens ?? aiSettingsStore.max_tokens);
              aiSettingsStore.temperature = Number(payload.temperature ?? aiSettingsStore.temperature);
              res.end(JSON.stringify({ success: true }));
            } catch (e) {
              res.statusCode = 400;
              res.end(JSON.stringify({ error: "Invalid JSON" }));
            }
          });
          return;
        }
        if (req.method === "GET" && url.startsWith("/api/v1/settings/system")) {
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify(systemSettingsStore));
          return;
        }
        if (req.method === "PUT" && url.startsWith("/api/v1/settings/system")) {
          res.setHeader("Content-Type", "application/json");
          let body = "";
          req.on("data", (chunk) => {
            body += chunk;
          });
          req.on("end", () => {
            try {
              const payload = JSON.parse(body || "{}");
              systemSettingsStore.system_name = payload.system_name ?? systemSettingsStore.system_name;
              systemSettingsStore.timezone = payload.timezone ?? systemSettingsStore.timezone;
              systemSettingsStore.language = payload.language ?? systemSettingsStore.language;
              systemSettingsStore.auto_analysis = payload.auto_analysis ?? systemSettingsStore.auto_analysis;
              systemSettingsStore.data_retention_days = Number(payload.data_retention_days ?? systemSettingsStore.data_retention_days);
              res.end(JSON.stringify({ success: true }));
            } catch (e) {
              res.statusCode = 400;
              res.end(JSON.stringify({ error: "Invalid JSON" }));
            }
          });
          return;
        }
        if (req.method === "POST" && url.startsWith("/api/v1/settings/ai/test")) {
          res.setHeader("Content-Type", "application/json");
          let body = "";
          req.on("data", (chunk) => {
            body += chunk;
          });
          req.on("end", () => {
            try {
              const payload = JSON.parse(body || "{}");
              const hasKey = !!(payload.api_key || aiSettingsStore.api_key);
              const provider = (payload.provider || aiSettingsStore.provider || "").toLowerCase();
              const okProviders = ["openrouter", "openai", "claude"];
              const success = hasKey && okProviders.includes(provider);
              const responseText = success ? "\u670D\u52A1\u53EF\u7528\uFF0C\u8BA4\u8BC1\u901A\u8FC7" : "\u7F3A\u5C11\u6709\u6548\u5BC6\u94A5\u6216\u4E0D\u652F\u6301\u7684\u63D0\u4F9B\u5546";
              res.end(JSON.stringify({ success, response: responseText, message: success ? "OK" : "Failed" }));
            } catch (e) {
              res.statusCode = 400;
              res.end(JSON.stringify({ success: false, message: "Invalid JSON" }));
            }
          });
          return;
        }
        if (req.method === "GET" && url.startsWith("/api/v1/settings/export")) {
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ message: "\u6570\u636E\u5BFC\u51FA\u5B8C\u6210\uFF08\u6A21\u62DF\uFF09" }));
          return;
        }
        if (req.method === "POST" && url.startsWith("/api/v1/settings/clear-cache")) {
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ success: true }));
          return;
        }
        if (req.method === "POST" && url.startsWith("/api/v1/settings/reset")) {
          res.setHeader("Content-Type", "application/json");
          Object.assign(aiSettingsStore, defaultAISettings);
          Object.assign(systemSettingsStore, defaultSystemSettings);
          res.end(JSON.stringify({ success: true }));
          return;
        }
        return next();
      });
    }
  };
}
var vite_config_default = defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const useMock = env.VITE_USE_MOCK === "true" || env.USE_MOCK === "true";
  return {
    plugins: useMock ? [
      vue(),
      devMockPlugin(),
      Components({
        resolvers: [IconsResolver({ componentPrefix: "i" })]
      }),
      Icons({ compiler: "vue3" })
    ] : [
      vue(),
      Components({
        resolvers: [IconsResolver({ componentPrefix: "i" })]
      }),
      Icons({ compiler: "vue3" })
    ],
    resolve: {
      alias: {
        "@": path.resolve(__vite_injected_original_dirname, "src")
      }
    },
    server: {
      port: 3001,
      proxy: useMock ? {} : {
        "/api/v1": {
          target: "http://127.0.0.1:8000",
          changeOrigin: true
        }
      }
    }
  };
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcuanMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJFOlxcXFw1MVxcXFxBSVxcXFxLaWxsZXJBcHBcXFxcZnJvbnRlbmRcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfZmlsZW5hbWUgPSBcIkU6XFxcXDUxXFxcXEFJXFxcXEtpbGxlckFwcFxcXFxmcm9udGVuZFxcXFx2aXRlLmNvbmZpZy5qc1wiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9pbXBvcnRfbWV0YV91cmwgPSBcImZpbGU6Ly8vRTovNTEvQUkvS2lsbGVyQXBwL2Zyb250ZW5kL3ZpdGUuY29uZmlnLmpzXCI7aW1wb3J0IHsgZGVmaW5lQ29uZmlnLCBsb2FkRW52IH0gZnJvbSAndml0ZSdcbmltcG9ydCBwYXRoIGZyb20gJ3BhdGgnXG5pbXBvcnQgdnVlIGZyb20gJ0B2aXRlanMvcGx1Z2luLXZ1ZSdcbmltcG9ydCBDb21wb25lbnRzIGZyb20gJ3VucGx1Z2luLXZ1ZS1jb21wb25lbnRzL3ZpdGUnXG5pbXBvcnQgSWNvbnMgZnJvbSAndW5wbHVnaW4taWNvbnMvdml0ZSdcbmltcG9ydCBJY29uc1Jlc29sdmVyIGZyb20gJ3VucGx1Z2luLWljb25zL3Jlc29sdmVyJ1xuXG5mdW5jdGlvbiBkZXZNb2NrUGx1Z2luKCkge1xuICByZXR1cm4ge1xuICAgIG5hbWU6ICdkZXYtbW9jay1wbHVnaW4nLFxuICAgIGFwcGx5OiAnc2VydmUnLFxuICAgIGNvbmZpZ3VyZVNlcnZlcihzZXJ2ZXIpIHtcbiAgICAgIC8vIFx1N0I4MFx1NjYxM1x1NTE4NVx1NUI1OFx1NUI1OFx1NTBBOFx1RkYxQVx1NEUyQVx1NEVCQVx1NjcwOFx1NUVBNlx1NzZFRVx1NjgwN1xuICAgICAgY29uc3QgcGVyc29uYWxHb2Fsc1N0b3JlID0ge31cbiAgICAgIC8vIFx1OEJCRVx1N0Y2RVx1OTg3NVx1NjcyQ1x1NTczMFx1NUI1OFx1NTBBOFx1RkYwOEFJIFx1NEUwRVx1N0NGQlx1N0VERlx1OEJCRVx1N0Y2RVx1RkYwOVxuICAgICAgY29uc3QgZGVmYXVsdEFJU2V0dGluZ3MgPSB7XG4gICAgICAgIHByb3ZpZGVyOiAnb3BlbnJvdXRlcicsXG4gICAgICAgIGFwaV9rZXk6ICcnLFxuICAgICAgICBiYXNlX3VybDogJ2h0dHBzOi8vb3BlbnJvdXRlci5haS9hcGkvdjEnLFxuICAgICAgICBtb2RlbF9uYW1lOiAnb3BlbmFpL2dwdC01JyxcbiAgICAgICAgbWF4X3Rva2VuczogMjAwMCxcbiAgICAgICAgdGVtcGVyYXR1cmU6IDAuN1xuICAgICAgfVxuICAgICAgY29uc3QgZGVmYXVsdFN5c3RlbVNldHRpbmdzID0ge1xuICAgICAgICBzeXN0ZW1fbmFtZTogJ0tpbGxlckFwcCcsXG4gICAgICAgIHRpbWV6b25lOiAnQXNpYS9TaGFuZ2hhaScsXG4gICAgICAgIGxhbmd1YWdlOiAnemgtQ04nLFxuICAgICAgICBhdXRvX2FuYWx5c2lzOiB0cnVlLFxuICAgICAgICBkYXRhX3JldGVudGlvbl9kYXlzOiA5MFxuICAgICAgfVxuICAgICAgY29uc3QgYWlTZXR0aW5nc1N0b3JlID0geyAuLi5kZWZhdWx0QUlTZXR0aW5ncyB9XG4gICAgICBjb25zdCBzeXN0ZW1TZXR0aW5nc1N0b3JlID0geyAuLi5kZWZhdWx0U3lzdGVtU2V0dGluZ3MgfVxuICAgICAgLy8gXHU3QjgwXHU2NjEzXHU3NTI4XHU2MjM3XHU0RTBFXHU3RUM0XHU2NTcwXHU2MzZFXHVGRjA4XHU3NTI4XHU0RThFXHU2NzJDXHU1NzMwXHU4MDU0XHU4QzAzXHVGRjA5XG4gICAgICBjb25zdCBtb2NrVXNlcnMgPSBbXG4gICAgICAgIHsgaWQ6IDEwMSwgdXNlcm5hbWU6ICdhbGljZScsIGlkZW50aXR5X3R5cGU6ICdDQycsIGdyb3VwX2lkOiAxLCBncm91cF9uYW1lOiAnXHU5NTAwXHU1NTJFXHU0RTAwXHU3RUM0JyB9LFxuICAgICAgICB7IGlkOiAxMDIsIHVzZXJuYW1lOiAnYm9iJywgaWRlbnRpdHlfdHlwZTogJ0NDJywgZ3JvdXBfaWQ6IDEsIGdyb3VwX25hbWU6ICdcdTk1MDBcdTU1MkVcdTRFMDBcdTdFQzQnIH0sXG4gICAgICAgIHsgaWQ6IDIwMSwgdXNlcm5hbWU6ICdjaGFybGllJywgaWRlbnRpdHlfdHlwZTogJ1NTJywgZ3JvdXBfaWQ6IDIsIGdyb3VwX25hbWU6ICdcdTY1NTlcdTUyQTFcdTRFMDBcdTdFQzQnIH0sXG4gICAgICAgIHsgaWQ6IDIwMiwgdXNlcm5hbWU6ICdkaWFuYScsIGlkZW50aXR5X3R5cGU6ICdTUycsIGdyb3VwX2lkOiAyLCBncm91cF9uYW1lOiAnXHU2NTU5XHU1MkExXHU0RTAwXHU3RUM0JyB9LFxuICAgICAgICB7IGlkOiAzMDEsIHVzZXJuYW1lOiAnZXZlJywgaWRlbnRpdHlfdHlwZTogJ0xQJywgZ3JvdXBfaWQ6IDMsIGdyb3VwX25hbWU6ICdcdTRFQTdcdTU0QzFcdTRFMDBcdTdFQzQnIH1cbiAgICAgIF1cbiAgICAgIHNlcnZlci5taWRkbGV3YXJlcy51c2UoKHJlcSwgcmVzLCBuZXh0KSA9PiB7XG4gICAgICAgIGNvbnN0IHVybCA9IHJlcS51cmwgfHwgJydcblxuICAgICAgICAvLyBBbmFseXRpY3Mgc3VtbWFyeSAoaWRlbnRpdHktYmFzZWQgbW9udGhseSBhZ2dyZWdhdGlvbilcbiAgICAgICAgaWYgKHJlcS5tZXRob2QgPT09ICdHRVQnICYmIHVybC5zdGFydHNXaXRoKCcvYXBpL3YxL2FuYWx5dGljcy9zdW1tYXJ5JykpIHtcbiAgICAgICAgICByZXMuc2V0SGVhZGVyKCdDb250ZW50LVR5cGUnLCAnYXBwbGljYXRpb24vanNvbicpXG4gICAgICAgICAgY29uc3QgdSA9IG5ldyBVUkwodXJsLCAnaHR0cDovL2xvY2FsaG9zdCcpXG4gICAgICAgICAgY29uc3QgaWR0ID0gKHUuc2VhcmNoUGFyYW1zLmdldCgnaWRlbnRpdHlfdHlwZScpIHx8ICcnKS50b1VwcGVyQ2FzZSgpXG4gICAgICAgICAgaWYgKGlkdCA9PT0gJ0NDJykge1xuICAgICAgICAgICAgcmVzLmVuZChKU09OLnN0cmluZ2lmeSh7XG4gICAgICAgICAgICAgIG1vbnRoOiB7XG4gICAgICAgICAgICAgICAgYWN0dWFsX2Ftb3VudDogMjUwMDAwLFxuICAgICAgICAgICAgICAgIG5ld19zaWduX2Ftb3VudDogMjE1MDAwLFxuICAgICAgICAgICAgICAgIHJlZmVycmFsX2Ftb3VudDogMzUwMDAsXG4gICAgICAgICAgICAgICAgcmVmZXJyYWxfY291bnQ6IDEyXG4gICAgICAgICAgICAgIH0sXG4gICAgICAgICAgICAgIHByb2dyZXNzX2Rpc3BsYXk6IHtcbiAgICAgICAgICAgICAgICBhbW91bnRfcmF0ZTogMC44LFxuICAgICAgICAgICAgICAgIG5ld19zaWduX2FjaGlldmVtZW50X3JhdGU6IDAuNzIsXG4gICAgICAgICAgICAgICAgcmVmZXJyYWxfYWNoaWV2ZW1lbnRfcmF0ZTogMC4zNVxuICAgICAgICAgICAgICB9XG4gICAgICAgICAgICB9KSlcbiAgICAgICAgICAgIHJldHVyblxuICAgICAgICAgIH1cbiAgICAgICAgICBpZiAoaWR0ID09PSAnU1MnKSB7XG4gICAgICAgICAgICByZXMuZW5kKEpTT04uc3RyaW5naWZ5KHtcbiAgICAgICAgICAgICAgbW9udGg6IHtcbiAgICAgICAgICAgICAgICBhY3R1YWxfYW1vdW50OiAyMDAwMDAsXG4gICAgICAgICAgICAgICAgcmVuZXdhbF9hbW91bnQ6IDEyMDAwMCxcbiAgICAgICAgICAgICAgICB1cGdyYWRlX2Ftb3VudDogODAwMDAsXG4gICAgICAgICAgICAgICAgcmVuZXdhbF9jb3VudDogMjQsXG4gICAgICAgICAgICAgICAgdXBncmFkZV9jb3VudDogOVxuICAgICAgICAgICAgICB9LFxuICAgICAgICAgICAgICBwcm9ncmVzc19kaXNwbGF5OiB7XG4gICAgICAgICAgICAgICAgdG90YWxfcmVuZXdhbF9hY2hpZXZlbWVudF9yYXRlOiAwLjZcbiAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgfSkpXG4gICAgICAgICAgICByZXR1cm5cbiAgICAgICAgICB9XG4gICAgICAgICAgLy8gZGVmYXVsdCBmYWxsYmFja1xuICAgICAgICAgIHJlcy5lbmQoSlNPTi5zdHJpbmdpZnkoeyBtb250aDogeyBhY3R1YWxfYW1vdW50OiAwIH0gfSkpXG4gICAgICAgICAgcmV0dXJuXG4gICAgICAgIH1cblxuICAgICAgICAvLyBBbmFseXRpY3MgdHJlbmQgKHByb3ZpZGUgZGV0YWlsZWQgbWV0cmljIGZpZWxkcyBmb3IgY29tcGF0aWJpbGl0eSlcbiAgICAgICAgaWYgKHJlcS5tZXRob2QgPT09ICdHRVQnICYmIHVybC5zdGFydHNXaXRoKCcvYXBpL3YxL2FuYWx5dGljcy90cmVuZCcpKSB7XG4gICAgICAgICAgcmVzLnNldEhlYWRlcignQ29udGVudC1UeXBlJywgJ2FwcGxpY2F0aW9uL2pzb24nKVxuICAgICAgICAgIGNvbnN0IG5vdyA9IG5ldyBEYXRlKClcbiAgICAgICAgICBjb25zdCBzZXJpZXMgPSBbXVxuICAgICAgICAgIGZvciAobGV0IGkgPSA5OyBpID49IDA7IGktLSkge1xuICAgICAgICAgICAgY29uc3QgZCA9IG5ldyBEYXRlKG5vdylcbiAgICAgICAgICAgIGQuc2V0RGF0ZShub3cuZ2V0RGF0ZSgpIC0gaSlcbiAgICAgICAgICAgIGNvbnN0IGRheSA9IGQudG9JU09TdHJpbmcoKS5zbGljZSgwLCAxMClcbiAgICAgICAgICAgIGNvbnN0IG5zID0gTWF0aC5yb3VuZCg2MDAwMCArIE1hdGgucmFuZG9tKCkgKiA0MDAwMClcbiAgICAgICAgICAgIGNvbnN0IHJmID0gTWF0aC5yb3VuZCgxNTAwMCArIE1hdGgucmFuZG9tKCkgKiAyMDAwMClcbiAgICAgICAgICAgIGNvbnN0IHJuID0gTWF0aC5yb3VuZCg1MDAwMCArIE1hdGgucmFuZG9tKCkgKiA0MDAwMClcbiAgICAgICAgICAgIGNvbnN0IHVnID0gTWF0aC5yb3VuZCgyMDAwMCArIE1hdGgucmFuZG9tKCkgKiAzMDAwMClcbiAgICAgICAgICAgIHNlcmllcy5wdXNoKHtcbiAgICAgICAgICAgICAgZGF0ZTogZGF5LFxuICAgICAgICAgICAgICBuZXdfc2lnbl9hbW91bnQ6IG5zLFxuICAgICAgICAgICAgICByZWZlcnJhbF9hbW91bnQ6IHJmLFxuICAgICAgICAgICAgICByZW5ld2FsX2Ftb3VudDogcm4sXG4gICAgICAgICAgICAgIHVwZ3JhZGVfYW1vdW50OiB1ZyxcbiAgICAgICAgICAgICAgcmVmZXJyYWxfY291bnQ6IE1hdGguZmxvb3IoMSArIE1hdGgucmFuZG9tKCkgKiA1KSxcbiAgICAgICAgICAgICAgcmVuZXdhbF9jb3VudDogTWF0aC5mbG9vcigzICsgTWF0aC5yYW5kb20oKSAqIDgpLFxuICAgICAgICAgICAgICB1cGdyYWRlX2NvdW50OiBNYXRoLmZsb29yKDEgKyBNYXRoLnJhbmRvbSgpICogNClcbiAgICAgICAgICAgIH0pXG4gICAgICAgICAgfVxuICAgICAgICAgIHJlcy5lbmQoSlNPTi5zdHJpbmdpZnkoeyBzZXJpZXMgfSkpXG4gICAgICAgICAgcmV0dXJuXG4gICAgICAgIH1cblxuICAgICAgICAvLyBBbmFseXRpY3MgZGF0YSAodW5pZmllZCBtZXRyaWNzIGFjcm9zcyBzY29wZXMpXG4gICAgICAgIGlmIChyZXEubWV0aG9kID09PSAnR0VUJyAmJiB1cmwuc3RhcnRzV2l0aCgnL2FwaS92MS9hbmFseXRpY3MvZGF0YScpKSB7XG4gICAgICAgICAgcmVzLnNldEhlYWRlcignQ29udGVudC1UeXBlJywgJ2FwcGxpY2F0aW9uL2pzb24nKVxuICAgICAgICAgIGNvbnN0IG1ldHJpY3MgPSB7XG4gICAgICAgICAgICB0YXNrX2NvbXBsZXRpb25fcmF0ZTogMC44MixcbiAgICAgICAgICAgIHJlcG9ydF9zdWJtaXNzaW9uX3JhdGU6IDAuOTMsXG4gICAgICAgICAgICBjYWxsX2NvdW50OiAxODAsXG4gICAgICAgICAgICBuZXdfbGVhZHNfY291bnQ6IDQ1LFxuICAgICAgICAgICAgY29udmVyc2lvbl9yYXRlOiAwLjIzLFxuICAgICAgICAgICAgYWN0aXZlX3N0dWRlbnRzOiA2MjAsXG4gICAgICAgICAgICByZWZ1bmRfcmF0ZTogMC4wMTUsXG4gICAgICAgICAgICBjb3Vyc2VfY29tcGxldGlvbl9yYXRlOiAwLjcxXG4gICAgICAgICAgfVxuICAgICAgICAgIHJlcy5lbmQoSlNPTi5zdHJpbmdpZnkoeyBtZXRyaWNzIH0pKVxuICAgICAgICAgIHJldHVyblxuICAgICAgICB9XG5cbiAgICAgICAgLy8gQW5hbHl0aWNzIEFJIGluc2lnaHQgKGxlZ2FjeSlcbiAgICAgICAgaWYgKHJlcS5tZXRob2QgPT09ICdQT1NUJyAmJiB1cmwuc3RhcnRzV2l0aCgnL2FwaS92MS9hbmFseXRpY3MvYWktaW5zaWdodCcpKSB7XG4gICAgICAgICAgcmVzLnNldEhlYWRlcignQ29udGVudC1UeXBlJywgJ2FwcGxpY2F0aW9uL2pzb24nKVxuICAgICAgICAgIHJlcy5lbmQoSlNPTi5zdHJpbmdpZnkoeyBpbnNpZ2h0OiAnXHU4RkQ5XHU2NjJGXHU1N0ZBXHU0RThFXHU2QTIxXHU2MkRGXHU1MzlGXHU1OUNCXHU2NTcwXHU2MzZFXHU3Njg0QUlcdTZEMUVcdTVCREZcdTc5M0FcdTRGOEJcdUZGMUFcdTk1MDBcdTU1MkVcdTk4OURcdTZDRTJcdTUyQThcdTRFM0JcdTg5ODFcdTUzRDdcdTU0NjhcdTY3MkJcdTRGQzNcdTk1MDBcdTVGNzFcdTU0Q0RcdUZGMENcdTVFRkFcdThCQUVcdTU3MjhcdTU0NjhcdTRFMkRcdTU4OUVcdTUyQTBcdThGNkNcdTRFQ0JcdTdFQ0RcdTZEM0JcdTUyQThcdTRFRTVcdTVFNzNcdTZFRDFcdThEOEJcdTUyQkZcdTMwMDInIH0pKVxuICAgICAgICAgIHJldHVyblxuICAgICAgICB9XG4gICAgICAgIC8vIEFuYWx5dGljcyBBSSBpbnNpZ2h0IHN1bW1hcnkgKGN1cnJlbnQpXG4gICAgICAgIGlmIChyZXEubWV0aG9kID09PSAnUE9TVCcgJiYgdXJsLnN0YXJ0c1dpdGgoJy9hcGkvdjEvYW5hbHl0aWNzL2FpLWluc2lnaHQtc3VtbWFyeScpKSB7XG4gICAgICAgICAgcmVzLnNldEhlYWRlcignQ29udGVudC1UeXBlJywgJ2FwcGxpY2F0aW9uL2pzb24nKVxuICAgICAgICAgIGxldCBib2R5ID0gJydcbiAgICAgICAgICByZXEub24oJ2RhdGEnLCBjaHVuayA9PiB7IGJvZHkgKz0gY2h1bmsgfSlcbiAgICAgICAgICByZXEub24oJ2VuZCcsICgpID0+IHtcbiAgICAgICAgICAgIHJlcy5lbmQoSlNPTi5zdHJpbmdpZnkoeyBpbnNpZ2h0OiAnQUlcdTZEMUVcdTVCREZcdUZGMUFcdTVGNTNcdTUyNERcdTY3MUZcdTk1RjRcdTk1MDBcdTU1MkVcdTgyODJcdTU5NEZcdTdBMzNcdTVCOUFcdUZGMENcdTUzNDdcdTdFQTdcdThEMjFcdTczMkVcdTUzNjBcdTZCRDRcdThGODNcdTlBRDhcdTMwMDJcdTVFRkFcdThCQUVcdTRGMThcdTUzMTZcdThGNkNcdTRFQ0JcdTdFQ0RcdTZEM0JcdTUyQThcdTRFRTVcdTYzRDBcdTUzNDdcdThGNkNcdTUzMTZcdTczODdcdTMwMDInIH0pKVxuICAgICAgICAgIH0pXG4gICAgICAgICAgcmV0dXJuXG4gICAgICAgIH1cblxuICAgICAgICAvLyBNb250aGx5IGdvYWxzXG4gICAgICAgIGlmIChyZXEubWV0aG9kID09PSAnR0VUJyAmJiB1cmwuc3RhcnRzV2l0aCgnL2FwaS92MS9nb2Fscy9tb250aGx5JykpIHtcbiAgICAgICAgICBjb25zdCB1ID0gbmV3IFVSTCh1cmwsICdodHRwOi8vbG9jYWxob3N0JylcbiAgICAgICAgICBjb25zdCB5ZWFyID0gTnVtYmVyKHUuc2VhcmNoUGFyYW1zLmdldCgneWVhcicpIHx8IG5ldyBEYXRlKCkuZ2V0RnVsbFllYXIoKSlcbiAgICAgICAgICBjb25zdCBtb250aCA9IE51bWJlcih1LnNlYXJjaFBhcmFtcy5nZXQoJ21vbnRoJykgfHwgKG5ldyBEYXRlKCkuZ2V0TW9udGgoKSArIDEpKVxuICAgICAgICAgIHJlcy5zZXRIZWFkZXIoJ0NvbnRlbnQtVHlwZScsICdhcHBsaWNhdGlvbi9qc29uJylcbiAgICAgICAgICBjb25zdCBjY19uZXcgPSAzMDAwMDBcbiAgICAgICAgICBjb25zdCBjY19yZWYgPSAxMDAwMDBcbiAgICAgICAgICBjb25zdCBzc190b3RhbCA9IDEyMDAwMFxuICAgICAgICAgIGNvbnN0IGdvYWxzID0gW1xuICAgICAgICAgICAge1xuICAgICAgICAgICAgICBpZDogMSxcbiAgICAgICAgICAgICAgaWRlbnRpdHlfdHlwZTogJ0NDJyxcbiAgICAgICAgICAgICAgc2NvcGU6ICdnbG9iYWwnLFxuICAgICAgICAgICAgICB5ZWFyLFxuICAgICAgICAgICAgICBtb250aCxcbiAgICAgICAgICAgICAgYW1vdW50X3RhcmdldDogY2NfbmV3ICsgY2NfcmVmLFxuICAgICAgICAgICAgICBuZXdfc2lnbl90YXJnZXRfYW1vdW50OiBjY19uZXcsXG4gICAgICAgICAgICAgIHJlZmVycmFsX3RhcmdldF9hbW91bnQ6IGNjX3JlZixcbiAgICAgICAgICAgICAgcmVuZXdhbF90b3RhbF90YXJnZXRfYW1vdW50OiAwLFxuICAgICAgICAgICAgICB1cGdyYWRlX3RhcmdldF9jb3VudDogOCxcbiAgICAgICAgICAgICAgcmVuZXdhbF90YXJnZXRfY291bnQ6IDAsXG4gICAgICAgICAgICAgIG5vdGVzOiBudWxsLFxuICAgICAgICAgICAgICBjcmVhdGVkX2F0OiBudWxsLFxuICAgICAgICAgICAgICB1cGRhdGVkX2F0OiBudWxsXG4gICAgICAgICAgICB9LFxuICAgICAgICAgICAge1xuICAgICAgICAgICAgICBpZDogMixcbiAgICAgICAgICAgICAgaWRlbnRpdHlfdHlwZTogJ1NTJyxcbiAgICAgICAgICAgICAgc2NvcGU6ICdnbG9iYWwnLFxuICAgICAgICAgICAgICB5ZWFyLFxuICAgICAgICAgICAgICBtb250aCxcbiAgICAgICAgICAgICAgYW1vdW50X3RhcmdldDogc3NfdG90YWwsXG4gICAgICAgICAgICAgIG5ld19zaWduX3RhcmdldF9hbW91bnQ6IDAsXG4gICAgICAgICAgICAgIHJlZmVycmFsX3RhcmdldF9hbW91bnQ6IDAsXG4gICAgICAgICAgICAgIHJlbmV3YWxfdG90YWxfdGFyZ2V0X2Ftb3VudDogc3NfdG90YWwsXG4gICAgICAgICAgICAgIHVwZ3JhZGVfdGFyZ2V0X2NvdW50OiAxMixcbiAgICAgICAgICAgICAgcmVuZXdhbF90YXJnZXRfY291bnQ6IDAsXG4gICAgICAgICAgICAgIG5vdGVzOiBudWxsLFxuICAgICAgICAgICAgICBjcmVhdGVkX2F0OiBudWxsLFxuICAgICAgICAgICAgICB1cGRhdGVkX2F0OiBudWxsXG4gICAgICAgICAgICB9XG4gICAgICAgICAgXVxuICAgICAgICAgIHJlcy5lbmQoSlNPTi5zdHJpbmdpZnkoZ29hbHMpKVxuICAgICAgICAgIHJldHVyblxuICAgICAgICB9XG5cbiAgICAgICAgaWYgKHJlcS5tZXRob2QgPT09ICdQT1NUJyAmJiB1cmwuc3RhcnRzV2l0aCgnL2FwaS92MS9nb2Fscy9tb250aGx5JykpIHtcbiAgICAgICAgICBsZXQgYm9keSA9ICcnXG4gICAgICAgICAgcmVxLm9uKCdkYXRhJywgY2h1bmsgPT4geyBib2R5ICs9IGNodW5rIH0pXG4gICAgICAgICAgcmVxLm9uKCdlbmQnLCAoKSA9PiB7XG4gICAgICAgICAgICB0cnkge1xuICAgICAgICAgICAgICBjb25zdCBwYXlsb2FkID0gSlNPTi5wYXJzZShib2R5IHx8ICd7fScpXG4gICAgICAgICAgICAgIHJlcy5zZXRIZWFkZXIoJ0NvbnRlbnQtVHlwZScsICdhcHBsaWNhdGlvbi9qc29uJylcbiAgICAgICAgICAgICAgcmVzLmVuZChKU09OLnN0cmluZ2lmeSh7IGlkOiBNYXRoLmZsb29yKE1hdGgucmFuZG9tKCkgKiAxMDAwMCksIC4uLnBheWxvYWQgfSkpXG4gICAgICAgICAgICB9IGNhdGNoIChlKSB7XG4gICAgICAgICAgICAgIHJlcy5zdGF0dXNDb2RlID0gNDAwXG4gICAgICAgICAgICAgIHJlcy5lbmQoSlNPTi5zdHJpbmdpZnkoeyBlcnJvcjogJ0ludmFsaWQgSlNPTicgfSkpXG4gICAgICAgICAgICB9XG4gICAgICAgICAgfSlcbiAgICAgICAgICByZXR1cm5cbiAgICAgICAgfVxuXG4gICAgICAgIC8vIFBlcnNvbmFsIG1vbnRobHkgZ29hbHMgKGJhdGNoKVxuICAgICAgICBpZiAocmVxLm1ldGhvZCA9PT0gJ0dFVCcgJiYgdXJsLnN0YXJ0c1dpdGgoJy9hcGkvdjEvZ29hbHMvbW9udGhseS9wZXJzb25hbCcpKSB7XG4gICAgICAgICAgY29uc3QgdSA9IG5ldyBVUkwodXJsLCAnaHR0cDovL2xvY2FsaG9zdCcpXG4gICAgICAgICAgY29uc3QgaWRlbnRpdHlfdHlwZSA9ICh1LnNlYXJjaFBhcmFtcy5nZXQoJ2lkZW50aXR5X3R5cGUnKSB8fCAnJykudG9VcHBlckNhc2UoKVxuICAgICAgICAgIGNvbnN0IGdyb3VwX2lkID0gdS5zZWFyY2hQYXJhbXMuZ2V0KCdncm91cF9pZCcpIHx8ICcnXG4gICAgICAgICAgY29uc3QgeWVhciA9IHUuc2VhcmNoUGFyYW1zLmdldCgneWVhcicpIHx8ICcnXG4gICAgICAgICAgY29uc3QgbW9udGggPSB1LnNlYXJjaFBhcmFtcy5nZXQoJ21vbnRoJykgfHwgJydcbiAgICAgICAgICBjb25zdCB1c2VyX2lkID0gdS5zZWFyY2hQYXJhbXMuZ2V0KCd1c2VyX2lkJykgfHwgbnVsbFxuICAgICAgICAgIGNvbnN0IGtleSA9IGAke2lkZW50aXR5X3R5cGV9fCR7Z3JvdXBfaWR9fCR7eWVhcn18JHttb250aH1gXG4gICAgICAgICAgY29uc3QgYnVja2V0ID0gcGVyc29uYWxHb2Fsc1N0b3JlW2tleV0gfHwge31cbiAgICAgICAgICBsZXQgaXRlbXMgPSBPYmplY3QudmFsdWVzKGJ1Y2tldClcbiAgICAgICAgICBpZiAodXNlcl9pZCkgaXRlbXMgPSBpdGVtcy5maWx0ZXIoaXQgPT4gU3RyaW5nKGl0LnVzZXJfaWQpID09PSBTdHJpbmcodXNlcl9pZCkpXG4gICAgICAgICAgcmVzLnNldEhlYWRlcignQ29udGVudC1UeXBlJywgJ2FwcGxpY2F0aW9uL2pzb24nKVxuICAgICAgICAgIHJlcy5lbmQoSlNPTi5zdHJpbmdpZnkoeyBpdGVtcyB9KSlcbiAgICAgICAgICByZXR1cm5cbiAgICAgICAgfVxuICAgICAgICBpZiAocmVxLm1ldGhvZCA9PT0gJ1BPU1QnICYmIHVybC5zdGFydHNXaXRoKCcvYXBpL3YxL2dvYWxzL21vbnRobHkvcGVyc29uYWwnKSkge1xuICAgICAgICAgIGxldCBib2R5ID0gJydcbiAgICAgICAgICByZXEub24oJ2RhdGEnLCBjaHVuayA9PiB7IGJvZHkgKz0gY2h1bmsgfSlcbiAgICAgICAgICByZXEub24oJ2VuZCcsICgpID0+IHtcbiAgICAgICAgICAgIHRyeSB7XG4gICAgICAgICAgICAgIGNvbnN0IHBheWxvYWQgPSBKU09OLnBhcnNlKGJvZHkgfHwgJ1tdJylcbiAgICAgICAgICAgICAgY29uc3QgYXJyID0gQXJyYXkuaXNBcnJheShwYXlsb2FkKSA/IHBheWxvYWQgOiAocGF5bG9hZC5pdGVtcyB8fCBbXSlcbiAgICAgICAgICAgICAgLy8gXHU2QkNGXHU2NzYxXHU4QkIwXHU1RjU1XHVGRjFBaWRlbnRpdHlfdHlwZSwgZ3JvdXBfaWQsIHVzZXJfaWQsIHllYXIsIG1vbnRoLCAuLi5maWVsZHNcbiAgICAgICAgICAgICAgZm9yIChjb25zdCBpdCBvZiBhcnIpIHtcbiAgICAgICAgICAgICAgICBjb25zdCBpZGVudGl0eV90eXBlID0gU3RyaW5nKGl0LmlkZW50aXR5X3R5cGUgfHwgJycpLnRvVXBwZXJDYXNlKClcbiAgICAgICAgICAgICAgICBjb25zdCBncm91cF9pZCA9IGl0Lmdyb3VwX2lkID8/ICcnXG4gICAgICAgICAgICAgICAgY29uc3QgeWVhciA9IGl0LnllYXIgPz8gJydcbiAgICAgICAgICAgICAgICBjb25zdCBtb250aCA9IGl0Lm1vbnRoID8/ICcnXG4gICAgICAgICAgICAgICAgY29uc3Qga2V5ID0gYCR7aWRlbnRpdHlfdHlwZX18JHtncm91cF9pZH18JHt5ZWFyfXwke21vbnRofWBcbiAgICAgICAgICAgICAgICBpZiAoIXBlcnNvbmFsR29hbHNTdG9yZVtrZXldKSBwZXJzb25hbEdvYWxzU3RvcmVba2V5XSA9IHt9XG4gICAgICAgICAgICAgICAgY29uc3QgdXNlcktleSA9IFN0cmluZyhpdC51c2VyX2lkKVxuICAgICAgICAgICAgICAgIHBlcnNvbmFsR29hbHNTdG9yZVtrZXldW3VzZXJLZXldID0ge1xuICAgICAgICAgICAgICAgICAgaWRlbnRpdHlfdHlwZSxcbiAgICAgICAgICAgICAgICAgIGdyb3VwX2lkLFxuICAgICAgICAgICAgICAgICAgdXNlcl9pZDogaXQudXNlcl9pZCxcbiAgICAgICAgICAgICAgICAgIHllYXIsXG4gICAgICAgICAgICAgICAgICBtb250aCxcbiAgICAgICAgICAgICAgICAgIG5ld19zaWduX3RhcmdldF9hbW91bnQ6IE51bWJlcihpdC5uZXdfc2lnbl90YXJnZXRfYW1vdW50IHx8IDApLFxuICAgICAgICAgICAgICAgICAgcmVmZXJyYWxfdGFyZ2V0X2Ftb3VudDogTnVtYmVyKGl0LnJlZmVycmFsX3RhcmdldF9hbW91bnQgfHwgMCksXG4gICAgICAgICAgICAgICAgICByZW5ld2FsX3RvdGFsX3RhcmdldF9hbW91bnQ6IE51bWJlcihpdC5yZW5ld2FsX3RvdGFsX3RhcmdldF9hbW91bnQgfHwgMCksXG4gICAgICAgICAgICAgICAgICB1cGdyYWRlX3RhcmdldF9jb3VudDogTnVtYmVyKGl0LnVwZ3JhZGVfdGFyZ2V0X2NvdW50IHx8IDApXG4gICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgIHJlcy5zZXRIZWFkZXIoJ0NvbnRlbnQtVHlwZScsICdhcHBsaWNhdGlvbi9qc29uJylcbiAgICAgICAgICAgICAgcmVzLmVuZChKU09OLnN0cmluZ2lmeSh7IHN1Y2Nlc3M6IHRydWUsIHNhdmVkOiBhcnIubGVuZ3RoIH0pKVxuICAgICAgICAgICAgfSBjYXRjaCAoZSkge1xuICAgICAgICAgICAgICByZXMuc3RhdHVzQ29kZSA9IDQwMFxuICAgICAgICAgICAgICByZXMuZW5kKEpTT04uc3RyaW5naWZ5KHsgZXJyb3I6ICdJbnZhbGlkIEpTT04nIH0pKVxuICAgICAgICAgICAgfVxuICAgICAgICAgIH0pXG4gICAgICAgICAgcmV0dXJuXG4gICAgICAgIH1cblxuICAgICAgICAvLyBVc2VycyAobW9jaylcbiAgICAgICAgaWYgKHJlcS5tZXRob2QgPT09ICdHRVQnICYmIHVybC5zdGFydHNXaXRoKCcvYXBpL3YxL3VzZXJzJykpIHtcbiAgICAgICAgICBjb25zdCB1ID0gbmV3IFVSTCh1cmwsICdodHRwOi8vbG9jYWxob3N0JylcbiAgICAgICAgICBjb25zdCBwYWdlID0gTnVtYmVyKHUuc2VhcmNoUGFyYW1zLmdldCgncGFnZScpIHx8ICcxJylcbiAgICAgICAgICBjb25zdCBzaXplID0gTnVtYmVyKHUuc2VhcmNoUGFyYW1zLmdldCgnc2l6ZScpIHx8ICcxMCcpXG4gICAgICAgICAgY29uc3Qgc3RhcnQgPSAocGFnZSAtIDEpICogc2l6ZVxuICAgICAgICAgIGNvbnN0IGl0ZW1zID0gbW9ja1VzZXJzLnNsaWNlKHN0YXJ0LCBzdGFydCArIHNpemUpXG4gICAgICAgICAgcmVzLnNldEhlYWRlcignQ29udGVudC1UeXBlJywgJ2FwcGxpY2F0aW9uL2pzb24nKVxuICAgICAgICAgIHJlcy5lbmQoSlNPTi5zdHJpbmdpZnkoeyBpdGVtcywgdG90YWw6IG1vY2tVc2Vycy5sZW5ndGgsIHBhZ2UsIHNpemUgfSkpXG4gICAgICAgICAgcmV0dXJuXG4gICAgICAgIH1cblxuICAgICAgICAvLyBHcm91cHMgKG1vY2ssIGRlcml2ZWQgZnJvbSB1c2VycylcbiAgICAgICAgaWYgKHJlcS5tZXRob2QgPT09ICdHRVQnICYmIHVybC5zdGFydHNXaXRoKCcvYXBpL3YxL2dyb3VwcycpKSB7XG4gICAgICAgICAgY29uc3QgdW5pcSA9IG5ldyBNYXAoKVxuICAgICAgICAgIGZvciAoY29uc3QgdSBvZiBtb2NrVXNlcnMpIHtcbiAgICAgICAgICAgIGlmICh1Lmdyb3VwX2lkICE9IG51bGwpIHtcbiAgICAgICAgICAgICAgY29uc3QgZ2lkID0gU3RyaW5nKHUuZ3JvdXBfaWQpXG4gICAgICAgICAgICAgIGlmICghdW5pcS5oYXMoZ2lkKSkgdW5pcS5zZXQoZ2lkLCB7IGlkOiB1Lmdyb3VwX2lkLCBuYW1lOiB1Lmdyb3VwX25hbWUsIGRlc2NyaXB0aW9uOiAnJywgbWVtYmVyX2NvdW50OiAwIH0pXG4gICAgICAgICAgICB9XG4gICAgICAgICAgfVxuICAgICAgICAgIGNvbnN0IGl0ZW1zID0gQXJyYXkuZnJvbSh1bmlxLnZhbHVlcygpKVxuICAgICAgICAgIHJlcy5zZXRIZWFkZXIoJ0NvbnRlbnQtVHlwZScsICdhcHBsaWNhdGlvbi9qc29uJylcbiAgICAgICAgICByZXMuZW5kKEpTT04uc3RyaW5naWZ5KHsgaXRlbXMsIHRvdGFsOiBpdGVtcy5sZW5ndGgsIHBhZ2U6IDEsIHNpemU6IGl0ZW1zLmxlbmd0aCB9KSlcbiAgICAgICAgICByZXR1cm5cbiAgICAgICAgfVxuXG4gICAgICAgIC8vIEdyb3VwIG1lbWJlcnMgKG1vY2spOiAvYXBpL3YxL2dyb3Vwcy86aWQvbWVtYmVyc1xuICAgICAgICBpZiAocmVxLm1ldGhvZCA9PT0gJ0dFVCcgJiYgdXJsLnN0YXJ0c1dpdGgoJy9hcGkvdjEvZ3JvdXBzLycpICYmIHVybC5pbmNsdWRlcygnL21lbWJlcnMnKSkge1xuICAgICAgICAgIGNvbnN0IHUgPSBuZXcgVVJMKHVybCwgJ2h0dHA6Ly9sb2NhbGhvc3QnKVxuICAgICAgICAgIGNvbnN0IHBhdGhuYW1lID0gdS5wYXRobmFtZSB8fCAnJ1xuICAgICAgICAgIGNvbnN0IHBhcnRzID0gcGF0aG5hbWUuc3BsaXQoJy8nKVxuICAgICAgICAgIC8vIFsnJywgJ2FwaScsICd2MScsICdncm91cHMnLCAnOmlkJywgJ21lbWJlcnMnXVxuICAgICAgICAgIGNvbnN0IGdpZCA9IHBhcnRzWzRdXG4gICAgICAgICAgY29uc3QgaXRlbXMgPSBtb2NrVXNlcnMuZmlsdGVyKG0gPT4gU3RyaW5nKG0uZ3JvdXBfaWQpID09PSBTdHJpbmcoZ2lkKSkubWFwKG0gPT4gKHtcbiAgICAgICAgICAgIGlkOiBtLmlkLFxuICAgICAgICAgICAgdXNlcm5hbWU6IG0udXNlcm5hbWUsXG4gICAgICAgICAgICBpZGVudGl0eV90eXBlOiBtLmlkZW50aXR5X3R5cGUsXG4gICAgICAgICAgICBncm91cF9pZDogbS5ncm91cF9pZCxcbiAgICAgICAgICAgIGdyb3VwX25hbWU6IG0uZ3JvdXBfbmFtZVxuICAgICAgICAgIH0pKVxuICAgICAgICAgIHJlcy5zZXRIZWFkZXIoJ0NvbnRlbnQtVHlwZScsICdhcHBsaWNhdGlvbi9qc29uJylcbiAgICAgICAgICByZXMuZW5kKEpTT04uc3RyaW5naWZ5KHsgaXRlbXMsIHRvdGFsOiBpdGVtcy5sZW5ndGgsIHBhZ2U6IDEsIHNpemU6IGl0ZW1zLmxlbmd0aCB9KSlcbiAgICAgICAgICByZXR1cm5cbiAgICAgICAgfVxuXG4gICAgICAgIC8vIEFkbWluIG1ldHJpY3NcbiAgICAgICAgaWYgKHJlcS5tZXRob2QgPT09ICdHRVQnICYmIHVybC5zdGFydHNXaXRoKCcvYXBpL3YxL2FkbWluL21ldHJpY3MnKSkge1xuICAgICAgICAgIHJlcy5zZXRIZWFkZXIoJ0NvbnRlbnQtVHlwZScsICdhcHBsaWNhdGlvbi9qc29uJylcbiAgICAgICAgICBjb25zdCBpdGVtcyA9IFtcbiAgICAgICAgICAgIHsgaWQ6IDEsIGtleTogJ3BlcmlvZF9zYWxlc19hbW91bnQnLCBuYW1lOiAnXHU2NzFGXHU5NUY0XHU5NTAwXHU1NTJFXHU2MDNCXHU5ODlEJywgaXNfYWN0aXZlOiB0cnVlLCBkZWZhdWx0X3JvbGVzOiBbJ0NDJywgJ1NTJ10gfSxcbiAgICAgICAgICAgIHsgaWQ6IDIsIGtleTogJ3Rhc2tfY29tcGxldGlvbl9yYXRlJywgbmFtZTogJ1x1NEVGQlx1NTJBMVx1NUI4Q1x1NjIxMFx1NzM4NycsIGlzX2FjdGl2ZTogdHJ1ZSwgZGVmYXVsdF9yb2xlczogWydDQycsICdTUycsICdMUCddIH0sXG4gICAgICAgICAgICB7IGlkOiAzLCBrZXk6ICdyZXBvcnRfc3VibWlzc2lvbl9yYXRlJywgbmFtZTogJ1x1NjVFNVx1NjJBNVx1NjNEMFx1NEVBNFx1NzM4NycsIGlzX2FjdGl2ZTogdHJ1ZSwgZGVmYXVsdF9yb2xlczogWydDQycsICdTUycsICdMUCddIH1cbiAgICAgICAgICBdXG4gICAgICAgICAgcmVzLmVuZChKU09OLnN0cmluZ2lmeShpdGVtcykpXG4gICAgICAgICAgcmV0dXJuXG4gICAgICAgIH1cblxuICAgICAgICBpZiAocmVxLm1ldGhvZCA9PT0gJ1BVVCcgJiYgdXJsLnN0YXJ0c1dpdGgoJy9hcGkvdjEvYWRtaW4vbWV0cmljcy8nKSkge1xuICAgICAgICAgIHJlcy5zZXRIZWFkZXIoJ0NvbnRlbnQtVHlwZScsICdhcHBsaWNhdGlvbi9qc29uJylcbiAgICAgICAgICByZXMuZW5kKEpTT04uc3RyaW5naWZ5KHsgc3VjY2VzczogdHJ1ZSB9KSlcbiAgICAgICAgICByZXR1cm5cbiAgICAgICAgfVxuXG4gICAgICAgIC8vIEF1dGggbW9ja3MgKHRvIGF2b2lkIDQwMSBkdXJpbmcgcHJldmlldylcbiAgICAgICAgaWYgKHJlcS5tZXRob2QgPT09ICdQT1NUJyAmJiB1cmwuc3RhcnRzV2l0aCgnL2FwaS92MS9hdXRoL2xvZ2luJykpIHtcbiAgICAgICAgICByZXMuc2V0SGVhZGVyKCdDb250ZW50LVR5cGUnLCAnYXBwbGljYXRpb24vanNvbicpXG4gICAgICAgICAgcmVzLmVuZChKU09OLnN0cmluZ2lmeSh7IHVzZXI6IHsgaWQ6IDEsIHVzZXJuYW1lOiAnZGVtbycsIHJvbGU6ICdzdXBlcl9hZG1pbicgfSB9KSlcbiAgICAgICAgICByZXR1cm5cbiAgICAgICAgfVxuXG4gICAgICAgIGlmIChyZXEubWV0aG9kID09PSAnUE9TVCcgJiYgdXJsLnN0YXJ0c1dpdGgoJy9hcGkvdjEvYXV0aC9sb2dvdXQnKSkge1xuICAgICAgICAgIHJlcy5zZXRIZWFkZXIoJ0NvbnRlbnQtVHlwZScsICdhcHBsaWNhdGlvbi9qc29uJylcbiAgICAgICAgICByZXMuZW5kKEpTT04uc3RyaW5naWZ5KHsgc3VjY2VzczogdHJ1ZSB9KSlcbiAgICAgICAgICByZXR1cm5cbiAgICAgICAgfVxuXG4gICAgICAgIGlmIChyZXEubWV0aG9kID09PSAnR0VUJyAmJiB1cmwuc3RhcnRzV2l0aCgnL2FwaS92MS9hdXRoL21lJykpIHtcbiAgICAgICAgICByZXMuc2V0SGVhZGVyKCdDb250ZW50LVR5cGUnLCAnYXBwbGljYXRpb24vanNvbicpXG4gICAgICAgICAgcmVzLmVuZChKU09OLnN0cmluZ2lmeSh7IGlkOiAxLCB1c2VybmFtZTogJ2RlbW8nLCByb2xlOiAnc3VwZXJfYWRtaW4nIH0pKVxuICAgICAgICAgIHJldHVyblxuICAgICAgICB9XG5cbiAgICAgICAgLy8gQUkgc3lzdGVtIGtub3dsZWRnZVxuICAgICAgICBpZiAocmVxLm1ldGhvZCA9PT0gJ0dFVCcgJiYgdXJsLnN0YXJ0c1dpdGgoJy9hcGkvdjEvYWkvc3lzdGVtLWtub3dsZWRnZScpKSB7XG4gICAgICAgICAgcmVzLnNldEhlYWRlcignQ29udGVudC1UeXBlJywgJ2FwcGxpY2F0aW9uL2pzb24nKVxuICAgICAgICAgIHJlcy5lbmQoSlNPTi5zdHJpbmdpZnkoe1xuICAgICAgICAgICAgd2VsY29tZTogJ1x1NEY2MFx1NTk3RFx1RkYwMVx1NjIxMVx1NjYyRlx1N0NGQlx1N0VERlx1NTQxMVx1NUJGQ1x1RkYwQ1x1NUUyRVx1NEY2MFx1NUZFQlx1OTAxRlx1NjI3RVx1NTIzMFx1NTI5Rlx1ODBGRFx1NTE2NVx1NTNFM1x1MzAwMicsXG4gICAgICAgICAgICByZWNvbW1lbmRlZDogW1xuICAgICAgICAgICAgICAnXHU1OTgyXHU0RjU1XHU2N0U1XHU3NzBCXHU2MjExXHU3Njg0XHU0RUZCXHU1MkExXHU4RkRCXHU1RUE2XHVGRjFGJyxcbiAgICAgICAgICAgICAgJ1x1NTk4Mlx1NEY1NVx1NjNEMFx1NEVBNFx1NUY1M1x1NTkyOVx1NzY4NFx1NjVFNVx1NjJBNVx1RkYxRicsXG4gICAgICAgICAgICAgICdcdTU0RUFcdTkxQ0NcdTUzRUZcdTRFRTVcdThCQkVcdTdGNkVcdTY3MDhcdTVFQTZcdTc2RUVcdTY4MDdcdUZGMUYnXG4gICAgICAgICAgICBdXG4gICAgICAgICAgfSkpXG4gICAgICAgICAgcmV0dXJuXG4gICAgICAgIH1cblxuICAgICAgICAvLyBBSSBjaGF0XG4gICAgICAgIGlmIChyZXEubWV0aG9kID09PSAnUE9TVCcgJiYgdXJsLnN0YXJ0c1dpdGgoJy9hcGkvdjEvYWkvY2hhdCcpKSB7XG4gICAgICAgICAgcmVzLnNldEhlYWRlcignQ29udGVudC1UeXBlJywgJ2FwcGxpY2F0aW9uL2pzb24nKVxuICAgICAgICAgIGxldCBib2R5ID0gJydcbiAgICAgICAgICByZXEub24oJ2RhdGEnLCBjaHVuayA9PiB7IGJvZHkgKz0gY2h1bmsgfSlcbiAgICAgICAgICByZXEub24oJ2VuZCcsICgpID0+IHtcbiAgICAgICAgICAgIHRyeSB7XG4gICAgICAgICAgICAgIGNvbnN0IHBheWxvYWQgPSBKU09OLnBhcnNlKGJvZHkgfHwgJ3t9JylcbiAgICAgICAgICAgICAgY29uc3QgcSA9IFN0cmluZyhwYXlsb2FkLnF1ZXN0aW9uIHx8ICcnKVxuICAgICAgICAgICAgICAvLyBcdTdCODBcdTUzNTVcdTg5QzRcdTUyMTlcdUZGMUFcdTY4MzlcdTYzNkVcdTUxNzNcdTk1MkVcdThCQ0RcdTdFRDlcdTUxRkFcdTYzMDdcdTVGMTVcbiAgICAgICAgICAgICAgbGV0IGFuc3dlciA9ICdcdThGRDlcdTY2MkYgQUkgXHU1NDExXHU1QkZDXHU3Njg0XHU3OTNBXHU0RjhCXHU1NkRFXHU3QjU0XHVGRjFBXHU4QkY3XHU1NzI4XHU3Q0ZCXHU3RURGXHU0RTJEXHU2N0U1XHU2MjdFXHU1QkY5XHU1RTk0XHU1MjlGXHU4MEZEXHU1MTY1XHU1M0UzXHUzMDAyJ1xuICAgICAgICAgICAgICBpZiAoL1x1NEVGQlx1NTJBMXxcdThGREJcdTVFQTYvLnRlc3QocSkpIHtcbiAgICAgICAgICAgICAgICBhbnN3ZXIgPSAnXHU0RUZCXHU1MkExXHU4RkRCXHU1RUE2XHU1M0VGXHU1NzI4XHUyMDFDXHU0RUZCXHU1MkExXHU3QkExXHU3NDA2XHUyMDFEXHU0RTBFXHUyMDFDXHU0RUVBXHU4ODY4XHU3NkQ4XHUyMDFEXHU2N0U1XHU3NzBCXHUzMDAyJ1xuICAgICAgICAgICAgICB9IGVsc2UgaWYgKC9cdTY1RTVcdTYyQTV8XHU2M0QwXHU0RUE0Ly50ZXN0KHEpKSB7XG4gICAgICAgICAgICAgICAgYW5zd2VyID0gJ1x1NjNEMFx1NEVBNFx1NjVFNVx1NjJBNVx1OEJGN1x1OEZEQlx1NTE2NVx1MjAxQ1x1NjVFNVx1NjJBNVx1MjAxRFx1OTg3NVx1OTc2Mlx1RkYwQ1x1NzBCOVx1NTFGQlx1NjVCMFx1NUVGQVx1NTQwRVx1NTg2Qlx1NTE5OVx1NUU3Nlx1NjNEMFx1NEVBNFx1MzAwMidcbiAgICAgICAgICAgICAgfSBlbHNlIGlmICgvXHU3NkVFXHU2ODA3fFx1NjcwOFx1NUVBNi8udGVzdChxKSkge1xuICAgICAgICAgICAgICAgIGFuc3dlciA9ICdcdTY3MDhcdTVFQTZcdTc2RUVcdTY4MDdcdTUzRUZcdTU3MjhcdTIwMUNcdTUyMDZcdTY3OTAvXHU3NkVFXHU2ODA3XHU3QkExXHU3NDA2XHUyMDFEXHU5ODc1XHU4RkRCXHU4ODRDXHU4QkJFXHU3RjZFXHU0RTBFXHU2N0U1XHU3NzBCXHUzMDAyJ1xuICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgIHJlcy5lbmQoSlNPTi5zdHJpbmdpZnkoeyBhbnN3ZXIgfSkpXG4gICAgICAgICAgICB9IGNhdGNoIChlKSB7XG4gICAgICAgICAgICAgIHJlcy5zdGF0dXNDb2RlID0gNDAwXG4gICAgICAgICAgICAgIHJlcy5lbmQoSlNPTi5zdHJpbmdpZnkoeyBlcnJvcjogJ0ludmFsaWQgSlNPTicgfSkpXG4gICAgICAgICAgICB9XG4gICAgICAgICAgfSlcbiAgICAgICAgICByZXR1cm5cbiAgICAgICAgfVxuXG4gICAgICAgIC8vIFNldHRpbmdzOiBcdTgzQjdcdTUzRDZBSVx1OEJCRVx1N0Y2RVxuICAgICAgICBpZiAocmVxLm1ldGhvZCA9PT0gJ0dFVCcgJiYgdXJsLnN0YXJ0c1dpdGgoJy9hcGkvdjEvc2V0dGluZ3MvYWknKSkge1xuICAgICAgICAgIHJlcy5zZXRIZWFkZXIoJ0NvbnRlbnQtVHlwZScsICdhcHBsaWNhdGlvbi9qc29uJylcbiAgICAgICAgICByZXMuZW5kKEpTT04uc3RyaW5naWZ5KGFpU2V0dGluZ3NTdG9yZSkpXG4gICAgICAgICAgcmV0dXJuXG4gICAgICAgIH1cblxuICAgICAgICAvLyBTZXR0aW5nczogXHU0RkREXHU1QjU4QUlcdThCQkVcdTdGNkVcbiAgICAgICAgaWYgKHJlcS5tZXRob2QgPT09ICdQVVQnICYmIHVybC5zdGFydHNXaXRoKCcvYXBpL3YxL3NldHRpbmdzL2FpJykpIHtcbiAgICAgICAgICByZXMuc2V0SGVhZGVyKCdDb250ZW50LVR5cGUnLCAnYXBwbGljYXRpb24vanNvbicpXG4gICAgICAgICAgbGV0IGJvZHkgPSAnJ1xuICAgICAgICAgIHJlcS5vbignZGF0YScsIGNodW5rID0+IHsgYm9keSArPSBjaHVuayB9KVxuICAgICAgICAgIHJlcS5vbignZW5kJywgKCkgPT4ge1xuICAgICAgICAgICAgdHJ5IHtcbiAgICAgICAgICAgICAgY29uc3QgcGF5bG9hZCA9IEpTT04ucGFyc2UoYm9keSB8fCAne30nKVxuICAgICAgICAgICAgICAvLyBcdTY2MjBcdTVDMDRcdTVCNTdcdTZCQjVcdTVFNzZcdTRGRERcdTVCNThcbiAgICAgICAgICAgICAgYWlTZXR0aW5nc1N0b3JlLnByb3ZpZGVyID0gcGF5bG9hZC5wcm92aWRlciA/PyBhaVNldHRpbmdzU3RvcmUucHJvdmlkZXJcbiAgICAgICAgICAgICAgYWlTZXR0aW5nc1N0b3JlLmFwaV9rZXkgPSBwYXlsb2FkLmFwaV9rZXkgPz8gYWlTZXR0aW5nc1N0b3JlLmFwaV9rZXlcbiAgICAgICAgICAgICAgYWlTZXR0aW5nc1N0b3JlLmJhc2VfdXJsID0gcGF5bG9hZC5iYXNlX3VybCA/PyBhaVNldHRpbmdzU3RvcmUuYmFzZV91cmxcbiAgICAgICAgICAgICAgYWlTZXR0aW5nc1N0b3JlLm1vZGVsX25hbWUgPSBwYXlsb2FkLm1vZGVsX25hbWUgPz8gYWlTZXR0aW5nc1N0b3JlLm1vZGVsX25hbWVcbiAgICAgICAgICAgICAgYWlTZXR0aW5nc1N0b3JlLm1heF90b2tlbnMgPSBOdW1iZXIocGF5bG9hZC5tYXhfdG9rZW5zID8/IGFpU2V0dGluZ3NTdG9yZS5tYXhfdG9rZW5zKVxuICAgICAgICAgICAgICBhaVNldHRpbmdzU3RvcmUudGVtcGVyYXR1cmUgPSBOdW1iZXIocGF5bG9hZC50ZW1wZXJhdHVyZSA/PyBhaVNldHRpbmdzU3RvcmUudGVtcGVyYXR1cmUpXG4gICAgICAgICAgICAgIHJlcy5lbmQoSlNPTi5zdHJpbmdpZnkoeyBzdWNjZXNzOiB0cnVlIH0pKVxuICAgICAgICAgICAgfSBjYXRjaCAoZSkge1xuICAgICAgICAgICAgICByZXMuc3RhdHVzQ29kZSA9IDQwMFxuICAgICAgICAgICAgICByZXMuZW5kKEpTT04uc3RyaW5naWZ5KHsgZXJyb3I6ICdJbnZhbGlkIEpTT04nIH0pKVxuICAgICAgICAgICAgfVxuICAgICAgICAgIH0pXG4gICAgICAgICAgcmV0dXJuXG4gICAgICAgIH1cblxuICAgICAgICAvLyBTZXR0aW5nczogXHU4M0I3XHU1M0Q2XHU3Q0ZCXHU3RURGXHU4QkJFXHU3RjZFXG4gICAgICAgIGlmIChyZXEubWV0aG9kID09PSAnR0VUJyAmJiB1cmwuc3RhcnRzV2l0aCgnL2FwaS92MS9zZXR0aW5ncy9zeXN0ZW0nKSkge1xuICAgICAgICAgIHJlcy5zZXRIZWFkZXIoJ0NvbnRlbnQtVHlwZScsICdhcHBsaWNhdGlvbi9qc29uJylcbiAgICAgICAgICByZXMuZW5kKEpTT04uc3RyaW5naWZ5KHN5c3RlbVNldHRpbmdzU3RvcmUpKVxuICAgICAgICAgIHJldHVyblxuICAgICAgICB9XG5cbiAgICAgICAgLy8gU2V0dGluZ3M6IFx1NEZERFx1NUI1OFx1N0NGQlx1N0VERlx1OEJCRVx1N0Y2RVxuICAgICAgICBpZiAocmVxLm1ldGhvZCA9PT0gJ1BVVCcgJiYgdXJsLnN0YXJ0c1dpdGgoJy9hcGkvdjEvc2V0dGluZ3Mvc3lzdGVtJykpIHtcbiAgICAgICAgICByZXMuc2V0SGVhZGVyKCdDb250ZW50LVR5cGUnLCAnYXBwbGljYXRpb24vanNvbicpXG4gICAgICAgICAgbGV0IGJvZHkgPSAnJ1xuICAgICAgICAgIHJlcS5vbignZGF0YScsIGNodW5rID0+IHsgYm9keSArPSBjaHVuayB9KVxuICAgICAgICAgIHJlcS5vbignZW5kJywgKCkgPT4ge1xuICAgICAgICAgICAgdHJ5IHtcbiAgICAgICAgICAgICAgY29uc3QgcGF5bG9hZCA9IEpTT04ucGFyc2UoYm9keSB8fCAne30nKVxuICAgICAgICAgICAgICBzeXN0ZW1TZXR0aW5nc1N0b3JlLnN5c3RlbV9uYW1lID0gcGF5bG9hZC5zeXN0ZW1fbmFtZSA/PyBzeXN0ZW1TZXR0aW5nc1N0b3JlLnN5c3RlbV9uYW1lXG4gICAgICAgICAgICAgIHN5c3RlbVNldHRpbmdzU3RvcmUudGltZXpvbmUgPSBwYXlsb2FkLnRpbWV6b25lID8/IHN5c3RlbVNldHRpbmdzU3RvcmUudGltZXpvbmVcbiAgICAgICAgICAgICAgc3lzdGVtU2V0dGluZ3NTdG9yZS5sYW5ndWFnZSA9IHBheWxvYWQubGFuZ3VhZ2UgPz8gc3lzdGVtU2V0dGluZ3NTdG9yZS5sYW5ndWFnZVxuICAgICAgICAgICAgICBzeXN0ZW1TZXR0aW5nc1N0b3JlLmF1dG9fYW5hbHlzaXMgPSBwYXlsb2FkLmF1dG9fYW5hbHlzaXMgPz8gc3lzdGVtU2V0dGluZ3NTdG9yZS5hdXRvX2FuYWx5c2lzXG4gICAgICAgICAgICAgIHN5c3RlbVNldHRpbmdzU3RvcmUuZGF0YV9yZXRlbnRpb25fZGF5cyA9IE51bWJlcihwYXlsb2FkLmRhdGFfcmV0ZW50aW9uX2RheXMgPz8gc3lzdGVtU2V0dGluZ3NTdG9yZS5kYXRhX3JldGVudGlvbl9kYXlzKVxuICAgICAgICAgICAgICByZXMuZW5kKEpTT04uc3RyaW5naWZ5KHsgc3VjY2VzczogdHJ1ZSB9KSlcbiAgICAgICAgICAgIH0gY2F0Y2ggKGUpIHtcbiAgICAgICAgICAgICAgcmVzLnN0YXR1c0NvZGUgPSA0MDBcbiAgICAgICAgICAgICAgcmVzLmVuZChKU09OLnN0cmluZ2lmeSh7IGVycm9yOiAnSW52YWxpZCBKU09OJyB9KSlcbiAgICAgICAgICAgIH1cbiAgICAgICAgICB9KVxuICAgICAgICAgIHJldHVyblxuICAgICAgICB9XG5cbiAgICAgICAgLy8gU2V0dGluZ3M6IFx1NkQ0Qlx1OEJENUFJXHU4RkRFXHU2M0E1XG4gICAgICAgIGlmIChyZXEubWV0aG9kID09PSAnUE9TVCcgJiYgdXJsLnN0YXJ0c1dpdGgoJy9hcGkvdjEvc2V0dGluZ3MvYWkvdGVzdCcpKSB7XG4gICAgICAgICAgcmVzLnNldEhlYWRlcignQ29udGVudC1UeXBlJywgJ2FwcGxpY2F0aW9uL2pzb24nKVxuICAgICAgICAgIGxldCBib2R5ID0gJydcbiAgICAgICAgICByZXEub24oJ2RhdGEnLCBjaHVuayA9PiB7IGJvZHkgKz0gY2h1bmsgfSlcbiAgICAgICAgICByZXEub24oJ2VuZCcsICgpID0+IHtcbiAgICAgICAgICAgIHRyeSB7XG4gICAgICAgICAgICAgIGNvbnN0IHBheWxvYWQgPSBKU09OLnBhcnNlKGJvZHkgfHwgJ3t9JylcbiAgICAgICAgICAgICAgY29uc3QgaGFzS2V5ID0gISEocGF5bG9hZC5hcGlfa2V5IHx8IGFpU2V0dGluZ3NTdG9yZS5hcGlfa2V5KVxuICAgICAgICAgICAgICBjb25zdCBwcm92aWRlciA9IChwYXlsb2FkLnByb3ZpZGVyIHx8IGFpU2V0dGluZ3NTdG9yZS5wcm92aWRlciB8fCAnJykudG9Mb3dlckNhc2UoKVxuICAgICAgICAgICAgICBjb25zdCBva1Byb3ZpZGVycyA9IFsnb3BlbnJvdXRlcicsICdvcGVuYWknLCAnY2xhdWRlJ11cbiAgICAgICAgICAgICAgY29uc3Qgc3VjY2VzcyA9IGhhc0tleSAmJiBva1Byb3ZpZGVycy5pbmNsdWRlcyhwcm92aWRlcilcbiAgICAgICAgICAgICAgY29uc3QgcmVzcG9uc2VUZXh0ID0gc3VjY2VzcyA/ICdcdTY3MERcdTUyQTFcdTUzRUZcdTc1MjhcdUZGMENcdThCQTRcdThCQzFcdTkwMUFcdThGQzcnIDogJ1x1N0YzQVx1NUMxMVx1NjcwOVx1NjU0OFx1NUJDNlx1OTRBNVx1NjIxNlx1NEUwRFx1NjUyRlx1NjMwMVx1NzY4NFx1NjNEMFx1NEY5Qlx1NTU0NidcbiAgICAgICAgICAgICAgcmVzLmVuZChKU09OLnN0cmluZ2lmeSh7IHN1Y2Nlc3MsIHJlc3BvbnNlOiByZXNwb25zZVRleHQsIG1lc3NhZ2U6IHN1Y2Nlc3MgPyAnT0snIDogJ0ZhaWxlZCcgfSkpXG4gICAgICAgICAgICB9IGNhdGNoIChlKSB7XG4gICAgICAgICAgICAgIHJlcy5zdGF0dXNDb2RlID0gNDAwXG4gICAgICAgICAgICAgIHJlcy5lbmQoSlNPTi5zdHJpbmdpZnkoeyBzdWNjZXNzOiBmYWxzZSwgbWVzc2FnZTogJ0ludmFsaWQgSlNPTicgfSkpXG4gICAgICAgICAgICB9XG4gICAgICAgICAgfSlcbiAgICAgICAgICByZXR1cm5cbiAgICAgICAgfVxuXG4gICAgICAgIC8vIFNldHRpbmdzOiBcdTVCRkNcdTUxRkFcdTY1NzBcdTYzNkVcbiAgICAgICAgaWYgKHJlcS5tZXRob2QgPT09ICdHRVQnICYmIHVybC5zdGFydHNXaXRoKCcvYXBpL3YxL3NldHRpbmdzL2V4cG9ydCcpKSB7XG4gICAgICAgICAgcmVzLnNldEhlYWRlcignQ29udGVudC1UeXBlJywgJ2FwcGxpY2F0aW9uL2pzb24nKVxuICAgICAgICAgIHJlcy5lbmQoSlNPTi5zdHJpbmdpZnkoeyBtZXNzYWdlOiAnXHU2NTcwXHU2MzZFXHU1QkZDXHU1MUZBXHU1QjhDXHU2MjEwXHVGRjA4XHU2QTIxXHU2MkRGXHVGRjA5JyB9KSlcbiAgICAgICAgICByZXR1cm5cbiAgICAgICAgfVxuXG4gICAgICAgIC8vIFNldHRpbmdzOiBcdTZFMDVcdTc0MDZcdTdGMTNcdTVCNThcbiAgICAgICAgaWYgKHJlcS5tZXRob2QgPT09ICdQT1NUJyAmJiB1cmwuc3RhcnRzV2l0aCgnL2FwaS92MS9zZXR0aW5ncy9jbGVhci1jYWNoZScpKSB7XG4gICAgICAgICAgcmVzLnNldEhlYWRlcignQ29udGVudC1UeXBlJywgJ2FwcGxpY2F0aW9uL2pzb24nKVxuICAgICAgICAgIC8vIFx1N0I4MFx1NTM1NVx1NkEyMVx1NjJERlx1RkYxQVx1NEUwRFx1NTA1QVx1NUI5RVx1OTY0NVx1NkUwNVx1NzQwNlxuICAgICAgICAgIHJlcy5lbmQoSlNPTi5zdHJpbmdpZnkoeyBzdWNjZXNzOiB0cnVlIH0pKVxuICAgICAgICAgIHJldHVyblxuICAgICAgICB9XG5cbiAgICAgICAgLy8gU2V0dGluZ3M6IFx1OTFDRFx1N0Y2RVx1OEJCRVx1N0Y2RVxuICAgICAgICBpZiAocmVxLm1ldGhvZCA9PT0gJ1BPU1QnICYmIHVybC5zdGFydHNXaXRoKCcvYXBpL3YxL3NldHRpbmdzL3Jlc2V0JykpIHtcbiAgICAgICAgICByZXMuc2V0SGVhZGVyKCdDb250ZW50LVR5cGUnLCAnYXBwbGljYXRpb24vanNvbicpXG4gICAgICAgICAgT2JqZWN0LmFzc2lnbihhaVNldHRpbmdzU3RvcmUsIGRlZmF1bHRBSVNldHRpbmdzKVxuICAgICAgICAgIE9iamVjdC5hc3NpZ24oc3lzdGVtU2V0dGluZ3NTdG9yZSwgZGVmYXVsdFN5c3RlbVNldHRpbmdzKVxuICAgICAgICAgIHJlcy5lbmQoSlNPTi5zdHJpbmdpZnkoeyBzdWNjZXNzOiB0cnVlIH0pKVxuICAgICAgICAgIHJldHVyblxuICAgICAgICB9XG5cbiAgICAgICAgcmV0dXJuIG5leHQoKVxuICAgICAgfSlcbiAgICB9XG4gIH1cbn1cblxuZXhwb3J0IGRlZmF1bHQgZGVmaW5lQ29uZmlnKCh7IG1vZGUgfSkgPT4ge1xuICBjb25zdCBlbnYgPSBsb2FkRW52KG1vZGUsIHByb2Nlc3MuY3dkKCksICcnKVxuICBjb25zdCB1c2VNb2NrID0gZW52LlZJVEVfVVNFX01PQ0sgPT09ICd0cnVlJyB8fCBlbnYuVVNFX01PQ0sgPT09ICd0cnVlJ1xuICByZXR1cm4ge1xuICAgIHBsdWdpbnM6IHVzZU1vY2tcbiAgICAgID8gW1xuICAgICAgICAgIHZ1ZSgpLFxuICAgICAgICAgIGRldk1vY2tQbHVnaW4oKSxcbiAgICAgICAgICBDb21wb25lbnRzKHtcbiAgICAgICAgICAgIHJlc29sdmVyczogW0ljb25zUmVzb2x2ZXIoeyBjb21wb25lbnRQcmVmaXg6ICdpJyB9KV1cbiAgICAgICAgICB9KSxcbiAgICAgICAgICBJY29ucyh7IGNvbXBpbGVyOiAndnVlMycgfSlcbiAgICAgICAgXVxuICAgICAgOiBbXG4gICAgICAgICAgdnVlKCksXG4gICAgICAgICAgQ29tcG9uZW50cyh7XG4gICAgICAgICAgICByZXNvbHZlcnM6IFtJY29uc1Jlc29sdmVyKHsgY29tcG9uZW50UHJlZml4OiAnaScgfSldXG4gICAgICAgICAgfSksXG4gICAgICAgICAgSWNvbnMoeyBjb21waWxlcjogJ3Z1ZTMnIH0pXG4gICAgICAgIF0sXG4gICAgcmVzb2x2ZToge1xuICAgICAgYWxpYXM6IHtcbiAgICAgICAgJ0AnOiBwYXRoLnJlc29sdmUoX19kaXJuYW1lLCAnc3JjJylcbiAgICAgIH1cbiAgICB9LFxuICAgIHNlcnZlcjoge1xuICAgICAgcG9ydDogMzAwMSxcbiAgICAgIHByb3h5OiB1c2VNb2NrID8ge30gOiB7XG4gICAgICAgICcvYXBpL3YxJzoge1xuICAgICAgICAgIHRhcmdldDogJ2h0dHA6Ly8xMjcuMC4wLjE6ODAwMCcsXG4gICAgICAgICAgY2hhbmdlT3JpZ2luOiB0cnVlXG4gICAgICAgIH1cbiAgICAgIH1cbiAgICB9XG4gIH1cbn0pIl0sCiAgIm1hcHBpbmdzIjog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
