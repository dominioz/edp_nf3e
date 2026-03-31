import email
import imaplib
import logging
from email.header import decode_header

_LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------
# Conecta ao servidor IMAP
# ---------------------------------------------------------
def connect_imap(server, username, password, folder):
    mail = imaplib.IMAP4_SSL(server)
    mail.login(username, password)
    mail.select(folder)
    return mail


# ---------------------------------------------------------
# Busca e-mails recentes do remetente
# ---------------------------------------------------------
def search_recent_emails(mail, remetente, days):
    try:
        # Exemplo: SINCE "04-Apr-2025"
        from datetime import datetime, timedelta

        since_date = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
        query = f'(SINCE "{since_date}" FROM "{remetente}")'

        _LOGGER.info("Executando busca IMAP: %s", query)

        result, data = mail.search(None, query)

        if result != "OK":
            _LOGGER.error("Erro ao buscar e-mails: %s", result)
            return []

        ids = data[0].split()
        return [int(x) for x in ids]

    except Exception as e:
        _LOGGER.error("Erro no search_recent_emails: %s", e)
        return []


# ---------------------------------------------------------
# Extrai o XML do e-mail (anexo ou inline)
# ---------------------------------------------------------
def extract_xml_from_email(mail, email_id):
    try:
        result, data = mail.fetch(str(email_id), "(RFC822)")
        if result != "OK":
            _LOGGER.error("Erro ao fazer FETCH do e-mail %s", email_id)
            return None

        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)

        # 1) Procura anexos XML
        for part in msg.walk():
            content_type = part.get_content_type()
            filename = part.get_filename()

            if filename:
                decoded = decode_header(filename)[0][0]
                if isinstance(decoded, bytes):
                    decoded = decoded.decode()

                if decoded.lower().endswith(".xml"):
                    _LOGGER.info("XML encontrado como anexo: %s", decoded)
                    return part.get_payload(decode=True).decode("utf-8", errors="ignore")

        # 2) Procura XML inline no corpo
        for part in msg.walk():
            if part.get_content_type() in ["text/xml", "application/xml"]:
                _LOGGER.info("XML encontrado inline no corpo do e-mail")
                return part.get_payload(decode=True).decode("utf-8", errors="ignore")

        # 3) Procura XML embedado em HTML (caso raro)
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                html = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                if "<nf3eProc" in html:
                    _LOGGER.info("XML encontrado embedado em HTML")
                    start = html.find("<nf3eProc")
                    end = html.find("</nf3eProc>") + len("</nf3eProc>")
                    return html[start:end]

        _LOGGER.warning("Nenhum XML encontrado no e-mail %s", email_id)
        return None

    except Exception as e:
        _LOGGER.error("Erro ao extrair XML do e-mail %s: %s", email_id, e)
        return None