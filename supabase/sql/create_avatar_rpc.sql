-- Drop the old function first to avoid ambiguity
drop function if exists update_avatar_url(uuid, text);

-- Create RPC function to update avatar_url securely using Username (more reliable than auth_uid)
create or replace function update_avatar_url(target_username text, new_avatar_url text)
returns void
language plpgsql
security definer -- Runs with privileges of the creator (admin)
as $$
begin
  update public.user_account
  set avatar_url = new_avatar_url
  where username = target_username;
end;
$$;

-- Grant execute permission to anon and authenticated roles
grant execute on function update_avatar_url(text, text) to anon;
grant execute on function update_avatar_url(text, text) to authenticated;
