DOMAIN = "edp_nf3e"

CONF_IMAP_SERVER = "imap_server"
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_FOLDER = "folder"
CONF_REMETENTE = "remetente"
CONF_UCS = "ucs"
CONF_EXTRA_UC = "extra_uc"

DEFAULT_FOLDER = "INBOX"
DEFAULT_REMETENTE = "edpcontaporemail@edpbr.com.br"
DEFAULT_DAYS = 90

# Sensores
SENSOR_TYPES = {
    "energia_consumida": ["Energia Consumida", "kWh"],
    "energia_injetada": ["Energia Injetada", "kWh"],

    "consumo_tusd": ["Tarifa TUSD Consumo", "R$/kWh"],
    "consumo_te": ["Tarifa TE Consumo", "R$/kWh"],
    "injetada_tusd": ["Tarifa TUSD Injetada", "R$/kWh"],
    "injetada_te": ["Tarifa TE Injetada", "R$/kWh"],

    "tarifa_consumo": ["Tarifa Total Consumo", "R$/kWh"],
    "tarifa_geracao": ["Tarifa Total Geração", "R$/kWh"],

    "valor_consumo": ["Valor Consumo", "R$"],
    "valor_geracao": ["Valor Geração", "R$"],
    "te_tusd_total": ["Total TE+TUSD", "R$"],
    "valor_total": ["Valor Total da Fatura", "R$"],

    "iluminacao_publica": ["Iluminação Pública", "R$"],
    "compensacoes": ["Compensações", "R$"],

    "saldo_credito_anterior": ["Crédito Anterior", "kWh"],
    "credito_expirado": ["Crédito Expirado", "kWh"],
    "saldo_credito_atual": ["Crédito Atual", "kWh"],

    "data_vencimento": ["Data de Vencimento", None],
    "ultima_leitura": ["Última Leitura", None],
    "proxima_leitura": ["Próxima Leitura", None],

    "resumo": ["Resumo", None],
}