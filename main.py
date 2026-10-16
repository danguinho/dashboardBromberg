
# MAIN.PY - Inicialização e navegação do Dashboard Bromberg

import os
import tkinter as tk
import threading
import queue
import traceback

from tkinter import filedialog, messagebox
from PIL import Image, ImageTk


# ============================================================
# CONFIGURAÇÕES
# ============================================================

PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))
CAMINHO_LOGO = os.path.join(
    PASTA_PROJETO,
    "imagens",
    "imagem.png"
)

# Identidade visual Bromberg
AZUL = "#303394"
ROXO = "#25266F"
CIANO = "#2CB5F5"
BRANCO = "#FFFFFF"
CINZA = "#F1F5F9"
CINZA_TEXTO = "#4B5563"
VERMELHO = "#DC2626"


# ============================================================
# APLICAÇÃO PRINCIPAL
# ============================================================

class Aplicacao:

    def __init__(self, root):
        self.root = root

        self.caminho_carteira = ""
        self.caminho_processos = ""

        self.logo = None
        self.carregando = False
        self.dashboard = None

        self.root.title("Dashboard Bromberg")
        self.root.geometry("850x560")
        self.root.minsize(750, 500)
        self.root.configure(bg=CINZA)
        self.root.protocol("WM_DELETE_WINDOW", self.fechar)

        self.centralizar()
        self.mostrar_abertura()

        self.root.after(1600, self.mostrar_selecao)

    # --------------------------------------------------------
    # JANELA
    # --------------------------------------------------------

    def centralizar(self):
        self.root.update_idletasks()

        largura = 850
        altura = 560

        x = (
            self.root.winfo_screenwidth() - largura
        ) // 2

        y = (
            self.root.winfo_screenheight() - altura
        ) // 2

        self.root.geometry(
            f"{largura}x{altura}+{x}+{y}"
        )

    def limpar_janela(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def fechar(self):
        self.root.destroy()

    # --------------------------------------------------------
    # LOGO
    # --------------------------------------------------------

    def carregar_logo(self):
        if not os.path.isfile(CAMINHO_LOGO):
            print(
                f"Logo não encontrado: {CAMINHO_LOGO}"
            )
            return None

        try:
            with Image.open(CAMINHO_LOGO) as imagem:
                imagem = imagem.convert("RGBA")
                imagem.thumbnail((180, 180))

                logo = ImageTk.PhotoImage(imagem)

            return logo

        except Exception as erro:
            print(
                f"Erro ao carregar logo: {erro}"
            )
            return None

    # --------------------------------------------------------
    # TELA DE ABERTURA
    # --------------------------------------------------------

    def mostrar_abertura(self):
        self.limpar_janela()
        self.root.configure(bg=ROXO)

        painel = tk.Frame(
            self.root,
            bg=ROXO
        )
        painel.pack(
            fill="both",
            expand=True
        )

        tk.Label(
            painel,
            text="BROMBERG",
            font=("Arial", 30, "bold"),
            fg=CIANO,
            bg=ROXO
        ).pack(pady=(70, 18))

        self.logo = self.carregar_logo()

        if self.logo:
            tk.Label(
                painel,
                image=self.logo,
                bg=ROXO
            ).pack(pady=10)

        else:
            tk.Label(
                painel,
                text="DASHBOARD OPERACIONAL",
                font=("Arial", 17, "bold"),
                fg=BRANCO,
                bg=ROXO
            ).pack(pady=25)

        tk.Label(
            painel,
            text="Inicializando o sistema...",
            font=("Arial", 12),
            fg=BRANCO,
            bg=ROXO
        ).pack(pady=15)

        tk.Label(
            painel,
            text="Desenvolvido por Daniel Moure",
            font=("Arial", 9),
            fg="#DDDDDD",
            bg=ROXO
        ).pack(
            side="bottom",
            pady=15
        )

    # --------------------------------------------------------
    # SELEÇÃO DAS PLANILHAS
    # --------------------------------------------------------

    def mostrar_selecao(self):
        if not self.root.winfo_exists():
            return

        self.limpar_janela()
        self.root.configure(bg=CINZA)

        cabecalho = tk.Frame(
            self.root,
            bg=ROXO,
            height=80
        )
        cabecalho.pack(fill="x")
        cabecalho.pack_propagate(False)

        tk.Label(
            cabecalho,
            text="DASHBOARD BROMBERG",
            font=("Arial", 23, "bold"),
            fg=BRANCO,
            bg=ROXO
        ).pack(
            side="left",
            padx=25,
            pady=18
        )

        conteudo = tk.Frame(
            self.root,
            bg=CINZA
        )
        conteudo.pack(
            fill="both",
            expand=True,
            padx=32,
            pady=20
        )

        tk.Label(
            conteudo,
            text="Selecione as planilhas",
            font=("Arial", 20, "bold"),
            fg=ROXO,
            bg=CINZA
        ).pack(
            anchor="w",
            pady=(0, 4)
        )

        tk.Label(
            conteudo,
            text=(
                "Escolha a Carteira e o "
                "Controle de Processos."
            ),
            font=("Arial", 10),
            fg=CINZA_TEXTO,
            bg=CINZA
        ).pack(
            anchor="w",
            pady=(0, 12)
        )

        self.criar_seletor(
            conteudo,
            "1. CARTEIRA",
            "Planilha de carteira de ordens de serviço.",
            "carteira"
        )

        self.criar_seletor(
            conteudo,
            "2. CONTROLE DE PROCESSOS",
            "Planilha com jateamento, pintura e liberações.",
            "processos"
        )

        self.status = tk.Label(
            conteudo,
            text="Selecione os dois arquivos para continuar.",
            font=("Arial", 10),
            fg=CINZA_TEXTO,
            bg=CINZA,
            anchor="w",
            justify="left",
            wraplength=760
        )
        self.status.pack(
            fill="x",
            pady=(8, 8)
        )

        botoes = tk.Frame(
            conteudo,
            bg=CINZA
        )
        botoes.pack(
            fill="x",
            pady=5
        )

        self.botao_carregar = tk.Button(
            botoes,
            text="CARREGAR DASHBOARD",
            command=self.carregar_dashboard,
            font=("Arial", 11, "bold"),
            bg=CIANO,
            fg=BRANCO,
            activebackground=AZUL,
            activeforeground=BRANCO,
            relief="flat",
            padx=20,
            pady=11,
            width=22,
            cursor="hand2"
        )
        self.botao_carregar.pack(side="left")

        tk.Button(
            botoes,
            text="Limpar seleção",
            command=self.limpar_selecao,
            font=("Arial", 10),
            bg="#DDDDDD",
            fg="#222222",
            relief="flat",
            padx=15,
            pady=11,
            cursor="hand2"
        ).pack(
            side="left",
            padx=(10, 0)
        )

        tk.Label(
            self.root,
            text="Desenvolvido por Daniel Moure",
            font=("Arial", 9),
            fg=CINZA_TEXTO,
            bg=CINZA
        ).pack(
            side="bottom",
            pady=9
        )

        self.atualizar_caminhos()

    def criar_seletor(
        self,
        pai,
        titulo,
        descricao,
        atributo
    ):
        caixa = tk.Frame(
            pai,
            bg=BRANCO,
            highlightbackground="#D0D0D0",
            highlightthickness=1
        )
        caixa.pack(
            fill="x",
            pady=6
        )

        interior = tk.Frame(
            caixa,
            bg=BRANCO
        )
        interior.pack(
            fill="x",
            padx=13,
            pady=9
        )

        tk.Label(
            interior,
            text=titulo,
            font=("Arial", 11, "bold"),
            fg=ROXO,
            bg=BRANCO
        ).pack(anchor="w")

        tk.Label(
            interior,
            text=descricao,
            font=("Arial", 9),
            fg=CINZA_TEXTO,
            bg=BRANCO
        ).pack(
            anchor="w",
            pady=(2, 7)
        )

        linha = tk.Frame(
            interior,
            bg=BRANCO
        )
        linha.pack(fill="x")

        campo = tk.Entry(
            linha,
            font=("Arial", 9),
            relief="solid",
            bd=1,
            state="readonly",
            readonlybackground="#FAFAFA"
        )
        campo.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=6
        )

        tk.Button(
            linha,
            text="Procurar arquivo...",
            command=lambda: self.selecionar_arquivo(
                atributo
            ),
            font=("Arial", 9, "bold"),
            bg=AZUL,
            fg=BRANCO,
            activebackground=ROXO,
            activeforeground=BRANCO,
            relief="flat",
            padx=12,
            pady=7,
            cursor="hand2"
        ).pack(
            side="left",
            padx=(9, 0)
        )

        if atributo == "carteira":
            self.campo_carteira = campo
        else:
            self.campo_processos = campo

    def selecionar_arquivo(self, tipo):
        if tipo == "carteira":
            atual = self.caminho_carteira
            titulo = "Selecione a planilha da CARTEIRA"
        else:
            atual = self.caminho_processos
            titulo = "Selecione o CONTROLE DE PROCESSOS"

        opcoes = {
            "parent": self.root,
            "title": titulo,
            "filetypes": [
                (
                    "Planilhas Excel",
                    "*.xlsm *.xlsx *.xlsb *.xls"
                ),
                ("Todos os arquivos", "*.*")
            ]
        }

        if atual and os.path.isfile(atual):
            opcoes["initialdir"] = os.path.dirname(
                atual
            )

        caminho = filedialog.askopenfilename(
            **opcoes
        )

        if not caminho:
            return

        if tipo == "carteira":
            self.caminho_carteira = caminho
        else:
            self.caminho_processos = caminho

        print(f"Arquivo selecionado: {caminho}")

        self.atualizar_caminhos()

    def atualizar_campo(self, campo, caminho):
        campo.config(state="normal")
        campo.delete(0, tk.END)

        if caminho:
            campo.insert(0, caminho)

        campo.config(state="readonly")

    def atualizar_caminhos(self):
        self.atualizar_campo(
            self.campo_carteira,
            self.caminho_carteira
        )

        self.atualizar_campo(
            self.campo_processos,
            self.caminho_processos
        )

        if (
            self.caminho_carteira
            and self.caminho_processos
        ):
            self.status.config(
                text=(
                    "Os dois arquivos foram selecionados. "
                    "Clique em CARREGAR DASHBOARD."
                ),
                fg=AZUL
            )

        elif self.caminho_carteira:
            self.status.config(
                text=(
                    "Carteira selecionada. Agora escolha "
                    "o Controle de Processos."
                ),
                fg=CINZA_TEXTO
            )

        elif self.caminho_processos:
            self.status.config(
                text=(
                    "Controle selecionado. Agora escolha "
                    "a Carteira."
                ),
                fg=CINZA_TEXTO
            )

        else:
            self.status.config(
                text="Selecione os dois arquivos para continuar.",
                fg=CINZA_TEXTO
            )

    def limpar_selecao(self):
        if self.carregando:
            return

        self.caminho_carteira = ""
        self.caminho_processos = ""

        self.atualizar_caminhos()

    # --------------------------------------------------------
    # CARREGAMENTO DAS PLANILHAS
    # --------------------------------------------------------

    def carregar_dashboard(self):
        if self.carregando:
            return

        if (
            not self.caminho_carteira
            or not self.caminho_processos
        ):
            messagebox.showwarning(
                "Arquivos pendentes",
                (
                    "Selecione a Carteira e "
                    "o Controle de Processos."
                ),
                parent=self.root
            )
            return

        arquivos = [
            ("Carteira", self.caminho_carteira),
            (
                "Controle de Processos",
                self.caminho_processos
            )
        ]

        for nome, caminho in arquivos:
            if not os.path.isfile(caminho):
                messagebox.showerror(
                    "Arquivo não encontrado",
                    (
                        f"O arquivo de {nome} não existe:\n"
                        f"{caminho}"
                    ),
                    parent=self.root
                )
                return

        self.carregando = True

        self.botao_carregar.config(
            state="disabled",
            text="CARREGANDO..."
        )

        self.status.config(
            text="Preparando para ler as planilhas...",
            fg=ROXO
        )

        self.root.update_idletasks()

        try:
            from interface import TelaLoad

            tela_load = TelaLoad(self.root)

            tela_load.atualizar_status(
                "Iniciando leitura das planilhas..."
            )

        except Exception as erro:
            self.carregando = False

            self.botao_carregar.config(
                state="normal",
                text="CARREGAR DASHBOARD"
            )

            messagebox.showerror(
                "Erro na interface de carregamento",
                str(erro),
                parent=self.root
            )
            return

        resultados = queue.Queue()

        caminho_carteira = self.caminho_carteira
        caminho_processos = self.caminho_processos

        def processar_planilhas():
            try:
                print("ETAPA 1: importando módulos...")

                from dados import carregar_dados
                from filtros import preparar_dados_dashboard

                print("ETAPA 2: lendo os arquivos Excel...")

                carteira, processos = carregar_dados(
                    caminho_carteira,
                    caminho_processos
                )

                print("ETAPA 3: arquivos lidos.")
                print(
                    "Linhas da carteira:",
                    len(carteira)
                )
                print(
                    "Linhas dos processos:",
                    len(processos)
                )

                print(
                    "ETAPA 4: preparando e cruzando os dados..."
                )

                dados = preparar_dados_dashboard(
                    carteira,
                    processos
                )

                print(
                    "ETAPA 5: dados preparados:",
                    len(dados)
                )

                resultados.put(
                    (
                        "sucesso",
                        {
                            "carteira": carteira,
                            "processos": processos,
                            "dados": dados
                        }
                    )
                )

            except Exception as erro:
                traceback.print_exc()

                resultados.put(
                    (
                        "erro",
                        (
                            f"{type(erro).__name__}: "
                            f"{erro}"
                        )
                    )
                )

        def verificar_resultado():
            if not self.root.winfo_exists():
                return

            try:
                tipo, resultado = resultados.get_nowait()

            except queue.Empty:
                self.root.after(
                    150,
                    verificar_resultado
                )
                return

            try:
                tela_load.fechar()
            except Exception:
                pass

            if tipo == "erro":
                self.carregando = False

                self.botao_carregar.config(
                    state="normal",
                    text="CARREGAR DASHBOARD"
                )

                self.status.config(
                    text=(
                        "Falha ao carregar as planilhas. "
                        "Consulte a mensagem de erro."
                    ),
                    fg=VERMELHO
                )

                messagebox.showerror(
                    "Falha ao carregar",
                    (
                        "Não foi possível carregar "
                        "o Dashboard.\n\n"
                        f"{resultado}"
                    ),
                    parent=self.root
                )
                return

            try:
                from interface import Dashboard

                self.limpar_janela()
                self.root.configure(bg=BRANCO)

                # Mantém os dados completos disponíveis
                # para as duas áreas do dashboard.
                self.dashboard = Dashboard(
                    self.root,
                    resultado["dados"],
                    caminho_carteira,
                    caminho_processos
                )

                # Os dados completos ficam disponíveis
                # na aplicação para a integração posterior.
                self.carteira = resultado["carteira"]
                self.processos = resultado["processos"]
                self.dados_dashboard = resultado["dados"]

            except Exception as erro:
                traceback.print_exc()

                self.carregando = False

                messagebox.showerror(
                    "Erro ao abrir a interface",
                    (
                        "Os dados foram carregados, mas "
                        "a interface não pôde ser aberta.\n\n"
                        f"{type(erro).__name__}: {erro}"
                    ),
                    parent=self.root
                )

                if self.root.winfo_exists():
                    self.mostrar_selecao()

        threading.Thread(
            target=processar_planilhas,
            daemon=True
        ).start()

        self.root.after(
            150,
            verificar_resultado
        )


# ============================================================
# INICIALIZAÇÃO
# ============================================================

def main():
    print("=" * 60)
    print("DASHBOARD BROMBERG")
    print("Iniciando...")
    print("=" * 60)

    root = tk.Tk()

    Aplicacao(root)

    root.mainloop()


if __name__ == "__main__":
    main()
