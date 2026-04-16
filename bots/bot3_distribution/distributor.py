"""Distribution wrapper for bot 3."""

import logging

from bots.bot3_distribution.channel_manager import broadcast_channels_from_env
from signal_platform.services.distribution_service import DistributionService

logger = logging.getLogger(__name__)


def distribute_signal(db, signal):
    channels = broadcast_channels_from_env()
    if channels:
        logger.info("Bot3 broadcast channels configured: %d", len(channels))
    return DistributionService.distribute(db, signal)
