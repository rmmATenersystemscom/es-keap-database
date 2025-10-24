# 🔄 CHECK-IN Process Documentation

## 🚨 **CRITICAL DIRECTIVE: When You Yell "CHECK-IN!"**

**⚠️ IMMEDIATE ACTION REQUIRED**: When you type "CHECK-IN!" in the chat, the AI assistant MUST immediately execute the complete Git commit and versioning process described below. This is a **MANDATORY COMMAND** that triggers the full deployment workflow for the Keap Database project.

## **What "CHECK-IN!" Means:**
- **Trigger Command**: "CHECK-IN!" is your signal to commit all current changes
- **Complete Process**: Execute ALL steps below in sequence
- **No Exceptions**: This process must be completed fully every time
- **Version Management**: Always increment version numbers appropriately
- **Documentation**: Update README and project documentation version numbers to match new tags

## **MANDATORY CHECK-IN Workflow (Execute in Order):**

### **Step 1: Pre-Check**
- **Check existing tags**: `git tag --sort=-version:refname | head -5`
- **Determine next version**: Based on change type (patch/minor/major)
- **Verify all changes**: Ensure all modifications are ready for commit

### **Step 2: Documentation Version Updates (BEFORE Commit)**
- **Update README.md version references**: Look for version numbers in the main content sections
- **Update any other version references** in README.md
- **Update project documentation**: Check docs/ directory for version references
- **Standard approach**: Search for version patterns like `vX.Y.Z` and update appropriately

### **Step 2a: Update Modified Documentation Files (BEFORE Commit)**
- **Identify modified .md files**: `git status --porcelain | grep "\.md$"`
- **For each modified .md file**, update version/date stamps at the END of the file:
  - **Standard location**: Last few lines of the document (before any related links)
  - **Standard format**: Use `date -u +"%B %d, %Y %H:%M UTC"` for consistency
- **Standardized footer format** (add if missing, update if present):
  ```markdown
  ---
  
  **Version**: vX.Y.Z  
  **Last Updated**: [Current UTC Date/Time]  
  **Maintainer**: ES Dashboards Team
  ```
- **Special handling for USER_STORY.md files**:
  - **Location**: End of file (same as other .md files)
  - **Format**: Same standardized footer format
  - **Pattern**: `**Last Updated**: [date]` → `**Last Updated**: [current UTC date/time]`
- **Update patterns to look for**:
  - `**Version**: vX.Y.Z` → `**Version**: vX.Y.Z+1`
  - `**Last Updated**: [date]` → `**Last Updated**: [current UTC date/time]`
  - `**Document Version**: X.Y` → `**Document Version**: X.Y+0.1`
  - `**Analysis Date**: [date]` → `**Analysis Date**: [current UTC date/time]`
- **Files that commonly need updates**:
  - STD_*.md files (standards documents)
  - API_*.md files (API documentation)
  - ARCH_*.md files (architecture documents)
  - GUIDE_*.md files (guide documents)
  - TROUBLESHOOT_*.md files (troubleshooting documents)
  - export_guide.md (export functionality documentation)
  - file_management_guide.md (file management documentation)
  - etl_tracker_migration.md (ETL tracker migration guide)
  - implementation_story.md (project implementation documentation)
  - keap_api_reference.md (Keap API reference)
  - project_layout.md (project structure documentation)

### **Step 3: Git Operations**
1. **Stage all changes**: `git add .`
2. **Create detailed commit**: `git commit -m "[Detailed description of all changes including version update]"`
3. **Create version tag**: `git tag -a vX.Y.Z -m "[Comprehensive change description]"`
4. **Push everything**: `git push origin main --tags`

### **Step 4: Confirmation**
- **Display completion message** with tag used and changes committed
- **List all modified files** and their purposes
- **Confirm successful push** to GitHub

## **Version Numbering Rules:**
- **Patch (vX.Y.Z+1)**: Bug fixes, minor improvements (v1.14.2 → v1.14.3)
- **Minor (vX.Y+1.0)**: New features, dashboard additions (v1.14.2 → v1.15.0)  
- **Major (vX+1.0.0)**: Breaking changes, architecture changes (v1.14.2 → v2.0.0)

## **Required Output Format:**
```
CHECK-IN COMPLETE! ✅

Tag Used: vX.Y.Z

Changes Committed:
- [Detailed list of all changes made]
- [Specific improvements and fixes]
- [Files modified and their purposes]
- [Documentation version stamps updated]

Files Modified:
- [List of all changed files with descriptions]
- [Documentation files with updated version/date stamps]

The changes have been successfully committed and pushed to GitHub with tag vX.Y.Z
All detailed revision notes are preserved in Git tag messages and commit history
```

## **Example CHECK-IN Output**
```
CHECK-IN COMPLETE! ✅

Tag Used: v1.15.0

Changes Committed:
- Implemented comprehensive ETL tracker rewrite with simplified, reliable implementation
- Added CSV/Parquet export functionality for external data analysis
- Enhanced observability metrics with detailed performance tracking
- Implemented optional file download functionality for contact file box items
- Added run resume capability with checkpoint-based recovery
- Enhanced throttle handling with intelligent backoff strategies
- Improved custom fields handling across all sync modules
- Updated documentation with comprehensive guides and migration instructions
- Updated version numbers across all documentation files

Files Modified:
- src/keap_export/etl_tracker_v2.py - New simplified ETL tracker implementation
- src/keap_export/exporters.py - CSV/Parquet export functionality
- src/keap_export/file_manager.py - File download and management system
- src/keap_export/sync_base.py - Enhanced sync capabilities with resume support
- src/keap_export/client.py - Improved throttle handling and metrics tracking
- docs/export_guide.md - Export functionality documentation
- docs/file_management_guide.md - File management documentation
- docs/etl_tracker_migration.md - ETL tracker migration guide
- README.md - Updated version number to v1.15.0

The changes have been successfully committed and pushed to GitHub with the descriptive tag v1.15.0
All detailed revision notes are preserved in Git tag messages and commit history
```

---

*This documentation is part of the Keap Database project and should be updated whenever the CHECK-IN! process is modified.*

---

**Version**: v1.0.0  
**Last Updated**: October 24, 2025 01:20 UTC  
**Maintainer**: Keap Database Team
