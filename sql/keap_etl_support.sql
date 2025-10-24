
-- Keap Export ETL Support Objects (PostgreSQL)
-- Use these to log runs, capture per-endpoint page metrics, and snapshot table counts/checksums.

create schema if not exists keap_meta;

create table if not exists keap_meta.etl_run_log (
  id bigserial primary key,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  status text check (status in ('running','success','error')) default 'running',
  notes text
);

create table if not exists keap_meta.etl_request_log (
  id bigserial primary key,
  run_id bigint references keap_meta.etl_run_log(id) on delete cascade,
  endpoint text not null,
  page_offset int,
  page_limit int,
  http_status int,
  item_count int,
  duration_ms int,
  throttled boolean default false,
  error text,
  created_at timestamptz default now()
);

-- Optional: record how many items you retrieved per logical entity
create table if not exists keap_meta.source_counts (
  run_id bigint references keap_meta.etl_run_log(id) on delete cascade,
  entity text not null,        -- e.g., 'contacts', 'companies', ...
  items_retrieved bigint not null,
  primary key (run_id, entity)
);

create table if not exists keap_meta.table_snapshot (
  id bigserial primary key,
  run_id bigint references keap_meta.etl_run_log(id) on delete cascade,
  schema_name text not null,
  table_name  text not null,
  row_count bigint not null,
  id_min bigint,
  id_max bigint,
  checksum_md5 text,
  taken_at timestamptz not null default now(),
  unique (run_id, schema_name, table_name)
);

-- NOTE: For very large tables, checksum aggregation using string_agg can be memory heavy.
-- This digest function is fine for small/medium tables; for huge tables consider sampling or rolling hashes.
create or replace function keap_meta.table_digest(_schema text, _table text)
returns table(row_count bigint, id_min bigint, id_max bigint, checksum_md5 text)
language plpgsql as $$
declare
  sql text;
  has_id_col boolean;
begin
  -- Check if table has an 'id' column
  select exists(
    select 1 from information_schema.columns 
    where table_schema = _schema and table_name = _table and column_name = 'id'
  ) into has_id_col;
  
  if has_id_col then
    -- Standard table with id column
    sql := format($f$
      select count(*)::bigint as row_count,
             min(id)::bigint as id_min,
             max(id)::bigint as id_max,
             md5(string_agg(id::text, ',' order by id)) as checksum_md5
      from %I.%I
    $f$, _schema, _table);
  else
    -- Table without id column (like contact_tags with composite PK)
    sql := format($f$
      select count(*)::bigint as row_count,
             null::bigint as id_min,
             null::bigint as id_max,
             md5(string_agg(ctid::text, ',' order by ctid)) as checksum_md5
      from %I.%I
    $f$, _schema, _table);
  end if;
  
  return query execute sql;
end $$;

-- Procedure snippet to snapshot all keap.* tables for the *current run* (assumes a row was inserted into etl_run_log).
-- Execute after your exporter finishes loading.
-- Example usage:
--   insert into keap_meta.etl_run_log(status) values ('running') returning id;  -- capture run id in your app
--   ... export work ...
--   -- then run this block (set the run id as needed)
--   do $$ begin perform 1; end $$;
--   update keap_meta.etl_run_log set status='success', finished_at=now() where id = <run_id>;
do $$
declare t record;
declare _run_id bigint;
begin
  -- Use the latest run id by default; set explicitly in production from your app.
  select id into _run_id from keap_meta.etl_run_log order by id desc limit 1;

  for t in
    select table_schema, table_name
    from information_schema.tables
    where table_schema='keap' and table_type='BASE TABLE'
  loop
    insert into keap_meta.table_snapshot(run_id, schema_name, table_name, row_count, id_min, id_max, checksum_md5)
    select _run_id, t.table_schema, t.table_name, s.*
    from keap_meta.table_digest(t.table_schema, t.table_name) s;
  end loop;
end $$;

-- Compare this run's table counts to the previous run (basic regression check)
with ranked as (
  select table_name, row_count, run_id,
         row_number() over (partition by table_name order by run_id desc) as rn
  from keap_meta.table_snapshot
  where schema_name='keap'
)
select cur.table_name,
       cur.row_count as current_rows,
       prev.row_count as previous_rows,
       (cur.row_count - coalesce(prev.row_count,0)) as delta
from ranked cur
left join ranked prev
  on prev.table_name = cur.table_name and prev.rn = 2
where cur.rn = 1
order by cur.table_name;
