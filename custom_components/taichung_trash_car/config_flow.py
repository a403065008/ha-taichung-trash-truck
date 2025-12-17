"""Config flow for Taichung Trash Car integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from .const import (
    DOMAIN, 
    CONF_LINEID, 
    CONF_PLATE_N,
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
            line_id = user_input.get(CONF_LINEID)
            plate_n = user_input.get(CONF_PLATE_N)

            if not (line_id or plate_n) or (line_id and plate_n):
                errors["base"] = "line_id_or_plate_n"
            else:
                title_id = line_id if line_id else plate_n
                title = f"垃圾車 {title_id}"
                return self.async_create_entry(title=title, data=user_input)

        # 預設抓取目前 HA 設定的經緯度
        default_lat = self.hass.config.latitude
        default_lon = self.hass.config.longitude

        # 表單架構
        data_schema = vol.Schema({
            vol.Optional(CONF_LINEID): str,
            vol.Optional(CONF_PLATE_N): str,
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
        errors = {}
        if user_input is not None:
            line_id = user_input.get(CONF_LINEID)
            plate_n = user_input.get(CONF_PLATE_N)

            if not (line_id or plate_n) or (line_id and plate_n):
                errors["base"] = "line_id_or_plate_n"
            else:
                return self.async_create_entry(title="", data=user_input)

        # 預設抓取目前 HA 設定的經緯度
        default_lat = self.hass.config.latitude
        default_lon = self.hass.config.longitude

        data_schema = vol.Schema({
            vol.Optional(
                CONF_LINEID, 
                default=self.config_entry.options.get(CONF_LINEID, self.config_entry.data.get(CONF_LINEID))
            ): str,
            vol.Optional(
                CONF_PLATE_N, 
                default=self.config_entry.options.get(CONF_PLATE_N, self.config_entry.data.get(CONF_PLATE_N))
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
        return self.async_show_form(step_id="init", data_schema=data_schema, errors=errors)