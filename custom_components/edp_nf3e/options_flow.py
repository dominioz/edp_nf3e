import voluptuous as vol
import logging

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_FOLDER,
    CONF_REMETENTE,
    CONF_UCS,
    CONF_EXTRA_UC,
)
from .util import normalize_uc

_LOGGER = logging.getLogger(__name__)


class EdpNf3eOptionsFlow(config_entries.OptionsFlow):
    """Options flow para adicionar/remover UCs e ajustar configurações."""

    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        errors = {}

        if user_input is not None:
            # Lista atual de UCs
            ucs = user_input.get(CONF_UCS, [])

            # UC manual
            extra = user_input.get(CONF_EXTRA_UC)
            if extra:
                extra_norm = normalize_uc(extra)
                if not extra_norm:
                    errors["base"] = "invalid_uc"
                else:
                    ucs.append(extra_norm)

            # Remove duplicadas
            ucs = sorted(list(set(ucs)))

            if not ucs:
                errors["base"] = "no_uc_selected"
            else:
                # Salva SOMENTE OPTIONS (não sobrescreve entry.data)
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_FOLDER: user_input.get(CONF_FOLDER),
                        CONF_REMETENTE: user_input.get(CONF_REMETENTE),
                        CONF_UCS: ucs,
                    },
                )

        # Valores atuais
        current_folder = self.entry.options.get(CONF_FOLDER, self.entry.data.get(CONF_FOLDER))
        current_remetente = self.entry.options.get(CONF_REMETENTE, self.entry.data.get(CONF_REMETENTE))
        current_ucs = self.entry.options.get(CONF_UCS, self.entry.data.get(CONF_UCS, []))

        schema = vol.Schema(
            {
                vol.Optional(CONF_FOLDER, default=current_folder): str,
                vol.Optional(CONF_REMETENTE, default=current_remetente): str,
                vol.Optional(CONF_UCS, default=current_ucs): vol.MultipleChoice(current_ucs),
                vol.Optional(CONF_EXTRA_UC): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)


async def async_get_options_flow(config_entry):
    return EdpNf3eOptionsFlow(config_entry)