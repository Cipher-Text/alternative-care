"""The systems that have case-taking forms. Herbal is added here when its fields are reviewed."""

from app.shared.case_taking import System
from app.shared.case_taking.ayurveda import AYURVEDA
from app.shared.case_taking.homeopathy import HOMEOPATHY
from app.shared.case_taking.unani import UNANI

SYSTEMS: dict[str, System] = {HOMEOPATHY.key: HOMEOPATHY, AYURVEDA.key: AYURVEDA, UNANI.key: UNANI}
