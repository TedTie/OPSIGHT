-- Drop existing policies
drop policy if exists "Authenticated users can upload avatars" on storage.objects;
drop policy if exists "Authenticated users can update avatars" on storage.objects;
drop policy if exists "Authenticated users can delete avatars" on storage.objects;
drop policy if exists "Anyone can upload avatars" on storage.objects;
drop policy if exists "Anyone can update avatars" on storage.objects;
drop policy if exists "Anyone can delete avatars" on storage.objects;
drop policy if exists "Anyone can view avatars" on storage.objects;

-- Create new policies (allow anon key users to upload)
create policy "Anyone can upload avatars"
on storage.objects for insert
to anon, authenticated
with check (bucket_id = 'avatars');

create policy "Anyone can update avatars"
on storage.objects for update
to anon, authenticated
using (bucket_id = 'avatars');

create policy "Anyone can delete avatars"
on storage.objects for delete
to anon, authenticated
using (bucket_id = 'avatars');

create policy "Anyone can view avatars"
on storage.objects for select
to public
using (bucket_id = 'avatars');
