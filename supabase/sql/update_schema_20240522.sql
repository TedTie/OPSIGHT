-- Add missing columns for Analytics Dashboard

-- 1. Add columns to daily_reports
ALTER TABLE public.daily_reports ADD COLUMN IF NOT EXISTS new_sign_amount numeric DEFAULT 0;
ALTER TABLE public.daily_reports ADD COLUMN IF NOT EXISTS new_sign_count int DEFAULT 0;
ALTER TABLE public.daily_reports ADD COLUMN IF NOT EXISTS referral_amount numeric DEFAULT 0;
ALTER TABLE public.daily_reports ADD COLUMN IF NOT EXISTS referral_count int DEFAULT 0;
ALTER TABLE public.daily_reports ADD COLUMN IF NOT EXISTS renewal_amount numeric DEFAULT 0;
ALTER TABLE public.daily_reports ADD COLUMN IF NOT EXISTS upgrade_amount numeric DEFAULT 0;
ALTER TABLE public.daily_reports ADD COLUMN IF NOT EXISTS renewal_count int DEFAULT 0;
ALTER TABLE public.daily_reports ADD COLUMN IF NOT EXISTS upgrade_count int DEFAULT 0;

-- 2. Add columns to monthly_goals
ALTER TABLE public.monthly_goals ADD COLUMN IF NOT EXISTS new_sign_target_amount numeric DEFAULT 0;
ALTER TABLE public.monthly_goals ADD COLUMN IF NOT EXISTS referral_target_amount numeric DEFAULT 0;
ALTER TABLE public.monthly_goals ADD COLUMN IF NOT EXISTS renewal_total_target_amount numeric DEFAULT 0;
ALTER TABLE public.monthly_goals ADD COLUMN IF NOT EXISTS upgrade_target_count int DEFAULT 0;
ALTER TABLE public.monthly_goals ADD COLUMN IF NOT EXISTS renewal_target_count int DEFAULT 0;

-- 3. Add columns to personal_monthly_goals
ALTER TABLE public.personal_monthly_goals ADD COLUMN IF NOT EXISTS new_sign_target_amount numeric DEFAULT 0;
ALTER TABLE public.personal_monthly_goals ADD COLUMN IF NOT EXISTS referral_target_amount numeric DEFAULT 0;
ALTER TABLE public.personal_monthly_goals ADD COLUMN IF NOT EXISTS renewal_total_target_amount numeric DEFAULT 0;
ALTER TABLE public.personal_monthly_goals ADD COLUMN IF NOT EXISTS upgrade_target_count int DEFAULT 0;

-- 4. Add columns to user_account if missing (for security)
ALTER TABLE public.user_account ADD COLUMN IF NOT EXISTS hashed_password text;
ALTER TABLE public.user_account ADD COLUMN IF NOT EXISTS is_active boolean DEFAULT true;
