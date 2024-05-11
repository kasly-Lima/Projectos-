import random
import time
import ipywidgets as widgets
from IPython.display import display, HTML

class Cores:
    DISPONIVEIS = {
        'vermelho': 'red',
        'verde': 'green',
        'amarelo': 'yellow',
        'azul': 'blue',
        'magenta': 'magenta',
        'ciano': 'cyan',
    }

class Numeros:
    def __init__(self, maximo=75):
        self.maximo = maximo
        self.sorteados = []

    def sortear(self):
        if len(self.sorteados) < self.maximo:
            while True:
                numero = random.randint(1, self.maximo)
                if numero not in self.sorteados:
                    self.sorteados.append(numero)
                    return numero
        else:
            return None

class Cartela:
    def __init__(self, nome_jogador, cor_marcacao):
        self.nome_jogador = nome_jogador[0].upper() + nome_jogador[1:].lower()
        self.cor_marcacao = cor_marcacao
        self.cartela = [[None for _ in range(5)] for _ in range(5)]
        self.marcadas = [[False for _ in range(5)] for _ in range(5)]
        self.popular_cartela()

    def popular_cartela(self):
        numeros = list(range(1, 76))
        random.shuffle(numeros)
        for i in range(5):
            for j in range(5):
                self.cartela[i][j] = numeros.pop()

    def marcar_numero(self, numero):
        for i in range(5):
            for j in range(5):
                if self.cartela[i][j] == numero:
                    self.marcadas[i][j] = True
                    return True
        return False

    def checar_vitoria(self):
        return any(all(row) for row in self.marcadas) or \
               any(all(self.marcadas[row][col] for row in range(5)) for col in range(5)) or \
               all(self.marcadas[i][i] for i in range(5)) or \
               all(self.marcadas[i][4-i] for i in range(5)) or \
               all(all(row) for row in self.marcadas)

    def exibir(self):
        cartela_html = f"<h2>Cartela de {self.nome_jogador}</h2>"
        cartela_html += "<table>"
        for i in range(5):
            cartela_html += "<tr>"
            for j in range(5):
                numero = self.cartela[i][j]
                if self.marcadas[i][j]:
                    cartela_html += f"<td style='background-color: {self.cor_marcacao}; color: white;'>{numero}</td>"
                else:
                    cartela_html += f"<td>{numero}</td>"
            cartela_html += "</tr>"
        cartela_html += "</table>"
        display(HTML(cartela_html))

class Bingo:
    def __init__(self, intervalo_max=75, velocidade=1):
        self.numeros = Numeros(intervalo_max)
        self.cartelas = []
        self.velocidade = velocidade

    def adicionar_cartela(self, nome_jogador, cor):
        self.cartelas.append(Cartela(nome_jogador, cor))

    def jogar(self, max_rodadas=None):
        rodada_atual = 0

        while True:
            if max_rodadas is not None and rodada_atual >= max_rodadas:
                print("O jogo terminou sem vencedores.")
                break

            num = self.numeros.sortear()
            if num is None:
                print("Todos os números foram sorteados. Jogo encerrado.")
                break
            print(f"Número sorteado: {num}")
            vencedor = False
            for cartela in self.cartelas:
                cartela.marcar_numero(num)
                cartela.exibir()
                if cartela.checar_vitoria():
                    print(f"{cartela.nome_jogador} venceu o jogo!")
                    vencedor = True
                    break
            if vencedor:
                break
            rodada_atual += 1
            time.sleep(self.velocidade)

# Função para iniciar o jogo de Bingo
def iniciar_bingo(quantidade_cartelas, nomes_jogadores, cores):
    bingo = Bingo(75)

    for i in range(quantidade_cartelas):
        bingo.adicionar_cartela(nomes_jogadores[i], cores[i])

    bingo.jogar()

# Interface interativa para iniciar o jogo
quantidade_cartelas = widgets.IntSlider(value=1, min=1, max=5, description='Quantidade de Cartelas:')
nomes_jogadores = [widgets.Text(description=f"Nome do Jogador {i+1}:") for i in range(5)]
cores = [widgets.Dropdown(options=Cores.DISPONIVEIS.keys(), value='vermelho', description=f"Cor do Jogador {i+1}:") for i in range(5)]

botao_iniciar = widgets.Button(description="Iniciar Jogo")

def iniciar_jogo(b):
    nomes = [nome.value for nome in nomes_jogadores[:quantidade_cartelas.value]]
    cores_jogadores = [Cores.DISPONIVEIS[cor.value] for cor in cores[:quantidade_cartelas.value]]
    iniciar_bingo(quantidade_cartelas.value, nomes, cores_jogadores)

botao_iniciar.on_click(iniciar_jogo)

display(quantidade_cartelas)
for nome in nomes_jogadores:
    display(nome)
for cor in cores:
    display(cor)
display(botao_iniciar)
