# INTERFACE.PY
# Dashboard Bromberg
# Tela inicial, Carteira e Controle de Processos

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os
import unicodedata

import pandas as pd

from config import BRANCO, CINZA, CINZA_ESCURO

from filtros import (
    dados_prazos,
    dados_prontos,
    dados_jateamento,
    dados_pintura,
    texto_prazo,
)

# ============================================================
# CORES
# ============================================================

AZUL = "#303394"
ROXO = "#25266F"
CIANO = "#2CB5F5"

CINZA_ATRASADO = "#D1D5DB"
TEXTO_ATRASADO = "#1F2937"

VERMELHO_FUNDO = "#FCA5A5"
VERMELHO_TEXTO = "#7F1D1D"

AMARELO_FUNDO = "#FDE68A"
AMARELO_TEXTO = "#78350F"

AZUL_CLARO_FUNDO = "#BAE6FD"
AZUL_CLARO_TEXTO = "#075985"

VERDE_FUNDO = "#198754"
VERDE_TEXTO = "#FFFFFF"

CINZA_JATEAMENTO = "#6B7280"

COR_PINTURA_FUNDO = "#FEF08A"
COR_PINTURA_TEXTO = "#B91C1C"

# Alternância automática das telas
TEMPO_TELA_MS = 30_000

# Rolagem automática mais lenta
INTERVALO_ROLAGEM_MS = 100
PASSO_ROLAGEM = 0.001


# ============================================================
# TELA DE CARREGAMENTO
# ============================================================


class TelaLoad:

    def __init__(self, root):
        self.janela = tk.Toplevel(root)
        self.janela.title("Carregando Dashboard")
        self.janela.geometry("380x130")
        self.janela.resizable(False, False)
        self.janela.transient(root)
        self.janela.grab_set()

        self.texto = tk.Label(
            self.janela,
            text="Preparando o Dashboard...",
            font=("Segoe UI", 11, "bold"),
            padx=20,
            pady=18,
        )
        self.texto.pack(fill="both", expand=True)

        self.progresso = ttk.Progressbar(
            self.janela,
            mode="indeterminate",
            length=300,
        )
        self.progresso.pack(padx=20, pady=(0, 15))
        self.progresso.start(10)

        self.janela.update_idletasks()

    def atualizar_status(self, texto):
        try:
            if self.janela.winfo_exists():
                self.texto.config(text=texto)
                self.janela.update_idletasks()
        except tk.TclError:
            pass

    def fechar(self):
        try:
            if self.janela.winfo_exists():
                self.progresso.stop()
                self.janela.grab_release()
                self.janela.destroy()
        except tk.TclError:
            pass


# ============================================================
# DASHBOARD
# ============================================================


class Dashboard:

    def __init__(
        self,
        root,
        dados,
        caminho_carteira="",
        caminho_processos="",
    ):
        self.root = root

        if isinstance(dados, pd.DataFrame):
            self.dados = dados.copy()
        else:
            self.dados = pd.DataFrame(dados)

        self.caminho_carteira = caminho_carteira
        self.caminho_processos = caminho_processos

        self.area_atual = "inicio"
        self.indice_tela = 0
        self.automatica_ativa = True
        self.busca_os = ""
        self._id_busca = None
        self._campo_busca_processos = None
        self._campo_busca_carteira = None
        self._pausa_por_busca = False
        self.modo_apresentacao = False
        self._geometria_anterior = None

        self._id_troca = None
        self._id_rolagem = None
        self._canvas_rolagem = None
        self._inicio_rolagem = None
        self._conteudo_rolagem = None
        self._itens_rolagem = 0

        # Estado independente da rolagem automática
        self.rolagem_ativa = True
        self.rolagem_pausada_manual = False
        self.botao_rolagem = None

        self.root.title("Dashboard Bromberg")
        self.root.geometry("1350x800")
        self.root.minsize(1000, 650)
        self.root.configure(bg=CINZA)
        self.root.bind_all("<F11>", self.alternar_modo_apresentacao)
        self.root.bind_all("<Escape>", self.sair_modo_apresentacao)

        self.telas_processos = [
            {
                "nome": "EM PINTURA",
                "fundo": COR_PINTURA_FUNDO,
                "texto": COR_PINTURA_TEXTO,
                "funcao": self._mostrar_pintura,
            },
            {
                "nome": "PRONTO",
                "fundo": VERDE_FUNDO,
                "texto": VERDE_TEXTO,
                "funcao": self._mostrar_prontos,
            },
            {
                "nome": "JATEANDO",
                "fundo": CINZA_JATEAMENTO,
                "texto": BRANCO,
                "funcao": self._mostrar_jateando,
            },
            {
                "nome": "PRAZOS DA CARTEIRA",
                "fundo": AZUL_CLARO_FUNDO,
                "texto": AZUL_CLARO_TEXTO,
                "funcao": self._mostrar_prazos_processos,
            },
        ]

        self._configurar_estilos()
        self._criar_cabecalho()
        self._criar_corpo()
        self._criar_rodape()

        self.mostrar_inicio()
        self._atualizar_relogio()

    # ========================================================
    # ESTILOS
    # ========================================================

    def _configurar_estilos(self):
        estilo = ttk.Style(self.root)
        estilo.theme_use("clam")

        estilo.configure(
            "Bromberg.Treeview",
            font=("Segoe UI", 11),
            rowheight=38,
            background=BRANCO,
            fieldbackground=BRANCO,
            foreground="#1F2937",
            borderwidth=0,
        )

        estilo.configure(
            "Bromberg.Treeview.Heading",
            font=("Segoe UI", 11, "bold"),
            background=ROXO,
            foreground=BRANCO,
            padding=(8, 10),
        )

        estilo.map(
            "Bromberg.Treeview",
            background=[("selected", AZUL)],
            foreground=[("selected", BRANCO)],
        )

    # ========================================================
    # CABEÇALHO
    # ========================================================

    def _criar_cabecalho(self):
        self.cabecalho = tk.Frame(
            self.root,
            bg=ROXO,
            height=78,
        )
        self.cabecalho.pack(fill="x")
        self.cabecalho.pack_propagate(False)

        tk.Label(
            self.cabecalho,
            text="BROMBERG",
            bg=ROXO,
            fg=CIANO,
            font=("Segoe UI", 23, "bold"),
        ).pack(side="left", padx=(24, 18))

        self.titulo_cabecalho = tk.Label(
            self.cabecalho,
            text="DASHBOARD OPERACIONAL",
            bg=ROXO,
            fg=BRANCO,
            font=("Segoe UI", 14, "bold"),
        )
        self.titulo_cabecalho.pack(side="left")

        self.relogio = tk.Label(
            self.cabecalho,
            bg=ROXO,
            fg=BRANCO,
            font=("Segoe UI", 10, "bold"),
        )
        self.relogio.pack(side="right", padx=22)

    def _atualizar_relogio(self):
        try:
            self.relogio.config(text=datetime.now().strftime("%d/%m/%Y  %H:%M:%S"))
            self.root.after(
                1000,
                self._atualizar_relogio,
            )
        except tk.TclError:
            pass

    # ========================================================
    # CORPO E RODAPÉ
    # ========================================================

    def _criar_corpo(self):
        self.corpo = tk.Frame(
            self.root,
            bg=CINZA,
        )
        self.corpo.pack(
            fill="both",
            expand=True,
            padx=22,
            pady=18,
        )

    def _criar_rodape(self):
        self.rodape = tk.Frame(
            self.root,
            bg=ROXO,
        )
        self.rodape.pack(
            fill="x",
            side="bottom",
        )

        tk.Label(
            self.rodape,
            text="Desenvolvido por Daniel Moure",
            bg=ROXO,
            fg=BRANCO,
            anchor="e",
            padx=18,
            pady=7,
            font=("Segoe UI", 9, "bold"),
        ).pack(fill="x")

    def _limpar_corpo(self):
        self._parar_rolagem()

        # Os controles podem ser destruídos ao entrar no modo TV ou trocar
        # de tela. Limpe as referências para que callbacks da rolagem não
        # tentem atualizar botões que já não existem no Tcl/Tk.
        self.botao_rolagem = None
        self.botao_pausa = None
        self.indicador_tela = None

        for widget in self.corpo.winfo_children():
            widget.destroy()

    # ========================================================
    # BOTÕES REUTILIZÁVEIS
    # ========================================================

    def _botao(
        self,
        pai,
        texto,
        comando,
        fundo=AZUL,
        cor=BRANCO,
        fonte=11,
    ):
        return tk.Button(
            pai,
            text=texto,
            command=comando,
            bg=fundo,
            fg=cor,
            activebackground=ROXO,
            activeforeground=BRANCO,
            relief="flat",
            padx=16,
            pady=10,
            cursor="hand2",
            font=("Segoe UI", fonte, "bold"),
        )

    # ========================================================
    # TELA INICIAL
    # ========================================================

    def mostrar_inicio(self):
        self._parar_alternancia()
        self.area_atual = "inicio"
        self.busca_os = ""
        self._campo_busca_processos = None
        self._campo_busca_carteira = None
        self._limpar_corpo()

        self.titulo_cabecalho.config(text="DASHBOARD OPERACIONAL")

        tk.Label(
            self.corpo,
            text="PAINEL DE ACOMPANHAMENTO",
            bg=CINZA,
            fg=ROXO,
            font=("Segoe UI", 24, "bold"),
        ).pack(
            anchor="w",
            pady=(12, 4),
        )

        tk.Label(
            self.corpo,
            text="Escolha a área que deseja acompanhar.",
            bg=CINZA,
            fg=CINZA_ESCURO,
            font=("Segoe UI", 12),
        ).pack(
            anchor="w",
            pady=(0, 22),
        )

        opcoes = tk.Frame(
            self.corpo,
            bg=CINZA,
        )
        opcoes.pack(
            fill="both",
            expand=True,
        )

        opcoes.columnconfigure(0, weight=1)
        opcoes.columnconfigure(1, weight=1)
        opcoes.rowconfigure(0, weight=1)

        carteira = tk.Frame(
            opcoes,
            bg=AZUL,
            padx=24,
            pady=28,
            cursor="hand2",
        )
        carteira.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 10),
            pady=8,
        )

        tk.Label(
            carteira,
            text="01",
            bg=AZUL,
            fg=CIANO,
            font=("Segoe UI", 17, "bold"),
        ).pack(anchor="w")

        tk.Label(
            carteira,
            text="CARTEIRA DE PEDIDOS",
            bg=AZUL,
            fg=BRANCO,
            font=("Segoe UI", 18, "bold"),
            wraplength=340,
            justify="left",
        ).pack(
            anchor="w",
            pady=(14, 10),
        )

        tk.Label(
            carteira,
            text=("Prazos de entrega, prioridades e " "necessidade de materiais."),
            bg=AZUL,
            fg=BRANCO,
            font=("Segoe UI", 11),
            wraplength=340,
            justify="left",
        ).pack(anchor="w")

        self._botao(
            carteira,
            "ABRIR CARTEIRA",
            self.mostrar_carteira,
            fundo=CIANO,
            cor=ROXO,
            fonte=12,
        ).pack(
            anchor="w",
            pady=(28, 0),
        )

        processos = tk.Frame(
            opcoes,
            bg=CIANO,
            padx=24,
            pady=28,
            cursor="hand2",
        )
        processos.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(10, 0),
            pady=8,
        )

        tk.Label(
            processos,
            text="02",
            bg=CIANO,
            fg=ROXO,
            font=("Segoe UI", 17, "bold"),
        ).pack(anchor="w")

        tk.Label(
            processos,
            text="CONTROLE DE PROCESSOS",
            bg=CIANO,
            fg=ROXO,
            font=("Segoe UI", 18, "bold"),
            wraplength=340,
            justify="left",
        ).pack(
            anchor="w",
            pady=(14, 10),
        )

        tk.Label(
            processos,
            text=("Acompanhamento de pintura, processos " "prontos, jateamento e prazos."),
            bg=CIANO,
            fg=ROXO,
            font=("Segoe UI", 11),
            wraplength=340,
            justify="left",
        ).pack(anchor="w")

        self._botao(
            processos,
            "ABRIR CONTROLE",
            self.mostrar_controle_processos,
            fundo=ROXO,
            cor=BRANCO,
            fonte=12,
        ).pack(
            anchor="w",
            pady=(28, 0),
        )

        carteira.bind(
            "<Button-1>",
            lambda evento: self.mostrar_carteira(),
        )
        processos.bind(
            "<Button-1>",
            lambda evento: self.mostrar_controle_processos(),
        )

    # ========================================================
    # CABEÇALHO INTERNO
    # ========================================================

    def _titulo(
        self,
        texto,
        quantidade,
        pai=None,
        fundo=CINZA,
        cor=ROXO,
    ):
        pai = pai or self.corpo

        tk.Label(
            pai,
            text=texto.upper(),
            bg=fundo,
            fg=cor,
            font=("Segoe UI", 21, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 4),
        )

        titulo_normalizado = str(texto).strip().upper()
        if titulo_normalizado == "PRONTO":
            descricao_quantidade = f"{quantidade} OS nos últimos 30 dias"
        elif titulo_normalizado == "PRAZOS DA CARTEIRA":
            descricao_quantidade = f"{quantidade} OS com prazos nos próximos 14 dias"
        else:
            descricao_quantidade = f"{quantidade} OS"

        tk.Label(
            pai,
            text=descricao_quantidade,
            bg=fundo,
            fg=cor,
            font=("Segoe UI", 10, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 12),
        )

    def _barra_interna(self, titulo):
        barra = tk.Frame(
            self.corpo,
            bg=CINZA,
        )
        barra.pack(
            fill="x",
            pady=(0, 12),
        )

        self._botao(
            barra,
            "⌂ Menu inicial",
            self.mostrar_inicio,
            fundo=ROXO,
        ).pack(side="left")

        tk.Label(
            barra,
            text=titulo,
            bg=CINZA,
            fg=ROXO,
            font=("Segoe UI", 15, "bold"),
        ).pack(
            side="left",
            padx=18,
        )

    # ========================================================
    # TABELA DA CARTEIRA
    # ========================================================

    def _tabela(
        self,
        pai,
        colunas,
        altura=15,
    ):
        caixa = tk.Frame(
            pai,
            bg=BRANCO,
        )
        caixa.pack(
            fill="both",
            expand=True,
        )

        nomes = list(colunas.keys())

        tabela = ttk.Treeview(
            caixa,
            columns=nomes,
            show="headings",
            style="Bromberg.Treeview",
            height=altura,
        )

        barra_y = ttk.Scrollbar(
            caixa,
            orient="vertical",
            command=tabela.yview,
        )

        barra_x = ttk.Scrollbar(
            caixa,
            orient="horizontal",
            command=tabela.xview,
        )

        tabela.configure(
            yscrollcommand=barra_y.set,
            xscrollcommand=barra_x.set,
        )

        tabela.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        barra_y.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        barra_x.grid(
            row=1,
            column=0,
            sticky="ew",
        )

        caixa.rowconfigure(0, weight=1)
        caixa.columnconfigure(0, weight=1)

        for nome, largura in colunas.items():
            tabela.heading(
                nome,
                text=nome,
                anchor="center",
            )

            tabela.column(
                nome,
                width=largura,
                minwidth=75,
                anchor="center",
                stretch=True,
            )

        return tabela

    @staticmethod
    def _texto(valor):
        if valor is None:
            return ""

        try:
            if pd.isna(valor):
                return ""
        except (TypeError, ValueError):
            pass

        if isinstance(
            valor,
            (pd.Timestamp, datetime),
        ):
            return valor.strftime("%d/%m/%Y")

        texto = str(valor).strip()

        if texto.lower() in ("nan", "nat", "none"):
            return ""

        return texto

    def _vazio(
        self,
        texto,
        pai=None,
        fundo=BRANCO,
        cor=ROXO,
    ):
        pai = pai or self.corpo

        tk.Label(
            pai,
            text=texto,
            bg=fundo,
            fg=cor,
            font=("Segoe UI", 12, "bold"),
            padx=20,
            pady=24,
            wraplength=950,
            justify="left",
        ).pack(
            fill="x",
            pady=12,
        )

    # ========================================================
    # BUSCA POR ORDEM DE SERVIÇO
    # ========================================================

    @staticmethod
    def _normalizar_busca_os(valor):
        """Normaliza a busca sem remover hífens do identificador da OS."""
        texto = unicodedata.normalize("NFKD", str(valor or ""))
        texto = "".join(c for c in texto if not unicodedata.combining(c))
        return " ".join(texto.casefold().strip().split())

    def _filtrar_os_busca(self, registros, consulta=None):
        consulta = self._normalizar_busca_os(
            self.busca_os if consulta is None else consulta
        )
        if registros is None or registros.empty or not consulta:
            return registros.copy() if isinstance(registros, pd.DataFrame) else pd.DataFrame()
        if "OS" not in registros.columns:
            return registros.iloc[0:0].copy()
        os_normalizadas = registros["OS"].apply(self._normalizar_busca_os)
        return registros[os_normalizadas.str.contains(consulta, regex=False, na=False)].copy()

    def _agendar_busca_processos(self, evento=None):
        """Pausa a rolagem imediatamente ao digitar e agenda o filtro."""
        campo = self._campo_busca_processos
        if campo is not None:
            try:
                consulta_atual = campo.get().strip()
            except tk.TclError:
                consulta_atual = ""

            if consulta_atual:
                # Só retomaremos automaticamente se a rolagem estava ativa
                # antes da busca; uma pausa manual do usuário é respeitada.
                if self._id_rolagem is not None and not self.rolagem_pausada_manual:
                    self._pausa_por_busca = True
                if self._pausa_por_busca:
                    self.pausar_rolagem_manual()
            elif self._pausa_por_busca:
                # A consulta foi apagada: o render da lista reinicia a rolagem.
                self._pausa_por_busca = False

        if self._id_busca is not None:
            try:
                self.root.after_cancel(self._id_busca)
            except tk.TclError:
                pass
        self._id_busca = self.root.after(180, self._aplicar_busca_processos)

    def _aplicar_busca_processos(self):
        self._id_busca = None
        campo = self._campo_busca_processos
        if campo is None:
            return
        try:
            if not campo.winfo_exists():
                return
            self.busca_os = campo.get().strip()
            cursor = campo.index(tk.INSERT)
        except tk.TclError:
            return

        self._mostrar_tela_processo()
        novo_campo = self._campo_busca_processos
        if novo_campo is not None:
            try:
                novo_campo.focus_set()
                novo_campo.icursor(tk.END if cursor is None else min(cursor, len(self.busca_os)))
            except tk.TclError:
                pass
        self._agendar_troca()

    def _agendar_busca_carteira(self, evento=None):
        if self._id_busca is not None:
            try:
                self.root.after_cancel(self._id_busca)
            except tk.TclError:
                pass
        self._id_busca = self.root.after(180, self._aplicar_busca_carteira)

    def _aplicar_busca_carteira(self):
        self._id_busca = None
        campo = self._campo_busca_carteira
        if campo is None:
            return
        try:
            if not campo.winfo_exists():
                return
            self.busca_os = campo.get().strip()
            cursor = campo.index(tk.INSERT)
        except tk.TclError:
            return
        self.mostrar_carteira()
        novo_campo = self._campo_busca_carteira
        if novo_campo is not None:
            try:
                novo_campo.focus_set()
                novo_campo.icursor(min(cursor, len(self.busca_os)))
            except tk.TclError:
                pass

    # ========================================================
    # CARTEIRA E PRAZOS
    # ========================================================

    def mostrar_carteira(self):
        self._parar_alternancia()
        self.area_atual = "carteira"
        self._limpar_corpo()

        self.titulo_cabecalho.config(text="CARTEIRA DE PEDIDOS")
        self._barra_interna("Prazos e prioridades")

        barra_busca = tk.Frame(self.corpo, bg=CINZA)
        barra_busca.pack(fill="x", pady=(0, 10))
        tk.Label(
            barra_busca, text="Buscar OS:", bg=CINZA, fg=ROXO,
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left", padx=(0, 8))
        campo_busca = ttk.Entry(barra_busca, width=22, font=("Segoe UI", 11))
        campo_busca.pack(side="left")
        campo_busca.insert(0, self.busca_os)
        campo_busca.bind("<KeyRelease>", self._agendar_busca_carteira)
        self._campo_busca_carteira = campo_busca
        tk.Label(
            barra_busca, text="Digite a OS completa ou parte dela.",
            bg=CINZA, fg=CINZA_ESCURO, font=("Segoe UI", 9),
        ).pack(side="left", padx=10)

        try:
            registros = dados_prazos(self.dados)
        except Exception as erro:
            self._vazio(f"Não foi possível preparar os prazos:\n{erro}")
            return

        registros = self._filtrar_os_busca(registros)
        self._titulo("Carteira e prazos", len(registros))
        if registros.empty:
            mensagem = (
                f"Nenhuma OS correspondente a '{self.busca_os}' foi encontrada na janela de prazos."
                if self.busca_os
                else "Nenhuma OS foi encontrada na janela de prazos."
            )
            self._vazio(mensagem)
            return

        # Os status ficam associados à OS, mas não ocupam mais as três últimas
        # colunas da tabela. A edição é feita pelos três botões abaixo.
        self._status_materiais_por_os = {}
        # Alterações ficam em memória até o usuário clicar em Salvar alterações.
        self._alteracoes_pendentes_carteira = {}
        for _, linha in registros.iterrows():
            os_chave = self._texto(linha.get("OS")).strip()
            status_isolamento = self._texto(linha.get("Isolamento")).strip() or "Não Solicitado"
            status_mascara = self._texto(linha.get("Máscara")).strip() or "Não Solicitado"
            status_tintas = self._texto(linha.get("Solicitação - Tinta")).strip() or "Não Solicitado"
            self._status_materiais_por_os[os_chave] = {
                "Isolamento": status_isolamento,
                "Máscara": status_mascara,
                "Tintas": status_tintas,
            }
        self._status_materiais_originais_carteira = {
            os_chave: dict(status) for os_chave, status in self._status_materiais_por_os.items()
        }

        colunas = {
            "OS": 125,
            "Cliente": 240,
            "Prazo": 125,
            "Dias": 75,
            "Alerta": 220,
        }
        barra_acoes = tk.Frame(self.corpo, bg=CINZA)
        barra_acoes.pack(fill="x", pady=(10, 0))
        tk.Label(
            barra_acoes,
            text="Selecione uma OS e use os botões para alternar o status de cada material:",
            bg=CINZA, fg=CINZA_ESCURO, font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(0, 8))

        botoes_materiais = tk.Frame(barra_acoes, bg=CINZA)
        botoes_materiais.pack(fill="x")
        self._botoes_status_carteira = {}
        for nome in ("Isolamento", "Máscara", "Tintas"):
            botao = self._botao(
                botoes_materiais,
                f"{nome}: selecione uma OS",
                lambda material=nome: self._alternar_status_material(tabela, material),
                fundo="#D1D5DB",
                cor=ROXO,
                fonte=10,
            )
            botao.pack(side="left", padx=(0, 8), pady=(0, 4))
            botao.configure(state="disabled")
            self._botoes_status_carteira[nome] = botao

        self._botao(
            botoes_materiais,
            "Salvar alterações",
            self._salvar_alteracoes_pendentes_carteira,
            fundo=CIANO,
            cor=ROXO,
            fonte=10,
        ).pack(side="right", padx=(8, 0), pady=(0, 4))

        self._label_pendencias_carteira = tk.Label(
            barra_acoes,
            text="Nenhuma alteração pendente.",
            bg=CINZA,
            fg=CINZA_ESCURO,
            font=("Segoe UI", 9),
        )
        self._label_pendencias_carteira.pack(anchor="w", pady=(2, 0))

        tabela = self._tabela(self.corpo, colunas, altura=10)
        tabela.tag_configure("cinza", background=CINZA_ATRASADO, foreground=TEXTO_ATRASADO)
        tabela.tag_configure("vermelho", background=VERMELHO_FUNDO, foreground=VERMELHO_TEXTO)
        tabela.tag_configure("amarelo", background=AMARELO_FUNDO, foreground=AMARELO_TEXTO)
        tabela.tag_configure("azul", background=AZUL_CLARO_FUNDO, foreground=AZUL_CLARO_TEXTO)

        for _, linha in registros.iterrows():
            try:
                dias = int(linha.get("Dias_Prazo", 0))
            except (TypeError, ValueError):
                dias = 0
            tag = "cinza" if dias <= -2 else "vermelho" if dias <= 2 else "amarelo" if dias <= 6 else "azul"
            tabela.insert(
                "", "end",
                values=(
                    self._texto(linha.get("OS")),
                    self._texto(linha.get("Cliente")),
                    self._texto(linha.get("Prazo")),
                    dias,
                    texto_prazo(dias),
                ),
                tags=(tag,),
            )

        tabela.bind("<<TreeviewSelect>>", lambda _evento: self._atualizar_botoes_status_carteira(tabela))
        tk.Label(
            self.corpo,
            text="Cada clique alterna entre Não Solicitado → Solicitado → Peça sem material → Não Solicitado."
            "A alteração é gravada somente na planilha Carteira.",
            bg=CINZA, fg=CINZA_ESCURO, font=("Segoe UI", 9), wraplength=1100, justify="left",
        ).pack(anchor="w", pady=(5, 0))

    def _atualizar_botoes_status_carteira(self, tabela):
        selecionados = tabela.selection()
        if not selecionados:
            return
        valores = tabela.item(selecionados[0], "values")
        if not valores:
            return
        os_chave = str(valores[0]).strip()
        status = getattr(self, "_status_materiais_por_os", {}).get(os_chave, {})
        for nome, botao in getattr(self, "_botoes_status_carteira", {}).items():
            atual = status.get(nome, "Não Solicitado")
            if atual == "Solicitado":
                fundo, cor = "#198754", "#FFFFFF"  # verde: solicitado
            elif atual.startswith("Peça Sem"):
                fundo, cor = "#F59E0B", "#422006"  # âmbar: peça sem material
            else:
                fundo, cor = "#D1D5DB", ROXO  # cinza: ainda não solicitado
            botao.configure(text=f"{nome}: {atual}", state="normal", bg=fundo, fg=cor, activebackground=fundo, 
                            activeforeground=cor)

    def _alternar_status_material(self, tabela, material):
        selecionados = tabela.selection()
        if not selecionados:
            messagebox.showwarning("Selecionar OS", "Selecione uma OS na tabela primeiro.", parent=self.root)
            return
        valores = tabela.item(selecionados[0], "values")
        if not valores:
            return
        os_chave = str(valores[0]).strip()
        status_os = getattr(self, "_status_materiais_por_os", {}).get(os_chave)
        if status_os is None:
            messagebox.showerror("Status não encontrado",
                                 "Não consegui identificar os status dessa OS.",
                                 parent=self.root)
            return

        atual = status_os.get(material, "Não Solicitado")
        status_sem = {
            "Isolamento": "Peça Sem Isolamento",
            "Máscara": "Peça Sem Máscara",
            "Tintas": "Peça Sem Pintura",
        }[material]
        ciclo = ["Não Solicitado", "Solicitado", status_sem]
        novo = ciclo[(ciclo.index(atual) + 1) % len(ciclo)] if atual in ciclo else "Solicitado"

        # Não acessa o Excel aqui: apenas registra a mudança pendente na interface.
        status_os[material] = novo
        pendentes = self._alteracoes_pendentes_carteira.setdefault(os_chave, {})
        valor_original = self._status_materiais_originais_carteira.get(os_chave, {}).get(material, "Não Solicitado")
        if novo == valor_original:
            pendentes.pop(material, None)
            if not pendentes:
                self._alteracoes_pendentes_carteira.pop(os_chave, None)
        else:
            pendentes[material] = novo
        self._atualizar_botoes_status_carteira(tabela)
        total = sum(len(v) for v in self._alteracoes_pendentes_carteira.values())
        texto = f"{total} alteração(ões) pendente(s) — clique em Salvar alterações." if total else "Nenhuma "
        "alteração pendente."
        self._label_pendencias_carteira.config(text=texto)

    def _salvar_alteracoes_pendentes_carteira(self):
        pendentes = getattr(self, "_alteracoes_pendentes_carteira", {})
        if not pendentes:
            messagebox.showinfo("Carteira", "Não há alterações pendentes para salvar.", parent=self.root)
            return
        try:
            self._salvar_status_excel_lote(pendentes)
        except Exception as erro:
            messagebox.showerror(
                "Erro ao salvar",
                f"Não foi possível salvar as alterações na planilha Carteira.\n\n{erro}",
                parent=self.root,
            )
            return

        self._status_materiais_originais_carteira = {
            os_chave: dict(status) for os_chave, status in self._status_materiais_por_os.items()
        }
        quantidade = sum(len(v) for v in pendentes.values())
        self._alteracoes_pendentes_carteira = {}
        self._label_pendencias_carteira.config(text="Alterações salvas na planilha Carteira.")
        messagebox.showinfo(
            "Alterações salvas",
            f"{quantidade} alteração(ões) gravada(s) na planilha Carteira.",
            parent=self.root,
        )

    @staticmethod
    def _normalizar_cabecalho(valor):
        texto = unicodedata.normalize("NFKD", str(valor or ""))
        texto = "".join(c for c in texto if not unicodedata.combining(c))
        return " ".join(texto.lower().strip().replace("_", " ").split())

    def _abrir_editor_status(self, tabela):
        selecionados = tabela.selection()
        if not selecionados:
            messagebox.showwarning("Editar status", "Selecione uma OS na tabela primeiro.", parent=self.root)
            return

        item_id = selecionados[0]
        valores = list(tabela.item(item_id, "values"))
        if len(valores) < 8:
            messagebox.showerror("Editar status", "Não foi possível ler os dados da OS selecionada.", parent=self.root)
            return

        os_numero = str(valores[0]).strip()
        janela = tk.Toplevel(self.root)
        janela.title(f"Editar status — OS {os_numero}")
        janela.transient(self.root)
        janela.grab_set()
        janela.resizable(False, False)
        janela.configure(bg=CINZA)

        tk.Label(janela, text=f"OS: {os_numero}", bg=CINZA, fg=ROXO, font=("Segoe UI", 15, "bold")).grid(
            row=0, column=0, columnspan=2, padx=22, pady=(18, 12), sticky="w"
        )

        # Cada coluna tem suas próprias opções. Assim, uma situação de máscara
        # não pode ser selecionada por engano em isolamento ou tintas.
        opcoes_por_campo = {
            "Isolamento": ["Não Solicitado", "Solicitado", "Peça Sem Isolamento", "Não se aplica"],
            "Máscara": ["Não Solicitado", "Solicitado", "Peça Sem Máscara", "Não se aplica"],
            "Tintas": ["Não Solicitado", "Solicitado", "Peça Sem Pintura", "Não se aplica"],
        }
        campos = [("Isolamento", 5), ("Máscara", 6), ("Tintas", 7)]
        variaveis = {}
        for linha_idx, (nome, indice) in enumerate(campos, start=1):
            tk.Label(janela, text=nome, bg=CINZA, fg=ROXO, font=("Segoe UI", 11, "bold")).grid(
                row=linha_idx, column=0, padx=(22, 12), pady=7, sticky="w"
            )

            atual = str(valores[indice] or "Não Solicitado").strip()
            lista = list(opcoes_por_campo[nome])
            # Preserva qualquer valor já existente na carteira, mesmo que seja legado.
            if atual and atual not in lista:
                lista.insert(0, atual)
            var = tk.StringVar(value=atual or "Não Solicitado")
            combo = ttk.Combobox(janela, textvariable=var, values=lista, state="readonly", width=30)
            combo.grid(row=linha_idx, column=1, padx=(0, 22), pady=7, sticky="ew")
            variaveis[nome] = var

        def salvar():
            novos = {nome: var.get().strip() for nome, var in variaveis.items()}
            alterados = {
                nome: valor
                for nome, valor in novos.items()
                if valor != str(valores[{"Isolamento": 5, "Máscara": 6, "Tintas": 7}[nome]] or "Não Solicitado").strip()
            }
            if not alterados:
                janela.destroy()
                return
            try:
                self._salvar_status_excel(os_numero, alterados)
            except Exception as erro:
                messagebox.showerror("Erro ao salvar", f"Não foi possível salvar no Excel.\n\n{erro}", parent=janela)
                return

            for nome, indice in (("Isolamento", 5), ("Máscara", 6), ("Tintas", 7)):
                if nome in alterados:
                    valores[indice] = alterados[nome]
            tabela.item(item_id, values=valores)
            # A confirmação é exibida pela própria janela de edição.
            messagebox.showinfo(
                "Status atualizado", f"As alterações da OS {os_numero} foram salvas na carteira Excel.", parent=janela
            )
            janela.destroy()

        botoes = tk.Frame(janela, bg=CINZA)
        botoes.grid(row=4, column=0, columnspan=2, padx=22, pady=(16, 20), sticky="e")
        self._botao(botoes, "Cancelar", janela.destroy, fundo="#D1D5DB", cor=ROXO).pack(side="right", padx=(8, 0))
        self._botao(botoes, "Salvar alterações", salvar, fundo=CIANO, cor=ROXO).pack(side="right")
        janela.bind("<Escape>", lambda _event: janela.destroy())

    def _salvar_status_excel_lote(self, alteracoes):
        """Grava todas as alterações pendentes na Carteira em uma única sessão COM."""
        caminho = str(self.caminho_carteira or "").strip()
        if not caminho or not os.path.isfile(caminho):
            raise FileNotFoundError(f"Arquivo da carteira não encontrado:\n{caminho or '(caminho vazio)'}")
        try:
            import win32com.client as win32
        except ImportError as erro:
            raise RuntimeError("Instale pywin3 usado pelo Dashboard: python -m pip install pywin32") from erro

        def norm(v):
            return self._normalizar_cabecalho(v)

        aliases = {
            "OS": {norm(x) for x in ("OS", "Ordem de Serviço", "Ordem Serviço", "N OS", "Número OS")},
            "Isolamento": {norm(x) for x in ("Isolamento", "Status Isolamento", 
                                             "Solicitação Isolamento", "Solicitação de Isolamento")},
            "Máscara": {norm(x) for x in ("Máscara", "Status Máscara",
                                          "Solicitação Máscara", "Solicitação de Máscara")},
            "Tintas": {norm(x) for x in ("Solicitação - Tinta", "Solicitação Tinta", "Solicitação de Tinta", "Tintas",
                                         "Status Tinta", "Status Tintas")},
        }
        excel = None
        workbook = None
        abriu_arquivo = False
        salvamento_concluido = False
        try:
            excel = win32.DispatchEx("Excel.Application")
            excel.Visible = False
            excel.DisplayAlerts = False
            excel.EnableEvents = False
            caminho_norm = os.path.normcase(os.path.abspath(caminho))
            for wb in excel.Workbooks:
                try:
                    if os.path.normcase(os.path.abspath(wb.FullName)) == caminho_norm:
                        workbook = wb
                        break
                except Exception:
                    pass
            if workbook is None:
                workbook = excel.Workbooks.Open(os.path.abspath(caminho), UpdateLinks=0, ReadOnly=False)
                abriu_arquivo = True
            encontrados = set()
            pendentes_normalizados = {str(k).strip().replace(".0", ""): v for k, v in alteracoes.items()}
            for planilha in workbook.Worksheets:
                usado = planilha.UsedRange
                ultima_linha = usado.Row + usado.Rows.Count - 1
                ultima_coluna = usado.Column + usado.Columns.Count - 1
                mapa = None
                linha_cabecalho = None
                for r in range(1, min(max(ultima_linha, 1), 10) + 1):
                    cab = {}
                    for c in range(1, ultima_coluna + 1):
                        chave = norm(planilha.Cells(r, c).Value or "")
                        for campo, nomes in aliases.items():
                            if chave in nomes and campo not in cab:
                                cab[campo] = c
                    if "OS" in cab and any(k in cab for k in ("Isolamento", "Máscara", "Tintas")):
                        mapa, linha_cabecalho = cab, r
                        break
                if not mapa:
                    continue
                for r in range(linha_cabecalho + 1, ultima_linha + 1):
                    valor_os = planilha.Cells(r, mapa["OS"]).Value
                    if valor_os is None:
                        continue
                    os_planilha = str(valor_os).strip()
                    if os_planilha.endswith(".0"):
                        os_planilha = os_planilha[:-2]
                    if os_planilha not in pendentes_normalizados:
                        continue
                    for material, novo_status in pendentes_normalizados[os_planilha].items():
                        if material not in mapa:
                            raise RuntimeError(f"A coluna de status '{material}' não foi encontrada na planilha.")
                        planilha.Cells(r, mapa[material]).Value = novo_status
                    encontrados.add(os_planilha)
            faltantes = set(pendentes_normalizados) - encontrados
            if faltantes:
                raise RuntimeError("Não encontrei estas OS na planilha Carteira: " + ", ".join(sorted(faltantes)))
            workbook.Save()
            salvamento_concluido = True
        finally:
            if workbook is not None and abriu_arquivo:
                try:
                    workbook.Close(SaveChanges=salvamento_concluido)
                except Exception:
                    pass
            if excel is not None:
                try:
                    excel.Quit()
                except Exception:
                    pass

    def _salvar_status_excel(self, os_numero, novos_status):
        """Atualiza os status na carteira usando Excel COM, preservando macros.

        Procura a OS e os cabeçalhos nas planilhas; não depende de um nome fixo
        de aba. Requer Microsoft Excel e pywin32 instalados no Windows.
        """
        caminho = str(self.caminho_carteira or "").strip()
        if not caminho:
            raise RuntimeError("O caminho da carteira não foi informado ao Dashboard. Confira main.py e config.py.")
        if not os.path.isfile(caminho):
            raise FileNotFoundError(f"Arquivo da carteira não encontrado:\n{caminho}")

        try:
            import win32com.client as win32
        except ImportError as erro:
            raise RuntimeError(
                "Instale pywin32 no mesmo Python que executa o Dashboard: python -m pip install pywin32"
            ) from erro

        def norm(v):
            return self._normalizar_cabecalho(v)

        aliases = {
            "OS": {"os", "ordem de servico", "ordem servico", "n os", "numero os"},
            "Isolamento": {"isolamento", "status isolamento", "solicitacao isolamento", "solicitacao de isolamento"},
            "Máscara": {"mascara", "status mascara", "solicitacao mascara", "solicitacao de mascara"},
            "Tintas": {
                "solicitacao - tinta",
                "solicitacao tinta",
                "solicitacao de tinta",
                "tintas",
                "status tinta",
                "status tintas",
            },
        }
        aliases = {k: {norm(x) for x in v} for k, v in aliases.items()}

        excel = None
        workbook = None
        abriu_excel = False
        abriu_arquivo = False
        try:
            # Usa uma instância COM própria e oculta: não abre nem traz a janela
            # do Excel para frente quando o usuário altera um status no Dashboard.
            excel = win32.DispatchEx("Excel.Application")
            abriu_excel = True
            excel.Visible = False
            excel.DisplayAlerts = False
            excel.EnableEvents = True

            caminho_norm = os.path.normcase(os.path.abspath(caminho))
            for wb in excel.Workbooks:
                try:
                    if os.path.normcase(os.path.abspath(wb.FullName)) == caminho_norm:
                        workbook = wb
                        break
                except Exception:
                    continue
            if workbook is None:
                workbook = excel.Workbooks.Open(os.path.abspath(caminho))
                abriu_arquivo = True

            os_alvo = str(os_numero).strip().replace(".0", "")
            for planilha in workbook.Worksheets:
                usado = planilha.UsedRange
                ultima_linha = usado.Row + usado.Rows.Count - 1
                ultima_coluna = usado.Column + usado.Columns.Count - 1
                limite_cabecalho = min(max(ultima_linha, 1), 10)
                mapa = None
                linha_cabecalho = None

                for r in range(1, limite_cabecalho + 1):
                    valores_cab = {}
                    for c in range(1, ultima_coluna + 1):
                        v = planilha.Cells(r, c).Value
                        chave = norm(v) if v is not None else ""
                        for campo, nomes in aliases.items():
                            if chave in nomes and campo not in valores_cab:
                                valores_cab[campo] = c
                    if "OS" in valores_cab and any(k in valores_cab for k in ("Isolamento", "Máscara", "Tintas")):
                        mapa = valores_cab
                        linha_cabecalho = r
                        break
                if not mapa:
                    continue

                for r in range(linha_cabecalho + 1, ultima_linha + 1):
                    valor_os = planilha.Cells(r, mapa["OS"]).Value
                    if valor_os is None:
                        continue
                    os_planilha = str(valor_os).strip()
                    if os_planilha.endswith(".0"):
                        os_planilha = os_planilha[:-2]
                    if os_planilha != os_alvo:
                        continue

                    for campo, valor in novos_status.items():
                        if campo in mapa:
                            planilha.Cells(r, mapa[campo]).Value = valor
                    workbook.Save()
                    return

            raise RuntimeError(
                "Não encontrei a OS e os cabeçalhos de status na carteira. "
                "Confira se a coluna OS e os cabeçalhos de Isolamento, Máscara e Tinta existem na planilha."
            )
        finally:
            if workbook is not None and abriu_arquivo:
                try:
                    workbook.Close(SaveChanges=True)
                except Exception:
                    pass
            if excel is not None and abriu_excel:
                try:
                    excel.Quit()
                except Exception:
                    pass

    # ========================================================
    # CONTROLE DE PROCESSOS
    # ========================================================

    def mostrar_controle_processos(self):
        self.area_atual = "processos"
        self.indice_tela = 0
        self.automatica_ativa = True

        self._limpar_corpo()

        self.titulo_cabecalho.config(text="CONTROLE DE PROCESSOS")

        self._mostrar_tela_processo()
        self._agendar_troca()

    def entrar_modo_apresentacao(self):
        """Exibe o carrossel em tela cheia, sem cabeçalho, rodapé ou controles."""
        if self.area_atual != "processos":
            self.mostrar_controle_processos()

        if self.modo_apresentacao:
            return

        self.modo_apresentacao = True
        try:
            self._geometria_anterior = self.root.geometry()
            self.cabecalho.pack_forget()
            self.rodape.pack_forget()
            self.corpo.pack_configure(padx=0, pady=0)
            self.root.attributes("-fullscreen", True)
        except tk.TclError:
            self.modo_apresentacao = False
            return

        self._mostrar_tela_processo()
        self._agendar_troca()

    def sair_modo_apresentacao(self, evento=None):
        """Sai do modo TV com Esc e restaura a janela normal."""
        if not self.modo_apresentacao:
            return

        self.modo_apresentacao = False
        self._parar_rolagem()
        self._parar_alternancia()

        try:
            self.root.attributes("-fullscreen", False)
            self.cabecalho.pack(fill="x", before=self.corpo)
            self.rodape.pack(fill="x", side="bottom")
            self.corpo.pack_configure(padx=22, pady=18)
            if self._geometria_anterior:
                self.root.geometry(self._geometria_anterior)
        except tk.TclError:
            pass

        if self.area_atual == "processos":
            self._mostrar_tela_processo()
            self._agendar_troca()

    def alternar_modo_apresentacao(self, evento=None):
        if self.modo_apresentacao:
            self.sair_modo_apresentacao()
        else:
            self.entrar_modo_apresentacao()

    def _parar_alternancia(self):
        if self._id_troca is not None:
            try:
                self.root.after_cancel(self._id_troca)
            except tk.TclError:
                pass

        self._id_troca = None

    def _agendar_troca(self):
        self._parar_alternancia()

        if self.area_atual == "processos" and self.automatica_ativa and not self.busca_os:
            self._id_troca = self.root.after(
                TEMPO_TELA_MS,
                self._trocar_tela_automatica,
            )

    def _trocar_tela_automatica(self):
        self._id_troca = None

        if self.area_atual != "processos" or not self.automatica_ativa:
            return

        self.indice_tela = (self.indice_tela + 1) % len(self.telas_processos)

        self._mostrar_tela_processo()
        self._agendar_troca()

    def anterior(self):
        if self.area_atual != "processos":
            return

        self.indice_tela = (self.indice_tela - 1) % len(self.telas_processos)

        self._mostrar_tela_processo()
        self._agendar_troca()

    def proximo(self):
        if self.area_atual != "processos":
            return

        self.indice_tela = (self.indice_tela + 1) % len(self.telas_processos)

        self._mostrar_tela_processo()
        self._agendar_troca()

    def alternar_pausa(self):
        self.automatica_ativa = not self.automatica_ativa

        if self.automatica_ativa:
            self.botao_pausa.config(
                text="⏸ Pausar",
            )
            self._agendar_troca()
        else:
            self._parar_alternancia()
            self.botao_pausa.config(
                text="▶ Retomar",
            )

        self._atualizar_indicador()

    def _mostrar_tela_processo(self):
        if self.area_atual != "processos":
            return

        self._limpar_corpo()

        tela = self.telas_processos[self.indice_tela]

        if not self.modo_apresentacao:
            self._criar_controles_processos()

        painel = tk.Frame(
            self.corpo,
            bg=tela["fundo"],
            padx=0 if self.modo_apresentacao else 18,
            pady=0 if self.modo_apresentacao else 15,
        )
        painel.pack(
            fill="both",
            expand=True,
        )

        quantidade = self._quantidade_tela(tela["funcao"])
        if self.busca_os:
            quantidade = self._quantidade_filtrada_tela(tela["funcao"])

        self._titulo(
            tela["nome"],
            quantidade,
            pai=painel,
            fundo=tela["fundo"],
            cor=tela["texto"],
        )

        try:
            tela["funcao"](
                painel,
                tela["fundo"],
                tela["texto"],
            )
        except Exception as erro:
            self._vazio(
                ("Não foi possível exibir esta tela.\n\n" f"{type(erro).__name__}: {erro}"),
                pai=painel,
                fundo=tela["fundo"],
                cor=tela["texto"],
            )

        self._atualizar_indicador()

    def _criar_controles_processos(self):
        # Primeira linha: navegação e rolagem. Segunda linha: busca,
        # evitando que os controles sejam cortados em janelas menores.
        barra = tk.Frame(self.corpo, bg=CINZA)
        barra.pack(fill="x", pady=(0, 4))

        self._botao(barra, "⌂ Menu inicial", self.mostrar_inicio, fundo=ROXO).pack(side="left")
        self._botao(barra, "◀ Anterior", self.anterior, fundo=AZUL).pack(side="left", padx=(8, 0))

        self.botao_pausa = self._botao(
            barra,
            ("⏸ Pausar" if self.automatica_ativa else "▶ Retomar"),
            self.alternar_pausa,
            fundo=CIANO,
            cor=ROXO,
        )
        self.botao_pausa.pack(side="left", padx=8)

        self._botao(barra, "Próxima ▶", self.proximo, fundo=AZUL).pack(side="left")

        self.botao_rolagem = self._botao(
            barra, "⏸ Pausar rolagem", self.alternar_rolagem,
            fundo=CIANO, cor=ROXO,
        )
        self.botao_rolagem.pack(side="left", padx=(8, 0))

        self._botao(
            barra, "▣ Ampliar", self.entrar_modo_apresentacao,
            fundo=ROXO, cor=BRANCO,
        ).pack(side="left", padx=(8, 0))

        self.indicador_tela = tk.Label(
            barra, text="", bg=CINZA, fg=ROXO,
            font=("Segoe UI", 10, "bold"),
        )
        self.indicador_tela.pack(side="right", padx=8)

        barra_busca = tk.Frame(self.corpo, bg=CINZA)
        barra_busca.pack(fill="x", pady=(0, 10))
        tk.Label(
            barra_busca, text="Buscar OS:", bg=CINZA, fg=ROXO,
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left", padx=(2, 8))
        campo_busca = ttk.Entry(barra_busca, width=24, font=("Segoe UI", 11))
        campo_busca.pack(side="left")
        campo_busca.insert(0, self.busca_os)
        campo_busca.bind("<KeyRelease>", self._agendar_busca_processos)
        self._campo_busca_processos = campo_busca
        tk.Label(
            barra_busca, text="Digite a OS completa ou parte dela.",
            bg=CINZA, fg=CINZA_ESCURO, font=("Segoe UI", 9),
        ).pack(side="left", padx=10)

    def _atualizar_indicador(self):
        if not hasattr(self, "indicador_tela"):
            return

        tela = self.telas_processos[self.indice_tela]

        estado = "AUTOMÁTICO" if self.automatica_ativa else "PAUSADO"

        self.indicador_tela.config(text=(f"{self.indice_tela + 1}/4 — " f"{tela['nome']} — {estado}"))

    def _quantidade_tela(self, funcao):
        try:
            if funcao == self._mostrar_pintura:
                return len(dados_pintura(self.dados))
            if funcao == self._mostrar_prontos:
                return len(dados_prontos(self.dados))
            if funcao == self._mostrar_jateando:
                return len(dados_jateamento(self.dados))
            if funcao == self._mostrar_prazos_processos:
                return len(dados_prazos(self.dados))
        except Exception:
            pass

        return 0

    def _quantidade_filtrada_tela(self, funcao):
        try:
            if funcao == self._mostrar_pintura:
                registros = dados_pintura(self.dados)
            elif funcao == self._mostrar_prontos:
                registros = dados_prontos(self.dados)
            elif funcao == self._mostrar_jateando:
                registros = dados_jateamento(self.dados)
            elif funcao == self._mostrar_prazos_processos:
                registros = dados_prazos(self.dados)
            else:
                return 0
            return len(self._filtrar_os_busca(registros))
        except Exception:
            return 0

    # ========================================================
    # ROLAGEM AUTOMÁTICA
    # ========================================================

    def _parar_rolagem(self):
        if self._id_rolagem is not None:
            try:
                self.root.after_cancel(self._id_rolagem)
            except tk.TclError:
                pass

        self._id_rolagem = None
        self._canvas_rolagem = None
        self._inicio_rolagem = None
        self._conteudo_rolagem = None

    def _criar_lista_rolavel(self, pai, fundo):
        exterior = tk.Frame(
            pai,
            bg=fundo,
        )
        exterior.pack(
            fill="both",
            expand=True,
        )

        canvas = tk.Canvas(
            exterior,
            bg=fundo,
            highlightthickness=0,
            borderwidth=0,
        )

        barra = ttk.Scrollbar(
            exterior,
            orient="vertical",
            command=self._rolagem_manual_movimento,
        )

        canvas.configure(
            yscrollcommand=barra.set,
        )

        canvas.pack(
            side="left",
            fill="both",
            expand=True,
        )
        barra.pack(
            side="right",
            fill="y",
        )

        conteudo = tk.Frame(
            canvas,
            bg=fundo,
        )

        janela_id = canvas.create_window(
            (0, 0),
            window=conteudo,
            anchor="nw",
        )

        def ajustar_conteudo(event=None):
            canvas.configure(
                scrollregion=canvas.bbox("all"),
            )

            canvas.itemconfigure(
                janela_id,
                width=canvas.winfo_width(),
            )

        conteudo.bind(
            "<Configure>",
            ajustar_conteudo,
        )
        canvas.bind(
            "<Configure>",
            ajustar_conteudo,
        )

        canvas.bind(
            "<MouseWheel>",
            self._rolagem_roda_mouse,
        )
        conteudo.bind(
            "<MouseWheel>",
            self._rolagem_roda_mouse,
        )

        self._canvas_rolagem = canvas
        self._conteudo_rolagem = conteudo

        return conteudo, canvas

    def _iniciar_rolagem(self, canvas):
        self._parar_rolagem()

        self._canvas_rolagem = canvas
        self._inicio_rolagem = 0.0

        # Durante uma busca, mantenha os cartões imóveis para facilitar a leitura.
        # A rolagem só é retomada automaticamente quando a busca é apagada,
        # caso ela tenha sido pausada por causa da própria busca.
        if self.busca_os and self._pausa_por_busca:
            self.rolagem_ativa = False
            self.rolagem_pausada_manual = True
            if self.botao_rolagem is not None:
                self.botao_rolagem.config(text="▶ Retomar rolagem")
            return

        self.rolagem_ativa = True
        self.rolagem_pausada_manual = False

        if self.botao_rolagem is not None:
            self.botao_rolagem.config(text="⏸ Pausar rolagem")

        def rolar():
            if self.area_atual != "processos" or self._canvas_rolagem is not canvas:
                return

            if not self.rolagem_ativa or self.rolagem_pausada_manual:
                self._id_rolagem = None
                return

            try:
                bbox = canvas.bbox("all")

                if not bbox:
                    self._id_rolagem = None
                    return

                altura_conteudo = bbox[3] - bbox[1]
                altura_visivel = canvas.winfo_height()

                if altura_conteudo <= altura_visivel + 5:
                    canvas.yview_moveto(0)
                else:
                    atual = canvas.yview()[0]
                    final = canvas.yview()[1]

                    if final >= 0.999:
                        canvas.yview_moveto(0)
                    else:
                        # Ajusta a fração de deslocamento à altura do conteúdo:
                        # cartões altos/listas longas não ficam lentos, e listas
                        # curtas não disparam rapidamente pela tela.
                        pixels_por_segundo = max(
                            12.0,
                            min(45.0, 12.0 + (altura_conteudo / 180.0)),
                        )
                        deslocamento_pixels = pixels_por_segundo * (
                            INTERVALO_ROLAGEM_MS / 1000.0
                        )
                        passo_adaptativo = deslocamento_pixels / altura_conteudo
                        canvas.yview_moveto(
                            min(atual + passo_adaptativo, 1.0)
                        )

                self._id_rolagem = self.root.after(
                    INTERVALO_ROLAGEM_MS,
                    rolar,
                )

            except (tk.TclError, IndexError):
                self._id_rolagem = None

        self._id_rolagem = self.root.after(
            1000,
            rolar,
        )

    def pausar_rolagem_manual(self, evento=None):
        self.rolagem_pausada_manual = True

        if self._id_rolagem is not None:
            try:
                self.root.after_cancel(self._id_rolagem)
            except tk.TclError:
                pass

            self._id_rolagem = None

        if self.botao_rolagem is not None:
            self.botao_rolagem.config(text="▶ Retomar rolagem")

    def alternar_rolagem(self):
        if self.rolagem_pausada_manual or not self.rolagem_ativa:
            self.rolagem_pausada_manual = False
            self.rolagem_ativa = True

            if self._canvas_rolagem is not None:
                self._iniciar_rolagem(self._canvas_rolagem)
        else:
            self.pausar_rolagem_manual()

    def _rolagem_manual_movimento(self, *args):
        self.pausar_rolagem_manual()

        if self._canvas_rolagem is not None:
            self._canvas_rolagem.yview(*args)

    def _rolagem_roda_mouse(self, evento):
        self.pausar_rolagem_manual()

        if self._canvas_rolagem is not None and evento.delta:
            unidades = -1 if evento.delta > 0 else 1

            self._canvas_rolagem.yview_scroll(
                unidades,
                "units",
            )

        return "break"

    # ========================================================
    # CARTÕES DAS ORDENS DE SERVIÇO
    # ========================================================

    def _cartao_os(
        self,
        pai,
        linha,
        fundo,
        texto,
        tipo="processo",
    ):
        cartao = tk.Frame(
            pai,
            bg=fundo,
            highlightbackground="#FFFFFF",
            highlightthickness=1,
            padx=14,
            pady=10,
        )
        cartao.pack(
            fill="x",
            padx=4,
            pady=5,
        )

        os_numero = self._texto(linha.get("OS")) or "OS sem número"

        cliente = self._texto(linha.get("Cliente"))

        cabine = self._primeiro_valor(
            linha,
            [
                "Cabine(Pintor)",
                "Cabine-Pintor",
                "Cabine/Pintor",
                "Cabine",
                "Pintor",
            ],
        )

        primeira = self._primeiro_valor(
            linha,
            [
                "1ª Demão",
                "1a Demão",
                "Primeira Demão",
                "Data 1ª Demão",
            ],
        )

        segunda = self._primeiro_valor(
            linha,
            [
                "2ª Demão",
                "2a Demão",
                "Segunda Demão",
                "Data 2ª Demão",
            ],
        )

        tk.Label(
            cartao,
            text=os_numero,
            bg=fundo,
            fg=texto,
            font=("Segoe UI", 19, "bold"),
        ).pack(anchor="w")

        if cliente:
            tk.Label(
                cartao,
                text=cliente,
                bg=fundo,
                fg=texto,
                font=("Segoe UI", 12, "bold"),
            ).pack(
                anchor="w",
                pady=(2, 0),
            )

        detalhes = []

        if cabine:
            detalhes.append(f"Cabine-pintor: {cabine}")

        if primeira:
            detalhes.append(f"1ª demão: {primeira}")

        if segunda:
            detalhes.append(f"2ª demão: {segunda}")

        # Prazo da peça pronta e prazo da carteira
        if tipo in ("prazo", "pronto"):
            prazo = self._primeiro_valor(
                linha,
                [
                    "Prazo",
                    "Prazo Entrega Contratual",
                    "Prazo Entrega Original",
                    "Data Prazo",
                ],
            )

            if prazo:
                detalhes.append(f"Prazo de entrega: {prazo}")

            if tipo == "prazo":
                dias = self._primeiro_valor(
                    linha,
                    ["Dias_Prazo", "Dias"],
                )

                if dias != "":
                    detalhes.append(f"Dias até o prazo: {dias}")

        # A data de jateamento deve aparecer no cartão da OS quando informada.
        if tipo == "jateando":
            data_jateamento = self._primeiro_valor(
                linha,
                ["Jateamento", "Data Jateamento", "Data do Jateamento"],
            )
            if data_jateamento:
                detalhes.append(f"Jateado em: {data_jateamento}")

        # Data da 2ª demão é considerada a data em que
        # a peça ficou pronta, conforme solicitado.
        if tipo == "pronto":
            data_pronta = self._primeiro_valor(
                linha,
                [
                    "Data_Peca_Pronta",
                    "2ª Demão",
                    "2a Demão",
                    "Data 2ª Demão",
                    "Data da 2ª Demão",
                ],
            )

            if data_pronta:
                detalhes.append(f"Peça pronta em: {data_pronta}")

        if detalhes:
            tk.Label(
                cartao,
                text="   •   ".join(detalhes),
                bg=fundo,
                fg=texto,
                font=("Segoe UI", 10),
                justify="left",
                wraplength=1050,
            ).pack(
                anchor="w",
                pady=(5, 0),
            )

        # Alerta visual para conferir a máscara.
        if tipo == "pronto":
            tk.Label(
                cartao,
                text="⚠ VERIFICAR MÁSCARA",
                bg=fundo,
                fg="#B91C1C",
                font=("Segoe UI", 12, "bold"),
            ).pack(
                anchor="w",
                pady=(8, 0),
            )

        return cartao

    def _primeiro_valor(self, linha, candidatos):
        for coluna in candidatos:
            if coluna in linha.index:
                valor = self._texto(linha.get(coluna))

                if valor:
                    return valor

        mapa = {str(coluna).strip().casefold(): coluna for coluna in linha.index}

        for candidato in candidatos:
            coluna_real = mapa.get(candidato.casefold())

            if coluna_real is not None:
                valor = self._texto(linha.get(coluna_real))

                if valor:
                    return valor

        return ""

    def _mostrar_lista_cartoes(
        self,
        registros,
        fundo,
        texto,
        tipo="processo",
        mensagem_vazia="Nenhuma OS encontrada.",
    ):
        registros = self._filtrar_os_busca(registros)
        if registros is None or registros.empty:
            if self.busca_os:
                mensagem_vazia = f"Nenhuma OS correspondente a '{self.busca_os}' foi encontrada nesta tela."
            self._vazio(
                mensagem_vazia,
                pai=self.corpo,
                fundo=fundo,
                cor=texto,
            )
            return

        conteudo, canvas = self._criar_lista_rolavel(
            self.corpo,
            fundo,
        )

        for _, linha in registros.iterrows():
            self._cartao_os(
                conteudo,
                linha,
                fundo,
                texto,
                tipo=tipo,
            )

        self._iniciar_rolagem(canvas)

    # ========================================================
    # TELA 1 — EM PINTURA
    # ========================================================

    def _mostrar_pintura(
        self,
        pai=None,
        fundo=None,
        texto=None,
    ):
        pai = pai or self.corpo
        fundo = fundo or COR_PINTURA_FUNDO
        texto = texto or COR_PINTURA_TEXTO

        registros = dados_pintura(self.dados)

        self._mostrar_lista_cartoes(
            registros,
            fundo,
            texto,
            mensagem_vazia=("Nenhum processo em pintura encontrado."),
        )

    # ========================================================
    # TELA 2 — PRONTO
    # ========================================================

    def _mostrar_prontos(
        self,
        pai=None,
        fundo=None,
        texto=None,
    ):
        pai = pai or self.corpo
        fundo = fundo or VERDE_FUNDO
        texto = texto or VERDE_TEXTO

        registros = dados_prontos(self.dados)

        self._mostrar_lista_cartoes(
            registros,
            fundo,
            texto,
            tipo="pronto",
            mensagem_vazia=("Nenhuma peça ficou pronta nos últimos 30 dias."),
        )

    # ========================================================
    # TELA 3 — JATEANDO
    # ========================================================

    def _mostrar_jateando(
        self,
        pai=None,
        fundo=None,
        texto=None,
    ):
        pai = pai or self.corpo
        fundo = fundo or CINZA_JATEAMENTO
        texto = texto or BRANCO

        registros = dados_jateamento(self.dados)

        self._mostrar_lista_cartoes(
            registros,
            fundo,
            texto,
            tipo="jateando",
            mensagem_vazia=("Nenhum processo em jateamento encontrado."),
        )

    # ========================================================
    # TELA 4 — PRAZOS DA CARTEIRA
    # ========================================================

    def _mostrar_prazos_processos(
        self,
        pai=None,
        fundo=None,
        texto=None,
    ):
        pai = pai or self.corpo
        fundo = fundo or AZUL_CLARO_FUNDO
        texto = texto or AZUL_CLARO_TEXTO

        try:
            registros = dados_prazos(self.dados).copy()
        except Exception as erro:
            self._vazio(
                f"Erro ao consultar os prazos:\n{erro}",
                pai=pai,
                fundo=fundo,
                cor=texto,
            )
            return

        self._aviso_materiais(
            pai,
            fundo,
            texto,
        )

        if registros.empty:
            self._vazio(
                "Nenhuma OS encontrada na janela de prazos.",
                pai=pai,
                fundo=fundo,
                cor=texto,
            )
            return

        if "Dias_Prazo" in registros.columns:
            registros = registros.sort_values(
                by="Dias_Prazo",
                ascending=True,
                na_position="last",
            )

        conteudo, canvas = self._criar_lista_rolavel(
            pai,
            fundo,
        )

        for _, linha in registros.iterrows():
            try:
                dias = int(linha.get("Dias_Prazo", 0))
            except (TypeError, ValueError):
                dias = 0

            if dias <= -2:
                cor_fundo = CINZA_ATRASADO
                cor_texto = TEXTO_ATRASADO
            elif dias <= 2:
                cor_fundo = VERMELHO_FUNDO
                cor_texto = VERMELHO_TEXTO
            elif dias <= 6:
                cor_fundo = AMARELO_FUNDO
                cor_texto = AMARELO_TEXTO
            else:
                cor_fundo = AZUL_CLARO_FUNDO
                cor_texto = AZUL_CLARO_TEXTO

            self._cartao_os(
                conteudo,
                linha,
                cor_fundo,
                cor_texto,
                tipo="prazo",
            )

        self._iniciar_rolagem(canvas)

    def _aviso_materiais(self, pai, fundo, texto):
        aviso = tk.Frame(
            pai,
            bg=fundo,
            highlightbackground=texto,
            highlightthickness=1,
            padx=12,
            pady=10,
        )
        aviso.pack(
            fill="x",
            pady=(0, 12),
        )

        tk.Label(
            aviso,
            text=("⚠ VERIFICAR A NECESSIDADE DE " "ISOLAMENTOS, MÁSCARAS E TINTAS"),
            bg=fundo,
            fg=texto,
            font=("Segoe UI", 13, "bold"),
            wraplength=1050,
            justify="left",
        ).pack(anchor="w")


# ============================================================
# FIM DA INTERFACE
# ============================================================
