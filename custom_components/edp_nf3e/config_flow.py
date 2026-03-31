import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
import xml.etree.ElementTree as ET

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_IMAP_SERVER,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_FOLDER,
    CONF_REMETENTE,
    CONF_UCS,
    CONF_EXTRA_UC,
    DEFAULT_FOLDER,
    DEFAULT_REMETENTE,
    DEFAULT_DAYS,
)
from .util import (
    connect_imap,
    search_recent_emails,
    extract_xml_from_email,
)

_LOGGER = logging.getLogger(__name__)


class EdpNf3eConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Fluxo de configuração da integração EDP NF3e."""

    VERSION = 2

    def __init__(self):
        self.imap_server = None
        self.email = None
        self.password = None
        self.folder = None
        self.remetente = None
        self.detected_ucs = []

    # ---------------------------------------------------------
    # PASSO 1 — Dados IMAP
    # ---------------------------------------------------------
    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}

        if user_input is not None:
            self.imap_server = user_input[CONF_IMAP_SERVER]
            self.email = user_input[CONF_EMAIL]
            self.password = user_input[CONF_PASSWORD]
            self.folder = user_input[CONF_FOLDER]
            self.remetente = user_input[CONF_REMETENTE]

            ok = await self._async_detect_ucs()

            if not ok:
                errors["base"] = "imap_error"
            else:
                return await self.async_step_select_ucs()

        schema = vol.Schema(
            {
                vol.Required(CONF_IMAP_SERVER): str,
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(CONF_FOLDER, default=DEFAULT_FOLDER): str,
                vol.Optional(CONF_REMETENTE, default=DEFAULT_REMETENTE): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    # ---------------------------------------------------------
    # Detecta automaticamente as UCs (CORRIGIDO)
    # ---------------------------------------------------------
    async def _async_detect_ucs(self) -> bool:
        _LOGGER.info("Testando IMAP e detectando UCs…")

        try:
            mail = await self.hass.async_add_executor_job(
                connect_imap,
                self.imap_server,
                self.email,
                self.password,
                self.folder,
            )
        except Exception as e:
            _LOGGER.error("Erro IMAP: %s", e)
            return False

        try:
            email_ids = await self.hass.async_add_executor_job(
                search_recent_emails,
                mail,
                self.remetente,
                DEFAULT_DAYS,
            )

            ucs = set()

            for email_id in reversed(email_ids):
                xml_text = await self.hass.async_add_executor_job(
                    extract_xml_from_email, mail, email_id
                )
                if not xml_text:
                    continue

                # -------------------------------
                # CORREÇÃO: leitura com namespace
                # -------------------------------
                try:
                    root = ET.fromstring(xml_text)
                    ns = {"n": "http://www.portalfiscal.inf.br/nf3e"}

                    id_acesso = root.find(".//n:idAcesso", ns)

                    if id_acesso is not None and id_acesso.text:
                        uc = id_acesso.text.strip()
                        if uc.isdigit():
                            ucs.add(uc)
                            _LOGGER.info("UC detectada automaticamente: %s", uc)

                except Exception as e:
                    _LOGGER.error("Erro ao processar XML para detectar UC: %s", e)

            self.detected_ucs = sorted(list(ucs))
            _LOGGER.info("UCs detectadas: %s", self.detected_ucs)
            return True

        finally:
            try:
                mail.logout()
            except:
                pass

    # ---------------------------------------------------------
    # PASSO 2 — Seleção das UCs
    # ---------------------------------------------------------
    async def async_step_select_ucs(self, user_input=None) -> FlowResult:
        errors = {}

        if user_input is not None:
            selected = user_input.get(CONF_UCS, [])
            extra = user_input.get(CONF_EXTRA_UC)

            if extra:
                if extra.isdigit():
                    selected.append(extra)
                else:
                    errors["base"] = "invalid_uc"

            selected = sorted(list(set(selected)))

            if not selected:
                errors["base"] = "no_uc_selected"
            else:
                await self.async_set_unique_id(self.email)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"EDP NF3e ({self.email})",
                    data={
                        CONF_IMAP_SERVER: self.imap_server,
                        CONF_EMAIL: self.email,
                        CONF_PASSWORD: self.password,
                        CONF_FOLDER: self.folder,
                        CONF_REMETENTE: self.remetente,
                        CONF_UCS: selected,
                    },
                )

        schema = vol.Schema(
            {
                vol.Optional(CONF_UCS, default=self.detected_ucs): cv.multi_select(self.detected_ucs),
                vol.Optional(CONF_EXTRA_UC): str,
            }
        )

        return self.async_show_form(
            step_id="select_ucs",
            data_schema=schema,
            errors=errors,
        )


# ---------------------------------------------------------
# FLUXO DE OPÇÕES
# ---------------------------------------------------------
class EdpNf3eOptionsFlow(config_entries.OptionsFlow):
    """Fluxo de opções da integração."""

    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        errors = {}

        if user_input is not None:
            ucs = user_input.get(CONF_UCS, [])
            extra = user_input.get(CONF_EXTRA_UC)

            if extra:
                if extra.isdigit():
                    ucs.append(extra)
                else:
                    errors["base"] = "invalid_uc"

            ucs = sorted(list(set(ucs)))

            if not ucs:
                errors["base"] = "no_uc_selected"
            else:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_FOLDER: user_input.get(CONF_FOLDER),
                        CONF_REMETENTE: user_input.get(CONF_REMETENTE),
                        CONF_UCS: ucs,
                    },
                )

        schema = vol.Schema(
            {
                vol.Optional(CONF_FOLDER, default=self.entry.data.get(CONF_FOLDER)): str,
                vol.Optional(CONF_REMETENTE, default=self.entry.data.get(CONF_REMETENTE)): str,
                vol.Optional(CONF_UCS, default=self.entry.data.get(CONF_UCS)): cv.multi_select(
                    self.entry.data.get(CONF_UCS)
                ),
                vol.Optional(CONF_EXTRA_UC): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)


async def async_get_options_flow(config_entry):
    return EdpNf3eOptionsFlow(config_entry)