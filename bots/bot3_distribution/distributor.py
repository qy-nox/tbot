"""Distribution wrapper for bot 3."""

from signal_platform.services.distribution_service import DistributionService


def distribute_signal(db, signal):
    return DistributionService.distribute(db, signal)
