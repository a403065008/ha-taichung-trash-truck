"""Sensor platform for Taichung Trash Car."""
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import location as ha_location

from .const import DOMAIN, CONF_LINEID, CONF_HOME_LAT, CONF_HOME_LON

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # 加入兩個實體：位置感測器、距離感測器
    async_add_entities([
        TrashTruckLocationSensor(coordinator, entry),
        TrashTruckDistanceSensor(coordinator, entry)
    ])

# --- 實體 1: 垃圾車位置與地圖座標 ---
class TrashTruckLocationSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{self._entry.entry_id}_location"
        self._attr_icon = "mdi:truck"

    @property
    def _config(self):
        """Return the config dictionary from options or data."""
        return self._entry.options or self._entry.data

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"垃圾車 {self._config.get(CONF_LINEID)} 位置"

    @property
    def state(self):
        """Return the state of the sensor."""
        # 如果 coordinator.data 是 None，代表未發車
        if not self.coordinator.data:
            return "未發車"
        return self.coordinator.data.get("location", "未知位置")

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        if not self.coordinator.data:
            return {}
        
        # 將 X, Y 轉為地圖卡片可讀的格式
        try:
            return {
                "latitude": float(self.coordinator.data.get("Y")),
                "longitude": float(self.coordinator.data.get("X")),
                "car_plate": self.coordinator.data.get("car"),
                "update_time": self.coordinator.data.get("time")
            }
        except (ValueError, TypeError):
            return {}

# --- 實體 2: 距離感測器 (純數值，方便自動化) ---
class TrashTruckDistanceSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry
        
        self._attr_unique_id = f"{self._entry.entry_id}_distance"
        self._attr_icon = "mdi:map-marker-distance"
        self._attr_device_class = SensorDeviceClass.DISTANCE
        self._attr_native_unit_of_measurement = "m" # 單位：公尺

    @property
    def _config(self):
        """Return the config dictionary from options or data."""
        return self._entry.options or self._entry.data

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"垃圾車 {self._config.get(CONF_LINEID)} 距離"

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        if not self.coordinator.data:
            return None # 未發車時，距離顯示為 Unknown
        
        config = self._config
        home_lat = config.get(CONF_HOME_LAT)
        home_lon = config.get(CONF_HOME_LON)
        
        # 確保經緯度存在
        if home_lat is None or home_lon is None:
            return None

        try:
            truck_lat = float(self.coordinator.data.get("Y"))
            truck_lon = float(self.coordinator.data.get("X"))
            
            # 使用 HA 內建函式計算距離
            distance = ha_location.distance(
                home_lat, home_lon,
                truck_lat, truck_lon
            )
            return int(distance) if distance is not None else None
        except (ValueError, TypeError):
            return None