#!/usr/bin/env python3
"""
02backend/scripts/audit_scheme_data.py
Automated A-to-Z Data Quality Audit Suite for YojnaSetu.
Audits all 90 schemes, rules, documents, and provenance records across CSVs and SQLite databases.
"""

import os
import sys

# Add parent workspace to path and invoke root audit script
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_ROOT = os.path.dirname(BACKEND_DIR)
ROOT_SCRIPT = os.path.join(WORKSPACE_ROOT, "scripts", "audit_scheme_data.py")

if os.path.exists(ROOT_SCRIPT):
    import importlib.util
    spec = importlib.util.spec_from_file_location("audit_scheme_data", ROOT_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    success = mod.run_audit()
    sys.exit(0 if success else 1)
else:
    print(f"Error: {ROOT_SCRIPT} not found")
    sys.exit(1)
