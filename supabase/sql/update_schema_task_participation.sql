-- Create table for Jielong (Chain) entries
create table if not exists public.task_jielong_entries (
  id bigserial primary key,
  task_id bigint not null references public.tasks(id) on delete cascade,
  user_id uuid not null references public.user_account(id) on delete cascade,
  sequence int not null,
  id_value text,
  remark text,
  intention text,
  custom_field text,
  created_at timestamp with time zone default now()
);

create index if not exists idx_jielong_entries_task_id on public.task_jielong_entries(task_id);
create index if not exists idx_jielong_entries_user_id on public.task_jielong_entries(user_id);

-- Create table for Amount/Quantity records
create table if not exists public.task_records (
  id bigserial primary key,
  task_id bigint not null references public.tasks(id) on delete cascade,
  user_id uuid not null references public.user_account(id) on delete cascade,
  record_type text not null check (record_type in ('amount', 'quantity')),
  value numeric not null,
  remark text,
  created_at timestamp with time zone default now()
);

create index if not exists idx_task_records_task_id on public.task_records(task_id);
create index if not exists idx_task_records_user_id on public.task_records(user_id);

-- Create table for Checkbox completions
create table if not exists public.task_completions (
  id bigserial primary key,
  task_id bigint not null references public.tasks(id) on delete cascade,
  user_id uuid not null references public.user_account(id) on delete cascade,
  is_completed boolean not null default true,
  completed_at timestamp with time zone,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone
);

create unique index if not exists idx_task_completions_task_user on public.task_completions(task_id, user_id);

-- Enable RLS
alter table public.task_jielong_entries enable row level security;
alter table public.task_records enable row level security;
alter table public.task_completions enable row level security;

-- RLS Policies for task_jielong_entries
create policy "Enable read access for authenticated users" on public.task_jielong_entries 
  for select using (auth.uid() is not null);
create policy "Enable insert access for authenticated users" on public.task_jielong_entries 
  for insert with check (auth.uid() is not null);

-- RLS Policies for task_records
create policy "Enable read access for authenticated users" on public.task_records 
  for select using (auth.uid() is not null);
create policy "Enable insert access for authenticated users" on public.task_records 
  for insert with check (auth.uid() is not null);

-- RLS Policies for task_completions
create policy "Enable read access for authenticated users" on public.task_completions 
  for select using (auth.uid() is not null);
create policy "Enable all access for authenticated users" on public.task_completions 
  for all using (auth.uid() is not null) with check (true);
