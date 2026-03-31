import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    SENSOR_DEFINITIONS,
    SUMMARY_SENSOR_KEY,
    SUMMARY_SENSOR_NAME,
    SUMMARY_SENSOR_UNIT,
)

_LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------
# SENSOR INDIVIDUAL POR UC
# ---------------------------------------------------------
class EdpNf3eSensor(CoordinatorEntity, SensorEntity):
    """Sensor individual da integração EDP NF3e."""

    def __init__(self, coordinator, uc, key, name, unit):
        super().__init__(coordinator)
        self.uc = uc
        self.key = key
        self._attr_name = f"EDP NF3e {uc} {name}"
        self._attr_unique_id = f"edp_nf3e_{uc}_{key}"
        self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self):
        data = self.coordinator.data.get(self.uc)
        if not data:
            return None
        return data.get(self.key)


# ---------------------------------------------------------
# SENSOR RESUMO
# ---------------------------------------------------------
class EdpNf3eResumoSensor(CoordinatorEntity, SensorEntity):
    """Sensor resumo com informações agregadas."""

    def __init__(self, coordinator, uc):
        super().__init__(coordinator)
        self.uc = uc
        self.key = SUMMARY_SENSOR_KEY
        self._attr_name = f"EDP NF3e {uc} {SUMMARY_SENSOR_NAME}"
        self._attr_unique_id = f"edp_nf3e_{uc}_resumo"
        self._attr_native_unit_of_measurement = SUMMARY_SENSOR_UNIT

    @property
    def native_value(self):
        data = self.coordinator.data.get(self.uc)
        if not data:
            return None

        try:
            consumo = data.get("energia_consumida", 0)
            geracao = data.get("energia_injetada", 0)
            valor_total = data.get("valor_total", 0)
            tarifa_consumo = data.get("tarifa_consumo", 0)

            return (
                f"Consumo: {consumo} kWh | "
                f"Geração: {geracao} kWh | "
                f"Tarifa: R$ {tarifa_consumo:.4f} | "
                f"Total: R$ {valor_total:.2f}"
            )
        except Exception as e:
            _LOGGER.error("Erro ao montar resumo da UC %s: %s", self.uc, e)
            return None


# ---------------------------------------------------------
# SETUP DOS SENSORES
# ---------------------------------------------------------
async def async_setup_entry(hass, entry, async_add_entities):
    """Cria todos os sensores da integração."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities = []

    for uc in entry.data["ucs"]:
        # Sensores individuais
        for key, name, unit in SENSOR_DEFINITIONS:
            entities.append(EdpNf3eSensor(coordinator, uc, key, name, unit))

        # Sensor resumo
        entities.append(EdpNf3eResumoSensor(coordinator, uc))

    async_add_entities(entities)