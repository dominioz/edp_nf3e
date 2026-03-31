import imaplib
import email
import logging
import re
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET

_LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------
# IMAP
# ---------------------------------------------------------
def connect_imap(server, user, password, folder):
    """Conecta ao servidor IMAP."""
    mail = imaplib.IMAP4_SSL(server)
    mail.login(user, password)
    mail.select(folder)
    return mail


def search_recent_emails(mail, remetente, days):
    """Busca e-mails recentes do remetente especificado."""
    date = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
    criteria = f'(SINCE "{date}" FROM "{remetente}")'
    result, data = mail.search(None, criteria)

    if result != "OK":
        return []

    return data[0].split()


def extract_xml_from_email(mail, email_id):
    """Extrai o XML NF3e do e-mail."""
    result, data = mail.fetch(email_id, "(RFC822)")
    if result != "OK":
        return None

    msg = email.message_from_bytes(data[0][1])

    for part in msg.walk():
        if part.get_content_type() in ["application/xml", "text/xml"]:
            return part.get_payload(decode=True).decode("utf-8")

    return None


# ---------------------------------------------------------
# PARSER NF3e
# ---------------------------------------------------------
def parse_nf3e(xml_text):
    """
    Parser completo da NF3e.

    Agora usando:
    - <vItem> como tarifa real (com impostos)
    - identificação precisa de TUSD/TE consumo e injetada
    - extração de créditos GD
    """

    ns = {"n": "http://www.portalfiscal.inf.br/nf3e"}
    root = ET.fromstring(xml_text)

    # -----------------------------
    # Valores iniciais
    # -----------------------------
    consumo_tusd = 0.0
    consumo_te = 0.0
    injetada_tusd = 0.0
    injetada_te = 0.0

    energia_consumida = 0.0
    energia_injetada = 0.0

    valor_bandeiras = 0.0
    iluminacao_publica = 0.0
    compensacoes = 0.0

    # -----------------------------
    # Leitura de datas
    # -----------------------------
    dMedAnt = None
    dMedAtu = None
    dProxLeitura = None
    data_vencimento = None

    # -----------------------------
    # Créditos GD
    # -----------------------------
    saldo_credito_anterior = 0.0
    credito_expirado = 0.0
    saldo_credito_atual = 0.0

    # -----------------------------
    # Extrai créditos GD
    # -----------------------------
    gSaldo = root.find(".//n:gSaldoCred", ns)
    if gSaldo is not None:
        saldo_credito_anterior = float(gSaldo.findtext("n:vSaldAnt", "0", ns))
        credito_expirado = float(gSaldo.findtext("n:vCredExpirado", "0", ns))
        saldo_credito_atual = float(gSaldo.findtext("n:vSaldAtual", "0", ns))

    # -----------------------------
    # Extrai datas
    # -----------------------------
    dMedAnt = root.findtext(".//n:gMed/n:dMedAnt", None, ns)
    dMedAtu = root.findtext(".//n:gMed/n:dMedAtu", None, ns)
    dProxLeitura = root.findtext(".//n:gFat/n:dProxLeitura", None, ns)
    data_vencimento = root.findtext(".//n:gFat/n:dVencFat", None, ns)

    # -----------------------------
    # Processa itens da NF3e
    # -----------------------------
    for det in root.findall(".//n:det", ns):
        xProd = det.findtext(".//n:xProd", "", ns).upper()
        vItem = float(det.findtext(".//n:vItem", "0", ns))
        qFaturada = float(det.findtext(".//n:qFaturada", "0", ns))

        # Energia consumida
        if "CONSUMO TUSD" in xProd:
            consumo_tusd = vItem
            energia_consumida = qFaturada

        elif "CONSUMO TE" in xProd:
            consumo_te = vItem

        # Energia injetada
        elif "INJETADA" in xProd and "TUSD" in xProd:
            injetada_tusd = vItem
            energia_injetada = qFaturada

        elif "INJETADA" in xProd and "TE" in xProd:
            injetada_te = vItem

        # Outros valores
        elif "ILUMINAÇÃO" in xProd:
            iluminacao_publica += vItem

        elif "BANDEIRA" in xProd:
            valor_bandeiras += vItem

        elif "COMPENSAÇÃO" in xProd or "DEDUÇÃO" in xProd:
            compensacoes += vItem

    # -----------------------------
    # Tarifas reais
    # -----------------------------
    tarifa_consumo = consumo_tusd + consumo_te
    tarifa_geracao = injetada_tusd + injetada_te

    # -----------------------------
    # Valores totais
    # -----------------------------
    valor_consumo = energia_consumida * tarifa_consumo
    valor_geracao = energia_injetada * tarifa_geracao
    te_tusd_total = energia_consumida * tarifa_consumo

    # Valor total da conta
    valor_total = float(root.findtext(".//n:total/n:vNF", "0", ns))

    # -----------------------------
    # Dias do período
    # -----------------------------
    dias_periodo = None
    if dMedAnt and dMedAtu:
        try:
            d1 = datetime.fromisoformat(dMedAnt)
            d2 = datetime.fromisoformat(dMedAtu)
            dias_periodo = (d2 - d1).days
        except:
            dias_periodo = None

    # -----------------------------
    # Retorno final
    # -----------------------------
    return {
        "energia_consumida": energia_consumida,
        "energia_injetada": energia_injetada,

        "consumo_tusd": consumo_tusd,
        "consumo_te": consumo_te,
        "injetada_tusd": injetada_tusd,
        "injetada_te": injetada_te,

        "tarifa_consumo": tarifa_consumo,
        "tarifa_geracao": tarifa_geracao,

        "valor_consumo": valor_consumo,
        "valor_geracao": valor_geracao,
        "te_tusd_total": te_tusd_total,

        "valor_total": valor_total,
        "valor_bandeiras": valor_bandeiras,
        "iluminacao_publica": iluminacao_publica,
        "compensacoes": compensacoes,

        "data_vencimento": data_vencimento,
        "ultima_leitura": dMedAnt,
        "proxima_leitura": dProxLeitura,
        "dias_periodo": dias_periodo,
        "dias_bandeira": None,  # não disponível no XML

        "saldo_credito_anterior": saldo_credito_anterior,
        "credito_expirado": credito_expirado,
        "saldo_credito_atual": saldo_credito_atual,
    }