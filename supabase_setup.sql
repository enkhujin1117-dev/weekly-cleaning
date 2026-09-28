create table if not exists kv (
  key text primary key,
  value jsonb not null
);
alter table kv enable row level security;  -- policy uguhgui: zuvhun service_role key ashiglana
