import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_FOLDER,
    CONF_REMETENTE,
    CONF_UCS,
    CONF_EXTRA_UC,
)


class EdpNf3eOptionsFlow(config_entries.OptionsFlow):
    """Fluxo de opções da integração EDP NF3e."""

    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        errors = {}

        if user_input is not None:
            ucs = user_input.get(CONF_UCS, [])
            extra = user_input.get(CONF_EXTRA_UC)

            # Adiciona UC manual
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