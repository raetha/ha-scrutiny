# tests/test_options_flow.py (or at the end of test_config_flow.py)

import pytest
from unittest.mock import patch  # AsyncMock not strictly necessary here

from homeassistant.data_entry_flow import InvalidData  # Import the exception

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant import data_entry_flow

from custom_components.scrutiny.const import (
    CONF_ENABLE_ALL_ATTRS,
    CONF_ENABLE_CRITICAL_ATTRS,
    CONF_SHOW_ARCHIVED,
    DOMAIN,
    CONF_URL,
    CONF_VERIFY_SSL,
    DEFAULT_VERIFY_SSL,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_MINUTES,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

# Data for the initial ConfigEntry
INITIAL_CONFIG_DATA = {
    CONF_URL: "http://scrutiny.options.local:8080",
    CONF_VERIFY_SSL: True,
    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL_MINUTES,  # Start with default
}


@pytest.mark.asyncio
async def test_options_flow_init_and_save(
    hass: HomeAssistant,
    enable_custom_integrations: None,  # Important for the OptionsFlow Handler to be found
):
    """Test initializing the options flow and saving a new scan interval."""
    # 1. Create and register a ConfigEntry for which options should be changed
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=INITIAL_CONFIG_DATA,
        title="Scrutiny Options Test",
        # Options are initially empty or have defaults
        options={},
    )
    config_entry.add_to_hass(hass)

    # 2. Start the Options Flow for this ConfigEntry
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    await hass.async_block_till_done()

    # 3. Check if the options form is displayed correctly
    assert result["type"] == data_entry_flow.FlowResultType.FORM  # type: ignore
    assert result["step_id"] == "init"  # type: ignore

    # 4. Simulate user input in the Options Flow
    new_scan_interval = 15
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_SCAN_INTERVAL: new_scan_interval},
    )
    await hass.async_block_till_done()

    # 5. Check if the flow was successful and created/saved the options
    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY  # type: ignore
    # The options now include the three new fields in addition to scan_interval.
    # When only scan_interval is submitted, the others default to False.
    assert result2["data"][CONF_SCAN_INTERVAL] == new_scan_interval  # type: ignore
    assert result2["data"][CONF_SHOW_ARCHIVED] is False  # type: ignore
    assert result2["data"][CONF_ENABLE_CRITICAL_ATTRS] is False  # type: ignore
    assert result2["data"][CONF_ENABLE_ALL_ATTRS] is False  # type: ignore

    # 6. Check the options in the ConfigEntry were updated
    assert config_entry.options[CONF_SCAN_INTERVAL] == new_scan_interval
    assert config_entry.options[CONF_SHOW_ARCHIVED] is False
    assert config_entry.options[CONF_ENABLE_CRITICAL_ATTRS] is False
    assert config_entry.options[CONF_ENABLE_ALL_ATTRS] is False

    print(f"SUCCESS: {test_options_flow_init_and_save.__name__} passed!")


@pytest.mark.asyncio
async def test_options_flow_invalid_input(
    hass: HomeAssistant,
    enable_custom_integrations: None,
):
    """Test options flow raises InvalidData for invalid scan interval input."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=INITIAL_CONFIG_DATA,
        options={},  # Start with empty options
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    await hass.async_block_till_done()

    # Simulate invalid input (0 is below the minimum of 1).
    invalid_scan_interval = 0

    # Our handler catches the voluptuous error internally and re-shows the form
    # with an error key rather than raising InvalidData.
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_SCAN_INTERVAL: invalid_scan_interval},
    )

    # The flow should stay on the init step with an error, not complete.
    assert result2["type"] == "form"
    assert result2["step_id"] == "init"
    assert "scan_interval" in result2["errors"] or "base" in result2["errors"]
    # Options should be unchanged since we haven't submitted a valid value.
    assert config_entry.options == {}

    print(f"SUCCESS: {test_options_flow_invalid_input.__name__} passed!")
