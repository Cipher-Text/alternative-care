"""The systems that have case-taking forms. Ayurveda and Unani are added here when their fields are reviewed."""

from app.shared.case_taking import System
from app.shared.case_taking.homeopathy import HOMEOPATHY

SYSTEMS: dict[str, System] = {HOMEOPATHY.key: HOMEOPATHY}
