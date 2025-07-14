"""Nest API client implementation."""
from typing import Dict, Any, Optional
import httpx
from ..utils.logging import logger
from ..utils.retry import with_retry
from ..auth.token_manager import TokenManager
from ..config.settings import NEST_API_URL, NEST_PROJECT_ID

class NestAPI:
    """Google Nest SDM API client with automatic token refresh."""
    
    def __init__(
        self,
        base_url: str = NEST_API_URL,
        project_id: str = NEST_PROJECT_ID,
        token_manager: Optional[TokenManager] = None
    ):
        self.base_url = base_url
        self.project_id = project_id
        self.token_manager = token_manager
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=10.0,
            http2=True
        )

    async def _get_headers(self) -> Dict[str, str]:
        """Get headers with a valid access token."""
        if not self.token_manager:
            raise ValueError("Token manager not configured")
            
        token = await self.token_manager.get_valid_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    @with_retry(max_retries=3)
    async def list_devices(self) -> Dict[str, Any]:
        """List all Nest devices in the project."""
        return await self._make_authenticated_request(
            "GET", f"/enterprises/{self.project_id}/devices"
        )

    @with_retry(max_retries=3)
    async def get_device(self, device_id: str) -> Dict[str, Any]:
        """Get a specific device's details."""
        return await self._make_authenticated_request(
            "GET", f"/enterprises/{self.project_id}/devices/{device_id}"
        )

    @with_retry(max_retries=3)
    async def set_temperature(
        self,
        device_id: str,
        heat: Optional[float] = None,
        cool: Optional[float] = None
    ) -> None:
        """Set target temperature for a thermostat."""
        if heat is None and cool is None:
            raise ValueError("Must specify at least one of heat or cool temperature")

        command = {
            "command": "sdm.devices.commands.ThermostatTemperatureSetpoint.SetRange",
            "params": {}
        }
        
        if heat is not None:
            command["params"]["heatCelsius"] = heat
        if cool is not None:
            command["params"]["coolCelsius"] = cool

        await self._make_authenticated_request(
            "POST", 
            f"/enterprises/{self.project_id}/devices/{device_id}:executeCommand",
            json_data=command
        )
        logger.info(f"[Nest] Set temperature for device {device_id}: heat={heat}, cool={cool}")

    async def _make_authenticated_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an authenticated request with automatic token refresh."""
        try:
            headers = await self._get_headers()
            
            if method.upper() == "GET":
                response = await self.client.get(endpoint, headers=headers)
            elif method.upper() == "POST":
                response = await self.client.post(endpoint, headers=headers, json=json_data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            result = response.json()
            if method.upper() == "GET" and "devices" in result:
                logger.info(f"[Nest] Found {len(result.get('devices', []))} devices")
            elif method.upper() == "GET":
                logger.info(f"[Nest] Got device: {result.get('name', 'Unknown')}")
                
            return result
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401 and self.token_manager:
                logger.warning("[Nest] Authentication failed (401), refreshing token...")
                await self.token_manager.get_valid_token()  # Force token refresh
                return await self._make_authenticated_request(method, endpoint, json_data)
            raise
            
    async def get_temperature(self, device_id: str) -> Dict[str, float]:
        """Get current and target temperatures for a thermostat."""
        device = await self.get_device(device_id)
        traits = device.get("traits", {})
        temp_data = {}
        
        if "sdm.devices.traits.Temperature" in traits:
            temp = traits["sdm.devices.traits.Temperature"]
            temp_data["ambient"] = temp.get("ambientTemperatureCelsius")
            
        if "sdm.devices.traits.ThermostatTemperatureSetpoint" in traits:
            setpoint = traits["sdm.devices.traits.ThermostatTemperatureSetpoint"]
            temp_data["heat"] = setpoint.get("heatCelsius")
            temp_data["cool"] = setpoint.get("coolCelsius")
            
        logger.info(f"[Nest] Device {device_id} temperatures: {temp_data}")
        return temp_data

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
