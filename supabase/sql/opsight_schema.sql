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

create table if not exists public.tasks (
  id bigserial primary key,
  title text not null,
  description text,
  type text,
  status text,
  priority int,
  assignee_id uuid references public.user_account(id) on delete set null,
  group_id int,
  identity_type text,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone
);

alter table public.tasks alter column priority type text using priority::text;
alter table public.tasks add column if not exists task_type text;
alter table public.tasks add column if not exists assignment_type text;
alter table public.tasks alter column assignment_type set default 'all';
alter table public.tasks add column if not exists assigned_group_ids int[];
alter table public.tasks add column if not exists assigned_user_ids uuid[];
alter table public.tasks add column if not exists target_amount numeric;
alter table public.tasks add column if not exists current_amount numeric default 0;
alter table public.tasks add column if not exists target_quantity int;
alter table public.tasks add column if not exists current_quantity int default 0;
alter table public.tasks add column if not exists jielong_target_count int;
alter table public.tasks add column if not exists jielong_current_count int default 0;
alter table public.tasks add column if not exists jielong_config jsonb;
alter table public.tasks add column if not exists is_completed boolean default false;
alter table public.tasks add column if not exists due_date timestamp with time zone;
alter table public.tasks add column if not exists tags jsonb default '[]'::jsonb;
alter table public.tasks alter column status set default 'pending';
alter table public.tasks add column if not exists participant_count int default 0;
alter table public.tasks add column if not exists completed_count int default 0;
alter table public.tasks add column if not exists target_group_id int;
alter table public.tasks add column if not exists target_group_name text;
alter table public.tasks add column if not exists assigned_to_username text;
alter table public.tasks add column if not exists target_identity text;
alter table public.tasks add column if not exists completion_note text;
alter table public.tasks add column if not exists completed_amount numeric;
alter table public.tasks add column if not exists completed_quantity int;

create index if not exists idx_tasks_assigned_group_ids on public.tasks using gin (assigned_group_ids);
create index if not exists idx_tasks_assigned_user_ids on public.tasks using gin (assigned_user_ids);
create index if not exists idx_tasks_tags on public.tasks using gin (tags);

update public.tasks set assignment_type = 'all' where assignment_type is null;
update public.tasks set status = coalesce(status, 'pending');

alter table public.user_account enable row level security;
alter table public.groups enable row level security;
alter table public.admin_metrics enable row level security;
alter table public.settings_ai enable row level security;
alter table public.settings_system enable row level security;
alter table public.monthly_goals enable row level security;
alter table public.personal_monthly_goals enable row level security;
alter table public.tasks enable row level security;
alter table public.user_account add column if not exists legacy_id bigserial unique;
update public.user_account set legacy_id = nextval('public.user_account_legacy_id_seq') where legacy_id is null;
alter table public.user_account add column if not exists is_active boolean default true;
update public.user_account set is_active = true where is_active is null;
alter table public.user_account add column if not exists hashed_password text;

drop policy if exists user_account_select_authenticated on public.user_account;
drop policy if exists user_account_insert_admin on public.user_account;
drop policy if exists user_account_update_admin on public.user_account;
create policy user_account_select_authenticated on public.user_account for select using (auth.uid() is not null);
create policy user_account_insert_admin on public.user_account for insert with check (exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin')));
create policy user_account_update_admin on public.user_account for update using (exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin')));

drop policy if exists groups_select_authenticated on public.groups;
drop policy if exists groups_write_admin on public.groups;
create policy groups_select_authenticated on public.groups for select using (auth.uid() is not null);
create policy groups_write_admin on public.groups for all using (exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin'))) with check (true);

drop policy if exists admin_metrics_select_authenticated on public.admin_metrics;
drop policy if exists admin_metrics_write_admin on public.admin_metrics;
create policy admin_metrics_select_authenticated on public.admin_metrics for select using (auth.uid() is not null);
create policy admin_metrics_write_admin on public.admin_metrics for all using (exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin'))) with check (true);

drop policy if exists settings_ai_select_authenticated on public.settings_ai;
drop policy if exists settings_ai_update_admin on public.settings_ai;
drop policy if exists settings_ai_insert_admin on public.settings_ai;
create policy settings_ai_select_authenticated on public.settings_ai for select using (auth.uid() is not null);
create policy settings_ai_update_admin on public.settings_ai for update using (exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin')));
create policy settings_ai_insert_admin on public.settings_ai for insert with check (exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin')));

drop policy if exists settings_system_select_authenticated on public.settings_system;
drop policy if exists settings_system_update_admin on public.settings_system;
drop policy if exists settings_system_insert_admin on public.settings_system;
create policy settings_system_select_authenticated on public.settings_system for select using (auth.uid() is not null);
create policy settings_system_update_admin on public.settings_system for update using (exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin')));
create policy settings_system_insert_admin on public.settings_system for insert with check (exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin')));

drop policy if exists monthly_goals_select_authenticated on public.monthly_goals;
drop policy if exists monthly_goals_write_admin on public.monthly_goals;
create policy monthly_goals_select_authenticated on public.monthly_goals for select using (auth.uid() is not null);
create policy monthly_goals_write_admin on public.monthly_goals for all using (exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin'))) with check (true);

drop policy if exists personal_goals_select_authenticated on public.personal_monthly_goals;
drop policy if exists personal_goals_insert_self_or_admin on public.personal_monthly_goals;
drop policy if exists personal_goals_update_self_or_admin on public.personal_monthly_goals;
create policy personal_goals_select_authenticated on public.personal_monthly_goals for select using (auth.uid() is not null);
create policy personal_goals_insert_self_or_admin on public.personal_monthly_goals for insert with check (
  exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and (ua.role in ('admin','super_admin') or ua.id = user_id))
);
create policy personal_goals_update_self_or_admin on public.personal_monthly_goals for update using (
  exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and (ua.role in ('admin','super_admin') or ua.id = user_id))
);

drop policy if exists tasks_select_authenticated on public.tasks;
drop policy if exists tasks_write_admin on public.tasks;
create policy tasks_select_authenticated on public.tasks for select using (auth.uid() is not null);
create policy tasks_write_admin on public.tasks for all using (
  exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin'))
) with check (true);

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

create table if not exists public.daily_reports (
  id bigserial primary key,
  work_date date not null,
  title text not null,
  content text,
  work_hours numeric,
  task_progress text,
  work_summary text,
  mood_score int,
  efficiency_score int,
  call_count int,
  call_duration int,
  achievements text,
  challenges text,
  tomorrow_plan text,
  ai_analysis jsonb,
  created_by uuid references public.user_account(id) on delete set null,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone
);

alter table public.daily_reports add column if not exists actual_amount numeric default 0;
alter table public.daily_reports add column if not exists new_sign_amount numeric default 0;
alter table public.daily_reports add column if not exists new_sign_count int default 0;
alter table public.daily_reports add column if not exists referral_amount numeric default 0;
alter table public.daily_reports add column if not exists referral_count int default 0;
alter table public.daily_reports add column if not exists renewal_amount numeric default 0;
alter table public.daily_reports add column if not exists upgrade_amount numeric default 0;
alter table public.daily_reports add column if not exists renewal_count int default 0;
alter table public.daily_reports add column if not exists upgrade_count int default 0;

create table if not exists public.knowledge_items (
  id bigserial primary key,
  module_type text not null,
  title text not null,
  content text,
  category text,
  status text,
  created_by uuid references public.user_account(id) on delete set null,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone
);

alter table public.knowledge_items add column if not exists description text;
alter table public.knowledge_items add column if not exists is_public boolean default false;
alter table public.knowledge_items add column if not exists tags jsonb default '[]'::jsonb;
alter table public.knowledge_items add column if not exists view_count int default 0;

create table if not exists public.knowledge_files (
  id bigserial primary key,
  knowledge_id bigint references public.knowledge_items(id) on delete cascade,
  filename text,
  size bigint,
  mime text,
  url text,
  created_at timestamp with time zone default now()
);

create index if not exists idx_knowledge_files_kid on public.knowledge_files(knowledge_id);

create table if not exists public.knowledge_categories (
  id bigserial primary key,
  module_type text not null,
  name text not null,
  created_at timestamp with time zone default now()
);

create table if not exists public.ai_agents (
  id bigserial primary key,
  name text not null,
  description text,
  is_active boolean default true,
  created_at timestamp with time zone default now()
);

create table if not exists public.ai_functions (
  id bigserial primary key,
  name text not null,
  description text,
  config jsonb,
  is_active boolean default true,
  created_at timestamp with time zone default now()
);

create table if not exists public.ai_features (
  id bigserial primary key,
  key text unique not null,
  name text not null,
  is_active boolean default true,
  created_at timestamp with time zone default now()
);

create table if not exists public.notifications (
  id bigserial primary key,
  title text not null,
  content text,
  group_id int,
  created_at timestamp with time zone default now()
);

create table if not exists public.notification_reads (
  id bigserial primary key,
  notification_id bigint references public.notifications(id) on delete cascade,
  user_id uuid references public.user_account(id) on delete cascade,
  created_at timestamp with time zone default now()
);

alter table public.daily_reports enable row level security;
alter table public.knowledge_items enable row level security;
alter table public.knowledge_files enable row level security;
alter table public.knowledge_categories enable row level security;
alter table public.ai_agents enable row level security;
alter table public.ai_functions enable row level security;
alter table public.ai_features enable row level security;
alter table public.notifications enable row level security;
alter table public.notification_reads enable row level security;

drop policy if exists daily_reports_select_authenticated on public.daily_reports;
drop policy if exists daily_reports_write_self_or_admin on public.daily_reports;
create policy daily_reports_select_authenticated on public.daily_reports for select using (auth.uid() is not null);
create policy daily_reports_write_self_or_admin on public.daily_reports for all using (
  exists (
    select 1 from public.user_account ua where ua.auth_uid = auth.uid() and (
      ua.role in ('admin','super_admin') or ua.id = created_by
    )
  )
) with check (true);

drop policy if exists knowledge_items_select_authenticated on public.knowledge_items;
drop policy if exists knowledge_items_write_admin on public.knowledge_items;
create policy knowledge_items_select_authenticated on public.knowledge_items for select using (auth.uid() is not null);
create policy knowledge_items_write_admin on public.knowledge_items for all using (
  exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin'))
) with check (true);

drop policy if exists knowledge_files_select_authenticated on public.knowledge_files;
drop policy if exists knowledge_files_write_admin on public.knowledge_files;
create policy knowledge_files_select_authenticated on public.knowledge_files for select using (auth.uid() is not null);
create policy knowledge_files_write_admin on public.knowledge_files for all using (
  exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin'))
) with check (true);

drop policy if exists knowledge_categories_select_authenticated on public.knowledge_categories;
drop policy if exists knowledge_categories_write_admin on public.knowledge_categories;
create policy knowledge_categories_select_authenticated on public.knowledge_categories for select using (auth.uid() is not null);
create policy knowledge_categories_write_admin on public.knowledge_categories for all using (
  exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin'))
) with check (true);

drop policy if exists ai_agents_select_authenticated on public.ai_agents;
drop policy if exists ai_agents_write_admin on public.ai_agents;
create policy ai_agents_select_authenticated on public.ai_agents for select using (auth.uid() is not null);
create policy ai_agents_write_admin on public.ai_agents for all using (
  exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin'))
) with check (true);

drop policy if exists ai_functions_select_authenticated on public.ai_functions;
drop policy if exists ai_functions_write_admin on public.ai_functions;
create policy ai_functions_select_authenticated on public.ai_functions for select using (auth.uid() is not null);
create policy ai_functions_write_admin on public.ai_functions for all using (
  exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin'))
) with check (true);

drop policy if exists ai_features_select_authenticated on public.ai_features;
drop policy if exists ai_features_write_admin on public.ai_features;
create policy ai_features_select_authenticated on public.ai_features for select using (auth.uid() is not null);
create policy ai_features_write_admin on public.ai_features for all using (
  exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin'))
) with check (true);

drop policy if exists notifications_select_authenticated on public.notifications;
drop policy if exists notifications_write_admin on public.notifications;
create policy notifications_select_authenticated on public.notifications for select using (auth.uid() is not null);
create policy notifications_write_admin on public.notifications for all using (
  exists (select 1 from public.user_account ua where ua.auth_uid = auth.uid() and ua.role in ('admin','super_admin'))
) with check (true);

drop policy if exists notification_reads_select_authenticated on public.notification_reads;
drop policy if exists notification_reads_write_authenticated on public.notification_reads;
create policy notification_reads_select_authenticated on public.notification_reads for select using (auth.uid() is not null);
create policy notification_reads_write_authenticated on public.notification_reads for all using (auth.uid() is not null) with check (true);

alter table public.user_account add column if not exists legacy_id bigserial unique;
update public.user_account set legacy_id = nextval('public.user_account_legacy_id_seq') where legacy_id is null;
alter table public.user_account add column if not exists is_active boolean default true;
update public.user_account set is_active = true where is_active is null;
alter table public.user_account add column if not exists hashed_password text;
