import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
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
    extract_uc_from_xml,
    normalize_uc,
)

_LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------
# 🔥 CONFIG FLOW PRINCIPAL
# ---------------------------------------------------------
class EdpNf3eConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self.imap_server = None
        self.email = None
        self.password = None
        self.folder = None
        self.remetente = None
        self.detected_ucs = []

    # -----------------------------------------------------
    # 🟦 Etapa 1 — Dados IMAP
    # -----------------------------------------------------
    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}

        if user_input is not None:
            self.imap_server = user_input[CONF_IMAP_SERVER]
            self.email = user_input[CONF_EMAIL]
            self.password = user_input[CONF_PASSWORD]
            self.folder = user_input[CONF_FOLDER]
            self.remetente = user_input[CONF_REMETENTE]

            # Testa conexão e detecta UCs
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

    # -----------------------------------------------------
    # 🔍 Detecta UCs automaticamente
    # -----------------------------------------------------
    async def _async_detect_ucs(self):
        try:
            mail = await self.hass.async_add_executor_job(
                connect_imap,
                self.imap_server,
                self.email,
                self.password,
                self.folder,
            )
        except Exception as e:
            _LOGGER.error("Erro ao conectar ao IMAP: %s", e)
            return False

        try:
            email_ids = await self.hass.async_add_executor_job(
                search_recent_emails,
                mail,
                self.remetente,
                DEFAULT_DAYS,
            )

            ucs = set()

            # Varre e-mails do mais recente para o mais antigo
            for email_id in reversed(email_ids):
                xml_text = await self.hass.async_add_executor_job(
                    extract_xml_from_email, mail, email_id
                )
                if not xml_text:
                    continue

                uc = extract_uc_from_xml(xml_text)
                if uc:
                    ucs.add(uc)

            self.detected_ucs = sorted(list(ucs))
            _LOGGER.debug("UCs detectadas: %s", self.detected_ucs)

            return True

        finally:
            try:
                mail.logout()
            except:
                pass

    # -----------------------------------------------------
    # 🟦 Etapa 2 — Seleção de UCs
    # -----------------------------------------------------
    async def async_step_select_ucs(self, user_input=None) -> FlowResult:
        errors = {}

        if user_input is not None:
            selected = user_input.get(CONF_UCS, [])
            extra = user_input.get(CONF_EXTRA_UC)

            # Normaliza UC manual
            if extra:
                extra_norm = normalize_uc(extra)
                if not extra_norm:
                    errors["base"] = "invalid_uc"
                else:
                    selected.append(extra_norm)

            # Remove duplicadas
            selected = sorted(list(set(selected)))

            if not selected:
                errors["base"] = "no_uc_selected"
            else:
                # Criar ID único baseado no e-mail
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

        # Schema dinâmico
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_UCS,
                    default=self.detected_ucs,
                ): cv.multi_select(self.detected_ucs),
                vol.Optional(CONF_EXTRA_UC): str,
            }
        )
        return self.async_show_form(
            step_id="select_ucs",
            data_schema=schema,
            errors=errors,
        )


# ---------------------------------------------------------
# 🔧 OPTIONS FLOW
# ---------------------------------------------------------
class EdpNf3eOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        errors = {}

        if user_input is not None:
            # Normaliza UC manual
            extra = user_input.get(CONF_EXTRA_UC)
            ucs = user_input.get(CONF_UCS, [])

            if extra:
                extra_norm = normalize_uc(extra)
                if not extra_norm:
                    errors["base"] = "invalid_uc"
                else:
                    ucs.append(extra_norm)

            ucs = sorted(list(set(ucs)))

            return self.async_create_entry(
                title="",
                data={
                    CONF_FOLDER: user_input.get(CONF_FOLDER),
                    CONF_REMETENTE: user_input.get(CONF_REMETENTE),
                    CONF_UCS: ucs,
                },
            )

        # Schema
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_FOLDER,
                    default=self.entry.data.get(CONF_FOLDER),
                ): str,
                vol.Optional(
                    CONF_REMETENTE,
                    default=self.entry.data.get(CONF_REMETENTE),
                ): str,
                vol.Optional(
                    CONF_UCS,
                    default=self.entry.data.get(CONF_UCS),
                ): cv.multi_select(self.entry.data.get(CONF_UCS)),
                vol.Optional(CONF_EXTRA_UC): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)


async def async_get_options_flow(config_entry):
    return EdpNf3eOptionsFlow(config_entry)