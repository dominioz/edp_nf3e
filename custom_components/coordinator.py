import logging
import os
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
    save_last_xml,
    load_last_xml,
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
        self.ucs = config_entry.options.get(CONF_UCS, config_entry.data.get(CONF_UCS, []))

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

        # Inicializa cache mantendo dados antigos
        if not self.data_by_uc:
            self.data_by_uc = {uc: None for uc in self.ucs}

        # Tenta conectar ao IMAP
        try:
            mail = connect_imap(self.server, self.email, self.password, self.folder)
        except Exception as e:
            _LOGGER.error("Erro ao conectar ao IMAP: %s", e)
            return self.data_by_uc  # mantém dados antigos

        try:
            email_ids = search_recent_emails(mail, self.remetente, DEFAULT_DAYS)
            _LOGGER.debug("E-mails encontrados: %s", email_ids)

            # Prepara estrutura para novos dados
            new_data = {uc: None for uc in self.ucs}

            # Varre e-mails do mais recente para o mais antigo
            for email_id in reversed(email_ids):
                xml_text = extract_xml_from_email(mail, email_id)
                if not xml_text:
                    continue

                uc = extract_uc_from_xml(xml_text)
                if not uc or uc not in self.ucs:
                    continue

                # Se já temos dados dessa UC, ignoramos (queremos o mais recente)
                if new_data.get(uc):
                    continue

                # Salva XML persistente por UC
                xml_path = f"{self.hass.config.path()}/custom_components/{DOMAIN}/last_xml/{uc}.xml"
                save_last_xml(xml_text, xml_path)

                # Parse completo
                parsed = parse_nf3e(xml_text)
                new_data[uc] = parsed

            # Agora tratamos UCs sem e-mail novo
            for uc in self.ucs:
                if new_data[uc] is None:
                    # Tenta carregar XML persistido
                    xml_path = f"{self.hass.config.path()}/custom_components/{DOMAIN}/last_xml/{uc}.xml"
                    xml_text = load_last_xml(xml_path)

                    if xml_text:
                        try:
                            parsed = parse_nf3e(xml_text)
                            new_data[uc] = parsed
                        except Exception as err:
                            _LOGGER.error("Erro ao parsear XML salvo da UC %s: %s", uc, err)
                            new_data[uc] = self.data_by_uc.get(uc)  # mantém dados antigos
                    else:
                        # Sem XML salvo → mantém dados antigos
                        new_data[uc] = self.data_by_uc.get(uc)

            # Atualiza cache
            self.data_by_uc = new_data
            return self.data_by_uc

        finally:
            try:
                mail.logout()
            except Exception:
                pass