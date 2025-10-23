# Project Layout

```
keap-export-starter/
├─ README.md
├─ requirements.txt
├─ .env.example
├─ Makefile
├─ pyproject.toml
├─ docs/
│  ├─ user_story.md
│  ├─ implementation_story.md
│  ├─ project_layout.md
│  ├─ keap_api_reference.md
│  └─ cursor_master_prompt.md
├─ sql/
│  ├─ schema.sql
│  ├─ keap_etl_support.sql
│  └─ keap_validation.sql
└─ src/
   └─ keap_export/
      ├─ __init__.py
      ├─ config.py
      ├─ auth.py
      ├─ client.py
      ├─ db.py
      └─ ../scripts/
         └─ sample_connect.py
```
