import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    SENSOR_DEFINITIONS,
    SUMMARY_SENSOR_KEY,
    SUMMARY_SENSOR_NAME,
    SUMMARY_SENSOR_UNIT,
)
from .coordinator import EdpNf3eCoordinator

_LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------
# 🔥 SETUP DOS SENSORES
# ---------------------------------------------------------
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: EdpNf3eCoordinator = data["coordinator"]

    entities = []

    # Para cada UC selecionada, cria sensores
    for uc in coordinator.ucs:
        # Sensor Resumo
        entities.append(EdpNf3eSummarySensor(coordinator, uc))

        # Sensores individuais
        for key, name, unit in SENSOR_DEFINITIONS:
            entities.append(EdpNf3eSensor(coordinator, uc, key, name, unit))

    async_add_entities(entities)


# ---------------------------------------------------------
# 🔵 SENSOR INDIVIDUAL
# ---------------------------------------------------------
class EdpNf3eSensor(SensorEntity):
    """Sensor individual por UC."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, uc, key, name, unit):
        self.coordinator = coordinator
        self.uc = uc
        self.key = key
        self._attr_name = f"{name}"
        self._attr_unique_id = f"edp_{uc}_{key}"
        self._attr_native_unit_of_measurement = unit

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, uc)},
            name=f"EDP – {uc}",
            manufacturer="EDP São Paulo",
            model="NF3e",
        )

    @property
    def native_value(self):
        data = self.coordinator.data_by_uc.get(self.uc)
        if not data:
            return None
        return data.get(self.key)

    @property
    def available(self):
        return self.coordinator.data_by_uc.get(self.uc) is not None

    async def async_update(self):
        await self.coordinator.async_request_refresh()


# ---------------------------------------------------------
# 🟣 SENSOR RESUMO
# ---------------------------------------------------------
class EdpNf3eSummarySensor(SensorEntity):
    """Sensor resumo por UC com atributos completos."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, uc):
        self.coordinator = coordinator
        self.uc = uc
        self._attr_name = SUMMARY_SENSOR_NAME
        self._attr_unique_id = f"edp_{uc}_{SUMMARY_SENSOR_KEY}"
        self._attr_native_unit_of_measurement = SUMMARY_SENSOR_UNIT

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, uc)},
            name=f"EDP – {uc}",
            manufacturer="EDP São Paulo",
            model="NF3e",
        )

    @property
    def native_value(self):
        """Valor principal do sensor resumo (valor total da conta)."""
        data = self.coordinator.data_by_uc.get(self.uc)
        if not data:
            return None
        return data.get("valor_total")

    @property
    def extra_state_attributes(self):
        """Atributos extras com JSON estruturado."""
        data = self.coordinator.data_by_uc.get(self.uc)
        if not data:
            return None

        # Remove valores None para deixar mais limpo
        clean = {k: v for k, v in data.items() if v is not None}

        return clean

    @property
    def available(self):
        return self.coordinator.data_by_uc.get(self.uc) is not None

    async def async_update(self):
        await self.coordinator.async_request_refresh()