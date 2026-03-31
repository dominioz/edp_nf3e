"""
Constantes da integração EDP NF3e.

Inclui:
- Campos de configuração
- Defaults
- Lista completa de sensores essenciais
- Sensores adicionais (tarifas, créditos, resumo)
- Padrões de nomes e IDs
"""

DOMAIN = "edp_nf3e"

# -----------------------------
# CONFIGURAÇÕES PRINCIPAIS
# -----------------------------
CONF_IMAP_SERVER = "imap_server"
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_FOLDER = "folder"
CONF_REMETENTE = "remetente"
CONF_UCS = "ucs"
CONF_EXTRA_UC = "extra_uc"

DEFAULT_FOLDER = "INBOX"
DEFAULT_REMETENTE = "edpcontaporemail@edpbr.com.br"
DEFAULT_DAYS = 360  # busca últimos 360 dias

# -----------------------------
# SENSORES ESSENCIAIS POR UC
# -----------------------------
SENSOR_DEFINITIONS = [
    ("energia_consumida", "Energia Consumida", "kWh"),
    ("energia_injetada", "Energia Injetada", "kWh"),

    ("consumo_tusd", "Tarifa TUSD Consumo", "R$/kWh"),
    ("consumo_te", "Tarifa TE Consumo", "R$/kWh"),
    ("injetada_tusd", "Tarifa TUSD Injetada", "R$/kWh"),
    ("injetada_te", "Tarifa TE Injetada", "R$/kWh"),

    ("tarifa_consumo", "Tarifa Total Consumo", "R$/kWh"),
    ("tarifa_geracao", "Tarifa Total Geração", "R$/kWh"),

    ("valor_consumo", "Valor Total Consumo", "R$"),
    ("valor_geracao", "Valor Total Geração", "R$"),

    ("te_tusd_total", "TE + TUSD Total", "R$"),

    ("valor_total", "Valor Total da Conta", "R$"),
    ("valor_bandeiras", "Valor Bandeiras", "R$"),
    ("iluminacao_publica", "Iluminação Pública", "R$"),
    ("compensacoes", "Compensações", "R$"),

    ("data_vencimento", "Data de Vencimento", None),
    ("ultima_leitura", "Última Leitura", None),
    ("proxima_leitura", "Próxima Leitura", None),
    ("dias_periodo", "Dias no Período", "dias"),
    ("dias_bandeira", "Dias na Bandeira", "dias"),

    # Créditos GD
    ("saldo_credito_anterior", "Saldo Crédito Anterior", "R$"),
    ("credito_expirado", "Crédito Expirado", "R$"),
    ("saldo_credito_atual", "Saldo Crédito Atual", "R$"),
]

# -----------------------------
# SENSOR ESPECIAL "RESUMO"
# -----------------------------
SUMMARY_SENSOR_KEY = "resumo"
SUMMARY_SENSOR_NAME = "Resumo"
SUMMARY_SENSOR_UNIT = None