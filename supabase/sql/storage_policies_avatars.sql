-- Storage policies for avatars bucket

-- Allow anyone with anon key to upload avatars
create policy "Anyone can upload avatars"
on storage.objects for insert
to anon, authenticated
with check (bucket_id = 'avatars');

-- Allow anyone with anon key to update avatars
create policy "Anyone can update avatars"
on storage.objects for update
to anon, authenticated
using (bucket_id = 'avatars');

-- Allow anyone with anon key to delete avatars
create policy "Anyone can delete avatars"
on storage.objects for delete
to anon, authenticated
using (bucket_id = 'avatars');

-- Allow everyone to read avatars (public access)
create policy "Anyone can view avatars"
on storage.objects for select
to public
using (bucket_id = 'avatars');
