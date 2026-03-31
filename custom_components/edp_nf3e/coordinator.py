import logging
import xml.etree.ElementTree as ET

from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .util import connect_imap, search_recent_emails, extract_xml_from_email

_LOGGER = logging.getLogger(__name__)


class EdpNf3eCoordinator(DataUpdateCoordinator):
    """Coordinator responsável por buscar e processar NF3e."""

    def __init__(self, hass, entry):
        super().__init__(
            hass,
            _LOGGER,
            name="EDP NF3e Coordinator",
            update_interval=timedelta(hours=6),
        )

        self.entry = entry
        self.imap_server = entry.data["imap_server"]
        self.email = entry.data["email"]
        self.password = entry.data["password"]
        self.folder = entry.data["folder"]
        self.remetente = entry.data["remetente"]
        self.ucs = entry.data["ucs"]

    # ---------------------------------------------------------
    # Atualização principal
    # ---------------------------------------------------------
    async def _async_update_data(self):
        data = {}

        try:
            mail = await self.hass.async_add_executor_job(
                connect_imap,
                self.imap_server,
                self.email,
                self.password,
                self.folder,
            )
        except Exception as e:
            _LOGGER.error("Erro ao conectar IMAP: %s", e)
            return {uc: None for uc in self.ucs}

        try:
            email_ids = await self.hass.async_add_executor_job(
                search_recent_emails,
                mail,
                self.remetente,
                40,
            )

            for uc in self.ucs:
                data[uc] = await self._async_process_uc(mail, email_ids, uc)

            return data

        finally:
            try:
                mail.logout()
            except:
                pass

    # ---------------------------------------------------------
    # Processa uma UC específica
    # ---------------------------------------------------------
    async def _async_process_uc(self, mail, email_ids, uc):
        for email_id in reversed(email_ids):
            xml_text = await self.hass.async_add_executor_job(
                extract_xml_from_email, mail, email_id
            )

            if not xml_text:
                continue

            try:
                root = ET.fromstring(xml_text)
                ns = {"n": "http://www.portalfiscal.inf.br/nf3e"}

                id_acesso = root.find(".//n:idAcesso", ns)
                if id_acesso is None or id_acesso.text.strip() != uc:
                    continue

                return self._parse_nf3e(root, ns)

            except Exception as e:
                _LOGGER.error("Erro ao processar XML: %s", e)

        return None

    # ---------------------------------------------------------
    # Parser completo da NF3e
    # ---------------------------------------------------------
    def _parse_nf3e(self, root, ns):
        try:
            dados = {}

            # Datas
            dados["ultima_leitura"] = self._get(root, ".//n:dMedAnt", ns)
            dados["proxima_leitura"] = self._get(root, ".//n:dProxLeitura", ns)
            dados["data_vencimento"] = self._get(root, ".//n:dVencFat", ns)

            # Energia
            dados["energia_consumida"] = float(self._get(root, ".//n:qFaturada", ns, item="CONSUMO"))
            dados["energia_injetada"] = float(self._get(root, ".//n:qFaturada", ns, item="INJETADA"))

            # Tarifas reais (vItem)
            dados["consumo_tusd"] = float(self._get(root, ".//n:vItem", ns, item="CONSUMO TUSD"))
            dados["consumo_te"] = float(self._get(root, ".//n:vItem", ns, item="CONSUMO TE"))
            dados["injetada_tusd"] = float(self._get(root, ".//n:vItem", ns, item="INJETADA|TUSD"))
            dados["injetada_te"] = float(self._get(root, ".//n:vItem", ns, item="INJETADA|TE"))

            # Tarifas totais
            dados["tarifa_consumo"] = dados["consumo_tusd"] + dados["consumo_te"]
            dados["tarifa_geracao"] = dados["injetada_tusd"] + dados["injetada_te"]

            # Valores
            dados["valor_consumo"] = dados["energia_consumida"] * dados["tarifa_consumo"]
            dados["valor_geracao"] = dados["energia_injetada"] * dados["tarifa_geracao"]

            dados["te_tusd_total"] = dados["valor_consumo"] + dados["valor_geracao"]

            dados["iluminacao_publica"] = float(self._get(root, ".//n:vItem", ns, item="ILUMINAÇÃO"))
            dados["compensacoes"] = float(self._get(root, ".//n:vItem", ns, item="COMPENSAÇÕES"))

            dados["valor_total"] = float(self._get(root, ".//n:vNF", ns))

            # Créditos GD
            dados["saldo_credito_anterior"] = float(self._get(root, ".//n:vSaldAnt", ns))
            dados["credito_expirado"] = float(self._get(root, ".//n:vCredExpirado", ns))
            dados["saldo_credito_atual"] = float(self._get(root, ".//n:vSaldAtual", ns))

            return dados

        except Exception as e:
            _LOGGER.error("Erro no parser NF3e: %s", e)
            return None

    # ---------------------------------------------------------
    # Helper para extrair valores
    # ---------------------------------------------------------
    def _get(self, root, path, ns, item=None):
        if item:
            for det in root.findall(".//n:det", ns):
                xprod = det.find(".//n:xProd", ns)
                if xprod is None:
                    continue

                texto = xprod.text.upper()

                # Critérios múltiplos (robusto)
                ok = True
                for termo in item.upper().split("|"):
                    if termo.strip() not in texto:
                        ok = False
                        break

                if ok:
                    val = det.find(path, ns)
                    if val is not None:
                        return val.text

            return "0"

        node = root.find(path, ns)
        return node.text if node is not None else "0"