#!/usr/bin/env python3
"""PHASE 6 LIVE E2E TEST - Verify actual deployment state"""

import os
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://postgres:postgres@nexusforge-postgres-1:5432/nexusforge'

import sys
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/app')

print("=" * 80)
print("PHASE 6 LIVE END-TO-END TEST - VERIFICATION OF ACTUAL DEPLOYMENT")
print("=" * 80)

# Test 1: Verify all required models exist
print("\n[TEST 1] Required model files...")
required_models = ['user', 'task', 'artifact', 'project', 'worker', 'approval']
for model in required_models:
    path = f'/app/app/models/{model}.py'
    if os.path.exists(path):
        print(f"  ✅ {model}.py exists")
    else:
        print(f"  ❌ {model}.py MISSING")

# Test 2: Check auth module
print("\n[TEST 2] Auth module...")
auth_path = '/app/app/auth.py'
if os.path.exists(auth_path):
    print(f"  ✅ auth.py exists")
    with open(auth_path) as f:
        content = f.read()
    if 'get_current_user' in content:
        print(f"  ✅ get_current_user function defined")
    if 'from app.models.user import User' in content:
        print(f"  ⚠️  auth.py imports from app.models.user - user.py must exist")
else:
    print(f"  ❌ auth.py missing")

# Test 3: Check API routers
print("\n[TEST 3] Phase 6 API routers...")
routers = ['approval', 'worker', 'artifact', 'execution']
for router_name in routers:
    path = f'/app/app/api/{router_name}.py'
    if os.path.exists(path):
        print(f"  ✅ {router_name}.py exists")
    else:
        print(f"  ❌ {router_name}.py MISSING")

# Test 4: Check migration file
print("\n[TEST 4] Migration files...")
migration_path = '/app/app/migrations/versions/1875b06d6a88_phase6_worker_controls.py'
if os.path.exists(migration_path):
    print(f"  ✅ Phase 6 migration file exists")
else:
    print(f"  ❌ Phase 6 migration MISSING")

# Test 5: Database connection test (sync)
print("\n[TEST 5] Database connectivity...")
try:
    from sqlalchemy import create_engine, text
    engine = create_engine("postgresql://postgres:postgres@nexusforge-postgres-1:5432/nexusforge")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(f"  ✅ PostgreSQL connection working")
        
        # Check for Phase 6 tables
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [r[0] for r in result.fetchall()]
        phase6_tables = ['worker_states', 'worker_controls']
        for table in phase6_tables:
            if table in tables:
                print(f"  ✅ Phase 6 table '{table}' exists in DB")
            else:
                print(f"  ❌ Phase 6 table '{table}' MISSING from DB")
        engine.dispose()
except Exception as e:
    print(f"  ❌ DB connection failed: {e}")

# Test 6: Import Phase 6 models with correct paths
print("\n[TEST 6] Phase 6 model imports...")
try:
    # Import base first
    from app.db import Base
    print(f"  ✅ Base imported from app.db")
    
    # Import Phase 6 specific models
    from app.models.approval import ApprovalRequest
    print(f"  ✅ ApprovalRequest model imported")
    
    # Check if WorkerState exists in models
    try:
        from app.models import WorkerState
        print(f"  ✅ WorkerState model imported")
    except ImportError as e:
        print(f"  ⚠️  WorkerState import: {e}")
        print(f"     (WorkerState may not be defined yet - this is expected for Phase 6)")
        
except Exception as e:
    print(f"  ❌ Phase 6 model import failed: {e}")

# Test 7: Check for user.py - critical for auth
print("\n[TEST 7] Critical file check...")
if not os.path.exists('/app/app/models/user.py'):
    print("  ❌ CRITICAL: user.py missing - auth will fail!")
else:
    print("  ✅ user.py exists")

print("\n" + "=" * 80)
print("PHASE 6 LIVE TEST COMPLETE")
print("=" * 80)
