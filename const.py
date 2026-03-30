DOMAIN = "edp_nf3e"

# Configurações principais
CONF_IMAP_SERVER = "imap_server"
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_FOLDER = "folder"
CONF_REMETENTE = "remetente"
CONF_UCS = "ucs"  # lista de UCs selecionadas pelo usuário
CONF_EXTRA_UC = "extra_uc"  # campo para adicionar UC manualmente

# Defaults
DEFAULT_FOLDER = "INBOX"
DEFAULT_REMETENTE = "edpcontaporemail@edpbr.com.br"
DEFAULT_DAYS = 360  # últimos 90 dias

# Sensores individuais por UC
SENSOR_DEFINITIONS = [
    ("energia_consumida", "Energia Consumida", "kWh"),
    ("energia_injetada", "Energia Injetada", "kWh"),
    ("tarifa_base", "Tarifa Base", "R$/kWh"),
    ("tarifa_real", "Tarifa Real", "R$/kWh"),
    ("tarifa_paga", "Tarifa Paga", "R$/kWh"),
    ("valor_total", "Valor Total Conta", "R$"),
    ("valor_bandeiras", "Valor Bandeiras", "R$"),
    ("iluminacao_publica", "Iluminação Pública", "R$"),
    ("compensacoes", "Valor Compensações", "R$"),
    ("te_tusd", "TE + TUSD", "R$"),
    ("data_vencimento", "Data Vencimento", None),
    ("ultima_leitura", "Última Leitura", None),
    ("proxima_leitura", "Próxima Leitura", None),
    ("dias_periodo", "Dias no Período", "dias"),
    ("dias_bandeira", "Dias na Bandeira", "dias"),
]

# Sensor especial "Resumo"
SUMMARY_SENSOR_KEY = "resumo"
SUMMARY_SENSOR_NAME = "Resumo"
SUMMARY_SENSOR_UNIT = None  # sem unidade