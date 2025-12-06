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
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._lineid = entry.data[CONF_LINEID]
        self._attr_unique_id = f"{self._lineid}_location"
        self._attr_name = f"垃圾車 {self._lineid} 位置"
        self._attr_icon = "mdi:truck"

    @property
    def state(self):
        # 如果 coordinator.data 是 None，代表未發車
        if not self.coordinator.data:
            return "未發車"
        return self.coordinator.data.get("location", "未知位置")

    @property
    def extra_state_attributes(self):
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
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._lineid = entry.data[CONF_LINEID]
        self._home_lat = entry.data[CONF_HOME_LAT]
        self._home_lon = entry.data[CONF_HOME_LON]
        
        self._attr_unique_id = f"{self._lineid}_distance"
        self._attr_name = f"垃圾車 {self._lineid} 距離"
        self._attr_icon = "mdi:map-marker-distance"
        self._attr_device_class = SensorDeviceClass.DISTANCE
        self._attr_native_unit_of_measurement = "m" # 單位：公尺

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None # 未發車時，距離顯示為 Unknown
        
        try:
            truck_lat = float(self.coordinator.data.get("Y"))
            truck_lon = float(self.coordinator.data.get("X"))
            
            # 使用 HA 內建函式計算距離
            distance = ha_location.distance(
                self._home_lat, self._home_lon,
                truck_lat, truck_lon
            )
            return int(distance) if distance is not None else None
        except (ValueError, TypeError):
            return None