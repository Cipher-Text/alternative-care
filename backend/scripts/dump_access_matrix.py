#!/usr/bin/env python3
"""Write tests/golden/access_matrix.json from the current route guards.

Only run this when a change of who-may-do-what is intended and reviewed: the snapshot is the proof that the move from
role checks to permission checks changed nobody's access (ADR 010, Phase 2)."""

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.main import app
from tests.access_matrix import matrix

path = Path(__file__).parent.parent / "tests" / "golden" / "access_matrix.json"
path.write_text(json.dumps(matrix(app), indent=1, sort_keys=True) + "\n")
print(f"wrote {path} ({len(matrix(app))} route/method pairs)")
