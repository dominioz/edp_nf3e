import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .coordinator import EdpNf3eCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Configura a integração EDP NF3e."""
    email = entry.data.get("email")
    _LOGGER.info("Iniciando integração EDP NF3e para %s", email)

    hass.data.setdefault(DOMAIN, {})

    coordinator = EdpNf3eCoordinator(hass, entry)

    # Primeira atualização obrigatória
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator
    }

    # Carrega a plataforma sensor
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Descarrega a integração."""
    _LOGGER.info("Descarregando integração EDP NF3e (%s)", entry.entry_id)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok