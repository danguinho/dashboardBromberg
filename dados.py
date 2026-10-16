# ============================================================
# DADOS.PY
# DASHBOARD BROMBERG
# Leitura e validação das planilhas Excel
# ============================================================

from pathlib import Path

import pandas as pd


# ============================================================
# NORMALIZAÇÃO DAS COLUNAS
# ============================================================

def normalizar_colunas(df):
    """
    Limpa os nomes das colunas, remove espaços
    e elimina colunas sem nome.
    """

    df = df.copy()

    novas_colunas = []

    for coluna in df.columns:
        if pd.isna(coluna):
            novas_colunas.append("")
        else:
            novas_colunas.append(
                str(coluna).strip()
            )

    df.columns = novas_colunas

    # Remove colunas completamente sem nome.
    df = df.loc[
        :,
        [
            coluna != ""
            for coluna in df.columns
        ],
    ].copy()

    # Remove colunas inteiramente vazias.
    df = df.dropna(
        axis=1,
        how="all",
    )

    return df


# ============================================================
# NORMALIZAÇÃO DAS OS
# ============================================================

def normalizar_os_coluna(df):
    """
    Padroniza a coluna OS para permitir o cruzamento
    entre a Carteira e o Controle de Processos.
    """

    df = df.copy()

    if "OS" not in df.columns:
        return df

    def limpar_os(valor):
        if pd.isna(valor):
            return pd.NA

        texto = str(valor).strip()

        if texto.lower() in (
            "",
            "nan",
            "none",
            "nat",
        ):
            return pd.NA

        # Remove o decimal artificial criado
        # quando uma OS numérica vem como 12345.0.
        if texto.endswith(".0"):
            parte_inteira = texto[:-2]

            if parte_inteira.isdigit():
                texto = parte_inteira

        return texto

    df["OS"] = (
        df["OS"]
        .apply(limpar_os)
        .astype("string")
    )

    return df


# ============================================================
# LEITURA DE UMA PLANILHA
# ============================================================

def carregar_arquivo(caminho, nome):
    """
    Carrega uma planilha Excel usando a terceira linha
    como cabeçalho.

    Formatos suportados:
    - XLSX
    - XLSM
    - XLSB
    - XLS
    """

    path = Path(caminho)

    if not path.is_file():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {path}"
        )

    extensao = path.suffix.lower()

    engines = {
        ".xlsx": "openpyxl",
        ".xlsm": "openpyxl",
        ".xlsb": "pyxlsb",
        ".xls": "xlrd",
    }

    engine = engines.get(extensao)

    if engine is None:
        raise ValueError(
            f"Formato não suportado: {extensao}"
        )

    print("\n" + "=" * 55)
    print(f"LENDO: {nome}")
    print(f"Arquivo: {path.name}")
    print("=" * 55)

    try:
        df = pd.read_excel(
            path,
            sheet_name=0,
            engine=engine,
            header=2,
        )

        df = normalizar_colunas(df)

        if df.empty:
            raise ValueError(
                f"A planilha {nome} está vazia "
                "ou não contém linhas de dados."
            )

        # Verifica se há pelo menos uma coluna.
        if len(df.columns) == 0:
            raise ValueError(
                f"Nenhuma coluna válida foi encontrada "
                f"na planilha {nome}."
            )

        print(f"{nome} carregada com sucesso.")
        print(f"Linhas: {len(df)}")
        print(f"Colunas: {list(df.columns)}")

        return df

    except Exception as erro:
        raise RuntimeError(
            f"Erro ao carregar {nome}: {erro}"
        ) from erro


# ============================================================
# CARREGAMENTO DA CARTEIRA E DOS PROCESSOS
# ============================================================

def carregar_dados(
    caminho_carteira,
    caminho_processos,
):
    """
    Carrega os dois arquivos e valida a coluna OS.

    Retorna:
        carteira, processos
    """

    carteira = carregar_arquivo(
        caminho_carteira,
        "Carteira",
    )

    processos = carregar_arquivo(
        caminho_processos,
        "Controle de Processos",
    )

    carteira = normalizar_os_coluna(
        carteira
    )

    processos = normalizar_os_coluna(
        processos
    )

    # Verifica a coluna OS da Carteira.
    if "OS" not in carteira.columns:
        raise ValueError(
            "A coluna 'OS' não foi encontrada na Carteira.\n"
            f"Colunas identificadas: {list(carteira.columns)}"
        )

    # Verifica a coluna OS do Controle de Processos.
    if "OS" not in processos.columns:
        raise ValueError(
            "A coluna 'OS' não foi encontrada "
            "no Controle de Processos.\n"
            f"Colunas identificadas: {list(processos.columns)}"
        )

    # Remove linhas sem número de OS.
    carteira = carteira[
        carteira["OS"].notna()
        & carteira["OS"].str.strip().ne("")
    ].copy()

    processos = processos[
        processos["OS"].notna()
        & processos["OS"].str.strip().ne("")
    ].copy()

    print("\n" + "=" * 55)
    print("RESUMO DO CARREGAMENTO")
    print("=" * 55)

    print(
        f"OS válidas na Carteira: {len(carteira)}"
    )

    print(
        f"OS válidas nos Processos: {len(processos)}"
    )

    print(
        f"OS distintas na Carteira: "
        f"{carteira['OS'].nunique()}"
    )

    print(
        f"OS distintas nos Processos: "
        f"{processos['OS'].nunique()}"
    )

    print("=" * 55)

    return carteira, processos


# ============================================================
# FIM DO DADOS.PY
# ============================================================
