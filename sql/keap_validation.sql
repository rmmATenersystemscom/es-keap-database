
-- Keap Export Validation Pack (PostgreSQL)
-- Run after each export to verify completeness, relationships, and basic data quality.
-- Assumes the schema from our prior message (schema "keap").

-- 0) Freshness & counts per table
--    Quickly see last update timestamps and counts.
with counts as (
  select 'users'::text tbl, count(*)::bigint n, max(updated_at) as max_updated_at from keap.users
  union all select 'companies', count(*), null from keap.companies
  union all select 'tags', count(*), null from keap.tags
  union all select 'pipelines', count(*), null from keap.pipelines
  union all select 'stages', count(*), null from keap.stages
  union all select 'contacts', count(*), max(updated_at) from keap.contacts
  union all select 'contact_tags', count(*), null from keap.contact_tags
  union all select 'opportunities', count(*), max(updated_at) from keap.opportunities
  union all select 'tasks', count(*), null from keap.tasks
  union all select 'notes', count(*), null from keap.notes
  union all select 'products', count(*), null from keap.products
  union all select 'orders', count(*), null from keap.orders
  union all select 'order_items', count(*), null from keap.order_items
  union all select 'payments', count(*), null from keap.payments
)
select * from counts order by tbl;

-- 1) Referential integrity sanity: orphans (should be zero rows)
--    If any rows return here, relationships were not fully preserved.
-- 1a) contact_tags must reference existing contacts and tags
select 'contact_tags_missing_contact_or_tag' as check, count(*) as orphans
from keap.contact_tags ct
left join keap.contacts c on c.id = ct.contact_id
left join keap.tags t on t.id = ct.tag_id
where c.id is null or t.id is null;

-- 1b) opportunities must reference existing stages/pipelines when set
select 'opps_missing_stage' as check, count(*) as orphans
from keap.opportunities o
left join keap.stages s on s.id = o.stage_id
where o.stage_id is not null and s.id is null;

select 'opps_missing_pipeline' as check, count(*) as orphans
from keap.opportunities o
left join keap.pipelines p on p.id = o.pipeline_id
where o.pipeline_id is not null and p.id is null;

-- 1c) tasks/notes must reference existing contacts/opps when set
select 'tasks_missing_parents' as check, count(*) as orphans
from keap.tasks t
left join keap.contacts c on c.id = t.contact_id
left join keap.opportunities o on o.id = t.opportunity_id
where (t.contact_id is not null and c.id is null)
   or (t.opportunity_id is not null and o.id is null);

select 'notes_missing_parents' as check, count(*) as orphans
from keap.notes n
left join keap.contacts c on c.id = n.contact_id
left join keap.opportunities o on o.id = n.opportunity_id
where (n.contact_id is not null and c.id is null)
   or (n.opportunity_id is not null and o.id is null);

-- 2) Cross-object consistency
-- 2a) Stage's pipeline must match opportunity.pipeline_id (when both present)
select o.id as opportunity_id, o.pipeline_id as opp_pipeline_id, s.pipeline_id as stage_pipeline_id
from keap.opportunities o
join keap.stages s on s.id = o.stage_id
where o.pipeline_id is not null and s.pipeline_id is not null and o.pipeline_id <> s.pipeline_id
limit 100;

-- 3) E‑commerce reconciliation (optional if you don't use orders)
-- 3a) Order items subtotal vs order.total (allowing 1 cent rounding tolerance)
select o.id, o.total,
       sum(coalesce(oi.subtotal, oi.unit_price * oi.qty)) as calc_subtotal,
       (o.total - sum(coalesce(oi.subtotal, oi.unit_price * oi.qty))) as diff
from keap.orders o
left join keap.order_items oi on oi.order_id = o.id
group by o.id, o.total
having abs(o.total - sum(coalesce(oi.subtotal, oi.unit_price * oi.qty))) > 0.01
order by abs(o.total - sum(coalesce(oi.subtotal, oi.unit_price * oi.qty))) desc
limit 100;

-- 3b) Payments should not exceed order total (flags overpayments/refunds to review)
select o.id, o.total, coalesce(sum(p.amount),0) as paid
from keap.orders o
left join keap.payments p on p.order_id = o.id
group by o.id, o.total
having coalesce(sum(p.amount),0) > o.total + 0.01
order by coalesce(sum(p.amount),0) - o.total desc
limit 100;

-- 4) Duplicate detection (contacts by primary-like emails)
with emails as (
  select c.id, lower((e->>'email')) as email
  from keap.contacts c
  cross join lateral jsonb_array_elements(c.emails) e
  where (e->>'email') is not null
    and coalesce(e->>'email','') <> ''
    and coalesce(e->>'field','') in ('EMAIL1','EMAIL','PRIMARY','Work','work','Other','Primary')
)
select email, count(*) as dupes, array_agg(id order by id) as contact_ids
from emails
group by email
having count(*) > 1
order by dupes desc
limit 100;

-- 5) Coverage metrics (sanity ratios)
select
  (select count(*) from keap.contacts) as contacts,
  (select count(*) from keap.contact_tags) as tag_links,
  (select count(*) from keap.opportunities) as opportunities,
  (select count(*) from keap.tasks) as tasks,
  (select count(*) from keap.notes) as notes;

select
  (select count(distinct contact_id) from keap.contact_tags) as contacts_with_tags,
  (select count(distinct contact_id) from keap.opportunities) as contacts_with_opps,
  (select count(distinct contact_id) from keap.tasks) as contacts_with_tasks;

-- 6) Required fields sanity
select id from keap.companies where coalesce(name,'') = '' limit 100;
select id from keap.contacts where coalesce(given_name,'') = '' and coalesce(family_name,'') = '' limit 100;

-- 7) JSON shape consistency (example: if 'raw' has email list but parsed array empty)
select id
from keap.contacts
where raw ? 'email_addresses' and (emails is null or jsonb_array_length(emails) = 0)
limit 100;

-- 8) Random spot‑check set to compare against Keap UI
select c.id, c.given_name, c.family_name,
       coalesce((select count(*) from keap.contact_tags ct where ct.contact_id=c.id),0) as tag_count,
       coalesce((select count(*) from keap.opportunities o where o.contact_id=c.id),0) as opp_count,
       coalesce((select count(*) from keap.tasks t where t.contact_id=c.id),0) as task_count
from keap.contacts c
order by random()
limit 20;
