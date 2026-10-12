"""The systems that have case-taking forms. Unani is added here when its fields are reviewed."""

from app.shared.case_taking import System
from app.shared.case_taking.ayurveda import AYURVEDA
from app.shared.case_taking.homeopathy import HOMEOPATHY

SYSTEMS: dict[str, System] = {HOMEOPATHY.key: HOMEOPATHY, AYURVEDA.key: AYURVEDA}
