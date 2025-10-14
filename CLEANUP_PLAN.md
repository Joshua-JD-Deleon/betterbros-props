# Production Cleanup Plan

## 📋 Current State
- **Total Size**: ~655 MB (653 MB is venv)
- **Root Files**: 28 files (many development docs)
- **Test Scripts**: 5 test files in root
- **Dev Documentation**: ~15 development-focused markdown files

---

## 🗑️ RECOMMENDED FOR REMOVAL

### Test Scripts in Root (5 files - REMOVE)
- ❌ `test_api_debug.py` (1.6K) - Debug script
- ❌ `test_multi_sport.py` (3.2K) - Dev testing script
- ❌ `test_odds_api.py` (3.7K) - API testing script
- ❌ `test_props_availability.py` (982B) - Testing script
- ❌ `test_specific_game.py` (2.4K) - Testing script
**Reason**: Tests belong in `tests/` directory, not root. These are dev tools.
**Feedback**: Do we still need them? Are there new versions? If yes and no, then put them in the correct folder. 
### Development Documentation (12 files - REMOVE)
- ❌ `CSS_CLEANUP_CHECKLIST.md` (7.5K) - Internal dev checklist
- ❌ `CSS_REFACTOR_SUMMARY.md` (16K) - Dev process doc
- ❌ `DECISIONS.md` (7.2K) - Internal decision log
- ❌ `DELIVERY_SUMMARY.md` (16K) - Internal delivery doc
- ❌ `EVALUATION_SYSTEM_GUIDE.md` (15K) - Internal dev guide
- ❌ `IMPLEMENTATION_PLAN.md` (2.3K) - Internal planning doc
- ❌ `IMPLEMENTATION_SUMMARY.md` (8.6K) - Internal dev doc
- ❌ `MODULE_INDEX.md` (6.9K) - Internal code index
- ❌ `OPTIMIZER_IMPLEMENTATION.md` (8.0K) - Internal dev guide
- ❌ `OPTIMIZER_QUICK_REFERENCE.md` (7.5K) - Internal dev reference
- ❌ `PHASE1_IMPLEMENTATION_PLAN.md` (14K) - Internal planning doc
- ❌ `STYLING_STANDARDS.md` (16K) - Internal dev standards
**Reason**: These are internal development docs, not user-facing. Production doesn't need them.
**Feedback**: Remove all unneccesary and create one master md file for me to understand each separate module/feature/capability etc. across whole app. Ensure sections have drop down menus since it will be a long doc. 
### Status/Process Documentation (2 files - REMOVE)
- ❌ `MULTI_SPORT_STATUS.md` (6.6K) - Implementation status tracker
- ❌ `STRUCTURE.txt` (3.8K) - Old structure doc
**Reason**: Status tracking is for development phase only.
**Feedback**: Similar to above, create one development doc for ongoing tracking of features, enhancements etc. 
### Redundant Documentation (2 files - REMOVE)
- ❌ `README_RUN.md` (3.5K) - Redundant with QUICKSTART.md
- ❌ `ODDS_API_SETUP.md` (4.9K) - Now covered in docs/api/README.md
**Reason**: Information is duplicated in better locations.
**Feedback**: Okay
### Deployment Artifacts (1 file - REMOVE)
- ❌ `betterbros-props-package.zip` (752K) - Old deployment package
**Reason**: This was for sharing, not needed in production folder.
**Feedback**: Okay
### Internal Process Docs (1 file - REMOVE)
- ❌ `PROJECT_SUMMARY.md` (8.6K) - Internal project summary
**Reason**: Development artifact, not production documentation.
**Feedback**: Okay
### Development Directories (5 directories - REMOVE or CLEAN)
- ❌ `examples/` (48K) - Example files from development
- ❌ `experiments/` (12K) - Experimental code
- ❌ `shares/` (8K) - Test sharing packages
- ❌ `.pytest_cache/` - Pytest cache directory
- ⚠️ `reports/` (96K) - Old reports (check if needed)
- ⚠️ `exports/` (72K) - Old exports (check if needed)
**Reason**: Development/testing artifacts not needed in production.
**Feedback**: Okay
### Cache/Temporary Files (REMOVE)
- ❌ All `.DS_Store` files (macOS metadata)
- ❌ All `__pycache__/` directories (Python cache)
- ❌ All `.pyc` files (Compiled Python)
**Reason**: System cache files, regenerated automatically.
**Feedback**: Okay
---

## ✅ KEEP (Essential Files)

### Core Application Files
- ✅ `README.md` - Main project documentation
- ✅ `QUICKSTART.md` - User quick start guide
- ✅ `requirements.txt` - Python dependencies
- ✅ `user_prefs.yaml` - Configuration file
- ✅ `Makefile` - Build/run commands
- ✅ `.env.example` - Environment template
- ✅ `.gitignore` - Git configuration

### Essential Directories
- ✅ `app/` - Streamlit UI (140K)
- ✅ `src/` - Backend source code (468K)
- ✅ `docs/` - User documentation (700K)
- ✅ `scripts/` - CLI scripts (36K)
- ✅ `tests/` - Test suite (152K)
- ✅ `data/` - Data storage (160K) - but should clean cached data
- ✅ `models/` - ML models directory (4K)
- ✅ `venv/` - Virtual environment (653M) - needed for running

### New Documentation (If Created)
- ✅ `DEPLOYMENT_PACKAGE_README.md` - Deployment instructions (can rename to DEPLOYMENT.md)

---

## 📁 REORGANIZATION SUGGESTIONS

### Option 1: Create `/archive` Directory
Move development docs here instead of deleting:
```
/archive/
  ├── development/
  │   ├── CSS_CLEANUP_CHECKLIST.md
  │   ├── CSS_REFACTOR_SUMMARY.md
  │   ├── DECISIONS.md
  │   ├── IMPLEMENTATION_*.md
  │   └── ...
  └── status/
      ├── MULTI_SPORT_STATUS.md
      └── DELIVERY_SUMMARY.md
```

### Option 2: Complete Removal
Delete all development docs entirely. They're tracked in git history if needed.
**Feedback**: Go with this
### Option 3: Keep Minimal Development Docs
Only keep 1-2 most relevant dev docs, remove the rest.

---

## 🧹 CLEANUP ACTIONS

### Phase 1: Safe Removals (No Risk)
1. Remove all test scripts from root (move to `tests/` or delete)
2. Remove all `.DS_Store` files
3. Remove all `__pycache__/` directories
4. Remove `.pytest_cache/`
5. Remove `betterbros-props-package.zip`

### Phase 2: Development Artifacts
6. Remove/archive `examples/`, `experiments/`, `shares/`
7. Clean old data in `data/` (cached parquet files from testing)
8. Clean old exports in `exports/` (if not needed)
9. Clean old reports in `reports/` (if not needed)

### Phase 3: Documentation Cleanup
10. Remove 12 internal development markdown files (or archive)
11. Rename `DEPLOYMENT_PACKAGE_README.md` → `DEPLOYMENT.md`
12. Remove redundant docs (`README_RUN.md`, `ODDS_API_SETUP.md`)

---

## 📊 SIZE IMPACT

**Before Cleanup**: ~655 MB total (653 MB venv + 2 MB files)
**After Cleanup**: ~654 MB total (653 MB venv + 1 MB files)

**Files Reduction**:
- Remove ~20 files from root
- Remove ~3-5 directories
- Clean cache files throughout

**Result**: Cleaner, production-ready structure with only essential files.

---

## ❓ QUESTIONS FOR YOU

1. **Development Docs**: Delete completely or move to `/archive`?
**Feedback**: Delete
2. **Reports/Exports**: Should I check and clean old files in these directories?
**Feedback**: Yes
3. **Data Cache**: Should I clean cached `.parquet` files in `data/`?
**Feedback**: Yes
4. **Virtual Environment**: Keep `venv/` or expect users to create their own?
**Feedback**: Can you explain this more? 
5. **Tests Directory**: Keep full test suite or remove for production?
**Feedback**: Keep for ongoing feature tests/enhancements no?
---

## 🎯 RECOMMENDED APPROACH

**My recommendation**: **Complete Removal (Option 2)**
 **Feedback**: Okay

**Rationale**:
- Production users don't need internal dev docs
- All code is in git history if needed
- Cleaner structure is more professional
- Easier to navigate for new users

**Alternative**: If you want to preserve history, use **Option 1** (archive) instead.

---

**Please review and let me know**:
- ✅ Approve entire plan
- ✅ Approve with modifications (tell me what to change)
- ✅ Answer the 5 questions above
- ❌ Cancel cleanup
