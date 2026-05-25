"""Canonical clause-type machine values and their human-readable labels."""

from enum import StrEnum


class ClauseType(StrEnum):
    """Closed set of clause categories the dashboard recognises."""

    LIMITATION_OF_LIABILITY = "limitation_of_liability"
    TERMINATION_FOR_CONVENIENCE = "termination_for_convenience"
    NON_COMPETE = "non_compete"
    CONFIDENTIALITY = "confidentiality"
    GOVERNING_LAW = "governing_law"
    INDEMNIFICATION = "indemnification"
    FORCE_MAJEURE = "force_majeure"


CLAUSE_TYPE_LABELS: dict[ClauseType, str] = {
    ClauseType.LIMITATION_OF_LIABILITY: "Limitation of Liability",
    ClauseType.TERMINATION_FOR_CONVENIENCE: "Termination for Convenience",
    ClauseType.NON_COMPETE: "Non-Compete",
    ClauseType.CONFIDENTIALITY: "Confidentiality",
    ClauseType.GOVERNING_LAW: "Governing Law",
    ClauseType.INDEMNIFICATION: "Indemnification",
    ClauseType.FORCE_MAJEURE: "Force Majeure",
}
