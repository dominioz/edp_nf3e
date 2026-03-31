import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_IMAP_SERVER,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_FOLDER,
    CONF_REMETENTE,
    CONF_UCS,
)
from .util import (
    connect_imap,
    search_recent_emails,
    extract_xml_from_email,
    parse_nf3e,
)

_LOGGER = logging.getLogger(__name__)


class EdpNf3eCoordinator(DataUpdateCoordinator):
    """Coordinator responsável por atualizar os dados da NF3e."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self.entry = entry

        self.imap_server = entry.data[CONF_IMAP_SERVER]
        self.email = entry.data[CONF_EMAIL]
        self.password = entry.data[CONF_PASSWORD]
        self.folder = entry.data[CONF_FOLDER]
        self.remetente = entry.data[CONF_REMETENTE]
        self.ucs = entry.data[CONF_UCS]

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=6),
        )

    async def _async_update_data(self):
        """Atualiza os dados de todas as UCs configuradas."""
        try:
            return await self.hass.async_add_executor_job(self._update_all_ucs)

        except Exception as err:
            raise UpdateFailed(f"Erro ao atualizar dados: {err}") from err

    # ---------------------------------------------------------
    # Atualiza todas as UCs
    # ---------------------------------------------------------
    def _update_all_ucs(self):
        """Processa e retorna os dados de todas as UCs."""
        data = {}

        try:
            mail = connect_imap(
                self.imap_server,
                self.email,
                self.password,
                self.folder,
            )
        except Exception as e:
            _LOGGER.error("Erro ao conectar ao IMAP: %s", e)
            return data

        # Busca e-mails recentes
        email_ids = search_recent_emails(mail, self.remetente, 360)

        # Processa cada UC separadamente
        for uc in self.ucs:
            uc_data = self._process_uc(mail, email_ids, uc)
            if uc_data:
                data[uc] = uc_data

        try:
            mail.logout()
        except:
            pass

        return data

    # ---------------------------------------------------------
    # Processa uma UC específica
    # ---------------------------------------------------------
    def _process_uc(self, mail, email_ids, uc):
        """Extrai a NF3e correspondente à UC e processa os dados."""
        for email_id in reversed(email_ids):
            xml_text = extract_xml_from_email(mail, email_id)
            if not xml_text:
                continue

            # Verifica se o XML pertence à UC desejada
            if uc not in xml_text:
                continue

            try:
                parsed = parse_nf3e(xml_text)
                _LOGGER.info("NF3e processada para UC %s", uc)
                return parsed

            except Exception as e:
                _LOGGER.error("Erro ao processar NF3e da UC %s: %s", uc, e)

        _LOGGER.warning("Nenhuma NF3e encontrada para UC %s", uc)
        return None