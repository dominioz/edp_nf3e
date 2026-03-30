import os
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

from .const import DEFAULT_DAYS

NS = {"n": "http://www.portalfiscal.inf.br/nf3e"}


# ---------------------------------------------------------
# 🔧 Normalização da UC
# ---------------------------------------------------------
def normalize_uc(raw: str) -> str:
    """Remove tudo que não for número e zeros à esquerda."""
    if not raw:
        return None
    digits = "".join(ch for ch in raw if ch.isdigit())
    return digits.lstrip("0") or digits


# ---------------------------------------------------------
# 📬 Conexão IMAP
# ---------------------------------------------------------
def connect_imap(server: str, user: str, password: str, folder: str):
    """Conecta ao servidor IMAP e seleciona a pasta."""
    mail = imaplib.IMAP4_SSL(server)
    mail.login(user, password)
    mail.select(f'"{folder}"')
    return mail


# ---------------------------------------------------------
# 📬 Busca e-mails dos últimos N dias
# ---------------------------------------------------------
def search_recent_emails(mail, remetente: str, days: int = DEFAULT_DAYS):
    """Busca e-mails do remetente nos últimos N dias."""
    date_limit = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
    query = f'(FROM "{remetente}" SINCE {date_limit})'

    status, data = mail.search(None, query)
    if status != "OK":
        return []

    ids = data[0].split()
    return ids


# ---------------------------------------------------------
# 📎 Extrai XML de um e-mail
# ---------------------------------------------------------
def extract_xml_from_email(mail, email_id):
    """Extrai o XML de um e-mail, ignorando PDFs e outros anexos."""
    status, data = mail.fetch(email_id, "(RFC822)")
    if status != "OK":
        return None

    msg = email.message_from_bytes(data[0][1])

    for part in msg.walk():
        filename = part.get_filename()
        content_type = part.get_content_type()

        # Decodifica nome do arquivo
        if filename:
            decoded, enc = decode_header(filename)[0]
            if isinstance(decoded, bytes):
                decoded = decoded.decode(enc or "utf-8", errors="ignore")
        else:
            decoded = ""

        # Ignorar PDFs
        if decoded.lower().endswith(".pdf") or content_type == "application/pdf":
            continue

        # Detectar XML mesmo com content-type errado
        is_xml = (
            decoded.lower().endswith(".xml")
            or content_type in ["application/xml", "text/xml"]
            or "xml" in content_type
        )

        if not is_xml:
            continue

        xml_bytes = part.get_payload(decode=True)
        if not xml_bytes:
            continue

        try:
            return xml_bytes.decode("utf-8", errors="ignore")
        except Exception:
            try:
                return xml_bytes.decode("latin-1", errors="ignore")
            except Exception:
                continue

    return None


# ---------------------------------------------------------
# 📄 Lê UC do XML (modo rápido)
# ---------------------------------------------------------
def extract_uc_from_xml(xml_text: str):
    """Extrai apenas a UC do XML, sem processar o resto."""
    try:
        root = ET.fromstring(xml_text)
        id_acesso = root.find(".//n:acessante/n:idAcesso", NS)
        if id_acesso is not None and id_acesso.text:
            return normalize_uc(id_acesso.text)
    except Exception:
        pass
    return None


# ---------------------------------------------------------
# 💾 Persistência do último XML
# ---------------------------------------------------------
def save_last_xml(xml_text: str, path: str):
    """Salva o último XML válido em disco."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(xml_text)
    except Exception:
        pass


def load_last_xml(path: str):
    """Carrega o último XML salvo, se existir."""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None
    return None


# ---------------------------------------------------------
# 📊 Parser completo da NF3e
# ---------------------------------------------------------
def parse_nf3e(xml_text: str):
    """Extrai todos os dados relevantes da NF3e e retorna JSON estruturado."""
    root = ET.fromstring(xml_text)

    # UC
    id_acesso = root.find(".//n:acessante/n:idAcesso", NS)
    uc = normalize_uc(id_acesso.text) if id_acesso is not None else None

    # Valor total
    vnf_elem = root.find(".//n:total/n:vNF", NS)
    valor_total = float(vnf_elem.text) if vnf_elem is not None else 0.0

    # Datas
    venc_elem = root.find(".//n:gFat/n:dVencFat", NS)
    ultima_elem = root.find(".//n:gMed/n:dMedAtu", NS)
    prox_elem = root.find(".//n:gFat/n:dProxLeitura", NS)

    data_venc = venc_elem.text if venc_elem is not None else None
    ultima_leitura = ultima_elem.text if ultima_elem is not None else None
    proxima_leitura = prox_elem.text if prox_elem is not None else None

    # Competência atual
    compet_elem = root.find(".//n:gFat/n:CompetFat", NS)
    competencia = compet_elem.text if compet_elem is not None else None

    # Dias no período
    dias_periodo = None
    for g in root.findall(".//n:gANEEL/n:gHistFat/n:gGrandFat", NS):
        comp = g.find("n:CompetFat", NS)
        dias = g.find("n:qtdDias", NS)
        if comp is not None and dias is not None and comp.text == competencia:
            try:
                dias_periodo = int(dias.text)
            except Exception:
                dias_periodo = None
            break

    # Energia e valores
    energia_consumida = 0.0
    energia_injetada = 0.0
    te_tusd_valor = 0.0
    iluminacao_publica = 0.0
    compensacoes = 0.0
    bandeiras_valor = 0.0  # não identificado nos XMLs enviados

    # Tarifas individuais
    tusd_fornecida = None
    te_fornecida = None
    tusd_injetada = None
    te_injetada = None

    # Loop dos itens
    for det in root.findall(".//n:NFdet/n:det", NS):
        xprod = det.find(".//n:detItem/n:prod/n:xProd", NS)
        q = det.find(".//n:detItem/n:prod/n:qFaturada", NS)
        vprod = det.find(".//n:detItem/n:prod/n:vProd", NS)
        vitem = det.find(".//n:detItem/n:prod/n:vItem", NS)
        cprod = det.find(".//n:detItem/n:prod/n:cProd", NS)

        xprod = xprod.text.upper() if xprod is not None and xprod.text else ""
        q = float(q.text) if q is not None and q.text else 0.0
        vprod = float(vprod.text) if vprod is not None and vprod.text else 0.0
        vitem = float(vitem.text) if vitem is not None and vitem.text else 0.0
        cprod = cprod.text if cprod is not None else ""

        # Energia consumida
        if "CONSUMO" in xprod and "INJETADA" not in xprod:
            energia_consumida += q
            te_tusd_valor += vprod

            if "TUSD" in xprod:
                tusd_fornecida = vitem
            if "TE" in xprod:
                te_fornecida = vitem

        # Energia injetada
        if "INJETADA" in xprod:
            energia_injetada += q

            if "TUSD" in xprod:
                tusd_injetada = vitem
            if "TE" in xprod:
                te_injetada = vitem

        # Outros itens
        if "ILUMINAÇÃO PÚBLICA" in xprod:
            iluminacao_publica += vprod

        if cprod == "ACCMNT" or "DEDUÇÕES E COMPENSAÇÕES" in xprod:
            compensacoes += vprod

    # Tarifas agregadas
    tarifa_base = te_tusd_valor / energia_consumida if energia_consumida else 0
    tarifa_real = (te_tusd_valor + bandeiras_valor) / energia_consumida if energia_consumida else 0
    tarifa_paga = valor_total / energia_consumida if energia_consumida else 0

    dias_bandeira = dias_periodo  # sem info específica

    return {
        "uc": uc,
        "energia_consumida": round(energia_consumida, 2),
        "energia_injetada": round(energia_injetada, 2),
        "tarifa_base": round(tarifa_base, 6),
        "tarifa_real": round(tarifa_real, 6),
        "tarifa_paga": round(tarifa_paga, 6),
        "valor_total": round(valor_total, 2),
        "valor_bandeiras": round(bandeiras_valor, 2),
        "iluminacao_publica": round(iluminacao_publica, 2),
        "compensacoes": round(compensacoes, 2),
        "te_tusd": round(te_tusd_valor, 2),
        "data_vencimento": data_venc,
        "ultima_leitura": ultima_leitura,
        "proxima_leitura": proxima_leitura,
        "dias_periodo": dias_periodo,
        "dias_bandeira": dias_bandeira,
        "tarifas": {
            "tusd_fornecida": tusd_fornecida,
            "te_fornecida": te_fornecida,
            "tusd_injetada": tusd_injetada,
            "te_injetada": te_injetada,
            "tarifa_consumida": (tusd_fornecida or 0) + (te_fornecida or 0),
            "tarifa_injetada": (tusd_injetada or 0) + (te_injetada or 0),
        },
        "nf3e_raw": {
            "competencia": competencia,
            "uc": uc,
            "valor_total": valor_total,
            "energia_consumida": energia_consumida,
            "energia_injetada": energia_injetada,
        },
    }