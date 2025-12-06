"""The Taichung Trash Car integration."""
import logging
import async_timeout
import aiohttp
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, API_URL, CONF_LINEID, CONF_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    lineid = entry.data[CONF_LINEID]
    update_interval = entry.data.get(CONF_UPDATE_INTERVAL, 60)

    # 定義 API 抓取邏輯
    async def async_update_data():
        async with aiohttp.ClientSession() as session:
            try:
                # 設定 10 秒超時
                async with async_timeout.timeout(10):
                    async with session.get(API_URL) as response:
                        response.raise_for_status()
                        data = await response.json()
                        
                        # 篩選特定 LineID
                        # 注意：如果API回傳格式有變，這裡需要調整
                        target_truck = next(
                            (item for item in data if item.get("lineid") == lineid), 
                            None
                        )
                        
                        # 如果找不到車(可能未發車)，回傳 None 或空字典，不要報錯
                        if not target_truck:
                            return None
                            
                        return target_truck

            except Exception as err:
                raise UpdateFailed(f"Error communicating with API: {err}")

    # 建立協調器 (Coordinator)，它會負責定時更新
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"trash_truck_{lineid}",
        update_method=async_update_data,
        update_interval=timedelta(seconds=update_interval),
    )

    # 首次立即抓取
    await coordinator.async_config_entry_first_refresh()

    # 將 coordinator 存入 hass.data，讓 sensor.py 可以取用
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # 載入 Sensor 平台
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok