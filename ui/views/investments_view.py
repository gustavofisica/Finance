from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QHBoxLayout, QPushButton, QTableWidgetItem, QHeaderView, QTabWidget, QMessageBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import logging
from datetime import datetime
from dialogs.investment_dialog import InsertInvestmentDialog, EditInvestmentDialog
from finance.database import FINANCE_DB

class InvestmentsView(QWidget):
    def __init__(self, investment_label):
        super().__init__()
        self.investment_label = investment_label
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        self.titleLabel = QLabel(self.investment_label)
        self.titleLabel.setFont(QFont("Arial", 22, QFont.Bold))
        layout.addWidget(self.titleLabel, alignment=Qt.AlignCenter)
        
        # Criar abas para as métricas
        self.tabWidget = QTabWidget()
        self.appliedValueTable = self.createTable()
        self.balanceTable = self.createTable()
        self.profitabilityTable = self.createTable()
        
        self.tabWidget.addTab(self.appliedValueTable, "Valor Aplicado")
        self.tabWidget.addTab(self.balanceTable, "Saldo do Investimento")
        self.tabWidget.addTab(self.profitabilityTable, "Rentabilidade (%)")
        layout.addWidget(self.tabWidget)
        
        # Botões para inserir e editar investimentos
        buttonLayout = QHBoxLayout()
        self.insertInvestmentButton = QPushButton("Inserir Investimento")
        self.insertInvestmentButton.clicked.connect(self.insertInvestment)
        self.editInvestmentButton = QPushButton("Editar Investimento")
        self.editInvestmentButton.clicked.connect(self.editInvestment)
        
        buttonLayout.addWidget(self.insertInvestmentButton)
        buttonLayout.addWidget(self.editInvestmentButton)
        layout.addLayout(buttonLayout)
        self.setLayout(layout)
    
    def createTable(self):
        """Cria uma tabela com 3 colunas fixas (Ativo, Tipo, Grupo) e 12 colunas para os meses."""
        table = QTableWidget()
        table.setColumnCount(15)  # 3 fixas + 12 meses
        months = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        headers = ["Ativo", "Tipo", "Grupo"] + months
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        return table

    def loadData(self):
        """
        Consulta o banco de dados para carregar os investimentos do ano atual,
        acumulando o saldo a partir do saldo final do ano anterior.
        O Valor Aplicado permanece mensal (não acumulado),
        enquanto o Saldo e a Rentabilidade são calculados de forma acumulada.
        """
        try:
            current_year = datetime.now().year
            previous_year = current_year - 1

            # Query para o ano atual
            query_current = """
                SELECT a.name AS asset, 
                    it.name AS type, 
                    g.name AS "group",
                    CAST(strftime('%m', i.date) AS INTEGER) AS month, 
                    SUM(i.invested_value) AS total_invested, 
                    SUM(i.current_value) AS total_balance
                FROM investments i
                JOIN assets a ON i.asset_id = a.id
                JOIN investment_types it ON i.type_id = it.id
                JOIN groups g ON i.group_id = g.id
                WHERE i.user_id = ? AND strftime('%Y', i.date) = ?
                GROUP BY asset, type, "group", month
                ORDER BY asset, month;
            """
            rows_current = FINANCE_DB.fetch_query(
                query_current, (FINANCE_DB.user_id, str(current_year))
            )
            if not rows_current:
                logging.info("Nenhum investimento encontrado para o ano atual.")
                return

            # Query para o ano anterior: pega o último saldo (último mês disponível) para cada combinação
            query_previous = """
                SELECT a.name AS asset, 
                    it.name AS type, 
                    g.name AS "group",
                    MAX(CAST(strftime('%m', i.date) AS INTEGER)) AS last_month, 
                    SUM(i.current_value) AS last_balance
                FROM investments i
                JOIN assets a ON i.asset_id = a.id
                JOIN investment_types it ON i.type_id = it.id
                JOIN groups g ON i.group_id = g.id
                WHERE i.user_id = ? AND strftime('%Y', i.date) = ?
                GROUP BY asset, type, "group";
            """
            rows_previous = FINANCE_DB.fetch_query(
                query_previous, (FINANCE_DB.user_id, str(previous_year))
            )
            prev_balance_data = {}
            for row in rows_previous:
                key = (row[0], row[1], row[2])
                # O último saldo registrado do ano anterior para essa combinação
                prev_balance_data[key] = float(row[4])

            # Constrói o dicionário para os dados do ano atual
            investment_data = {}
            for row in rows_current:
                asset, inv_type, group, month, total_invested, total_balance = (
                    row[0], row[1], row[2], int(row[3]), float(row[4]), float(row[5])
                )
                key = (asset, inv_type, group)
                if key not in investment_data:
                    investment_data[key] = {
                        "Valor Aplicado": {m: 0.0 for m in range(1, 13)},
                        "Saldo": {m: 0.0 for m in range(1, 13)},
                        "Rentabilidade": {m: 0.0 for m in range(1, 13)}
                    }
                investment_data[key]["Valor Aplicado"][month] = total_invested
                investment_data[key]["Saldo"][month] = total_balance
                if total_invested > 0:
                    investment_data[key]["Rentabilidade"][month] = ((total_balance - total_invested) / total_invested) * 100
                else:
                    investment_data[key]["Rentabilidade"][month] = 0.0

            # Acumula os valores de Saldo e recalcula a Rentabilidade de forma acumulada,
            # iniciando com o saldo final do ano anterior (se houver)
            for key, metrics in investment_data.items():
                cumulative_balance = prev_balance_data.get(key, 0.0)  # Saldo final do ano anterior
                cumulative_applied = 0.0
                for m in range(1, 13):
                    monthly_applied = metrics["Valor Aplicado"][m]  # Valor aplicado do mês (não acumulado)
                    monthly_balance = metrics["Saldo"][m]
                    cumulative_applied += monthly_applied
                    cumulative_balance += monthly_balance
                    metrics["Saldo"][m] = cumulative_balance
                    if cumulative_applied > 0:
                        metrics["Rentabilidade"][m] = ((cumulative_balance - cumulative_applied) / cumulative_applied) * 100
                    else:
                        metrics["Rentabilidade"][m] = 0.0

            self.updateTables(investment_data)

        except Exception as e:
            logging.error(f"Erro ao carregar investimentos: {e}", exc_info=True)
            QMessageBox.critical(self, "Erro", f"Erro ao carregar investimentos: {e}")

    def updateTables(self, investment_data):
        """Atualiza as três tabelas com os dados agregados."""
        total_rows = len(investment_data)
        self.appliedValueTable.setRowCount(total_rows)
        self.balanceTable.setRowCount(total_rows)
        self.profitabilityTable.setRowCount(total_rows)

        for index, ((asset, inv_type, group), metrics) in enumerate(investment_data.items()):
            for table in [self.appliedValueTable, self.balanceTable, self.profitabilityTable]:
                table.setItem(index, 0, QTableWidgetItem(asset))
                table.setItem(index, 1, QTableWidgetItem(inv_type))
                table.setItem(index, 2, QTableWidgetItem(group))
            # Preenche os valores de cada mês (colunas 3 a 14)
            for col, m in enumerate(range(1, 13)):
                item_applied = QTableWidgetItem(f"{metrics['Valor Aplicado'][m]:.2f}")
                item_applied.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.appliedValueTable.setItem(index, 3 + col, item_applied)

                item_balance = QTableWidgetItem(f"{metrics['Saldo'][m]:.2f}")
                item_balance.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.balanceTable.setItem(index, 3 + col, item_balance)

                item_profit = QTableWidgetItem(f"{metrics['Rentabilidade'][m]:.2f}")
                item_profit.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.profitabilityTable.setItem(index, 3 + col, item_profit)

        logging.info("Investment tables updated with aggregated monthly data.")

    def insertInvestment(self):
        """Abre o diálogo de inserção e recarrega os dados após o fechamento."""
        dialog = InsertInvestmentDialog()
        if dialog.exec_():
            self.loadData()
    
    def editInvestment(self):
        """Abre o diálogo de edição e recarrega os dados após o fechamento."""
        dialog = EditInvestmentDialog()
        if dialog.exec_():
            self.loadData()
