-- Add File Storage Schema for Contact Files
-- This script adds tables and functions for managing contact file downloads

-- Table to store contact file metadata
create table if not exists keap.contact_files (
    id bigserial primary key,
    contact_id bigint not null references keap.contacts(id) on delete cascade,
    file_name text not null,
    file_path text not null,
    file_size bigint default 0,
    mime_type text,
    file_hash text not null,
    keap_file_id text,
    created_at timestamptz default now(),
    updated_at timestamptz default now(),
    unique(contact_id, file_hash)
);

-- Indexes for performance
create index if not exists idx_contact_files_contact_id on keap.contact_files(contact_id);
create index if not exists idx_contact_files_file_hash on keap.contact_files(file_hash);
create index if not exists idx_contact_files_created_at on keap.contact_files(created_at);
create index if not exists idx_contact_files_mime_type on keap.contact_files(mime_type);

-- Table to track file download operations
create table if not exists keap.file_download_log (
    id bigserial primary key,
    contact_id bigint not null,
    operation text not null, -- 'sync', 'download', 'metadata_only'
    files_found int default 0,
    files_downloaded int default 0,
    files_skipped int default 0,
    total_size_bytes bigint default 0,
    duration_ms int,
    error_message text,
    created_at timestamptz default now()
);

-- Function to get file statistics
create or replace function keap.get_file_stats()
returns table(
    total_files bigint,
    total_size_bytes bigint,
    total_size_mb numeric,
    contacts_with_files bigint,
    avg_file_size_bytes numeric,
    files_by_type jsonb
) as $$
begin
    return query
    select 
        count(*) as total_files,
        sum(cf.file_size) as total_size_bytes,
        round(sum(cf.file_size) / (1024.0 * 1024.0), 2) as total_size_mb,
        count(distinct cf.contact_id) as contacts_with_files,
        round(avg(cf.file_size), 2) as avg_file_size_bytes,
        jsonb_object_agg(
            coalesce(cf.mime_type, 'unknown'), 
            count(*)
        ) as files_by_type
    from keap.contact_files cf;
end;
$$ language plpgsql;

-- Function to get contact file summary
create or replace function keap.get_contact_file_summary(contact_id_param bigint)
returns table(
    contact_id bigint,
    total_files bigint,
    total_size_bytes bigint,
    file_types jsonb
) as $$
begin
    return query
    select 
        cf.contact_id,
        count(*) as total_files,
        sum(cf.file_size) as total_size_bytes,
        jsonb_object_agg(
            coalesce(cf.mime_type, 'unknown'), 
            count(*)
        ) as file_types
    from keap.contact_files cf
    where cf.contact_id = contact_id_param
    group by cf.contact_id;
end;
$$ language plpgsql;

-- Function to find large files
create or replace function keap.get_large_files(size_threshold_mb int default 10)
returns table(
    contact_id bigint,
    file_name text,
    file_size_bytes bigint,
    file_size_mb numeric,
    mime_type text,
    created_at timestamptz
) as $$
begin
    return query
    select 
        cf.contact_id,
        cf.file_name,
        cf.file_size,
        round(cf.file_size / (1024.0 * 1024.0), 2) as file_size_mb,
        cf.mime_type,
        cf.created_at
    from keap.contact_files cf
    where cf.file_size > (size_threshold_mb * 1024 * 1024)
    order by cf.file_size desc;
end;
$$ language plpgsql;

-- Function to get files by type
create or replace function keap.get_files_by_type(mime_type_param text)
returns table(
    contact_id bigint,
    file_name text,
    file_size_bytes bigint,
    file_path text,
    created_at timestamptz
) as $$
begin
    return query
    select 
        cf.contact_id,
        cf.file_name,
        cf.file_size,
        cf.file_path,
        cf.created_at
    from keap.contact_files cf
    where cf.mime_type = mime_type_param
    order by cf.created_at desc;
end;
$$ language plpgsql;

-- Add comments
comment on table keap.contact_files is 'Metadata for contact file downloads';
comment on table keap.file_download_log is 'Log of file download operations';
comment on function keap.get_file_stats() is 'Get overall file storage statistics';
comment on function keap.get_contact_file_summary(bigint) is 'Get file summary for a specific contact';
comment on function keap.get_large_files(int) is 'Find files larger than specified threshold';
comment on function keap.get_files_by_type(text) is 'Get files of a specific MIME type';
