
# ============================================================
# FILTROS.PY
# DASHBOARD BROMBERG
# Tratamento, cruzamento e classificação das OS
# ============================================================

import re
import unicodedata
from datetime import datetime

import pandas as pd

from config import (
    DIAS_VENCIDOS_EXIBIR,
    DIAS_PRONTOS_EXIBIR,
)

# Janela de prazos da carteira
LIMITE_FUTURO = 14
LIMITE_VENCIDOS = DIAS_VENCIDOS_EXIBIR


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def texto_normalizado(valor):
    """Remove acentos e padroniza textos."""

    if valor is None:
        return ""

    try:
        if pd.isna(valor):
            return ""
    except (TypeError, ValueError):
        pass

    texto = str(valor).strip().lower()

    texto = unicodedata.normalize("NFKD", texto)

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    return " ".join(texto.split())


def campo_preenchido(valor):
    """Verifica se um campo possui informação útil."""

    texto = texto_normalizado(valor)

    return texto not in (
        "",
        "nan",
        "none",
        "nat",
        "na",
        "n/a",
        "nao informado",
    )


def normalizar_os(valor):
    """Padroniza o número da OS."""

    if not campo_preenchido(valor):
        return ""

    texto = str(valor).strip()
    texto = re.sub(r"\.0$", "", texto)

    return texto


# ============================================================
# TRATAMENTO DAS DATAS
# ============================================================

def data_valida(valor):
    """
    Converte datas do Excel para Timestamp.

    Aceita datas do Pandas, datetime, números seriais
    do Excel e datas em formato brasileiro.
    """

    if valor is None:
        return pd.NaT

    try:
        if pd.isna(valor):
            return pd.NaT
    except (TypeError, ValueError):
        return pd.NaT

    try:
        if isinstance(valor, (int, float)) and not isinstance(
            valor, bool
        ):
            if 20000 <= valor <= 60000:
                data = pd.to_datetime(
                    valor,
                    origin="1899-12-30",
                    unit="D",
                    errors="coerce",
                )
            else:
                return pd.NaT

        elif isinstance(valor, (pd.Timestamp, datetime)):
            data = pd.Timestamp(valor)

        else:
            texto = str(valor).strip()

            if not texto:
                return pd.NaT

            data = pd.to_datetime(
                texto,
                errors="coerce",
                dayfirst=True,
            )

        if pd.isna(data):
            return pd.NaT

        data = pd.Timestamp(data)

        if not (
            pd.Timestamp("2020-01-01")
            <= data
            <= pd.Timestamp("2035-12-31")
        ):
            return pd.NaT

        return data

    except (
        ValueError,
        TypeError,
        OverflowError,
    ):
        return pd.NaT


def converter_colunas_data(df, colunas):
    df = df.copy()

    for coluna in colunas:
        if coluna in df.columns:
            df[coluna] = df[coluna].apply(data_valida)

    return df


def encontrar_coluna(df, candidatos):
    """
    Encontra uma coluna ignorando diferenças de
    maiúsculas, minúsculas e espaços externos.
    """

    mapa = {
        str(coluna).strip().casefold(): coluna
        for coluna in df.columns
    }

    for candidato in candidatos:
        coluna_real = mapa.get(candidato.strip().casefold())

        if coluna_real is not None:
            return coluna_real

    return None


# ============================================================
# PREPARAÇÃO DA CARTEIRA
# ============================================================

def preparar_carteira(df):
    df = df.copy()

    if "OS" not in df.columns:
        raise ValueError(
            "A coluna OS não foi encontrada na Carteira."
        )

    df["OS"] = df["OS"].apply(normalizar_os)

    df = df[df["OS"] != ""].copy()

    colunas_data = [
        "Entrada",
        "Prazo",
        "Data da Solicitação - Máscara",
        "Data da Solicitação - Isolamento",
        "Data da Solicitação - Tinta",
    ]

    df = converter_colunas_data(df, colunas_data)

    return df


# ============================================================
# PREPARAÇÃO DO CONTROLE DE PROCESSOS
# ============================================================

def preparar_processos(df):
    df = df.copy()

    if "OS" not in df.columns:
        raise ValueError(
            "A coluna OS não foi encontrada "
            "no Controle de Processos."
        )

    df["OS"] = df["OS"].apply(normalizar_os)

    df = df[df["OS"] != ""].copy()

    colunas_data = [
        "Chegada",
        "Jateamento",
        "Data Jateamento",
        "Data do Jateamento",
        "1ª Demão",
        "2ª Demão",
        "3ª Demão",
        "Prazo Entrega Contratual",
        "Prazo Entrega Original",
    ]

    df = converter_colunas_data(df, colunas_data)

    return df


# ============================================================
# CRUZAMENTO DAS PLANILHAS
# ============================================================

def cruzar_dados(carteira, processos):
    """
    Associa as duas planilhas pela OS e mantém
    todas as OS da Carteira.
    """

    carteira = carteira.copy()
    processos = processos.copy()

    carteira["OS"] = carteira["OS"].apply(normalizar_os)
    processos["OS"] = processos["OS"].apply(normalizar_os)

    carteira = carteira[carteira["OS"] != ""].copy()
    processos = processos[processos["OS"] != ""].copy()

    processos = processos.drop_duplicates(
        subset="OS",
        keep="last",
    )

    # O Controle de Processos é a fonte oficial dos status de produção.
    # Um LEFT JOIN pela Carteira escondia OS que existiam no Controle,
    # mas ainda não estavam na Carteira. O OUTER JOIN preserva ambos os lados.
    resultado = carteira.merge(
        processos,
        on="OS",
        how="outer",
        suffixes=("", "_Processo"),
        validate="many_to_one",
        indicator=True,
    )

    # Quando há colunas repetidas (por exemplo Cliente), prioriza a Carteira,
    # mas completa os vazios com o valor disponível no Controle de Processos.
    colunas_sufixadas = [
        coluna for coluna in resultado.columns
        if coluna.endswith("_Processo")
    ]
    for coluna_secundaria in colunas_sufixadas:
        coluna_principal = coluna_secundaria[:-9]
        if coluna_principal in resultado.columns:
            resultado[coluna_principal] = resultado[coluna_principal].combine_first(
                resultado[coluna_secundaria]
            )
        else:
            resultado.rename(columns={coluna_secundaria: coluna_principal}, inplace=True)

    correspondencias = int((resultado["_merge"] == "both").sum())
    somente_controle = int((resultado["_merge"] == "right_only").sum())
    resultado.drop(columns=["_merge"], inplace=True)

    print("=" * 55)
    print("CRUZAMENTO DAS PLANILHAS")
    print(f"OS da Carteira: {len(carteira)}")
    print(f"OS do Controle: {len(processos)}")
    print(f"OS associadas entre as planilhas: {correspondencias}")
    print(f"OS preservadas somente do Controle: {somente_controle}")
    print(f"Linhas resultantes: {len(resultado)}")
    print("=" * 55)

    return resultado


# ============================================================
# SOLICITAÇÕES DE MATERIAIS
# ============================================================

def classificar_solicitacao(valor, data=None):
    """Classifica o status da solicitação de material."""

    texto = texto_normalizado(valor)

    if texto in (
        "sem mascara",
        "peca sem mascara",
        "sem isolamento",
        "peca sem isolamento",
        "sem tinta",
        "peca sem tinta",
        "nao necessita",
        "nao necessario",
    ):
        return "NÃO NECESSÁRIO"

    if texto in (
        "nao solicitado",
        "nao solicitada",
        "pendente",
    ):
        return "NÃO SOLICITADO"

    if texto in (
        "solicitado",
        "solicitada",
    ):
        return "SOLICITADO"

    if "solicitad" in texto and "nao" not in texto:
        return "SOLICITADO"

    if campo_preenchido(valor):
        return "VERIFICAR"

    if pd.notna(data_valida(data)):
        return "SOLICITADO"

    return "NÃO SOLICITADO"


def verificar_solicitacao(valor_principal, valor_data):
    return classificar_solicitacao(
        valor_principal,
        valor_data,
    )


def adicionar_status_solicitacoes(df):
    df = df.copy()

    campos = {
        "Status_Mascara": (
            "Máscara",
            "Data da Solicitação - Máscara",
        ),
        "Status_Isolamento": (
            "Isolamento",
            "Data da Solicitação - Isolamento",
        ),
        "Status_Tinta": (
            "Solicitação - Tinta",
            "Data da Solicitação - Tinta",
        ),
    }

    for destino, (coluna_status, coluna_data) in campos.items():
        df[destino] = df.apply(
            lambda linha: classificar_solicitacao(
                linha.get(coluna_status),
                linha.get(coluna_data),
            ),
            axis=1,
        )

    return df


# ============================================================
# CABINE E PINTOR
# ============================================================

def separar_cabine_pintor(valor):
    if not campo_preenchido(valor):
        return "", ""

    texto = str(valor).strip()

    if "(" in texto and ")" in texto:
        cabine = texto.split("(", 1)[0].strip()

        pintor = (
            texto.split("(", 1)[1]
            .split(")", 1)[0]
            .strip()
        )

        return cabine, pintor

    return texto, ""


def adicionar_cabine_pintor(df):
    df = df.copy()

    if "Cabine(Pintor)" not in df.columns:
        df["Cabine"] = ""
        df["Pintor"] = ""
        return df

    valores = df["Cabine(Pintor)"].apply(
        separar_cabine_pintor
    )

    df["Cabine"] = valores.apply(lambda item: item[0])
    df["Pintor"] = valores.apply(lambda item: item[1])

    return df


# ============================================================
# DEMÃOS DE PINTURA
# ============================================================

def identificar_demao(linha):
    colunas = [
        ("3ª Demão", "3ª DEMÃO"),
        ("2ª Demão", "2ª DEMÃO"),
        ("1ª Demão", "1ª DEMÃO"),
    ]

    for coluna, descricao in colunas:
        data = data_valida(linha.get(coluna, pd.NaT))

        if pd.notna(data):
            return descricao

    return "DEMÃO NÃO INFORMADA"


def identificar_data_demao(linha):
    colunas = [
        "3ª Demão",
        "2ª Demão",
        "1ª Demão",
    ]

    for coluna in colunas:
        data = data_valida(linha.get(coluna, pd.NaT))

        if pd.notna(data):
            return data

    return pd.NaT


# ============================================================
# PREPARAÇÃO GERAL
# ============================================================

def preparar_dados_dashboard(carteira, processos):
    """Prepara as informações utilizadas pela interface."""

    carteira = preparar_carteira(carteira)
    processos = preparar_processos(processos)
    processos = adicionar_cabine_pintor(processos)

    dados = cruzar_dados(carteira, processos)
    dados = adicionar_status_solicitacoes(dados)

    dados["Demao"] = dados.apply(
        identificar_demao,
        axis=1,
    )

    dados["Data_Demao"] = dados.apply(
        identificar_data_demao,
        axis=1,
    )

    return dados


# ============================================================
# FILTROS DOS PROCESSOS
# ============================================================

def _filtrar_processo(df, palavra):
    """Filtra pelo status exato, ignorando caixa, acentos e espaços."""
    if df is None or df.empty or "Processo" not in df.columns:
        return df.iloc[0:0].copy() if isinstance(df, pd.DataFrame) else pd.DataFrame()

    processo = df["Processo"].apply(texto_normalizado)
    palavra = texto_normalizado(palavra)

    return df[processo == palavra].copy()


def dados_jateamento(df):
    """Retorna todas as OS Jateando, com data de jateamento primeiro."""
    resultado = _filtrar_processo(df, "jateando")
    if resultado.empty:
        return resultado

    coluna_jateamento = encontrar_coluna(
        resultado,
        ["Jateamento", "Data Jateamento", "Data do Jateamento"],
    )
    if coluna_jateamento is None:
        return resultado

    resultado["_Data_Jateamento_Ordenacao"] = resultado[coluna_jateamento].apply(data_valida)
    resultado["_Jateamento_Preenchido"] = resultado["_Data_Jateamento_Ordenacao"].notna()
    resultado = resultado.sort_values(
        by=["_Jateamento_Preenchido", "_Data_Jateamento_Ordenacao"],
        ascending=[False, False],
        na_position="last",
    )
    return resultado.drop(columns=["_Data_Jateamento_Ordenacao", "_Jateamento_Preenchido"])


def dados_pintura(df):
    """Retorna apenas OS cujo status seja exatamente Em Pintura."""
    return _filtrar_processo(df, "Em Pintura")


# ============================================================
# TELA PRONTO — ÚLTIMOS 30 DIAS
# ============================================================

def dados_prontos(df):
    """
    Retorna processos com status Pronto cuja data da 2ª demão
    esteja dentro da janela configurada, incluindo hoje.

    A data da 2ª demão é utilizada como data em que
    a peça ficou pronta.
    """

    if df is None or df.empty:
        return df.iloc[0:0].copy()

    if "Processo" not in df.columns:
        print("AVISO: coluna 'Processo' não encontrada.")
        return df.iloc[0:0].copy()

    resultado = _filtrar_processo(df, "pronto")

    if resultado.empty:
        return resultado

    coluna_segunda = encontrar_coluna(
        resultado,
        [
            "2ª Demão",
            "2a Demão",
            "Segunda Demão",
            "Data 2ª Demão",
            "Data da 2ª Demão",
        ],
    )

    if coluna_segunda is None:
        print(
            "AVISO: não encontrei a coluna da 2ª demão."
        )
        return resultado.iloc[0:0].copy()

    resultado["Data_Peca_Pronta"] = (
        resultado[coluna_segunda].apply(data_valida)
    )

    hoje = pd.Timestamp.today().normalize()

    dias_janela = max(1, int(DIAS_PRONTOS_EXIBIR))
    inicio = hoje - pd.Timedelta(days=dias_janela - 1)

    datas = resultado["Data_Peca_Pronta"].dt.normalize()

    resultado = resultado[
        datas.notna()
        & (datas >= inicio)
        & (datas <= hoje)
    ].copy()

    resultado = resultado.sort_values(
        "Data_Peca_Pronta",
        ascending=False,
    )

    print(
        "Peças prontas encontradas nos últimos "
        f"{dias_janela} dias: {len(resultado)}"
    )

    return resultado


# ============================================================
# PRAZOS DA CARTEIRA
# ============================================================

def classificar_cor_prazo(dias):
    """
    Cinza: vencido há 2 dias ou mais.
    Vermelho: vencido ontem, hoje ou vence em até 2 dias.
    Amarelo: faltam de 3 a 6 dias.
    Azul-claro: faltam de 7 a 14 dias.
    """

    try:
        dias = int(dias)
    except (ValueError, TypeError):
        return "sem_prazo"

    if dias <= -2:
        return "cinza"

    if -1 <= dias <= 2:
        return "vermelho"

    if 3 <= dias <= 6:
        return "amarelo"

    if 7 <= dias <= 14:
        return "azul"

    return "fora_da_janela"


def dados_prazos(df):
    """
    Filtra OS vencidas há, no máximo, o limite
    retroativo configurado, e OS com prazo nos
    próximos 14 dias.
    """

    if df is None or df.empty:
        return df.iloc[0:0].copy()

    if "Prazo" not in df.columns:
        return df.iloc[0:0].copy()

    df = df.copy()
    df["Prazo"] = df["Prazo"].apply(data_valida)

    hoje = pd.Timestamp.today().normalize()

    df["Dias_Prazo"] = (
        df["Prazo"] - hoje
    ).dt.days

    resultado = df[
        df["Prazo"].notna()
        & (df["Dias_Prazo"] >= -LIMITE_VENCIDOS)
        & (df["Dias_Prazo"] <= LIMITE_FUTURO)
    ].copy()

    resultado["Cor_Prazo"] = (
        resultado["Dias_Prazo"]
        .apply(classificar_cor_prazo)
    )

    resultado["Permite_Interacao"] = (
        resultado["Dias_Prazo"] >= 0
    )

    return resultado.sort_values(
        by=["Prazo", "OS"],
        ascending=[True, True],
    )


def texto_prazo(dias):
    dias = int(dias)

    if dias < 0:
        quantidade = abs(dias)
        unidade = "DIA" if quantidade == 1 else "DIAS"

        return (
            f"PRAZO VENCIDO — {quantidade} {unidade}"
        )

    if dias == 0:
        return "PRAZO HOJE"

    if dias == 1:
        return "1 DIA PARA O PRAZO"

    return f"{dias} DIAS PARA O PRAZO"


def cor_prazo(dias):
    """Retorna a cor hexadecimal da categoria do prazo."""

    categoria = classificar_cor_prazo(dias)

    cores = {
        "cinza": "#D1D5DB",
        "vermelho": "#FCA5A5",
        "amarelo": "#FDE68A",
        "azul": "#BAE6FD",
    }

    return cores.get(categoria, "#FFFFFF")


# ============================================================
# MÁSCARAS
# ============================================================

def normalizar_status_mascara(valor):
    if not campo_preenchido(valor):
        return "VERIFICAR MÁSCARA"

    texto = texto_normalizado(valor)

    if "sem mascara" in texto:
        return "PEÇA SEM MÁSCARA"

    if "colada" in texto:
        return "MÁSCARA COLADA"

    if texto in ("solicitado", "solicitada"):
        return "MÁSCARA SOLICITADA"

    if texto in ("nao solicitado", "nao solicitada"):
        return "MÁSCARA NÃO SOLICITADA"

    return "VERIFICAR MÁSCARA"


# ============================================================
# FIM DO FILTROS.PY
# ============================================================
