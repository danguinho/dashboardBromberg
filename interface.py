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

        tk.Label(
            pai,
            text=f"{quantidade} OS",
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
    # CARTEIRA E PRAZOS
    # ========================================================

    def mostrar_carteira(self):
        self._parar_alternancia()
        self.area_atual = "carteira"
        self._limpar_corpo()

        self.titulo_cabecalho.config(text="CARTEIRA DE PEDIDOS")
        self._barra_interna("Prazos e prioridades")

        try:
            registros = dados_prazos(self.dados)
        except Exception as erro:
            self._vazio(f"Não foi possível preparar os prazos:\n{erro}")
            return

        self._titulo("Carteira e prazos", len(registros))
        if registros.empty:
            self._vazio("Nenhuma OS foi encontrada na janela de prazos.")
            return

        colunas = {
            "OS": 125,
            "Cliente": 220,
            "Prazo": 115,
            "Dias": 70,
            "Alerta": 190,
            "Isolamento": 140,
            "Máscara": 140,
            "Tintas": 140,
        }
        tabela = self._tabela(self.corpo, colunas)
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
                "",
                "end",
                values=(
                    self._texto(linha.get("OS")),
                    self._texto(linha.get("Cliente")),
                    self._texto(linha.get("Prazo")),
                    dias,
                    texto_prazo(dias),
                    self._texto(linha.get("Isolamento")),
                    self._texto(linha.get("Máscara")),
                    self._texto(linha.get("Solicitação - Tinta")),
                ),
                tags=(tag,),
            )

        # Duplo clique nas células de status abre uma setinha na própria célula.
        tabela.bind(
            "<Double-1>",
            lambda evento: self._editar_status_na_celula(evento, tabela),
        )

        tk.Label(
            self.corpo,
            text=(
                "Para alterar, dê dois cliques em uma célula de Isolamento, "
                "Máscara ou Tintas e escolha o status na setinha. "
                "A alteração será salva na planilha Excel."
            ),
            bg=CINZA,
            fg=CINZA_ESCURO,
            font=("Segoe UI", 10),
            wraplength=1000,
            justify="left",
        ).pack(anchor="w", pady=(8, 0))

    def _editar_status_na_celula(self, evento, tabela):
        """Mostra um Combobox na célula de status e grava a escolha no Excel."""
        item_id = tabela.identify_row(evento.y)
        coluna_id = tabela.identify_column(evento.x)
        if not item_id or coluna_id not in ("#6", "#7", "#8"):
            return

        bbox = tabela.bbox(item_id, coluna_id)
        if not bbox:
            return
        x, y, largura, altura = bbox
        valores = list(tabela.item(item_id, "values"))
        if len(valores) < 8:
            return

        indice = int(coluna_id[1:]) - 1
        os_numero = str(valores[0]).strip()
        nome_campo = {5: "Isolamento", 6: "Máscara", 7: "Tintas"}[indice]
        opcoes = [
            "Não Solicitado",
            "Solicitado",
            "Peça Sem Máscara",
            "Peça Sem Isolamento",
            "Peça Sem Pintura",
            "Não se aplica",
        ]
        atual = str(valores[indice] or "Não Solicitado").strip()
        if atual and atual not in opcoes:
            opcoes.insert(0, atual)

        combo = ttk.Combobox(tabela, values=opcoes, state="readonly", font=("Segoe UI", 10))
        combo.place(x=x, y=y, width=largura, height=altura)
        combo.set(atual or "Não Solicitado")
        combo.focus_set()
        combo.event_generate("<Button-1>")

        finalizado = {"valor": False}

        def concluir(_evento=None):
            if finalizado["valor"]:
                return
            novo_status = combo.get().strip()
            if not novo_status:
                combo.destroy()
                return
            if novo_status == atual:
                combo.destroy()
                return
            finalizado["valor"] = True
            combo.configure(state="disabled")
            try:
                self._salvar_status_excel(os_numero, {nome_campo: novo_status})
            except Exception as erro:
                combo.destroy()
                messagebox.showerror(
                    "Erro ao salvar status",
                    f"Não foi possível atualizar o status da OS {os_numero} na planilha.\n\n{erro}",
                    parent=self.root,
                )
                return

            valores[indice] = novo_status
            tabela.item(item_id, values=valores)
            combo.destroy()
            self.atualizar_status(f"OS {os_numero}: {nome_campo} atualizado para '{novo_status}'.")

        combo.bind("<<ComboboxSelected>>", concluir)
        combo.bind("<Escape>", lambda _e: combo.destroy())
        combo.bind("<FocusOut>", lambda _e: combo.after(150, combo.destroy))

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

        opcoes = [
            "Não Solicitado",
            "Solicitado",
            "Peça Sem Máscara",
            "Peça Sem Isolamento",
            "Peça Sem Pintura",
            "Não se aplica",
        ]
        campos = [
            ("Isolamento", 5),
            ("Máscara", 6),
            ("Tintas", 7),
        ]
        variaveis = {}
        for linha_idx, (nome, indice) in enumerate(campos, start=1):
            tk.Label(janela, text=nome, bg=CINZA, fg=ROXO, font=("Segoe UI", 11, "bold")).grid(
                row=linha_idx, column=0, padx=(22, 12), pady=7, sticky="w"
            )
            atual = str(valores[indice] or "Não Solicitado").strip()
            lista = list(opcoes)
            if atual and atual not in lista:
                lista.insert(0, atual)
            var = tk.StringVar(value=atual or "Não Solicitado")
            combo = ttk.Combobox(janela, textvariable=var, values=lista, state="readonly", width=27)
            combo.grid(row=linha_idx, column=1, padx=(0, 22), pady=7, sticky="ew")
            variaveis[nome] = var

        def salvar():
            novos = {nome: var.get().strip() for nome, var in variaveis.items()}
            try:
                self._salvar_status_excel(os_numero, novos)
            except Exception as erro:
                messagebox.showerror("Erro ao salvar", f"Não foi possível salvar no Excel.\n\n{erro}", parent=janela)
                return

            valores[5] = novos["Isolamento"]
            valores[6] = novos["Máscara"]
            valores[7] = novos["Tintas"]
            tabela.item(item_id, values=valores)
            messagebox.showinfo("Status atualizado", f"Os status da OS {os_numero} foram atualizados.", parent=janela)
            janela.destroy()

        botoes = tk.Frame(janela, bg=CINZA)
        botoes.grid(row=4, column=0, columnspan=2, padx=22, pady=(16, 20), sticky="e")
        self._botao(botoes, "Cancelar", janela.destroy, fundo="#D1D5DB", cor=ROXO).pack(side="right", padx=(8, 0))
        self._botao(botoes, "Salvar alterações", salvar, fundo=CIANO, cor=ROXO).pack(side="right")
        janela.bind("<Escape>", lambda _event: janela.destroy())

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
            try:
                excel = win32.GetActiveObject("Excel.Application")
            except Exception:
                excel = win32.DispatchEx("Excel.Application")
                abriu_excel = True
            excel.Visible = True
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

    def _parar_alternancia(self):
        if self._id_troca is not None:
            try:
                self.root.after_cancel(self._id_troca)
            except tk.TclError:
                pass

        self._id_troca = None

    def _agendar_troca(self):
        self._parar_alternancia()

        if self.area_atual == "processos" and self.automatica_ativa:
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

        self._criar_controles_processos()

        painel = tk.Frame(
            self.corpo,
            bg=tela["fundo"],
            padx=18,
            pady=15,
        )
        painel.pack(
            fill="both",
            expand=True,
        )

        self._titulo(
            tela["nome"],
            self._quantidade_tela(tela["funcao"]),
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
        barra = tk.Frame(
            self.corpo,
            bg=CINZA,
        )
        barra.pack(
            fill="x",
            pady=(0, 10),
        )

        self._botao(
            barra,
            "⌂ Menu inicial",
            self.mostrar_inicio,
            fundo=ROXO,
        ).pack(side="left")

        self._botao(
            barra,
            "◀ Anterior",
            self.anterior,
            fundo=AZUL,
        ).pack(
            side="left",
            padx=(10, 0),
        )

        self.botao_pausa = self._botao(
            barra,
            ("⏸ Pausar" if self.automatica_ativa else "▶ Retomar"),
            self.alternar_pausa,
            fundo=CIANO,
            cor=ROXO,
        )
        self.botao_pausa.pack(
            side="left",
            padx=10,
        )

        self._botao(
            barra,
            "Próxima ▶",
            self.proximo,
            fundo=AZUL,
        ).pack(side="left")

        self.botao_rolagem = self._botao(
            barra,
            "⏸ Pausar rolagem",
            self.alternar_rolagem,
            fundo=CIANO,
            cor=ROXO,
        )
        self.botao_rolagem.pack(
            side="left",
            padx=(10, 0),
        )

        self.indicador_tela = tk.Label(
            barra,
            text="",
            bg=CINZA,
            fg=ROXO,
            font=("Segoe UI", 10, "bold"),
        )
        self.indicador_tela.pack(
            side="right",
            padx=10,
        )

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
                        canvas.yview_moveto(
                            min(
                                atual + PASSO_ROLAGEM,
                                1.0,
                            )
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
        if registros is None or registros.empty:
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
            mensagem_vazia=("Nenhuma peça ficou pronta nos últimos 3 dias."),
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
