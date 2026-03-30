# ⚡ Integração EDP NF3e para Home Assistant

Integração personalizada para o Home Assistant que lê automaticamente as **Notas Fiscais de Energia Elétrica (NF3e)** enviadas pela **EDP São Paulo** por e‑mail, extrai os dados de consumo e gera:

- Um **dispositivo por Unidade Consumidora (UC)**
- Sensores individuais (energia, tarifas, valores, datas, etc.)
- Um **sensor “Resumo”** com todos os dados estruturados
- Atualização automática via IMAP
- Suporte a múltiplas Unidades Consumidoras
- Descoberta automática de Unidades Consumidoras nos últimos 90 dias

Tudo isso sem precisar baixar XML manualmente.

---

# 🚀 Recursos

### ✔️ Leitura automática dos e‑mails da EDP  
A integração conecta ao seu servidor IMAP e lê apenas os últimos **90 dias**.

### ✔️ Descoberta automática de Unidades Consumidoras  
Ela identifica todas as Unidades Consumidoras presentes nos XMLs recebidos.

### ✔️ Suporte a múltiplas Unidades Consumidoras  
Você escolhe quais quer monitorar — e pode adicionar mais depois.

### ✔️ Sensor “Resumo” por Unidade Consumidora  
Com todos os dados estruturados como atributos.

### ✔️ Sensores individuais  
Energia, tarifas, valores, datas, compensações, TE/TUSD, etc.

### ✔️ Atualização automática  
A cada 12 horas (ou manualmente).

### ✔️ Configuração 100% via interface  
Sem YAML.

---

# 📦 Instalação

## 🔹 Via HACS (recomendado)

1. Abra **HACS → Integrações**
2. Clique em **Adicionar Repositório Personalizado**
3. Informe o URL do repositório GitHub https://github.com/dominioz/edp_nf3e
4. Tipo: **Integração**
5. Instale a integração **EDP NF3e**
6. Reinicie o Home Assistant

---

## 🔹 Instalação Manual

1. Baixe o conteúdo da pasta:
			 custom_components/edp_nf3e/

2. Copie para:
			 config/custom_components/edp_nf3e/
			 

3. Reinicie o Home Assistant

---

# ⚙️ Configuração

1. Vá em **Configurações → Dispositivos e Serviços**
2. Clique em **Adicionar Integração**
3. Procure por **EDP NF3e**
4. Informe:
   - Servidor IMAP
   - E-mail
   - Senha
   - Pasta (INBOX por padrão)
   - Remetente (EDP por padrão)

A integração então:

- Conecta ao IMAP  
- Lê os últimos 90 dias  
- Extrai todos os XMLs  
- Detecta todas as Unidades Consumidoras  
- Mostra uma lista para você selecionar  

Você também pode adicionar uma Unidade Consumidora manualmente.

---

# 🔧 Opções da Integração

Após instalada, você pode:

- Adicionar novas Unidades Consumidoras
- Remover Unidades Consumidoras
- Alterar pasta IMAP
- Alterar remetente
- Forçar nova varredura

Tudo em **Configurações → Dispositivos e Serviços → EDP NF3e → Configurar**.

---

# 📊 Sensores Disponíveis

Para cada Unidade Consumidora, são criados:

### 🔹 Sensor Resumo			 

Atributos incluem:

- energia_consumida  
- energia_injetada  
- tarifa_base  
- tarifa_real  
- tarifa_paga  
- valor_total  
- valor_bandeiras  
- iluminacao_publica  
- compensacoes  
- te_tusd  
- data_vencimento  
- ultima_leitura  
- proxima_leitura  
- dias_periodo  
- dias_bandeira  
- nf3e_raw (JSON estruturado)

### 🔹 Sensores Individuais
- Energia Consumida (kWh)  
- Energia Injetada (kWh)  
- Tarifa Base (R$/kWh)  
- Tarifa Real (R$/kWh)  
- Tarifa Paga (R$/kWh)  
- Valor Total Conta (R$)  
- Valor Bandeiras (R$)  
- Iluminação Pública (R$)  
- Compensações (R$)  
- TE + TUSD (R$)  
- Data Vencimento  
- Última Leitura  
- Próxima Leitura  
- Dias no Período  
- Dias na Bandeira  

---

# 🧠 Como funciona internamente

- Conexão IMAP via SSL  
- Busca por remetente + últimos 90 dias  
- Extração de anexos XML  
- Parser completo da NF3e  
- Normalização da Unidade Consumidora  
- Cache por Unidade Consumidora  
- Atualização via `DataUpdateCoordinator`  

---

# 🛠️ Troubleshooting

### ❗ “Não foi possível conectar ao servidor IMAP”
- Verifique servidor, porta e senha  
- Alguns provedores exigem senha de app (Gmail, Outlook)

### ❗ “Nenhuma Unidade Consumidora encontrada”
- Verifique se os e‑mails da EDP estão na pasta correta  
- Verifique se há XMLs nos últimos 90 dias  
- Verifique o remetente configurado

### ❗ Sensores vazios
- A integração só usa **a fatura mais recente** de cada Unidade Consumidora  
- Verifique se há XMLs válidos para essa Unidade Consumidora

---

# 🗺️ Roadmap

- [ ] Suporte a anexos ZIP  
- [ ] Suporte a múltiplos remetentes  
- [ ] Histórico de faturas  
- [ ] Dashboard Lovelace pronto  
- [ ] Suporte a outras distribuidoras (Enel, CPFL, Neoenergia)

---

# 👨‍💻 Autor

Desenvolvido por **Alexandre Pires Avila** (ale.avilla@dominioz.com.br).


