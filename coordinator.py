import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    CONF_IMAP_SERVER,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_FOLDER,
    CONF_REMETENTE,
    CONF_UCS,
    DEFAULT_DAYS,
)
from .util import (
    connect_imap,
    search_recent_emails,
    extract_xml_from_email,
    extract_uc_from_xml,
    parse_nf3e,
)

_LOGGER = logging.getLogger(__name__)


class EdpNf3eCoordinator(DataUpdateCoordinator):
    """Coordenador que busca e processa NF3e para múltiplas UCs."""

    def __init__(self, hass: HomeAssistant, config_entry):
        self.hass = hass
        self.entry = config_entry

        self.server = config_entry.data[CONF_IMAP_SERVER]
        self.email = config_entry.data[CONF_EMAIL]
        self.password = config_entry.data[CONF_PASSWORD]
        self.folder = config_entry.data.get(CONF_FOLDER)
        self.remetente = config_entry.data.get(CONF_REMETENTE)
        self.ucs = config_entry.data.get(CONF_UCS, [])

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_coordinator",
            update_interval=timedelta(hours=12),
        )

        # Cache por UC
        self.data_by_uc = {}

    async def _async_update_data(self):
        """Atualiza dados de todas as UCs monitoradas."""
        try:
            return await self.hass.async_add_executor_job(self._update_all_ucs)
        except Exception as err:
            raise UpdateFailed(f"Erro ao atualizar dados: {err}") from err

    def _update_all_ucs(self):
        """Processa todas as UCs monitoradas."""
        _LOGGER.debug("Iniciando atualização das UCs: %s", self.ucs)

        try:
            mail = connect_imap(self.server, self.email, self.password, self.folder)
        except Exception as e:
            _LOGGER.error("Erro ao conectar ao IMAP: %s", e)
            raise

        try:
            email_ids = search_recent_emails(mail, self.remetente, DEFAULT_DAYS)
            _LOGGER.debug("E-mails encontrados: %s", email_ids)

            # Limpa cache
            self.data_by_uc = {uc: None for uc in self.ucs}

            # Varre e-mails do mais recente para o mais antigo
            for email_id in reversed(email_ids):
                xml_text = extract_xml_from_email(mail, email_id)
                if not xml_text:
                    continue

                uc = extract_uc_from_xml(xml_text)
                if not uc or uc not in self.ucs:
                    continue

                # Se já temos dados dessa UC, ignoramos (queremos o mais recente)
                if self.data_by_uc.get(uc):
                    continue

                # Parse completo
                parsed = parse_nf3e(xml_text)
                self.data_by_uc[uc] = parsed

            return self.data_by_uc

        finally:
            try:
                mail.logout()
            except:
                pass