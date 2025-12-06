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
            vol.Required(CONF_LINEID, default="15052"): str,
            vol.Required(CONF_HOME_LAT, default=default_lat): vol.Coerce(float),
            vol.Required(CONF_HOME_LON, default=default_lon): vol.Coerce(float),
            vol.Required(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
        })

        return self.async_show_form(
            step_id="user", 
            data_schema=data_schema, 
            errors=errors,
            description_placeholders={"common_name": "台中垃圾車"}
        )