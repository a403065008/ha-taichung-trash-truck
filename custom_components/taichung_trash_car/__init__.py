"""The Taichung Trash Car integration."""
import asyncio
import logging
import ssl
import async_timeout
import aiohttp
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, API_URL, CONF_LINEID, CONF_PLATE_N, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]

# 用於儲存上次成功取得的資料，避免 API 暫時失敗時變成 unavailable
_last_successful_data = {}

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # 監聽選項更新
    entry.async_on_unload(entry.add_update_listener(update_listener))

    # 從 options 或 data 讀取設定
    config = entry.options or entry.data
    lineid = config.get(CONF_LINEID)
    plate_n = config.get(CONF_PLATE_N)
    update_interval = config.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    
    entry_id = entry.entry_id

    # 定義 API 抓取邏輯
    async def async_update_data():
        # 台中市政府 API 的 SSL 憑證有問題，需要跳過驗證
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            try:
                # 設定 15 秒超時 (增加容錯時間)
                async with async_timeout.timeout(15):
                    async with session.get(API_URL) as response:
                        response.raise_for_status()
                        data = await response.json()
                        
                        # 篩選特定 LineID 或車牌
                        if lineid:
                            target_truck = next(
                                (item for item in data if item.get("lineid") == lineid), 
                                None
                            )
                        elif plate_n:
                            target_truck = next(
                                (item for item in data if item.get("car") == plate_n),
                                None
                            )
                        else:
                            target_truck = None
                        
                        # 儲存成功取得的資料
                        if target_truck:
                            _last_successful_data[entry_id] = target_truck
                            return target_truck
                        else:
                            # 找不到車(可能未發車)，回傳 None
                            return None

            except asyncio.TimeoutError:
                _LOGGER.warning(f"API request timed out for {entry_id}, using last successful data")
                return _last_successful_data.get(entry_id)
                
            except aiohttp.ClientError as err:
                _LOGGER.warning(f"API connection error for {entry_id}: {err}, using last successful data")
                return _last_successful_data.get(entry_id)
                
            except Exception as err:
                _LOGGER.error(f"Unexpected error for {entry_id}: {err}")
                if entry_id in _last_successful_data:
                    return _last_successful_data.get(entry_id)
                # 只有在完全沒有舊資料時才報錯
                raise UpdateFailed(f"Error communicating with API for {entry_id}: {err}")

    # 建立協調器 (Coordinator)，它會負責定時更新
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"trash_truck_{entry_id}",
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

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)