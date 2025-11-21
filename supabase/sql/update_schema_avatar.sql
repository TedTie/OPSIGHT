-- Add avatar_url to users table (used by Python Backend)
ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS avatar_url TEXT;

-- Add avatar_url to user_account table (used by Supabase Edge Functions / Analytics)
ALTER TABLE IF EXISTS user_account ADD COLUMN IF NOT EXISTS avatar_url TEXT;
