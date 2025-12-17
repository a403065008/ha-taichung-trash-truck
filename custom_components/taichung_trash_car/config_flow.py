"""Config flow for Taichung Trash Car integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from .const import (
    DOMAIN, 
    CONF_LINEID, 
    CONF_HOME_LAT, 
    CONF_HOME_LON, 
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL
)

class TaichungTrashConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Taichung Trash Car."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return TaichungTrashOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # 建立設定檔，標題設為 "垃圾車 {LineID}"
            title = f"垃圾車 {user_input[CONF_LINEID]}"
            return self.async_create_entry(title=title, data=user_input)

        # 預設抓取目前 HA 設定的經緯度
        default_lat = self.hass.config.latitude
        default_lon = self.hass.config.longitude

        # 表單架構
        data_schema = vol.Schema({
            vol.Required(CONF_LINEID): str,
            vol.Optional(CONF_HOME_LAT): vol.Coerce(float),
            vol.Optional(CONF_HOME_LON): vol.Coerce(float),
            vol.Required(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
        })

        return self.async_show_form(
            step_id="user", 
            data_schema=data_schema, 
            errors=errors,
            description_placeholders={"common_name": "台中垃圾車"}
        )

class TaichungTrashOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a option flow for Taichung Trash Car."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # 預設抓取目前 HA 設定的經緯度
        default_lat = self.hass.config.latitude
        default_lon = self.hass.config.longitude

        data_schema = vol.Schema({
            vol.Required(
                CONF_LINEID, 
                default=self.config_entry.options.get(CONF_LINEID, self.config_entry.data.get(CONF_LINEID))
            ): str,
            vol.Optional(
                CONF_HOME_LAT, 
                default=self.config_entry.options.get(CONF_HOME_LAT, self.config_entry.data.get(CONF_HOME_LAT))
            ): vol.Coerce(float),
            vol.Optional(
                CONF_HOME_LON, 
                default=self.config_entry.options.get(CONF_HOME_LON, self.config_entry.data.get(CONF_HOME_LON))
            ): vol.Coerce(float),
            vol.Required(
                CONF_UPDATE_INTERVAL, 
                default=self.config_entry.options.get(CONF_UPDATE_INTERVAL, self.config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL))
            ): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
        })
        return self.async_show_form(step_id="init", data_schema=data_schema)