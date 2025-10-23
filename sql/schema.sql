-- Keap Export Database Schema (PostgreSQL)
-- Complete schema for all Keap entities with relationships and constraints

-- Create keap schema
create schema if not exists keap;

-- Reference Tables (loaded first)
-- Users/Owners
create table if not exists keap.users (
    id bigint primary key,
    given_name text,
    family_name text,
    email text,
    created_at timestamptz,
    updated_at timestamptz,
    raw jsonb not null
);

-- Pipelines
create table if not exists keap.pipelines (
    id bigint primary key,
    name text not null,
    created_at timestamptz,
    updated_at timestamptz,
    raw jsonb not null
);

-- Stages
create table if not exists keap.stages (
    id bigint primary key,
    name text not null,
    pipeline_id bigint references keap.pipelines(id),
    created_at timestamptz,
    updated_at timestamptz,
    raw jsonb not null
);

-- Tags
create table if not exists keap.tags (
    id bigint primary key,
    name text not null,
    description text,
    created_at timestamptz,
    updated_at timestamptz,
    raw jsonb not null
);

-- Core Business Tables
-- Companies
create table if not exists keap.companies (
    id bigint primary key,
    name text not null,
    website text,
    phone text,
    address text,
    city text,
    state text,
    postal_code text,
    country_code text,
    created_at timestamptz,
    updated_at timestamptz,
    raw jsonb not null
);

-- Contacts
create table if not exists keap.contacts (
    id bigint primary key,
    company_id bigint references keap.companies(id),
    given_name text,
    family_name text,
    email text,
    phone text,
    address text,
    city text,
    state text,
    postal_code text,
    country_code text,
    owner_id bigint references keap.users(id),
    created_at timestamptz,
    updated_at timestamptz,
    raw jsonb not null
);

-- Contact Tags (many-to-many junction)
create table if not exists keap.contact_tags (
    contact_id bigint references keap.contacts(id) on delete cascade,
    tag_id bigint references keap.tags(id) on delete cascade,
    created_at timestamptz,
    raw jsonb not null,
    primary key (contact_id, tag_id)
);

-- Sales Pipeline Tables
-- Opportunities/Deals
create table if not exists keap.opportunities (
    id bigint primary key,
    contact_id bigint references keap.contacts(id),
    company_id bigint references keap.companies(id),
    name text not null,
    stage_id bigint references keap.stages(id),
    pipeline_id bigint references keap.pipelines(id),
    value decimal(15,2),
    owner_id bigint references keap.users(id),
    created_at timestamptz,
    updated_at timestamptz,
    raw jsonb not null
);

-- Tasks
create table if not exists keap.tasks (
    id bigint primary key,
    contact_id bigint references keap.contacts(id),
    opportunity_id bigint references keap.opportunities(id),
    title text not null,
    description text,
    due_date timestamptz,
    completed_date timestamptz,
    owner_id bigint references keap.users(id),
    created_at timestamptz,
    updated_at timestamptz,
    raw jsonb not null
);

-- Notes
create table if not exists keap.notes (
    id bigint primary key,
    contact_id bigint references keap.contacts(id),
    opportunity_id bigint references keap.opportunities(id),
    title text,
    body text,
    owner_id bigint references keap.users(id),
    created_at timestamptz,
    updated_at timestamptz,
    raw jsonb not null
);

-- E-commerce Tables
-- Products
create table if not exists keap.products (
    id bigint primary key,
    name text not null,
    description text,
    price decimal(15,2),
    sku text,
    active boolean default true,
    created_at timestamptz,
    updated_at timestamptz,
    raw jsonb not null
);

-- Orders
create table if not exists keap.orders (
    id bigint primary key,
    contact_id bigint references keap.contacts(id),
    order_number text,
    order_date timestamptz,
    total decimal(15,2),
    status text,
    created_at timestamptz,
    updated_at timestamptz,
    raw jsonb not null
);

-- Order Items
create table if not exists keap.order_items (
    id bigint primary key,
    order_id bigint references keap.orders(id) on delete cascade,
    product_id bigint references keap.products(id),
    name text not null,
    description text,
    unit_price decimal(15,2),
    quantity decimal(10,2),
    subtotal decimal(15,2),
    created_at timestamptz,
    updated_at timestamptz,
    raw jsonb not null
);

-- Payments
create table if not exists keap.payments (
    id bigint primary key,
    order_id bigint references keap.orders(id),
    amount decimal(15,2) not null,
    payment_date timestamptz,
    payment_method text,
    status text,
    created_at timestamptz,
    updated_at timestamptz,
    raw jsonb not null
);

-- Indexes for performance
create index if not exists idx_contacts_company_id on keap.contacts(company_id);
create index if not exists idx_contacts_owner_id on keap.contacts(owner_id);
create index if not exists idx_contacts_updated_at on keap.contacts(updated_at);
create index if not exists idx_contact_tags_contact_id on keap.contact_tags(contact_id);
create index if not exists idx_contact_tags_tag_id on keap.contact_tags(tag_id);
create index if not exists idx_opportunities_contact_id on keap.opportunities(contact_id);
create index if not exists idx_opportunities_company_id on keap.opportunities(company_id);
create index if not exists idx_opportunities_stage_id on keap.opportunities(stage_id);
create index if not exists idx_opportunities_pipeline_id on keap.opportunities(pipeline_id);
create index if not exists idx_opportunities_updated_at on keap.opportunities(updated_at);
create index if not exists idx_tasks_contact_id on keap.tasks(contact_id);
create index if not exists idx_tasks_opportunity_id on keap.tasks(opportunity_id);
create index if not exists idx_tasks_owner_id on keap.tasks(owner_id);
create index if not exists idx_notes_contact_id on keap.notes(contact_id);
create index if not exists idx_notes_opportunity_id on keap.notes(opportunity_id);
create index if not exists idx_notes_owner_id on keap.notes(owner_id);
create index if not exists idx_orders_contact_id on keap.orders(contact_id);
create index if not exists idx_order_items_order_id on keap.order_items(order_id);
create index if not exists idx_order_items_product_id on keap.order_items(product_id);
create index if not exists idx_payments_order_id on keap.payments(order_id);

-- Comments for documentation
comment on schema keap is 'Keap CRM data export schema with full relationship preservation';
comment on table keap.contacts is 'Contact records with company and owner relationships';
comment on table keap.companies is 'Company records';
comment on table keap.contact_tags is 'Many-to-many relationship between contacts and tags';
comment on table keap.opportunities is 'Sales opportunities/deals with pipeline and stage relationships';
comment on table keap.tasks is 'Tasks linked to contacts or opportunities';
comment on table keap.notes is 'Notes linked to contacts or opportunities';
comment on table keap.products is 'Product catalog';
comment on table keap.orders is 'Customer orders';
comment on table keap.order_items is 'Order line items';
comment on table keap.payments is 'Order payments';