"""
Created on Nov 18, 2026

@author: keith.chambers

EDS connection service.

Coordinates connection testing and configuration retrieval.
Keeps the active connection profile separate from candidate
profiles being tested.
"""

import logging

from EvalEDSApp.config import APP_NAMESPACE
from EvalEDSApp.eds.connection_profile import EDSConnectionProfile
from EvalEDSApp.eds.eds_client import EDSClient, EDSConnectionResult


logger = logging.getLogger(APP_NAMESPACE)


class EDSConnectionService:
    """
    Manages EDS connection operations.

    This service does not persist connection profiles.
    Persistence remains the responsibility of ConfigManager.
    """

    def __init__(
        self,
        client: EDSClient | None = None
    ):
        self.client = client or EDSClient()

        self.active_profile: EDSConnectionProfile | None = None

        # Represents the result of the most recent connection test.
        self.is_connected = False
        self.last_result: EDSConnectionResult | None = None

    # --------------------------------------------------------
    # Set active profile
    # --------------------------------------------------------

    def set_active_profile(
        self,
        profile: EDSConnectionProfile
    ) -> None:
        """
        Set the profile used for normal EDS operations.

        The caller should only invoke this after the profile
        has been successfully saved.
        """

        profile.validate()

        self.active_profile = profile

        # A profile change invalidates the previous test result.
        self.is_connected = False
        self.last_result = None

        logger.info("Active EDS connection profile updated")

    # --------------------------------------------------------
    # Test connection
    # --------------------------------------------------------

    def test_connection(
        self,
        profile: EDSConnectionProfile | None = None
    ) -> EDSConnectionResult:
        """
        Test an EDS connection.

        An optional candidate profile can be supplied.
        Testing a candidate does not change the active profile.
        """

        test_profile = profile or self.active_profile

        if test_profile is None:
            result = EDSConnectionResult(
                success=False,
                message="No EDS connection profile is available."
            )

        else:
            result = self.client.test_connection(test_profile)

        self.last_result = result
        self.is_connected = result.success

        return result

    # --------------------------------------------------------
    # Retrieve EDS configuration
    # --------------------------------------------------------

    def get_configuration(
        self,
        profile: EDSConnectionProfile | None = None
    ) -> EDSConnectionResult:
        """
        Retrieve EDS configuration.

        Uses the supplied profile or, if omitted, the active
        connection profile.
        """

        request_profile = profile or self.active_profile

        if request_profile is None:
            return EDSConnectionResult(
                success=False,
                message="No EDS connection profile is available."
            )

        result = self.client.get_configuration(request_profile)

        self.last_result = result
        self.is_connected = result.success

        return result
