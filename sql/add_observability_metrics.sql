-- Add Comprehensive Observability Metrics
-- This script adds tables and functions for detailed monitoring and analytics

-- Enhanced request log with more detailed metrics
create table if not exists keap_meta.etl_request_metrics (
    id bigserial primary key,
    run_id bigint references keap_meta.etl_run_log(id) on delete cascade,
    entity text not null,
    endpoint text not null,
    page_offset int,
    page_limit int,
    http_status int,
    item_count int,
    duration_ms int,
    throttle_remaining int,
    throttle_reset_time timestamptz,
    throttle_type text,
    retry_count int default 0,
    error_message text,
    response_size_bytes int,
    created_at timestamptz default now()
);

-- Performance metrics per entity
create table if not exists keap_meta.entity_performance (
    id bigserial primary key,
    run_id bigint references keap_meta.etl_run_log(id) on delete cascade,
    entity text not null,
    total_pages int,
    total_items int,
    total_duration_ms int,
    avg_page_duration_ms numeric,
    min_page_duration_ms int,
    max_page_duration_ms int,
    throttle_hits int default 0,
    retry_attempts int default 0,
    error_count int default 0,
    throughput_items_per_second numeric,
    created_at timestamptz default now()
);

-- Throttle tracking for detailed analysis
create table if not exists keap_meta.throttle_events (
    id bigserial primary key,
    run_id bigint references keap_meta.etl_run_log(id) on delete cascade,
    entity text not null,
    endpoint text not null,
    throttle_type text not null,
    throttle_remaining int,
    throttle_reset_time timestamptz,
    wait_time_ms int,
    created_at timestamptz default now()
);

-- Error tracking with categorization
create table if not exists keap_meta.error_events (
    id bigserial primary key,
    run_id bigint references keap_meta.etl_run_log(id) on delete cascade,
    entity text not null,
    endpoint text,
    error_type text not null,
    error_message text not null,
    error_context jsonb,
    retry_count int default 0,
    resolved boolean default false,
    created_at timestamptz default now()
);

-- System health metrics
create table if not exists keap_meta.system_health (
    id bigserial primary key,
    run_id bigint references keap_meta.etl_run_log(id) on delete cascade,
    metric_name text not null,
    metric_value numeric not null,
    metric_unit text,
    tags jsonb,
    recorded_at timestamptz default now()
);

-- Indexes for performance
create index if not exists idx_etl_request_metrics_run_entity on keap_meta.etl_request_metrics(run_id, entity);
create index if not exists idx_etl_request_metrics_endpoint on keap_meta.etl_request_metrics(endpoint);
create index if not exists idx_etl_request_metrics_created_at on keap_meta.etl_request_metrics(created_at);
create index if not exists idx_entity_performance_run_entity on keap_meta.entity_performance(run_id, entity);
create index if not exists idx_throttle_events_run_entity on keap_meta.throttle_events(run_id, entity);
create index if not exists idx_error_events_run_entity on keap_meta.error_events(run_id, entity);
create index if not exists idx_system_health_run_metric on keap_meta.system_health(run_id, metric_name);

-- Function to calculate entity performance metrics
create or replace function keap_meta.calculate_entity_performance(
    run_id_param bigint,
    entity_name text
)
returns void as $$
declare
    total_pages int;
    total_items int;
    total_duration_ms int;
    avg_page_duration_ms numeric;
    min_page_duration_ms int;
    max_page_duration_ms int;
    throttle_hits int;
    retry_attempts int;
    error_count int;
    throughput_items_per_second numeric;
begin
    -- Calculate metrics from request log
    select 
        count(*),
        sum(item_count),
        sum(duration_ms),
        avg(duration_ms),
        min(duration_ms),
        max(duration_ms),
        count(case when throttle_remaining < 100 then 1 end),
        sum(retry_count),
        count(case when error_message is not null then 1 end)
    into 
        total_pages,
        total_items,
        total_duration_ms,
        avg_page_duration_ms,
        min_page_duration_ms,
        max_page_duration_ms,
        throttle_hits,
        retry_attempts,
        error_count
    from keap_meta.etl_request_metrics
    where run_id = run_id_param and entity = entity_name;
    
    -- Calculate throughput
    if total_duration_ms > 0 then
        throughput_items_per_second := (total_items * 1000.0) / total_duration_ms;
    else
        throughput_items_per_second := 0;
    end if;
    
    -- Insert or update performance metrics
    insert into keap_meta.entity_performance (
        run_id, entity, total_pages, total_items, total_duration_ms,
        avg_page_duration_ms, min_page_duration_ms, max_page_duration_ms,
        throttle_hits, retry_attempts, error_count, throughput_items_per_second
    )
    values (
        run_id_param, entity_name, total_pages, total_items, total_duration_ms,
        avg_page_duration_ms, min_page_duration_ms, max_page_duration_ms,
        throttle_hits, retry_attempts, error_count, throughput_items_per_second
    )
    on conflict (run_id, entity) do update set
        total_pages = excluded.total_pages,
        total_items = excluded.total_items,
        total_duration_ms = excluded.total_duration_ms,
        avg_page_duration_ms = excluded.avg_page_duration_ms,
        min_page_duration_ms = excluded.min_page_duration_ms,
        max_page_duration_ms = excluded.max_page_duration_ms,
        throttle_hits = excluded.throttle_hits,
        retry_attempts = excluded.retry_attempts,
        error_count = excluded.error_count,
        throughput_items_per_second = excluded.throughput_items_per_second,
        created_at = now();
end;
$$ language plpgsql;

-- Function to get performance summary for a run
create or replace function keap_meta.get_run_performance_summary(run_id_param bigint)
returns table(
    entity text,
    total_pages int,
    total_items int,
    total_duration_ms int,
    avg_page_duration_ms numeric,
    throttle_hits int,
    error_count int,
    throughput_items_per_second numeric
) as $$
begin
    return query
    select 
        ep.entity,
        ep.total_pages,
        ep.total_items,
        ep.total_duration_ms,
        ep.avg_page_duration_ms,
        ep.throttle_hits,
        ep.error_count,
        ep.throughput_items_per_second
    from keap_meta.entity_performance ep
    where ep.run_id = run_id_param
    order by ep.total_items desc;
end;
$$ language plpgsql;

-- Function to get throttle analysis
create or replace function keap_meta.get_throttle_analysis(run_id_param bigint)
returns table(
    entity text,
    endpoint text,
    throttle_type text,
    throttle_events int,
    avg_throttle_remaining numeric,
    total_wait_time_ms int
) as $$
begin
    return query
    select 
        te.entity,
        te.endpoint,
        te.throttle_type,
        count(*) as throttle_events,
        avg(te.throttle_remaining) as avg_throttle_remaining,
        sum(te.wait_time_ms) as total_wait_time_ms
    from keap_meta.throttle_events te
    where te.run_id = run_id_param
    group by te.entity, te.endpoint, te.throttle_type
    order by throttle_events desc;
end;
$$ language plpgsql;

-- Function to get error analysis
create or replace function keap_meta.get_error_analysis(run_id_param bigint)
returns table(
    entity text,
    error_type text,
    error_count int,
    sample_error_message text
) as $$
begin
    return query
    select 
        ee.entity,
        ee.error_type,
        count(*) as error_count,
        (array_agg(ee.error_message))[1] as sample_error_message
    from keap_meta.error_events ee
    where ee.run_id = run_id_param
    group by ee.entity, ee.error_type
    order by error_count desc;
end;
$$ language plpgsql;

-- Add comments
comment on table keap_meta.etl_request_metrics is 'Detailed metrics for each API request';
comment on table keap_meta.entity_performance is 'Performance metrics aggregated per entity';
comment on table keap_meta.throttle_events is 'Detailed tracking of throttle events';
comment on table keap_meta.error_events is 'Categorized error tracking';
comment on table keap_meta.system_health is 'System health and resource metrics';
comment on function keap_meta.calculate_entity_performance(bigint, text) is 'Calculates and stores performance metrics for an entity';
comment on function keap_meta.get_run_performance_summary(bigint) is 'Returns performance summary for a run';
comment on function keap_meta.get_throttle_analysis(bigint) is 'Returns throttle analysis for a run';
comment on function keap_meta.get_error_analysis(bigint) is 'Returns error analysis for a run';
