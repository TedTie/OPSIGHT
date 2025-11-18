create extension if not exists pgcrypto;

create table if not exists public.user_account (
  id uuid primary key default gen_random_uuid(),
  auth_uid uuid unique,
  username text unique not null,
  role text not null check (role in ('user','admin','super_admin')),
  identity_type text,
  group_id int,
  group_name text,
  created_at timestamp with time zone default now()
);

create table if not exists public.groups (
  id bigserial primary key,
  name text unique not null,
  description text,
  created_at timestamp with time zone default now()
);

create table if not exists public.admin_metrics (
  id bigserial primary key,
  key text unique not null,
  name text not null,
  is_active boolean default true,
  default_roles text[] default array[]::text[]
);

create table if not exists public.settings_ai (
  id smallint primary key default 1,
  provider text not null,
  api_key text,
  base_url text not null,
  model_name text not null,
  max_tokens int not null,
  temperature numeric not null
);

create table if not exists public.settings_system (
  id smallint primary key default 1,
  system_name text not null,
  timezone text not null,
  language text not null,
  auto_analysis boolean not null,
  data_retention_days int not null
);

create table if not exists public.monthly_goals (
  id bigserial primary key,
  identity_type text not null,
  scope text not null,
  year int not null,
  month int not null,
  amount_target numeric not null,
  new_sign_target_amount numeric not null,
  referral_target_amount numeric not null,
  renewal_total_target_amount numeric not null,
  upgrade_target_count int not null,
  renewal_target_count int not null,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone
);

create table if not exists public.personal_monthly_goals (
  id bigserial primary key,
  identity_type text not null,
  group_id int,
  user_id uuid references public.user_account(id) on delete set null,
  year int not null,
  month int not null,
  new_sign_target_amount numeric not null default 0,
  referral_target_amount numeric not null default 0,
  renewal_total_target_amount numeric not null default 0,
  upgrade_target_count int not null default 0,
  created_at timestamp with time zone default now()
);

alter table public.user_account enable row level security;
alter table public.groups enable row level security;
alter table public.admin_metrics enable row level security;
alter table public.settings_ai enable row level security;
alter table public.settings_system enable row level security;
alter table public.monthly_goals enable row level security;
alter table public.personal_monthly_goals enable row level security;

create policy user_account_select_authenticated on public.user_account for select using (auth.uid() is not null);
create policy user_account_insert_admin on public.user_account for insert with check (exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin')));
create policy user_account_update_admin on public.user_account for update using (exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin')));

create policy groups_select_authenticated on public.groups for select using (auth.uid() is not null);
create policy groups_write_admin on public.groups for all using (exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin'))) with check (true);

create policy admin_metrics_select_authenticated on public.admin_metrics for select using (auth.uid() is not null);
create policy admin_metrics_write_admin on public.admin_metrics for all using (exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin'))) with check (true);

create policy settings_ai_select_authenticated on public.settings_ai for select using (auth.uid() is not null);
create policy settings_ai_update_admin on public.settings_ai for update using (exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin')));
create policy settings_ai_insert_admin on public.settings_ai for insert with check (exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin')));

create policy settings_system_select_authenticated on public.settings_system for select using (auth.uid() is not null);
create policy settings_system_update_admin on public.settings_system for update using (exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin')));
create policy settings_system_insert_admin on public.settings_system for insert with check (exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin')));

create policy monthly_goals_select_authenticated on public.monthly_goals for select using (auth.uid() is not null);
create policy monthly_goals_write_admin on public.monthly_goals for all using (exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin'))) with check (true);

create policy personal_goals_select_authenticated on public.personal_monthly_goals for select using (auth.uid() is not null);
create policy personal_goals_insert_self_or_admin on public.personal_monthly_goals for insert with check (
  exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and (ua.role in ('admin','super_admin') or ua.id = user_id))
);
create policy personal_goals_update_self_or_admin on public.personal_monthly_goals for update using (
  exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and (ua.role in ('admin','super_admin') or ua.id = user_id))
);

insert into public.settings_ai (id, provider, api_key, base_url, model_name, max_tokens, temperature)
values (1, 'openrouter', '', 'https://openrouter.ai/api/v1', 'openai/gpt-5', 2000, 0.7)
on conflict (id) do update set provider=excluded.provider, api_key=excluded.api_key, base_url=excluded.base_url, model_name=excluded.model_name, max_tokens=excluded.max_tokens, temperature=excluded.temperature;

insert into public.settings_system (id, system_name, timezone, language, auto_analysis, data_retention_days)
values (1, 'KillerApp', 'Asia/Shanghai', 'zh-CN', true, 90)
on conflict (id) do update set system_name=excluded.system_name, timezone=excluded.timezone, language=excluded.language, auto_analysis=excluded.auto_analysis, data_retention_days=excluded.data_retention_days;

insert into public.admin_metrics (key, name, is_active, default_roles) values
('period_sales_amount','期间销售总额', true, array['CC','SS']),
('task_completion_rate','任务完成率', true, array['CC','SS','LP']),
('report_submission_rate','日报提交率', true, array['CC','SS','LP'])
on conflict (key) do nothing;

insert into public.groups (name, description) values
('销售一组',''),('教务一组',''),('产品一组','')
on conflict (name) do nothing;