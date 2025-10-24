-- Add Resume Capability to ETL System
-- This script adds tables and functions to support resuming interrupted syncs

-- Table to track sync progress for each entity
create table if not exists keap_meta.sync_progress (
    id bigserial primary key,
    run_id bigint references keap_meta.etl_run_log(id) on delete cascade,
    entity text not null,
    status text check (status in ('pending', 'running', 'completed', 'failed')) default 'pending',
    started_at timestamptz,
    completed_at timestamptz,
    last_page_offset int default 0,
    last_page_limit int default 1000,
    total_pages_processed int default 0,
    total_items_processed int default 0,
    error_message text,
    created_at timestamptz default now(),
    updated_at timestamptz default now(),
    unique(run_id, entity)
);

-- Table to track checkpoint data for each entity
create table if not exists keap_meta.sync_checkpoints (
    id bigserial primary key,
    run_id bigint references keap_meta.etl_run_log(id) on delete cascade,
    entity text not null,
    checkpoint_type text check (checkpoint_type in ('page', 'batch', 'entity')) not null,
    checkpoint_data jsonb not null,
    created_at timestamptz default now(),
    unique(run_id, entity, checkpoint_type)
);

-- Indexes for performance
create index if not exists idx_sync_progress_run_entity on keap_meta.sync_progress(run_id, entity);
create index if not exists idx_sync_progress_status on keap_meta.sync_progress(status);
create index if not exists idx_sync_checkpoints_run_entity on keap_meta.sync_checkpoints(run_id, entity);

-- Function to get the last successful run for an entity
create or replace function keap_meta.get_last_successful_run(entity_name text)
returns bigint as $$
declare
    last_run_id bigint;
begin
    select rl.id into last_run_id
    from keap_meta.etl_run_log rl
    join keap_meta.sync_progress sp on sp.run_id = rl.id
    where sp.entity = entity_name
      and sp.status = 'completed'
      and rl.status = 'success'
    order by rl.started_at desc
    limit 1;
    
    return coalesce(last_run_id, 0);
end;
$$ language plpgsql;

-- Function to get the last checkpoint for an entity
create or replace function keap_meta.get_last_checkpoint(run_id_param bigint, entity_name text, checkpoint_type_param text)
returns jsonb as $$
declare
    checkpoint_data jsonb;
begin
    select sc.checkpoint_data into checkpoint_data
    from keap_meta.sync_checkpoints sc
    where sc.run_id = run_id_param
      and sc.entity = entity_name
      and sc.checkpoint_type = checkpoint_type_param
    order by sc.created_at desc
    limit 1;
    
    return coalesce(checkpoint_data, '{}'::jsonb);
end;
$$ language plpgsql;

-- Function to save a checkpoint
create or replace function keap_meta.save_checkpoint(
    run_id_param bigint,
    entity_name text,
    checkpoint_type_param text,
    checkpoint_data_param jsonb
)
returns void as $$
begin
    insert into keap_meta.sync_checkpoints (run_id, entity, checkpoint_type, checkpoint_data)
    values (run_id_param, entity_name, checkpoint_type_param, checkpoint_data_param)
    on conflict (run_id, entity, checkpoint_type) 
    do update set 
        checkpoint_data = excluded.checkpoint_data,
        created_at = now();
end;
$$ language plpgsql;

-- Function to update sync progress
create or replace function keap_meta.update_sync_progress(
    run_id_param bigint,
    entity_name text,
    status_param text,
    page_offset_param int default null,
    items_processed_param int default null,
    error_msg text default null
)
returns void as $$
begin
    insert into keap_meta.sync_progress (
        run_id, entity, status, started_at, last_page_offset, total_items_processed, error_message
    )
    values (
        run_id_param, entity_name, status_param, 
        case when status_param = 'running' then now() else null end,
        coalesce(page_offset_param, 0),
        coalesce(items_processed_param, 0),
        error_msg
    )
    on conflict (run_id, entity) 
    do update set 
        status = excluded.status,
        started_at = case when excluded.status = 'running' and sync_progress.started_at is null then now() else sync_progress.started_at end,
        completed_at = case when excluded.status in ('completed', 'failed') then now() else sync_progress.completed_at end,
        last_page_offset = coalesce(excluded.last_page_offset, sync_progress.last_page_offset),
        total_items_processed = coalesce(excluded.total_items_processed, sync_progress.total_items_processed),
        error_message = coalesce(excluded.error_message, sync_progress.error_message),
        updated_at = now();
end;
$$ language plpgsql;

-- Function to get entities that need to be resumed
create or replace function keap_meta.get_entities_to_resume(run_id_param bigint)
returns table(entity_name text, last_page_offset int, last_page_limit int) as $$
begin
    return query
    select sp.entity, sp.last_page_offset, sp.last_page_limit
    from keap_meta.sync_progress sp
    where sp.run_id = run_id_param
      and sp.status in ('pending', 'running', 'failed')
    order by sp.created_at;
end;
$$ language plpgsql;

-- Add comments
comment on table keap_meta.sync_progress is 'Tracks the progress of each entity sync within a run';
comment on table keap_meta.sync_checkpoints is 'Stores checkpoint data for resuming interrupted syncs';
comment on function keap_meta.get_last_successful_run(text) is 'Returns the last successful run ID for an entity';
comment on function keap_meta.get_last_checkpoint(bigint, text, text) is 'Returns the last checkpoint data for an entity';
comment on function keap_meta.save_checkpoint(bigint, text, text, jsonb) is 'Saves a checkpoint for an entity';
comment on function keap_meta.update_sync_progress(bigint, text, text, int, int, text) is 'Updates sync progress for an entity';
comment on function keap_meta.get_entities_to_resume(bigint) is 'Returns entities that need to be resumed';
