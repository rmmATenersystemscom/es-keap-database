"""
Keap Export UI - Streamlit MVP
Read-only interface to verify Keap → PostgreSQL export data
"""

import streamlit as st
import psycopg2
import httpx
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/opt/es-keap-database/.env')

# Page configuration
st.set_page_config(
    page_title="Keap Export Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    .diff-match {
        background-color: #d4edda;
        color: #155724;
        padding: 2px 4px;
        border-radius: 3px;
    }
    .diff-mismatch {
        background-color: #f8d7da;
        color: #721c24;
        padding: 2px 4px;
        border-radius: 3px;
    }
    .diff-missing {
        background-color: #fff3cd;
        color: #856404;
        padding: 2px 4px;
        border-radius: 3px;
    }
</style>
""", unsafe_allow_html=True)

class KeapExportUI:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'keap'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD')
        }
        self.keap_token = self._load_keap_token()
        
    def _load_keap_token(self) -> Optional[str]:
        """Load Keap access token from file"""
        try:
            with open('/opt/es-keap-database/.keap_tokens.json', 'r') as f:
                tokens = json.load(f)
                return tokens.get('access_token')
        except Exception as e:
            st.error(f"Failed to load Keap token: {e}")
            return None
    
    def get_db_connection(self):
        """Get PostgreSQL connection"""
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            st.error(f"Database connection failed: {e}")
            return None
    
    def get_entity_counts(self) -> Dict[str, int]:
        """Get record counts for all entities"""
        conn = self.get_db_connection()
        if not conn:
            return {}
        
        entities = ['contacts', 'companies', 'opportunities', 'tasks', 'notes', 'tags', 'users']
        counts = {}
        
        try:
            with conn.cursor() as cur:
                for entity in entities:
                    cur.execute(f"SELECT COUNT(*) FROM keap.{entity}")
                    counts[entity] = cur.fetchone()[0]
        except Exception as e:
            st.error(f"Error getting entity counts: {e}")
        finally:
            conn.close()
        
        return counts
    
    def get_etl_runs(self) -> List[Dict]:
        """Get recent ETL runs"""
        conn = self.get_db_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, started_at, finished_at, status, notes
                    FROM keap_meta.etl_run_log
                    ORDER BY started_at DESC
                    LIMIT 10
                """)
                runs = []
                for row in cur.fetchall():
                    duration = None
                    if row[2]:  # finished_at
                        start = row[1]
                        end = row[2]
                        if isinstance(start, str):
                            start = datetime.fromisoformat(start.replace('Z', '+00:00'))
                        if isinstance(end, str):
                            end = datetime.fromisoformat(end.replace('Z', '+00:00'))
                        duration = str(end - start)
                    
                    runs.append({
                        'id': row[0],
                        'started_at': row[1],
                        'finished_at': row[2],
                        'duration': duration,
                        'status': row[3],
                        'notes': row[4]
                    })
                return runs
        except Exception as e:
            st.error(f"Error getting ETL runs: {e}")
            return []
        finally:
            conn.close()
    
    def get_validation_results(self) -> Dict[str, int]:
        """Get validation results"""
        conn = self.get_db_connection()
        if not conn:
            return {}
        
        results = {}
        
        try:
            with conn.cursor() as cur:
                # Check for orphaned notes
                cur.execute("""
                    SELECT COUNT(*) FROM keap.notes n
                    LEFT JOIN keap.contacts c ON n.contact_id = c.id
                    WHERE c.id IS NULL AND n.contact_id IS NOT NULL
                """)
                results['orphaned_notes'] = cur.fetchone()[0]
                
                # Check for orphaned tasks
                cur.execute("""
                    SELECT COUNT(*) FROM keap.tasks t
                    LEFT JOIN keap.contacts c ON t.contact_id = c.id
                    WHERE c.id IS NULL AND t.contact_id IS NOT NULL
                """)
                results['orphaned_tasks'] = cur.fetchone()[0]
                
                # Check for duplicate emails
                cur.execute("""
                    SELECT COUNT(*) FROM (
                        SELECT email, COUNT(*) as cnt
                        FROM keap.contacts
                        WHERE email IS NOT NULL
                        GROUP BY email
                        HAVING COUNT(*) > 1
                    ) duplicates
                """)
                results['duplicate_emails'] = cur.fetchone()[0]
                
        except Exception as e:
            st.error(f"Error getting validation results: {e}")
        finally:
            conn.close()
        
        return results
    
    def fetch_keap_record(self, entity: str, record_id: str) -> Optional[Dict]:
        """Fetch record from Keap API"""
        if not self.keap_token:
            return None
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"https://api.infusionsoft.com/crm/rest/v1/{entity}/{record_id}",
                    headers={"Authorization": f"Bearer {self.keap_token}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            st.error(f"Error fetching from Keap: {e}")
            return None
    
    def fetch_db_record(self, entity: str, record_id: str) -> Optional[Dict]:
        """Fetch record from PostgreSQL"""
        conn = self.get_db_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor() as cur:
                cur.execute(f"SELECT * FROM keap.{entity} WHERE id = %s", (record_id,))
                row = cur.fetchone()
                if row:
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            st.error(f"Error fetching from database: {e}")
            return None
        finally:
            conn.close()
    
    def compare_records(self, keap_data: Dict, db_data: Dict) -> List[Dict]:
        """Compare Keap and database records"""
        diffs = []
        
        # Key fields to compare
        key_fields = {
            'contacts': ['id', 'given_name', 'family_name', 'email', 'phone', 'address', 'city', 'state', 'postal_code', 'country_code', 'owner_id', 'created_at', 'updated_at'],
            'companies': ['id', 'company_name', 'phone_number', 'address', 'city', 'state', 'postal_code', 'country_code', 'owner_id', 'created_at', 'updated_at'],
            'opportunities': ['id', 'name', 'contact_id', 'stage_id', 'pipeline_id', 'owner_id', 'created_at', 'updated_at'],
            'tasks': ['id', 'title', 'contact_id', 'owner_id', 'completed_date', 'created_at', 'updated_at'],
            'notes': ['id', 'body', 'contact_id', 'owner_id', 'created_at', 'updated_at'],
            'tags': ['id', 'name', 'category_id', 'category_name', 'description', 'created_at', 'updated_at'],
            'users': ['id', 'given_name', 'family_name', 'email', 'created_at', 'updated_at']
        }
        
        fields_to_check = key_fields.get('contacts', [])  # Default to contacts
        
        for field in fields_to_check:
            keap_value = keap_data.get(field)
            db_value = db_data.get(field)
            
            if keap_value != db_value:
                status = "mismatch" if keap_value is not None and db_value is not None else "missing"
                diffs.append({
                    'field': field,
                    'keap_value': keap_value,
                    'db_value': db_value,
                    'status': status
                })
        
        return diffs

def main():
    ui = KeapExportUI()
    
    st.title("📊 Keap Export Dashboard")
    st.markdown("Read-only interface to verify Keap → PostgreSQL export data")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Overview", "Entity Browser", "Record Inspector", "ETL Runs", "Validation Results"]
    )
    
    if page == "Overview":
        show_overview(ui)
    elif page == "Entity Browser":
        show_entity_browser(ui)
    elif page == "Record Inspector":
        show_record_inspector(ui)
    elif page == "ETL Runs":
        show_etl_runs(ui)
    elif page == "Validation Results":
        show_validation_results(ui)

def show_overview(ui: KeapExportUI):
    """Show overview dashboard"""
    st.header("📈 Overview Dashboard")
    
    # Get entity counts
    counts = ui.get_entity_counts()
    
    # KPI tiles
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Contacts", f"{counts.get('contacts', 0):,}")
    with col2:
        st.metric("Companies", f"{counts.get('companies', 0):,}")
    with col3:
        st.metric("Opportunities", f"{counts.get('opportunities', 0):,}")
    with col4:
        st.metric("Tasks", f"{counts.get('tasks', 0):,}")
    
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        st.metric("Notes", f"{counts.get('notes', 0):,}")
    with col6:
        st.metric("Tags", f"{counts.get('tags', 0):,}")
    with col7:
        st.metric("Users", f"{counts.get('users', 0):,}")
    with col8:
        st.metric("Products", "Not used", help="No products found in Keap")
    
    # Sync health
    st.subheader("🔄 Sync Health")
    runs = ui.get_etl_runs()
    
    if runs:
        latest_run = runs[0]
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_color = "status-success" if latest_run['status'] == 'success' else "status-error"
            st.markdown(f"**Last Run:** <span class='{status_color}'>{latest_run['status']}</span>", unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"**Duration:** {latest_run['duration'] or 'N/A'}")
        
        with col3:
            st.markdown(f"**Started:** {latest_run['started_at']}")
        
        if latest_run['notes']:
            st.info(f"**Notes:** {latest_run['notes']}")
    else:
        st.warning("No ETL runs found")
    
    # Data integrity
    st.subheader("🔍 Data Integrity")
    validation_results = ui.get_validation_results()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Orphaned Notes", validation_results.get('orphaned_notes', 0))
    with col2:
        st.metric("Orphaned Tasks", validation_results.get('orphaned_tasks', 0))
    with col3:
        st.metric("Duplicate Emails", validation_results.get('duplicate_emails', 0))

def show_entity_browser(ui: KeapExportUI):
    """Show entity browser"""
    st.header("🔍 Entity Browser")
    
    entity = st.selectbox(
        "Select Entity",
        ["contacts", "companies", "opportunities", "tasks", "notes", "tags", "users"]
    )
    
    # Search and filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("Search", placeholder="Enter search term...")
    with col2:
        limit = st.number_input("Limit", min_value=10, max_value=1000, value=100)
    with col3:
        has_diff = st.checkbox("Show records with differences only")
    
    # Fetch and display data
    conn = ui.get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                query = f"SELECT * FROM keap.{entity}"
                params = []
                
                if search_term:
                    if entity == 'contacts':
                        query += " WHERE given_name ILIKE %s OR family_name ILIKE %s OR email ILIKE %s"
                        params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])
                    elif entity == 'companies':
                        query += " WHERE company_name ILIKE %s"
                        params.append(f"%{search_term}%")
                
                query += f" ORDER BY id DESC LIMIT {limit}"
                
                cur.execute(query, params)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
                
                if rows:
                    st.dataframe(
                        data=[dict(zip(columns, row)) for row in rows],
                        use_container_width=True
                    )
                else:
                    st.info("No records found")
        except Exception as e:
            st.error(f"Error fetching data: {e}")
        finally:
            conn.close()

def show_record_inspector(ui: KeapExportUI):
    """Show record inspector"""
    st.header("🔬 Record Inspector")
    
    col1, col2 = st.columns(2)
    
    with col1:
        entity = st.selectbox(
            "Entity",
            ["contacts", "companies", "opportunities", "tasks", "notes", "tags", "users"]
        )
    
    with col2:
        record_id = st.text_input("Record ID", placeholder="Enter record ID...")
    
    if st.button("Fetch Record") and record_id:
        with st.spinner("Fetching records..."):
            # Fetch from both sources
            keap_data = ui.fetch_keap_record(entity, record_id)
            db_data = ui.fetch_db_record(entity, record_id)
            
            if keap_data and db_data:
                st.success("✅ Records fetched successfully")
                
                # Side-by-side comparison
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🔵 Keap (Live)")
                    st.json(keap_data)
                
                with col2:
                    st.subheader("🟢 PostgreSQL")
                    st.json(db_data)
                
                # Field-by-field comparison
                st.subheader("🔍 Field Comparison")
                diffs = ui.compare_records(keap_data, db_data)
                
                if diffs:
                    for diff in diffs:
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.markdown(f"**{diff['field']}**")
                        with col2:
                            st.code(str(diff['keap_value']))
                        with col3:
                            if diff['status'] == 'match':
                                st.markdown('<span class="diff-match">✅ Match</span>', unsafe_allow_html=True)
                            elif diff['status'] == 'mismatch':
                                st.markdown('<span class="diff-mismatch">❌ Mismatch</span>', unsafe_allow_html=True)
                            else:
                                st.markdown('<span class="diff-missing">⚠️ Missing</span>', unsafe_allow_html=True)
                            st.code(str(diff['db_value']))
                else:
                    st.success("✅ All fields match!")
            else:
                st.error("❌ Failed to fetch one or both records")

def show_etl_runs(ui: KeapExportUI):
    """Show ETL runs and logs"""
    st.header("📊 ETL Runs & Logs")
    
    runs = ui.get_etl_runs()
    
    if runs:
        for run in runs:
            with st.expander(f"Run {run['id']} - {run['status']} ({run['started_at']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Status:** {run['status']}")
                    st.markdown(f"**Duration:** {run['duration'] or 'N/A'}")
                    st.markdown(f"**Started:** {run['started_at']}")
                    st.markdown(f"**Finished:** {run['finished_at'] or 'N/A'}")
                
                with col2:
                    if run['notes']:
                        st.markdown(f"**Notes:** {run['notes']}")
                
                # Get request metrics for this run
                conn = ui.get_db_connection()
                if conn:
                    try:
                        with conn.cursor() as cur:
                            cur.execute("""
                                SELECT entity, endpoint, item_count, duration_ms, throttle_remaining
                                FROM keap_meta.etl_request_metrics
                                WHERE run_id = %s
                                ORDER BY created_at
                            """, (run['id'],))
                            
                            metrics = cur.fetchall()
                            if metrics:
                                st.subheader("Request Metrics")
                                st.dataframe(
                                    data=[{
                                        'Entity': m[0],
                                        'Endpoint': m[1],
                                        'Items': m[2],
                                        'Duration (ms)': m[3],
                                        'Throttle Remaining': m[4]
                                    } for m in metrics],
                                    use_container_width=True
                                )
                    except Exception as e:
                        st.error(f"Error fetching metrics: {e}")
                    finally:
                        conn.close()
    else:
        st.info("No ETL runs found")

def show_validation_results(ui: KeapExportUI):
    """Show validation results"""
    st.header("✅ Validation Results")
    
    validation_results = ui.get_validation_results()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Orphaned Notes",
            validation_results.get('orphaned_notes', 0),
            help="Notes with invalid contact_id references"
        )
    
    with col2:
        st.metric(
            "Orphaned Tasks",
            validation_results.get('orphaned_tasks', 0),
            help="Tasks with invalid contact_id references"
        )
    
    with col3:
        st.metric(
            "Duplicate Emails",
            validation_results.get('duplicate_emails', 0),
            help="Contacts with duplicate email addresses"
        )
    
    # Show detailed validation results
    if any(validation_results.values()):
        st.warning("⚠️ Some validation issues found")
        
        # Show orphaned notes
        if validation_results.get('orphaned_notes', 0) > 0:
            st.subheader("Orphaned Notes")
            conn = ui.get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT n.id, n.contact_id, n.body, n.created_at
                            FROM keap.notes n
                            LEFT JOIN keap.contacts c ON n.contact_id = c.id
                            WHERE c.id IS NULL AND n.contact_id IS NOT NULL
                            LIMIT 10
                        """)
                        orphaned_notes = cur.fetchall()
                        if orphaned_notes:
                            st.dataframe(
                                data=[{
                                    'Note ID': note[0],
                                    'Contact ID': note[1],
                                    'Body': note[2][:100] + '...' if len(note[2]) > 100 else note[2],
                                    'Created': note[3]
                                } for note in orphaned_notes],
                                use_container_width=True
                            )
                except Exception as e:
                    st.error(f"Error fetching orphaned notes: {e}")
                finally:
                    conn.close()
    else:
        st.success("✅ All validations passed!")

if __name__ == "__main__":
    main()
