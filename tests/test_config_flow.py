import pytest
from unittest.mock import patch, AsyncMock

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.scrutiny.config_flow import ScrutinyConfigFlowHandler
from custom_components.scrutiny.const import (
    CONF_ENABLE_ALL_ATTRS,
    CONF_ENABLE_CRITICAL_ATTRS,
    CONF_SCAN_INTERVAL,
    CONF_SHOW_ARCHIVED,
    CONF_URL,
    CONF_VERIFY_SSL,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)
from custom_components.scrutiny.api import (
    ScrutinyApiConnectionError,
    ScrutinyApiResponseError,
    ScrutinyApiAuthError,
)

TEST_URL = "http://scrutiny.test.local:8080"
USER_INPUT_FULL = {
    CONF_URL: TEST_URL,
    CONF_VERIFY_SSL: True,
    CONF_SCAN_INTERVAL: 30,
    CONF_SHOW_ARCHIVED: False,
    CONF_ENABLE_CRITICAL_ATTRS: True,
    CONF_ENABLE_ALL_ATTRS: False,
}

USER_INPUT_DEFAULTS = {
    CONF_URL: "http://scrutiny.defaults.local:8080",
}


@pytest.mark.asyncio
async def test_config_flow_user_step_success(
    hass: HomeAssistant,
    enable_custom_integrations: None,
):
    """Test a successful user configuration flow."""
    with (
        patch(
            "custom_components.scrutiny.config_flow.ScrutinyConfigFlowHandler._test_connection",
            new_callable=AsyncMock,
            return_value=None,
        ) as mock_test_connection,
        patch(
            "custom_components.scrutiny.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["errors"] == {}

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT_FULL
        )
        await hass.async_block_till_done()

    mock_test_connection.assert_called_once_with(
        USER_INPUT_FULL[CONF_URL].rstrip("/"), USER_INPUT_FULL[CONF_VERIFY_SSL]
    )

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == f"Scrutiny ({USER_INPUT_FULL[CONF_URL].rstrip('/')})"

    result2_data = result2["data"]
    assert result2_data[CONF_URL] == USER_INPUT_FULL[CONF_URL].rstrip("/")
    assert result2_data[CONF_VERIFY_SSL] == USER_INPUT_FULL[CONF_VERIFY_SSL]
    assert CONF_SCAN_INTERVAL not in result2_data

    result2_options = result2["options"]
    assert result2_options[CONF_SCAN_INTERVAL] == USER_INPUT_FULL[CONF_SCAN_INTERVAL]
    assert result2_options[CONF_SHOW_ARCHIVED] == USER_INPUT_FULL[CONF_SHOW_ARCHIVED]
    assert result2_options[CONF_ENABLE_CRITICAL_ATTRS] == USER_INPUT_FULL[CONF_ENABLE_CRITICAL_ATTRS]
    assert result2_options[CONF_ENABLE_ALL_ATTRS] == USER_INPUT_FULL[CONF_ENABLE_ALL_ATTRS]

    config_entry_obj = result2["result"]
    assert isinstance(config_entry_obj, config_entries.ConfigEntry)
    assert config_entry_obj.unique_id == USER_INPUT_FULL[CONF_URL].rstrip("/")

    print(f"SUCCESS: {test_config_flow_user_step_success.__name__} passed!")


@pytest.mark.asyncio
async def test_config_flow_user_step_cannot_connect(
    hass: HomeAssistant,
    enable_custom_integrations: None,
):
    """Test config flow when _test_connection raises ScrutinyApiConnectionError."""
    with patch(
        "custom_components.scrutiny.config_flow.ScrutinyConfigFlowHandler._test_connection",
        new_callable=AsyncMock,
        side_effect=ScrutinyApiConnectionError("Simulated connection error"),
    ) as mock_test_connection:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT_FULL
        )
        await hass.async_block_till_done()

    mock_test_connection.assert_called_once_with(
        USER_INPUT_FULL[CONF_URL].rstrip("/"), USER_INPUT_FULL[CONF_VERIFY_SSL]
    )
    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["step_id"] == "user"
    assert result2["errors"].get("base") == "cannot_connect"

    print(f"SUCCESS: {test_config_flow_user_step_cannot_connect.__name__} passed!")


@pytest.mark.asyncio
async def test_config_flow_user_step_already_configured(
    hass: HomeAssistant,
    enable_custom_integrations: None,
):
    """Test config flow aborts when the same URL is already configured."""
    unique_id = USER_INPUT_FULL[CONF_URL].rstrip("/")
    MockConfigEntry(
        domain=DOMAIN,
        unique_id=unique_id,
        data={CONF_URL: unique_id, CONF_VERIFY_SSL: True},
        title=f"Scrutiny ({unique_id})",
    ).add_to_hass(hass)

    with patch(
        "custom_components.scrutiny.config_flow.ScrutinyConfigFlowHandler._test_connection",
        new_callable=AsyncMock,
        return_value=None,
    ) as mock_test_connection:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT_FULL
        )
        await hass.async_block_till_done()

    mock_test_connection.assert_not_called()
    assert result2["type"] == data_entry_flow.FlowResultType.ABORT
    assert result2["reason"] == "already_configured"

    print(f"SUCCESS: {test_config_flow_user_step_already_configured.__name__} passed!")


@pytest.mark.asyncio
async def test_config_flow_user_step_defaults(
    hass: HomeAssistant,
    enable_custom_integrations: None,
):
    """Test config flow uses defaults when only URL is provided."""
    with (
        patch(
            "custom_components.scrutiny.config_flow.ScrutinyConfigFlowHandler._test_connection",
            new_callable=AsyncMock,
            return_value=None,
        ) as mock_test_connection,
        patch(
            "custom_components.scrutiny.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT_DEFAULTS
        )
        await hass.async_block_till_done()

    expected_url = USER_INPUT_DEFAULTS[CONF_URL].rstrip("/")
    mock_test_connection.assert_called_once_with(expected_url, DEFAULT_VERIFY_SSL)

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == f"Scrutiny ({expected_url})"

    result2_data = result2["data"]
    assert result2_data[CONF_URL] == expected_url
    assert result2_data[CONF_VERIFY_SSL] == DEFAULT_VERIFY_SSL
    assert result2["options"][CONF_SCAN_INTERVAL] == DEFAULT_SCAN_INTERVAL_MINUTES

    config_entry_obj = result2["result"]
    assert config_entry_obj.unique_id == expected_url

    print(f"SUCCESS: {test_config_flow_user_step_defaults.__name__} passed!")
