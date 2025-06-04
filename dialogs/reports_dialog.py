import sys
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QScrollArea, QWidget
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class ReportsHelpDialog(QDialog):
    """
    Janela de ajuda que explica os cálculos financeiros de forma didática e textual.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ajuda - Relatório Financeiro")
        self.setGeometry(300, 200, 700, 850)  
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()

        # Criando um widget para rolagem sem scroll horizontal
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Título
        titleLabel = QLabel("📊 Explicação dos Indicadores Financeiros")
        titleLabel.setFont(QFont("Arial", 18, QFont.Bold))
        titleLabel.setAlignment(Qt.AlignCenter)
        scroll_layout.addWidget(titleLabel)

        # Indicadores financeiros com fórmulas e explicações didáticas
        indicators = {
            "📍Receita Total": (
                "Soma de todas as receitas no mês",
                "Representa todo o dinheiro recebido em um determinado período. Inclui salários, vendas, rendimentos de investimentos, entre outros."
            ),
            "📍Despesa Total": (
                "Soma de todas as despesas no mês",
                "Total de dinheiro gasto em um determinado período, incluindo contas, impostos, compras e investimentos."
            ),
            "📍Inflação (%)": (
                "((Despesa Atual - Despesa Anterior) / Despesa Anterior) × 100",
                "Mostra o aumento percentual das despesas em relação ao mês anterior. Se for positiva, as despesas aumentaram; se for negativa, as despesas diminuíram."
            ),
            "📍Saldo Disponível": (
                "Receita Total - Despesa Total",
                "Valor restante após todas as despesas serem pagas. Indica o dinheiro livre para uso no mês."
            ),
            "📍Sobra do Mês Anterior": (
                "Fluxo de Caixa Líquido do mês anterior",
                "Mostra o saldo que restou do mês anterior e que pode ser utilizado no mês atual."
            ),
            "📍Fluxo de Caixa Livre": (
                "Saldo Disponível + Sobra do Mês Anterior",
                "Dinheiro disponível para investimentos ou outros usos depois de cobrir todas as despesas."
            ),
            "📍Aplicação Total": (
                "Total investido no mês",
                "Valor que foi destinado a investimentos durante o mês, como ações, renda fixa ou outros ativos."
            ),
            "📍Fluxo de Caixa Líquido": (
                "Fluxo de Caixa Livre - Aplicação Total",
                "Valor restante após realizar investimentos, mostrando quanto dinheiro ainda está disponível."
            ),
            "📍Saldo Total Investimentos": (
                "Acumulado de todos os investimentos ao longo do tempo",
                "Soma de todos os investimentos realizados até o momento."
            ),
            "📍Renda dos Investimentos": (
                "Rendimento gerado pelos investimentos",
                "Mostra quanto de lucro foi obtido a partir dos investimentos no período analisado."
            ),
            "📍Grau de Independência (%)": (
                "(Renda dos Investimentos / Despesa Total) × 100",
                "Mede o quanto dos seus gastos pode ser coberto apenas pelos rendimentos dos investimentos."
            ),
            "📍Rentabilidade Média Investimentos (%)": (
                "(Renda dos Investimentos / Saldo Total Investimentos) × 100",
                "Média percentual de quanto os investimentos estão rendendo em relação ao total investido."
            ),
            "📍Taxa de Poupança (%)": (
                "((Receita Total - Despesa Total) / Receita Total) × 100",
                "Mostra o percentual da renda que não foi gasta. Uma taxa de poupança alta indica maior capacidade de economia."
            ),
            "📍Taxa de Investimento (%)": (
                "(Aplicação Total / Receita Total) × 100",
                "Indica a porcentagem da receita mensal que foi investida."
            ),
            "📍Margem de Segurança (%)": (
                "((Receita Total - Despesa Total) / Despesa Total) × 100",
                "Mostra a diferença entre receita e despesas. Se positiva, indica um excedente. Se negativa, indica que os gastos estão acima da receita."
            ),
            "📍Índice de Liquidez": (
                "(Saldo Disponível + Sobra do Mês Anterior) / Despesa Total",
                "Mede a capacidade de cobrir despesas inesperadas. Um índice abaixo de 1 indica risco financeiro."
            ),
            "📍Crescimento Patrimonial (%)": (
                "((Saldo Total Investimentos no Mês - Saldo Total Investimentos Mês Anterior) / Saldo Total Investimentos Mês Anterior) × 100",
                "Mostra a evolução do patrimônio investido ao longo do tempo."
            ),
        }

        # Adiciona os títulos, explicações e as fórmulas formatadas
        for title, (formula, explanation) in indicators.items():
            section_title = QLabel(f"<h3>{title}</h3>")
            section_title.setFont(QFont("Arial", 13, QFont.Bold))
            scroll_layout.addWidget(section_title)

            formula_label = QLabel(f"<p><b>Fórmula:</b> {formula}</p>")
            formula_label.setFont(QFont("Arial", 12, QFont.Bold))
            formula_label.setWordWrap(True)
            scroll_layout.addWidget(formula_label)

            explanation_label = QLabel(f"<p>{explanation}</p>")
            explanation_label.setFont(QFont("Arial", 12))
            explanation_label.setWordWrap(True)
            scroll_layout.addWidget(explanation_label)

        # Botão para fechar
        closeButton = QPushButton("Fechar")
        closeButton.clicked.connect(self.close)
        scroll_layout.addWidget(closeButton, alignment=Qt.AlignCenter)

        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)

        layout.addWidget(scroll_area)
        self.setLayout(layout)


if __name__ == "__main__":
    app = sys.argv
    dialog = ReportsHelpDialog()
    dialog.show()
    sys.exit(app.exec_())
