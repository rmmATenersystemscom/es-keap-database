-- Add Custom Fields to Keap Tables
-- This script adds additional fields found in the raw Keap API data
-- that aren't currently captured in the standard schema

-- Add custom fields to contacts table
ALTER TABLE keap.contacts 
ADD COLUMN IF NOT EXISTS middle_name text,
ADD COLUMN IF NOT EXISTS email_status text,
ADD COLUMN IF NOT EXISTS email_opted_in boolean,
ADD COLUMN IF NOT EXISTS score_value numeric,
ADD COLUMN IF NOT EXISTS tag_ids jsonb,
ADD COLUMN IF NOT EXISTS email_addresses jsonb,
ADD COLUMN IF NOT EXISTS phone_numbers jsonb,
ADD COLUMN IF NOT EXISTS addresses jsonb;

-- Add custom fields to companies table
ALTER TABLE keap.companies 
ADD COLUMN IF NOT EXISTS website text,
ADD COLUMN IF NOT EXISTS phone_numbers jsonb,
ADD COLUMN IF NOT EXISTS addresses jsonb,
ADD COLUMN IF NOT EXISTS custom_fields jsonb;

-- Add custom fields to opportunities table
ALTER TABLE keap.opportunities 
ADD COLUMN IF NOT EXISTS custom_fields jsonb,
ADD COLUMN IF NOT EXISTS stage_moves jsonb,
ADD COLUMN IF NOT EXISTS notes jsonb;

-- Add custom fields to tasks table
ALTER TABLE keap.tasks 
ADD COLUMN IF NOT EXISTS custom_fields jsonb,
ADD COLUMN IF NOT EXISTS reminder_time timestamptz,
ADD COLUMN IF NOT EXISTS priority text;

-- Add custom fields to notes table
ALTER TABLE keap.notes 
ADD COLUMN IF NOT EXISTS custom_fields jsonb,
ADD COLUMN IF NOT EXISTS note_type text;

-- Add custom fields to products table
ALTER TABLE keap.products 
ADD COLUMN IF NOT EXISTS custom_fields jsonb,
ADD COLUMN IF NOT EXISTS product_family text,
ADD COLUMN IF NOT EXISTS subscription_plan_id bigint;

-- Add custom fields to orders table
ALTER TABLE keap.orders 
ADD COLUMN IF NOT EXISTS custom_fields jsonb,
ADD COLUMN IF NOT EXISTS order_status text,
ADD COLUMN IF NOT EXISTS payment_status text,
ADD COLUMN IF NOT EXISTS shipping_address jsonb,
ADD COLUMN IF NOT EXISTS billing_address jsonb;

-- Create indexes on commonly queried custom fields
CREATE INDEX IF NOT EXISTS idx_contacts_email_status ON keap.contacts(email_status);
CREATE INDEX IF NOT EXISTS idx_contacts_email_opted_in ON keap.contacts(email_opted_in);
CREATE INDEX IF NOT EXISTS idx_contacts_score_value ON keap.contacts(score_value);
CREATE INDEX IF NOT EXISTS idx_opportunities_custom_fields ON keap.opportunities USING GIN(custom_fields);
CREATE INDEX IF NOT EXISTS idx_contacts_tag_ids ON keap.contacts USING GIN(tag_ids);

-- Add comments to document the custom fields
COMMENT ON COLUMN keap.contacts.middle_name IS 'Middle name from Keap contact data';
COMMENT ON COLUMN keap.contacts.email_status IS 'Email marketing status (SingleOptIn, NonMarketable, Invalid, etc.)';
COMMENT ON COLUMN keap.contacts.email_opted_in IS 'Whether contact has opted in to email marketing';
COMMENT ON COLUMN keap.contacts.score_value IS 'Contact score value from Keap scoring system';
COMMENT ON COLUMN keap.contacts.tag_ids IS 'Array of tag IDs associated with this contact';
COMMENT ON COLUMN keap.contacts.email_addresses IS 'Array of email addresses (JSONB)';
COMMENT ON COLUMN keap.contacts.phone_numbers IS 'Array of phone numbers with types (JSONB)';
COMMENT ON COLUMN keap.contacts.addresses IS 'Array of addresses (billing, shipping, etc.) (JSONB)';
COMMENT ON COLUMN keap.companies.website IS 'Company website URL';
COMMENT ON COLUMN keap.companies.phone_numbers IS 'Array of company phone numbers (JSONB)';
COMMENT ON COLUMN keap.companies.addresses IS 'Array of company addresses (JSONB)';
COMMENT ON COLUMN keap.companies.custom_fields IS 'Custom fields specific to this company (JSONB)';
COMMENT ON COLUMN keap.opportunities.custom_fields IS 'Custom fields specific to this opportunity (JSONB)';
COMMENT ON COLUMN keap.opportunities.stage_moves IS 'History of stage moves (JSONB)';
COMMENT ON COLUMN keap.opportunities.notes IS 'Additional notes (JSONB)';
COMMENT ON COLUMN keap.tasks.custom_fields IS 'Custom fields specific to this task (JSONB)';
COMMENT ON COLUMN keap.tasks.reminder_time IS 'Reminder time for the task';
COMMENT ON COLUMN keap.tasks.priority IS 'Task priority level';
COMMENT ON COLUMN keap.notes.custom_fields IS 'Custom fields specific to this note (JSONB)';
COMMENT ON COLUMN keap.notes.note_type IS 'Type of note (call, email, meeting, etc.)';
COMMENT ON COLUMN keap.products.custom_fields IS 'Custom fields specific to this product (JSONB)';
COMMENT ON COLUMN keap.products.product_family IS 'Product family or category';
COMMENT ON COLUMN keap.products.subscription_plan_id IS 'Associated subscription plan ID';
COMMENT ON COLUMN keap.orders.custom_fields IS 'Custom fields specific to this order (JSONB)';
COMMENT ON COLUMN keap.orders.order_status IS 'Current order status';
COMMENT ON COLUMN keap.orders.payment_status IS 'Payment status';
COMMENT ON COLUMN keap.orders.shipping_address IS 'Shipping address (JSONB)';
COMMENT ON COLUMN keap.orders.billing_address IS 'Billing address (JSONB)';
