import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_TYPES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    for uc in entry.data["ucs"]:
        for key, (name, unit) in SENSOR_TYPES.items():
            entities.append(EdpNf3eSensor(coordinator, uc, key, name, unit))

    async_add_entities(entities)


class EdpNf3eSensor(CoordinatorEntity, SensorEntity):
    """Sensor individual da NF3e."""

    def __init__(self, coordinator, uc, key, name, unit):
        super().__init__(coordinator)
        self.uc = uc
        self.key = key
        self._attr_name = f"EDP NF3e {uc} {name}"
        self._attr_unique_id = f"edp_nf3e_{uc}_{key}"
        self._attr_native_unit_of_measurement = unit

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"edp_nf3e_{self.uc}")},
            "name": f"EDP NF3e {self.uc}",
            "manufacturer": "EDP",
            "model": "NF3e",
        }

    @property
    def native_value(self):
        data = self.coordinator.data.get(self.uc)

        if not data:
            return None

        value = data.get(self.key)

        if isinstance(value, str):
            return value

        try:
            return round(float(value), 4)
        except:
            return value

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data.get(self.uc)
        if not data:
            return {}

        return {
            "uc": self.uc,
            "ultima_atualizacao": self.coordinator.last_update_success,
        }