-- Create RPC function to update avatar_url securely using Anon Key
create or replace function update_avatar_url(target_auth_uid uuid, new_avatar_url text)
returns void
language plpgsql
security definer -- Runs with privileges of the creator (admin)
as $$
begin
  update public.user_account
  set avatar_url = new_avatar_url
  where auth_uid = target_auth_uid;
end;
$$;

-- Grant execute permission to anon and authenticated roles
grant execute on function update_avatar_url(uuid, text) to anon;
grant execute on function update_avatar_url(uuid, text) to authenticated;
