
"""
EDS HTTP client.

Provides basic HTTP communication with an AVEVA Edge
Data Store instance.
"""

import json
import logging
from dataclasses import dataclass
from socket import timeout as SocketTimeout
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from common.configuration import ConfigValidationError

from EvalEDSApp.config import APP_NAMESPACE
from EvalEDSApp.eds.connection_profile import EDSConnectionProfile


logger = logging.getLogger(APP_NAMESPACE)


@dataclass
class EDSConnectionResult:
    """Result of an EDS connection operation."""

    success: bool
    message: str
    status_code: int | None = None
    response_data: dict | list | None = None


class EDSClient:
    """HTTP client for communicating with an EDS instance."""

    CONFIGURATION_ENDPOINT = "/api/v1/configuration"

    def test_connection(
        self,
        profile: EDSConnectionProfile
    ) -> EDSConnectionResult:
        """
        Test connectivity to EDS.

        Returns a connection result without exposing the
        configuration response to the caller.
        """

        result = self._request_configuration(profile)

        if result.success:
            return EDSConnectionResult(
                success=True,
                message="Successfully connected to EDS.",
                status_code=result.status_code
            )

        return result

    def get_configuration(
        self,
        profile: EDSConnectionProfile
    ) -> EDSConnectionResult:
        """
        Retrieve the EDS system configuration.

        The returned result includes the JSON response data.
        """

        return self._request_configuration(profile)

    def _request_configuration(
        self,
        profile: EDSConnectionProfile
    ) -> EDSConnectionResult:
        """Perform the HTTP request to the EDS configuration endpoint."""

        # Validate the connection profile.
        try:
            profile.validate()

        except ConfigValidationError as exc:
            return EDSConnectionResult(
                success=False,
                message=f"Invalid connection profile: {exc}"
            )

        # Build the endpoint URL.
        base_url = profile.url.strip().rstrip("/")
        endpoint = (
            f"{base_url}:{profile.port}"
            f"{self.CONFIGURATION_ENDPOINT}"
        )

        request = Request(
            endpoint,
            method="GET",
            headers={
                "Accept": "application/json"
            }
        )

        try:
            logger.info("Requesting EDS configuration from %s", endpoint)

            with urlopen(
                request,
                timeout=profile.timeout
            ) as response:

                status_code = response.status
                response_text = response.read().decode("utf-8")

                if not 200 <= status_code < 300:
                    return EDSConnectionResult(
                        success=False,
                        message=f"EDS returned HTTP status {status_code}.",
                        status_code=status_code
                    )

                try:
                    response_data = json.loads(response_text)

                except json.JSONDecodeError:
                    return EDSConnectionResult(
                        success=False,
                        message="EDS returned an invalid JSON response.",
                        status_code=status_code
                    )

                return EDSConnectionResult(
                    success=True,
                    message="EDS configuration retrieved successfully.",
                    status_code=status_code,
                    response_data=response_data
                )

        except HTTPError as exc:
            logger.warning("EDS returned HTTP error %s", exc.code)

            return EDSConnectionResult(
                success=False,
                message=f"EDS returned HTTP error {exc.code}.",
                status_code=exc.code
            )

        except (SocketTimeout, TimeoutError):
            logger.warning("EDS request timed out")

            return EDSConnectionResult(
                success=False,
                message="Connection to EDS timed out."
            )

        except URLError as exc:
            logger.warning(
                "Unable to connect to EDS: %s",
                exc.reason
            )

            return EDSConnectionResult(
                success=False,
                message=f"Unable to connect to EDS: {exc.reason}"
            )

        except OSError as exc:
            logger.warning("EDS request failed: %s", exc)

            return EDSConnectionResult(
                success=False,
                message=f"EDS connection failed: {exc}"
            )
