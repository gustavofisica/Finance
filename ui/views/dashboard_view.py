import logging
from datetime import datetime
import numpy as np
import pandas as pd
import plotly.express as px
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, 
    QComboBox, QPushButton, QHBoxLayout, QScrollArea
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from finance.database import FINANCE_DB
from plotly.subplots import make_subplots
import plotly.graph_objects as go

logging.basicConfig(level=logging.INFO)

class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Main container with scroll
        mainLayout = QVBoxLayout(self)
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        mainWidget = QWidget()
        self.layout = QVBoxLayout(mainWidget)

        # Create dashboard areas
        self.createHeaderArea()
        self.createFiltersArea()
        self.createSummaryArea()
        self.createTransactionsArea()
        self.createInvestmentsArea()
        self.createGoalsArea()

        scrollArea.setWidget(mainWidget)
        mainLayout.addWidget(scrollArea)

    def createHeaderArea(self):
        headerFrame = QFrame()
        headerFrame.setObjectName("headerFrame")
        headerLayout = QVBoxLayout(headerFrame)

        title = QLabel("Dashboard Financeiro")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        subtitle = QLabel("Controle total das suas finanças")
        
        headerLayout.addWidget(title)
        headerLayout.addWidget(subtitle)
        self.layout.addWidget(headerFrame)

    def createFiltersArea(self):
        filterFrame = QFrame()
        filterLayout = QVBoxLayout(filterFrame)

        title = QLabel("Filtros e Controles")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        description = QLabel("Selecione o período e tipo de visualização")
        
        filterLayout.addWidget(title)
        filterLayout.addWidget(description)
        self.layout.addWidget(filterFrame)

    def createSummaryArea(self):
        summaryFrame = QFrame()
        summaryLayout = QVBoxLayout(summaryFrame)

        title = QLabel("Resumo Financeiro")
        title.setFont(QFont("Arial", 16, QFont.Bold))

        self.incomeLabel = QLabel("Receitas do Mês: 0.00")
        self.expenseLabel = QLabel("Despesas do Mês: 0.00")
        self.investReturnLabel = QLabel("Renda de Investimentos: 0.00")
        self.independenceLabel = QLabel("Independência Financeira: 0.00%")

        summaryLayout.addWidget(title)
        summaryLayout.addWidget(self.incomeLabel)
        summaryLayout.addWidget(self.expenseLabel)
        summaryLayout.addWidget(self.investReturnLabel)
        summaryLayout.addWidget(self.independenceLabel)
        self.layout.addWidget(summaryFrame)

    def createTransactionsArea(self):
        transactionsFrame = QFrame()
        transactionsLayout = QVBoxLayout(transactionsFrame)

        title = QLabel("Movimentações")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        description = QLabel("Análise detalhada de entradas e saídas")
        
        transactionsLayout.addWidget(title)
        transactionsLayout.addWidget(description)
        self.layout.addWidget(transactionsFrame)

    def createInvestmentsArea(self):
        investmentsFrame = QFrame()
        investmentsLayout = QVBoxLayout(investmentsFrame)

        title = QLabel("Investimentos")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        description = QLabel("Acompanhamento da carteira de investimentos")
        
        investmentsLayout.addWidget(title)
        investmentsLayout.addWidget(description)
        self.layout.addWidget(investmentsFrame)

    def createGoalsArea(self):
        goalsFrame = QFrame()
        goalsLayout = QVBoxLayout(goalsFrame)

        title = QLabel("Metas Financeiras")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        description = QLabel("Acompanhamento de objetivos e metas")
        
        goalsLayout.addWidget(title)
        goalsLayout.addWidget(description)
        self.layout.addWidget(goalsFrame)

    def loadDashboardData(self):
        """
        Load dashboard data from database
        """
        # Initialize data loading
        self.loadSummaryData()
        self.loadTransactionsData()
        self.loadInvestmentsData()
        self.loadGoalsData()

    def loadSummaryData(self):
        """Populate the summary labels with current month data."""
        try:
            current_month = datetime.now().strftime("%m")
            current_year = datetime.now().strftime("%Y")

            income_row = FINANCE_DB.fetch_query(
                """
                SELECT SUM(value) FROM transactions
                WHERE type = 'Receitas'
                  AND strftime('%Y', date) = ?
                  AND strftime('%m', date) = ?
                """,
                (current_year, current_month),
            )
            income = income_row[0][0] if income_row and income_row[0][0] else 0.0

            expense_row = FINANCE_DB.fetch_query(
                """
                SELECT SUM(value) FROM transactions
                WHERE type = 'Despesas'
                  AND strftime('%Y', date) = ?
                  AND strftime('%m', date) = ?
                """,
                (current_year, current_month),
            )
            expense = expense_row[0][0] if expense_row and expense_row[0][0] else 0.0

            invest_row = FINANCE_DB.fetch_query(
                """
                SELECT SUM(current_value - invested_value)
                FROM investments
                WHERE strftime('%Y', date) = ?
                  AND strftime('%m', date) = ?
                """,
                (current_year, current_month),
            )
            invest_income = invest_row[0][0] if invest_row and invest_row[0][0] else 0.0

            independence = (
                (invest_income / abs(expense)) * 100 if abs(expense) > 0 else 0.0
            )

            self.incomeLabel.setText(f"Receitas do Mês: {income:.2f}")
            self.expenseLabel.setText(f"Despesas do Mês: {abs(expense):.2f}")
            self.investReturnLabel.setText(
                f"Renda de Investimentos: {invest_income:.2f}"
            )
            self.independenceLabel.setText(
                f"Independência Financeira: {independence:.2f}%"
            )
        except Exception as exc:
            logging.error("Erro ao carregar resumo financeiro: %s", exc)

    def loadTransactionsData(self):
        # Load transactions data
        pass

    def loadInvestmentsData(self):
        # Load investments data  
        pass

    def loadGoalsData(self):
        # Load goals data
        pass
