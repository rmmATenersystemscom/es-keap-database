-- Foreign Key Validation Script
-- This script validates all foreign key relationships in the Keap database
-- Run this after any data changes to ensure referential integrity

-- Check for orphaned records in all tables with foreign keys
-- This query should return 0 rows if all foreign keys are valid

SELECT 'Orphaned contact_tags' as table_name, COUNT(*) as orphan_count
FROM keap.contact_tags ct
LEFT JOIN keap.contacts c ON c.id = ct.contact_id
LEFT JOIN keap.tags t ON t.id = ct.tag_id
WHERE c.id IS NULL OR t.id IS NULL

UNION ALL

SELECT 'Orphaned contacts', COUNT(*)
FROM keap.contacts c
LEFT JOIN keap.companies co ON co.id = c.company_id
LEFT JOIN keap.users u ON u.id = c.owner_id
WHERE (c.company_id IS NOT NULL AND co.id IS NULL) 
   OR (c.owner_id IS NOT NULL AND u.id IS NULL)

UNION ALL

SELECT 'Orphaned opportunities', COUNT(*)
FROM keap.opportunities o
LEFT JOIN keap.contacts c ON c.id = o.contact_id
LEFT JOIN keap.companies co ON co.id = o.company_id
LEFT JOIN keap.users u ON u.id = o.owner_id
LEFT JOIN keap.pipelines p ON p.id = o.pipeline_id
LEFT JOIN keap.stages s ON s.id = o.stage_id
WHERE (o.contact_id IS NOT NULL AND c.id IS NULL)
   OR (o.company_id IS NOT NULL AND co.id IS NULL)
   OR (o.owner_id IS NOT NULL AND u.id IS NULL)
   OR (o.pipeline_id IS NOT NULL AND p.id IS NULL)
   OR (o.stage_id IS NOT NULL AND s.id IS NULL)

UNION ALL

SELECT 'Orphaned tasks', COUNT(*)
FROM keap.tasks t
LEFT JOIN keap.contacts c ON c.id = t.contact_id
LEFT JOIN keap.opportunities o ON o.id = t.opportunity_id
LEFT JOIN keap.users u ON u.id = t.owner_id
WHERE (t.contact_id IS NOT NULL AND c.id IS NULL)
   OR (t.opportunity_id IS NOT NULL AND o.id IS NULL)
   OR (t.owner_id IS NOT NULL AND u.id IS NULL)

UNION ALL

SELECT 'Orphaned notes', COUNT(*)
FROM keap.notes n
LEFT JOIN keap.contacts c ON c.id = n.contact_id
LEFT JOIN keap.opportunities o ON o.id = n.opportunity_id
LEFT JOIN keap.users u ON u.id = n.owner_id
WHERE (n.contact_id IS NOT NULL AND c.id IS NULL)
   OR (n.opportunity_id IS NOT NULL AND o.id IS NULL)
   OR (n.owner_id IS NOT NULL AND u.id IS NULL)

UNION ALL

SELECT 'Orphaned orders', COUNT(*)
FROM keap.orders o
LEFT JOIN keap.contacts c ON c.id = o.contact_id
WHERE o.contact_id IS NOT NULL AND c.id IS NULL

UNION ALL

SELECT 'Orphaned order_items', COUNT(*)
FROM keap.order_items oi
LEFT JOIN keap.orders o ON o.id = oi.order_id
LEFT JOIN keap.products p ON p.id = oi.product_id
WHERE (oi.order_id IS NOT NULL AND o.id IS NULL)
   OR (oi.product_id IS NOT NULL AND p.id IS NULL)

UNION ALL

SELECT 'Orphaned payments', COUNT(*)
FROM keap.payments p
LEFT JOIN keap.orders o ON o.id = p.order_id
WHERE p.order_id IS NOT NULL AND o.id IS NULL

UNION ALL

SELECT 'Orphaned stages', COUNT(*)
FROM keap.stages s
LEFT JOIN keap.pipelines p ON p.id = s.pipeline_id
WHERE s.pipeline_id IS NOT NULL AND p.id IS NULL;

-- Summary: If all counts are 0, the database has referential integrity
-- If any counts are > 0, there are orphaned records that need to be cleaned up
