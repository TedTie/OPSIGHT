-- ============================================
-- Performance Optimization Indexes
-- ============================================
-- This script creates indexes to improve query performance
-- across the KillerApp database.
--
-- Expected improvements:
-- - Reduce query time by 3-10x for filtered queries
-- - Speed up JOIN operations
-- - Improve sorting and pagination performance
-- ============================================

-- Daily Reports Table Indexes
-- Used frequently for filtering by date and user
CREATE INDEX IF NOT EXISTS idx_daily_reports_created_by 
  ON daily_reports(created_by);

CREATE INDEX IF NOT EXISTS idx_daily_reports_work_date 
  ON daily_reports(work_date);

-- Composite index for date range queries with user filter
CREATE INDEX IF NOT EXISTS idx_daily_reports_work_date_created_by 
  ON daily_reports(work_date, created_by);

-- For sorting by created_at (recent reports)
CREATE INDEX IF NOT EXISTS idx_daily_reports_created_at 
  ON daily_reports(created_at DESC);

-- User Account Table Indexes
-- Used for filtering users by group and identity
CREATE INDEX IF NOT EXISTS idx_user_account_group_id 
  ON user_account(group_id);

CREATE INDEX IF NOT EXISTS idx_user_account_identity_type 
  ON user_account(identity_type);

-- Username lookups (for authentication and profile queries)
CREATE INDEX IF NOT EXISTS idx_user_account_username 
  ON user_account(username);

-- Legacy ID for backwards compatibility lookups
CREATE INDEX IF NOT EXISTS idx_user_account_legacy_id 
  ON user_account(legacy_id) 
  WHERE legacy_id IS NOT NULL;

-- Tasks Table Indexes
-- Used for filtering by assignee and status
CREATE INDEX IF NOT EXISTS idx_tasks_assignee_id 
  ON tasks(assignee_id);

CREATE INDEX IF NOT EXISTS idx_tasks_status 
  ON tasks(status);

CREATE INDEX IF NOT EXISTS idx_tasks_updated_at 
  ON tasks(updated_at DESC);

-- Composite index for date range + status queries
CREATE INDEX IF NOT EXISTS idx_tasks_updated_at_status 
  ON tasks(updated_at, status);

-- For created_by queries (if the column exists)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'tasks' AND column_name = 'created_by'
  ) THEN
    CREATE INDEX IF NOT EXISTS idx_tasks_created_by ON tasks(created_by);
  END IF;
END $$;

-- Performance Table Indexes (if exists)
-- Used for monthly performance reports
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_name = 'performance_table'
  ) THEN
    EXECUTE 'CREATE INDEX IF NOT EXISTS idx_performance_user_id ON performance_table(user_id)';
    EXECUTE 'CREATE INDEX IF NOT EXISTS idx_performance_report_month ON performance_table(report_month)';
    EXECUTE 'CREATE INDEX IF NOT EXISTS idx_performance_user_month ON performance_table(user_id, report_month)';
  END IF;
END $$;

-- Knowledge Base Indexes
-- Used for filtering knowledge items
CREATE INDEX IF NOT EXISTS idx_knowledge_items_module_type 
  ON knowledge_items(module_type)
  WHERE module_type IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_knowledge_items_category 
  ON knowledge_items(category)
  WHERE category IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_knowledge_items_status 
  ON knowledge_items(status)
  WHERE status IS NOT NULL;

-- For file attachments lookup
CREATE INDEX IF NOT EXISTS idx_knowledge_files_knowledge_id 
  ON knowledge_files(knowledge_id);

-- AI Features Indexes (if tables exist)
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ai_agents') THEN
    CREATE INDEX IF NOT EXISTS idx_ai_agents_created_at ON ai_agents(created_at DESC);
  END IF;
  
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ai_functions') THEN
    CREATE INDEX IF NOT EXISTS idx_ai_functions_created_at ON ai_functions(created_at DESC);
  END IF;
  
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ai_features') THEN
    CREATE INDEX IF NOT EXISTS idx_ai_features_created_at ON ai_features(created_at DESC);
  END IF;
END $$;

-- ============================================
-- Verification Query
-- ============================================
-- Run this to verify all indexes were created successfully:
-- 
-- SELECT
--   schemaname,
--   tablename,
--   indexname,
--   indexdef
-- FROM pg_indexes
-- WHERE schemaname = 'public'
--   AND indexname LIKE 'idx_%'
-- ORDER BY tablename, indexname;
-- ============================================

-- Print completion message
DO $$
BEGIN
  RAISE NOTICE 'Performance indexes created successfully!';
  RAISE NOTICE 'Run ANALYZE on tables to update query planner statistics.';
END $$;

-- Update statistics for query planner
ANALYZE daily_reports;
ANALYZE user_account;
ANALYZE tasks;
ANALYZE knowledge_items;
ANALYZE knowledge_files;
