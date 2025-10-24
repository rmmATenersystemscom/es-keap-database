from __future__ import annotations
import json
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import Dict, Any, Optional
from .config import Settings

def get_conn(cfg: Settings):
    """Get database connection."""
    return psycopg2.connect(
        host=cfg.db_host, 
        port=cfg.db_port, 
        dbname=cfg.db_name, 
        user=cfg.db_user, 
        password=cfg.db_password
    )

def to_jsonb(obj: Any) -> psycopg2.extras.Json:
    """Convert Python object to psycopg2 Json object for JSONB storage."""
    def json_serializer(o):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(o, datetime):
            return o.isoformat()
        raise TypeError(f"Object of type {type(o)} is not JSON serializable")
    
    # psycopg2.extras.Json will handle the JSON serialization automatically
    # We just need to ensure datetime objects are converted first
    serialized = json.loads(json.dumps(obj, ensure_ascii=False, default=json_serializer))
    return psycopg2.extras.Json(serialized)

def upsert_user(conn, row: Dict[str, Any]) -> None:
    """Upsert a user/owner record."""
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into keap.users (id, given_name, family_name, email, created_at, updated_at, raw)
            values (%(id)s, %(given_name)s, %(family_name)s, %(email)s, %(created_at)s, %(updated_at)s, %(raw)s)
            on conflict (id) do update set
                given_name=excluded.given_name,
                family_name=excluded.family_name,
                email=excluded.email,
                created_at=excluded.created_at,
                updated_at=excluded.updated_at,
                raw=excluded.raw
            """,
            row,
        )

def upsert_pipeline(conn, row: Dict[str, Any]) -> None:
    """Upsert a pipeline record."""
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into keap.pipelines (id, name, created_at, updated_at, raw)
            values (%(id)s, %(name)s, %(created_at)s, %(updated_at)s, %(raw)s)
            on conflict (id) do update set
                name=excluded.name,
                created_at=excluded.created_at,
                updated_at=excluded.updated_at,
                raw=excluded.raw
            """,
            row,
        )

def upsert_stage(conn, row: Dict[str, Any]) -> None:
    """Upsert a stage record."""
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into keap.stages (id, name, pipeline_id, created_at, updated_at, raw)
            values (%(id)s, %(name)s, %(pipeline_id)s, %(created_at)s, %(updated_at)s, %(raw)s)
            on conflict (id) do update set
                name=excluded.name,
                pipeline_id=excluded.pipeline_id,
                created_at=excluded.created_at,
                updated_at=excluded.updated_at,
                raw=excluded.raw
            """,
            row,
        )

def upsert_tag(conn, row: Dict[str, Any]) -> None:
    """Upsert a tag record."""
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into keap.tags (id, name, description, created_at, updated_at, raw)
            values (%(id)s, %(name)s, %(description)s, %(created_at)s, %(updated_at)s, %(raw)s)
            on conflict (id) do update set
                name=excluded.name,
                description=excluded.description,
                created_at=excluded.created_at,
                updated_at=excluded.updated_at,
                raw=excluded.raw
            """,
            row,
        )

def upsert_company(conn, row: Dict[str, Any]) -> None:
    """Upsert a company record."""
    # Convert datetime objects to strings for PostgreSQL
    processed_row = row.copy()
    if processed_row.get('created_at') and isinstance(processed_row['created_at'], datetime):
        processed_row['created_at'] = processed_row['created_at'].isoformat()
    if processed_row.get('updated_at') and isinstance(processed_row['updated_at'], datetime):
        processed_row['updated_at'] = processed_row['updated_at'].isoformat()
    
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into keap.companies (id, name, website, phone, address, city, state, postal_code, country_code, created_at, updated_at, raw)
            values (%(id)s, %(name)s, %(website)s, %(phone)s, %(address)s, %(city)s, %(state)s, %(postal_code)s, %(country_code)s, %(created_at)s, %(updated_at)s, %(raw)s)
            on conflict (id) do update set
                name=excluded.name,
                website=excluded.website,
                phone=excluded.phone,
                address=excluded.address,
                city=excluded.city,
                state=excluded.state,
                postal_code=excluded.postal_code,
                country_code=excluded.country_code,
                created_at=excluded.created_at,
                updated_at=excluded.updated_at,
                raw=excluded.raw
            """,
            processed_row,
        )

def upsert_contact(conn, row: Dict[str, Any]) -> None:
    """Upsert a contact record."""
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into keap.contacts (id, company_id, given_name, family_name, email, phone, address, city, state, postal_code, country_code, owner_id, middle_name, email_status, email_opted_in, score_value, tag_ids, email_addresses, phone_numbers, addresses, created_at, updated_at, raw)
            values (%(id)s, %(company_id)s, %(given_name)s, %(family_name)s, %(email)s, %(phone)s, %(address)s, %(city)s, %(state)s, %(postal_code)s, %(country_code)s, %(owner_id)s, %(middle_name)s, %(email_status)s, %(email_opted_in)s, %(score_value)s, %(tag_ids)s, %(email_addresses)s, %(phone_numbers)s, %(addresses)s, %(created_at)s, %(updated_at)s, %(raw)s)
            on conflict (id) do update set
                company_id=excluded.company_id,
                given_name=excluded.given_name,
                family_name=excluded.family_name,
                email=excluded.email,
                phone=excluded.phone,
                address=excluded.address,
                city=excluded.city,
                state=excluded.state,
                postal_code=excluded.postal_code,
                country_code=excluded.country_code,
                owner_id=excluded.owner_id,
                middle_name=excluded.middle_name,
                email_status=excluded.email_status,
                email_opted_in=excluded.email_opted_in,
                score_value=excluded.score_value,
                tag_ids=excluded.tag_ids,
                email_addresses=excluded.email_addresses,
                phone_numbers=excluded.phone_numbers,
                addresses=excluded.addresses,
                created_at=excluded.created_at,
                updated_at=excluded.updated_at,
                raw=excluded.raw
            """,
            row,
        )

def upsert_contact_tag(conn, row: Dict[str, Any]) -> None:
    """Upsert a contact-tag relationship."""
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into keap.contact_tags (contact_id, tag_id, created_at, raw)
            values (%(contact_id)s, %(tag_id)s, %(created_at)s, %(raw)s)
            on conflict (contact_id, tag_id) do update set
                created_at=excluded.created_at,
                raw=excluded.raw
            """,
            row,
        )

def upsert_opportunity(conn, row: Dict[str, Any]) -> None:
    """Upsert an opportunity/deal record."""
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into keap.opportunities (id, contact_id, company_id, name, stage_id, pipeline_id, value, owner_id, created_at, updated_at, raw)
            values (%(id)s, %(contact_id)s, %(company_id)s, %(name)s, %(stage_id)s, %(pipeline_id)s, %(value)s, %(owner_id)s, %(created_at)s, %(updated_at)s, %(raw)s)
            on conflict (id) do update set
                contact_id=excluded.contact_id,
                company_id=excluded.company_id,
                name=excluded.name,
                stage_id=excluded.stage_id,
                pipeline_id=excluded.pipeline_id,
                value=excluded.value,
                owner_id=excluded.owner_id,
                created_at=excluded.created_at,
                updated_at=excluded.updated_at,
                raw=excluded.raw
            """,
            row,
        )

def upsert_task(conn, row: Dict[str, Any]) -> None:
    """Upsert a task record."""
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into keap.tasks (id, contact_id, opportunity_id, title, description, due_date, completed_date, owner_id, created_at, updated_at, raw)
            values (%(id)s, %(contact_id)s, %(opportunity_id)s, %(title)s, %(description)s, %(due_date)s, %(completed_date)s, %(owner_id)s, %(created_at)s, %(updated_at)s, %(raw)s)
            on conflict (id) do update set
                contact_id=excluded.contact_id,
                opportunity_id=excluded.opportunity_id,
                title=excluded.title,
                description=excluded.description,
                due_date=excluded.due_date,
                completed_date=excluded.completed_date,
                owner_id=excluded.owner_id,
                created_at=excluded.created_at,
                updated_at=excluded.updated_at,
                raw=excluded.raw
            """,
            row,
        )

def upsert_note(conn, row: Dict[str, Any]) -> None:
    """Upsert a note record."""
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into keap.notes (id, contact_id, opportunity_id, title, body, owner_id, created_at, updated_at, raw)
            values (%(id)s, %(contact_id)s, %(opportunity_id)s, %(title)s, %(body)s, %(owner_id)s, %(created_at)s, %(updated_at)s, %(raw)s)
            on conflict (id) do update set
                contact_id=excluded.contact_id,
                opportunity_id=excluded.opportunity_id,
                title=excluded.title,
                body=excluded.body,
                owner_id=excluded.owner_id,
                created_at=excluded.created_at,
                updated_at=excluded.updated_at,
                raw=excluded.raw
            """,
            row,
        )

def upsert_product(conn, row: Dict[str, Any]) -> None:
    """Upsert a product record."""
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into keap.products (id, name, description, price, sku, active, created_at, updated_at, raw)
            values (%(id)s, %(name)s, %(description)s, %(price)s, %(sku)s, %(active)s, %(created_at)s, %(updated_at)s, %(raw)s)
            on conflict (id) do update set
                name=excluded.name,
                description=excluded.description,
                price=excluded.price,
                sku=excluded.sku,
                active=excluded.active,
                created_at=excluded.created_at,
                updated_at=excluded.updated_at,
                raw=excluded.raw
            """,
            row,
        )

def upsert_order(conn, row: Dict[str, Any]) -> None:
    """Upsert an order record."""
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into keap.orders (id, contact_id, order_number, order_date, total, status, created_at, updated_at, raw)
            values (%(id)s, %(contact_id)s, %(order_number)s, %(order_date)s, %(total)s, %(status)s, %(created_at)s, %(updated_at)s, %(raw)s)
            on conflict (id) do update set
                contact_id=excluded.contact_id,
                order_number=excluded.order_number,
                order_date=excluded.order_date,
                total=excluded.total,
                status=excluded.status,
                created_at=excluded.created_at,
                updated_at=excluded.updated_at,
                raw=excluded.raw
            """,
            row,
        )

def upsert_order_item(conn, row: Dict[str, Any]) -> None:
    """Upsert an order item record."""
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into keap.order_items (id, order_id, product_id, name, description, unit_price, quantity, subtotal, created_at, updated_at, raw)
            values (%(id)s, %(order_id)s, %(product_id)s, %(name)s, %(description)s, %(unit_price)s, %(quantity)s, %(subtotal)s, %(created_at)s, %(updated_at)s, %(raw)s)
            on conflict (id) do update set
                order_id=excluded.order_id,
                product_id=excluded.product_id,
                name=excluded.name,
                description=excluded.description,
                unit_price=excluded.unit_price,
                quantity=excluded.quantity,
                subtotal=excluded.subtotal,
                created_at=excluded.created_at,
                updated_at=excluded.updated_at,
                raw=excluded.raw
            """,
            row,
        )

def upsert_payment(conn, row: Dict[str, Any]) -> None:
    """Upsert a payment record."""
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into keap.payments (id, order_id, amount, payment_date, payment_method, status, created_at, updated_at, raw)
            values (%(id)s, %(order_id)s, %(amount)s, %(payment_date)s, %(payment_method)s, %(status)s, %(created_at)s, %(updated_at)s, %(raw)s)
            on conflict (id) do update set
                order_id=excluded.order_id,
                amount=excluded.amount,
                payment_date=excluded.payment_date,
                payment_method=excluded.payment_method,
                status=excluded.status,
                created_at=excluded.created_at,
                updated_at=excluded.updated_at,
                raw=excluded.raw
            """,
            row,
        )

# Generic upsert function that routes to the appropriate method
def upsert(conn, table: str, row: Dict[str, Any]) -> None:
    """Generic upsert function that routes to the appropriate entity method."""
    upsert_methods = {
        'users': upsert_user,
        'pipelines': upsert_pipeline,
        'stages': upsert_stage,
        'tags': upsert_tag,
        'companies': upsert_company,
        'contacts': upsert_contact,
        'contact_tags': upsert_contact_tag,
        'opportunities': upsert_opportunity,
        'tasks': upsert_task,
        'notes': upsert_note,
        'products': upsert_product,
        'orders': upsert_order,
        'order_items': upsert_order_item,
        'payments': upsert_payment,
    }
    
    if table not in upsert_methods:
        raise ValueError(f"Unknown table: {table}")
    
    upsert_methods[table](conn, row)
