import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfCurrency
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Configura sensores para cada UC monitorada."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for uc in coordinator.ucs:
        entities.append(EdpNf3eSensor(coordinator, uc))

    async_add_entities(entities)


class EdpNf3eSensor(CoordinatorEntity, SensorEntity):
    """Sensor principal da NF3e por UC."""

    def __init__(self, coordinator, uc):
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._uc = uc
        self._attr_name = f"EDP NF3e {uc}"
        self._attr_unique_id = f"{DOMAIN}_{uc}"
        self._attr_native_unit_of_measurement = UnitOfCurrency.REAL

    @property
    def available(self):
        """Sensor disponível se houver dados para a UC."""
        return (
            self._uc in self._coordinator.data_by_uc
            and self._coordinator.data_by_uc[self._uc] is not None
        )

    @property
    def native_value(self):
        """Valor total da fatura."""
        data = self._coordinator.data_by_uc.get(self._uc)
        if not data:
            return None
        return data.get("valor_total")

    @property
    def extra_state_attributes(self):
        """Atributos completos da NF3e."""
        data = self._coordinator.data_by_uc.get(self._uc)
        if not data:
            return {}

        tarifas = data.get("tarifas", {})

        return {
            # Identificação
            "uc": data.get("uc"),
            "competencia": data.get("nf3e_raw", {}).get("competencia"),

            # Energia
            "energia_consumida_kwh": data.get("energia_consumida"),
            "energia_injetada_kwh": data.get("energia_injetada"),

            # Tarifas agregadas
            "tarifa_base": data.get("tarifa_base"),
            "tarifa_real": data.get("tarifa_real"),
            "tarifa_paga": data.get("tarifa_paga"),

            # Tarifas individuais
            "tusd_fornecida": tarifas.get("tusd_fornecida"),
            "te_fornecida": tarifas.get("te_fornecida"),
            "tusd_injetada": tarifas.get("tusd_injetada"),
            "te_injetada": tarifas.get("te_injetada"),

            # Tarifas calculadas
            "tarifa_consumida": tarifas.get("tarifa_consumida"),
            "tarifa_injetada": tarifas.get("tarifa_injetada"),

            # Valores
            "valor_total": data.get("valor_total"),
            "valor_bandeiras": data.get("valor_bandeiras"),
            "iluminacao_publica": data.get("iluminacao_publica"),
            "compensacoes": data.get("compensacoes"),
            "te_tusd_total": data.get("te_tusd"),

            # Datas
            "data_vencimento": data.get("data_vencimento"),
            "ultima_leitura": data.get("ultima_leitura"),
            "proxima_leitura": data.get("proxima_leitura"),

            # Período
            "dias_periodo": data.get("dias_periodo"),
            "dias_bandeira": data.get("dias_bandeira"),
        }