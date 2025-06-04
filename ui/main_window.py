import logging

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QStackedWidget, QSplitter, QListWidget, QTableWidgetItem
)
from PyQt5.QtCore import Qt

# Importa as views separadas
from ui.views.dashboard_view import DashboardView
from ui.views.transactions_view import TransactionsView
from ui.views.investments_view import InvestmentsView
from ui.views.reports_view import ReportsView
from ui.views.settings_view import SettingsView

from finance.database import FINANCE_DB

logging.basicConfig(level=logging.INFO)

# Constantes para os rótulos da sidebar
UI_LABEL_DASHBOARD    = "📊 Dashboard"
UI_LABEL_INCOME       = "💰 Receitas"
UI_LABEL_EXPENSE      = "💸 Despesas"
UI_LABEL_INVESTMENTS  = "📈 Investimentos"
UI_LABEL_REPORTS      = "📑 Relatórios"
UI_LABEL_SETTINGS     = "⚙️ Configurações"

class FinancePanel(QWidget):
    """
    Janela principal da aplicação financeira.
    Contém uma sidebar para navegação e um painel com as views em um QStackedWidget.
    """
    def __init__(self, ui_label):
        super().__init__()
        self.ui_label = ui_label
        self.currentView = UI_LABEL_DASHBOARD
        self.initUI()
        self.loadData(self.currentView)

    def initUI(self):
        self.setWindowTitle(self.ui_label)
        self.setGeometry(100, 100, 1400, 700)

        # Cria um splitter horizontal para a sidebar e o painel principal
        splitter = QSplitter(Qt.Horizontal)

        # Sidebar de navegação
        self.sideBar = QListWidget()
        self.sideBar.setFixedWidth(220)
        items = [
            UI_LABEL_DASHBOARD,
            UI_LABEL_INCOME,
            UI_LABEL_EXPENSE,
            UI_LABEL_INVESTMENTS,
            UI_LABEL_REPORTS,
            UI_LABEL_SETTINGS
        ]
        for item in items:
            self.sideBar.addItem(item)
        self.sideBar.itemClicked.connect(self.changeView)
        splitter.addWidget(self.sideBar)

        # Painel principal: cada view é uma página do QStackedWidget
        self.mainPanel = QStackedWidget()

        # Cria instâncias das views
        self.dashboardView = DashboardView()                                            # Dashboard (ex.: resumo financeiro)
        self.transactionsIncomeView = TransactionsView("Receitas", UI_LABEL_INCOME)     # View para receitas
        self.transactionsExpenseView = TransactionsView("Despesas", UI_LABEL_EXPENSE)   # View para despesas
        self.investmentsView = InvestmentsView(UI_LABEL_INVESTMENTS)                    # View para investimentos
        self.reportsView = ReportsView(UI_LABEL_REPORTS)                                # View para relatórios
        self.settingsView = SettingsView(UI_LABEL_SETTINGS)                             # View para configurações

        # Adiciona as views ao painel principal (a ordem deve corresponder à sidebar)
        self.mainPanel.addWidget(self.dashboardView)            # índice 0
        self.mainPanel.addWidget(self.transactionsIncomeView)   # índice 1
        self.mainPanel.addWidget(self.transactionsExpenseView)  # índice 2
        self.mainPanel.addWidget(self.investmentsView)          # índice 3
        self.mainPanel.addWidget(self.reportsView)              # índice 4
        self.mainPanel.addWidget(self.settingsView)             # índice 5

        splitter.addWidget(self.mainPanel)
        splitter.setStretchFactor(1, 1)

        # Layout principal da janela
        layout = QHBoxLayout(self)
        layout.addWidget(splitter)
        self.setLayout(layout)

    def changeView(self, item):
        """
        Altera a view exibida conforme o item selecionado na sidebar e recarrega os dados.
        """
        view = item.text()
        self.currentView = view
        index = self.sideBar.row(item)
        self.mainPanel.setCurrentIndex(index)
        self.loadData(view)

    def loadData(self, view):
        """
        Carrega os dados para a view atual.
        Cada view implementa seu próprio método de carregamento.
        """
        if view == UI_LABEL_DASHBOARD:
            # Atualiza o resumo financeiro do dashboard
            self.dashboardView.loadDashboardData()

        elif view in (UI_LABEL_INCOME, UI_LABEL_EXPENSE):
            # Obtém o ano selecionado nas configurações
            selected_year = self.getSelectedYear()
            dbType = "Receitas" if view == UI_LABEL_INCOME else "Despesas"
            
            query = """
                SELECT category, subcategory, strftime('%m', date) AS month, SUM(value) AS total
                FROM transactions
                WHERE type = ? AND user_id = ? AND strftime('%Y', date) = ?
                GROUP BY category, subcategory, month
                ORDER BY category, subcategory, month;
            """
            rows = FINANCE_DB.fetch_query(query, (dbType, FINANCE_DB.user_id, selected_year))
            
            # Organiza os resultados em um dicionário (pivot) para facilitar o preenchimento da tabela
            pivot = {}
            for category, subcategory, month, total in rows:
                key = (category, subcategory)
                if key not in pivot:
                    pivot[key] = {f"{i:02d}": 0.0 for i in range(1, 13)}
                pivot[key][month] = total

            # Chama o método da view para carregar os dados
            if view == UI_LABEL_INCOME:
                self.transactionsIncomeView.loadDataFromPivot(pivot)
            else:
                self.transactionsExpenseView.loadDataFromPivot(pivot)

        elif view == UI_LABEL_INVESTMENTS:
            self.investmentsView.loadData()

        elif view == UI_LABEL_REPORTS:
            # Atualiza os relatórios, se necessário
            self.reportsView.loadReports()

        elif view == UI_LABEL_SETTINGS:
            # Atualiza as configurações, se necessário
            self.settingsView.loadSettings()

    def getSelectedYear(self):
        """
        Obtém o ano selecionado pelo usuário na aba de Configurações.
        """
        try:
            row = FINANCE_DB.fetch_query("SELECT selected_year FROM app_settings LIMIT 1")
            if row and row[0][0]:
                return row[0][0]
        except Exception as e:
            logging.error("Erro ao carregar o ano selecionado: %s", e)

        from datetime import datetime
        return str(datetime.now().year)  # Retorna o ano atual como fallback

    def showEvent(self, event):
        """
        Sempre que a janela principal é exibida, recarrega os dados da view atual.
        """
        self.loadData(self.currentView)
        super().showEvent(event)
