
# ============================================================
# CONFIG.PY
# CONFIGURAÇÕES DO DASHBOARD BROMBERG
# ============================================================


# ============================================================
# PRAZOS DA CARTEIRA
# ============================================================

# Quantidade máxima de dias retroativos para exibir OS vencidas.
# 3650 dias equivale aproximadamente a 10 anos.
DIAS_VENCIDOS_EXIBIR = 1

# Exibe OS com prazo nos próximos 14 dias.
DIAS_FUTUROS_EXIBIR = 13

# Período de exibição dos processos prontos.
# Considera hoje e os dois dias anteriores.
DIAS_PRONTOS_EXIBIR = 4


# ============================================================
# IDENTIDADE VISUAL BROMBERG
# ============================================================

BROMBERG_CYAN = "#2CB5F5"
BROMBERG_BLUE = "#303394"
BROMBERG_DARK = "#25266F"

BRANCO = "#FFFFFF"
CINZA = "#F1F5F9"
CINZA_ESCURO = "#4B5563"


# ============================================================
# CORES DOS ALERTAS DE PRAZO
# ============================================================

# OS vencidas há 2 dias ou mais.
CINZA_PRAZO = "#D1D5DB"
CINZA_PRAZO_TEXTO = "#1F2937"

# OS vencidas ontem, com prazo hoje ou nos próximos 2 dias.
VERMELHO = "#FCA5A5"
VERMELHO_TEXTO = "#7F1D1D"

# OS com prazo entre 3 e 6 dias.
AMARELO = "#FDE68A"
AMARELO_TEXTO = "#78350F"

# OS com prazo entre 7 e 14 dias.
AZUL = "#BAE6FD"
AZUL_TEXTO = "#1E3A8A"

# Cor complementar para outros indicadores.
LARANJA = "#F97316"
VERDE = "#16A34A"


# ============================================================
# STATUS DOS PROCESSOS
# ============================================================

PROCESSO_PRONTO = "Pronto"
PROCESSO_PINTURA = "Em Pintura"
PROCESSO_JATEANDO = "Jateando"


# ============================================================
# CONFIGURAÇÕES DA JANELA
# ============================================================

NOME_DASHBOARD = "Dashboard Bromberg"

LARGURA_JANELA = 1400
ALTURA_JANELA = 800


# ============================================================
# FONTES
# ============================================================

FONTE_PADRAO = ("Segoe UI", 12)
FONTE_TITULO = ("Segoe UI", 18, "bold")
FONTE_TABELA = ("Segoe UI", 12, "bold")


# ============================================================
# TABELAS
# ============================================================

ALTURA_LINHA_TABELA = 42


# ============================================================
# ALTERNÂNCIA AUTOMÁTICA DAS TELAS
# ============================================================

INTERVALO_TELAS_SEGUNDOS = 30


# ============================================================
# FIM DO CONFIG.PY
# ============================================================
