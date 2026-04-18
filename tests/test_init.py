import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.scrutiny import async_setup_entry, async_unload_entry
from custom_components.scrutiny.const import (
    CONF_URL,
    CONF_VERIFY_SSL,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    PLATFORMS,
)
from custom_components.scrutiny.api import ScrutinyApiClient
from custom_components.scrutiny.coordinator import ScrutinyDataUpdateCoordinator

from pytest_homeassistant_custom_component.common import MockConfigEntry

MOCK_CONFIG_DATA = {
    CONF_URL: "http://test-scrutiny.local:8088",
    CONF_VERIFY_SSL: DEFAULT_VERIFY_SSL,
}


@pytest.mark.asyncio
async def test_async_setup_entry_success(hass: HomeAssistant):
    """Test successful setup of the integration."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG_DATA,
        title="Test Scrutiny Instance",
    )
    entry.add_to_hass(hass)

    mock_session = MagicMock()
    with (
        patch(
            "custom_components.scrutiny.async_get_clientsession",
            return_value=mock_session,
        ) as mock_get_session,
        patch(
            "custom_components.scrutiny.ScrutinyApiClient", autospec=True
        ) as mock_api_client_class,
        patch(
            "custom_components.scrutiny.ScrutinyDataUpdateCoordinator", autospec=True
        ) as mock_coordinator_class,
        patch(
            "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
            return_value=True,
        ) as mock_forward_setup,
        patch("homeassistant.helpers.device_registry.async_get") as mock_async_get_dr,
    ):
        mock_dr = MagicMock()
        mock_async_get_dr.return_value = mock_dr

        mock_coordinator_instance = mock_coordinator_class.return_value
        mock_coordinator_instance.async_config_entry_first_refresh = AsyncMock(
            return_value=None
        )
        mock_coordinator_instance.data = {"some_wwn": {}}

        setup_result = await async_setup_entry(hass, entry)
        assert setup_result is True
        await hass.async_block_till_done()

    # Session created with verify_ssl from config
    mock_get_session.assert_called_once_with(hass, verify_ssl=MOCK_CONFIG_DATA[CONF_VERIFY_SSL])

    # API client created with base_url
    mock_api_client_class.assert_called_once_with(
        base_url=MOCK_CONFIG_DATA[CONF_URL],
        session=mock_session,
    )

    coordinator_args = mock_coordinator_class.call_args[1]
    assert coordinator_args["hass"] == hass
    assert coordinator_args["api_client"] == mock_api_client_class.return_value

    mock_coordinator_instance.async_config_entry_first_refresh.assert_called_once()
    assert entry.runtime_data == mock_coordinator_instance
    mock_async_get_dr.assert_called_once_with(hass)
    mock_dr.async_get_or_create.assert_called_once()
    mock_forward_setup.assert_called_once_with(entry, PLATFORMS)

    print(f"SUCCESS: {test_async_setup_entry_success.__name__} passed!")


@pytest.mark.asyncio
async def test_async_setup_entry_first_refresh_fails(hass: HomeAssistant):
    """Test setup fails if coordinator.async_config_entry_first_refresh raises UpdateFailed."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_DATA)
    entry.add_to_hass(hass)

    with (
        patch("custom_components.scrutiny.async_get_clientsession", return_value=MagicMock()),
        patch("custom_components.scrutiny.ScrutinyApiClient", autospec=True),
        patch(
            "custom_components.scrutiny.ScrutinyDataUpdateCoordinator", autospec=True
        ) as mock_coordinator_class,
    ):
        mock_coordinator_instance = mock_coordinator_class.return_value
        mock_coordinator_instance.async_config_entry_first_refresh = AsyncMock(
            side_effect=UpdateFailed("Simulated first refresh failure")
        )

        with pytest.raises(UpdateFailed) as excinfo:
            await async_setup_entry(hass, entry)

        assert "Simulated first refresh failure" in str(excinfo.value)
        assert (
            not hasattr(entry, "runtime_data")
            or entry.runtime_data is None
            or entry.runtime_data != mock_coordinator_instance
        )

    print(f"SUCCESS: {test_async_setup_entry_first_refresh_fails.__name__} passed!")


@pytest.mark.asyncio
async def test_async_unload_entry_success(hass: HomeAssistant):
    """Test successful unload of the integration."""
    entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_DATA, title="Test Scrutiny to Unload"
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_unload_platforms:
        unload_result = await async_unload_entry(hass, entry)
        assert unload_result is True

    mock_unload_platforms.assert_called_once_with(entry, PLATFORMS)

    print(f"SUCCESS: {test_async_unload_entry_success.__name__} passed!")
