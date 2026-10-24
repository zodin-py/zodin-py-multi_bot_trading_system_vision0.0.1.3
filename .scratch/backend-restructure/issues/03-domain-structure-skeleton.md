# 03: Domain Structure Skeleton

**What to build:** Create the new `domains/` directory structure with all domain packages and `__init__.py` files. This is a pure structural change — no logic moved yet, just the scaffolding.

**Blocked by:** None (can start immediately)

**Status:** completed

- [ ] `backend/domains/` directory created
- [ ] Subdirectories: `data/`, `indicators/`, `strategies/`, `analysis/`, `execution/`, `trades/`, `portfolio/`, `risk/`, `api/`
- [ ] Each domain has `__init__.py` with `from .models import *` (empty for now) and `from .service import *` (empty)
- [ ] `api/` has subdirectory `routes/` with `__init__.py`
- [ ] `backend/domains/__init__.py` exists
- [ ] No circular imports possible with this structure