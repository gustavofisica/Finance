import calendar
import datetime
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from finance.database import FINANCE_DB
from dialogs.reports_dialog import ReportsHelpDialog

logging.basicConfig(level=logging.INFO)

class ReportsView(QWidget):
    def __init__(self, reports_label):
        super().__init__()
        self.reports_label = reports_label
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        # Título do Relatório
        self.titleLabel = QLabel(self.reports_label)
        self.titleLabel.setFont(QFont("Arial", 22, QFont.Bold))
        layout.addWidget(self.titleLabel, alignment=Qt.AlignCenter)
        # Botão de ajuda
        self.helpButton = QPushButton("❓")
        self.helpButton.setFont(QFont("Arial", 14, QFont.Bold))
        self.helpButton.setFixedSize(40, 40)
        self.helpButton.clicked.connect(self.showHelp)
        layout.addWidget(self.helpButton, alignment=Qt.AlignRight)
        # Tabela de Relatórios
        self.reportTable = QTableWidget()
        self.reportTable.setColumnCount(12)  # 12 meses
        self.reportTable.setHorizontalHeaderLabels([calendar.month_abbr[i] for i in range(1, 13)])
        self.reportTable.setRowCount(0)
        self.reportTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.reportTable)
        self.setLayout(layout)
            
    def showHelp(self):
        helpDialog = ReportsHelpDialog()
        helpDialog.exec_()
        
    def getSelectedYear(self):
        try:
            row = FINANCE_DB.fetch_query("SELECT selected_year FROM app_settings LIMIT 1")
            if row and row[0][0]:
                return row[0][0]
        except Exception as e:
            logging.error("Erro ao carregar o ano selecionado: %s", e)
        return str(datetime.datetime.now().year)
    
    def getIncomeExpenses(self, selected_year):
        query = """
            SELECT type, strftime('%m', date) AS month, SUM(value) 
            FROM transactions
            WHERE strftime('%Y', date) = ?
            GROUP BY type, month;
        """
        rows = FINANCE_DB.fetch_query(query, (selected_year,))
        income = {f"{i:02d}": 0.0 for i in range(1, 13)}
        expenses = {f"{i:02d}": 0.0 for i in range(1, 13)}
        for t, month, value in rows:
            if t == "Receitas":
                income[month] = value
            else:
                expenses[month] = value
        return income, expenses

    def getInvestments(self, selected_year):
        query = """
            SELECT strftime('%m', date) AS month, 
                SUM(invested_value), 
                SUM(current_value - invested_value) / COUNT(*)
            FROM investments
            WHERE strftime('%Y', date) = ?
            GROUP BY month;
        """
        rows = FINANCE_DB.fetch_query(query, (selected_year,))
        investments = {f"{i:02d}": 0.0 for i in range(1, 13)}
        returns = {f"{i:02d}": 0.0 for i in range(1, 13)}
        profitability = {f"{i:02d}": 0.0 for i in range(1, 13)}
        for month, invested, profit in rows:
            investments[month] = invested
            returns[month] = invested * (profit / 100) if invested > 0 else 0
            profitability[month] = profit
        return investments, returns, profitability

    def getPreviousYearData(self, selected_year):
        """
        Retorna dados do mês de dezembro do ano anterior para auxiliar nos cálculos acumulados.
        Retorna uma tupla (prev_net_cash, prev_invest_balance), onde:
          - prev_net_cash: diferença entre receitas e despesas de dezembro do ano anterior;
          - prev_invest_balance: saldo acumulado dos investimentos em dezembro do ano anterior.
        """
        prev_year = str(int(selected_year) - 1)
        # Dados de transações para dezembro do ano anterior
        query_trans = """
            SELECT 
                SUM(CASE WHEN type = 'Receitas' THEN value ELSE 0 END) AS total_income,
                SUM(CASE WHEN type = 'Despesas' THEN value ELSE 0 END) AS total_expense
            FROM transactions
            WHERE strftime('%Y', date) = ? AND strftime('%m', date) = '12'
        """
        row = FINANCE_DB.fetch_query(query_trans, (prev_year,))
        prev_income = row[0][0] if row and row[0][0] else 0
        prev_expense = row[0][1] if row and row[0][1] else 0
        prev_net_cash = prev_income - abs(prev_expense)
        
        # Dados de investimentos para dezembro do ano anterior
        query_inv = """
            SELECT SUM(current_value) 
            FROM investments
            WHERE strftime('%Y', date) = ? AND strftime('%m', date) = '12'
        """
        row = FINANCE_DB.fetch_query(query_inv, (prev_year,))
        prev_invest_balance = row[0][0] if row and row[0][0] else 0
        
        return prev_net_cash, prev_invest_balance

    def loadReports(self):
        logging.info("Carregando relatórios financeiros...")
        selected_year = self.getSelectedYear()
        logging.info(f"Ano selecionado: {selected_year}")
        
        # Obter dados de transações
        income, expenses = self.getIncomeExpenses(selected_year)
        # Obter dados do mês de dezembro do ano anterior (para cálculos acumulados)
        prev_net_cash, prev_invest_balance = self.getPreviousYearData(selected_year)
        
        # Cálculo de inflação: variação percentual das despesas mês a mês (para os meses do ano atual)
        inflation = {f"{i:02d}": 0.0 for i in range(1, 13)}
        months = sorted(expenses.keys())
        prev_expense = None
        for month in months:
            current_expense = abs(expenses[month])
            if prev_expense is not None and prev_expense > 0:
                inflation[month] = ((current_expense - prev_expense) / prev_expense) * 100
            prev_expense = current_expense
        
        # Obter dados de investimentos
        investments, investment_returns, avg_profitability = self.getInvestments(selected_year)
        
        # Cálculos financeiros adicionais:
        # Saldo Disponível (mensal) = Receita - Despesa (absoluta)
        available_balance = {m: income[m] - abs(expenses[m]) for m in income}
        # Para cálculos acumulados, iniciamos com os valores de dezembro do ano anterior:
        previous_surplus = {}
        free_cash_flow = {}
        net_cash_flow = {}
        # Para o primeiro mês (geralmente "01"), usamos o valor de dezembro do ano anterior
        for i, month in enumerate(months):
            if i == 0:
                previous_surplus[month] = prev_net_cash
            else:
                previous_surplus[month] = net_cash_flow[months[i-1]]
            free_cash_flow[month] = available_balance[month] + previous_surplus[month]
            net_cash_flow[month] = free_cash_flow[month] - investments[month]
        
        # Acumulado dos investimentos: iniciamos com o saldo de dezembro anterior
        total_investments_balance = {}
        acc = prev_invest_balance
        for m in income:
            acc += investments[m]
            total_investments_balance[m] = acc
        
        # Grau de Independência = (Renda dos Investimentos / Despesa Total) * 100 (por mês)
        financial_independence = {}
        for m in income:
            if abs(expenses[m]) > 0:
                financial_independence[m] = (investment_returns[m] / abs(expenses[m])) * 100
            else:
                financial_independence[m] = 0.0
        
        # Outros indicadores
        savings_rate = {m: ((income[m] - abs(expenses[m])) / income[m]) * 100 if income[m] > 0 else 0 for m in income}
        investment_rate = {m: (investments[m] / income[m]) * 100 if income[m] > 0 else 0 for m in income}
        safety_margin = {m: ((income[m] - abs(expenses[m])) / abs(expenses[m])) * 100 if abs(expenses[m]) > 0 else 0 for m in income}
        liquidity_index = {m: (available_balance[m] + previous_surplus[m]) / abs(expenses[m]) if abs(expenses[m]) > 0 else 0 for m in income}
        growth_rate = {}
        prev_balance = None
        for m in months:
            if prev_balance is not None and prev_balance > 0:
                growth_rate[m] = ((total_investments_balance[m] - prev_balance) / prev_balance) * 100
            else:
                growth_rate[m] = 0.0
            prev_balance = total_investments_balance[m]
        
        # Organizar indicadores para exibição
        indicators = [
            ("Receita Total", income),
            ("Despesa Total", expenses),
            ("Inflação (%)", inflation),
            ("Saldo Disponível", available_balance),
            ("Sobra do Mês Anterior", previous_surplus),
            ("Fluxo de Caixa Livre", free_cash_flow),
            ("Aplicação Total", investments),
            ("Fluxo de Caixa Líquido", net_cash_flow),
            ("Saldo Total Investimentos", total_investments_balance),
            ("Renda dos Investimentos", investment_returns),
            ("Grau de Independência (%)", financial_independence),
            ("Rentabilidade Média Investimentos (%)", avg_profitability),
            ("Taxa de Poupança (%)", savings_rate),
            ("Taxa de Investimento (%)", investment_rate),
            ("Margem de Segurança (%)", safety_margin),
            ("Índice de Liquidez", liquidity_index),
            ("Crescimento Patrimonial (%)", growth_rate)
        ]
        
        self.reportTable.setRowCount(len(indicators))
        self.reportTable.setVerticalHeaderLabels([ind[0] for ind in indicators])
        
        for row, (label, data) in enumerate(indicators):
            for col, month in enumerate(months):
                item = QTableWidgetItem(f"{data[month]:.2f}")
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.reportTable.setItem(row, col, item)
        
        logging.info("Relatórios financeiros carregados com sucesso.")

