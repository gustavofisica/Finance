from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QPushButton, QTableWidgetItem, QHeaderView, QHBoxLayout
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer
import calendar
import logging
from datetime import datetime
from dialogs.transaction_dialog import AddTransactionDialog, EditTransactionDialog
from finance.database import FINANCE_DB

logging.basicConfig(level=logging.INFO)

class TransactionsView(QWidget):
    def __init__(self, transactionType, transaction_label):
        super().__init__()
        self.transaction_label = transaction_label
        self.transactionType = transactionType
        self.currentPivotData = {}  # Armazena os dados atuais para atualização
        self.initUI()
        self.updateTableData()  # Carregar dados iniciais
    
    def initUI(self):
        layout = QVBoxLayout(self)
        self.titleLabel = QLabel(self.transaction_label)
        self.titleLabel.setFont(QFont("Arial", 22, QFont.Bold))
        layout.addWidget(self.titleLabel, alignment=Qt.AlignCenter)
        
        self.table = QTableWidget()
        layout.addWidget(self.table)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)  # Permitir seleção de linha inteira
        self.table.setSelectionMode(QTableWidget.SingleSelection)  # Seleção única
        
        buttonLayout = QHBoxLayout()
        
        # Botão para adicionar nova transação
        self.addButton = QPushButton(f"Nova {self.transactionType}")
        self.addButton.clicked.connect(self.openAddTransactionDialog)
        buttonLayout.addWidget(self.addButton)

        # Botão para editar transações do mês selecionado
        self.editButton = QPushButton(f"Editar {self.transactionType}")
        self.editButton.clicked.connect(self.openEditTransactionsDialog)
        buttonLayout.addWidget(self.editButton)

        layout.addLayout(buttonLayout)
        self.setLayout(layout)
    
    def openAddTransactionDialog(self):
        """
        Abre o modal para adicionar uma nova transação e garante que a view seja atualizada corretamente.
        """
        dialogCode = "Income" if self.transactionType == "Receitas" else "Expense"
        dialog = AddTransactionDialog(dialogCode)
        dialog.transactionUpdated.connect(self.updateTableData)  # Atualiza pelo FinancePanel
        dialog.exec_()

    def openEditTransactionsDialog(self):
        """
        Obtém o mês selecionado e abre o diálogo de edição de todas as transações do mês e ano selecionados.
        """
        selected_column = self.table.currentColumn()
        if selected_column < 2:
            logging.warning("Nenhuma coluna de mês selecionada!")
            return  # Nenhum mês foi selecionado
        
        month_selected = f"{selected_column - 1:02d}"  # Convertendo para formato MM
        selected_year = self.getSelectedYear()  # Obtendo o ano configurado
        db_type = "Income" if self.transactionType == "Receitas" else "Expense"

        logging.info(f"Abrindo edição para transações de {month_selected}/{selected_year} do tipo {self.transactionType}")
        
        dialog = EditTransactionDialog(db_type, month_selected, selected_year)
        dialog.transactionUpdated.connect(self.updateTableData)  # Atualiza pelo FinancePanel
        dialog.exec_()

        
    def updateTableData(self):
        """
        Atualiza os dados chamando loadData do FinancePanel, garantindo que a atualização ocorra da mesma forma
        que quando a aba é trocada.
        """
        logging.info("Atualizando TransactionsView através do FinancePanel...")

        parent = self.parent()
        while parent:
            if parent.__class__.__name__ == "FinancePanel":  # Encontra o FinancePanel
                logging.info("FinancePanel encontrado! Atualizando os dados...")
                parent.loadData(parent.currentView)  # Atualiza a aba atual
                return
            parent = parent.parent()

        logging.warning("FinancePanel não encontrado. Atualizando apenas localmente.")
        self.currentPivotData = self.loadDataFromDatabase()
        self.loadDataFromPivot(self.currentPivotData)


    def loadDataFromDatabase(self):
        """
        Busca os dados do banco de dados considerando o ano selecionado e garantindo que a data esteja no formato correto.
        """
        db_type = "Receitas" if self.transactionType == "Income" else "Despesas"
        selected_year = self.getSelectedYear()  # Obtendo o ano configurado
        
        logging.info(f"Buscando transações para {db_type} no ano {selected_year}") 

        query = """
            SELECT category, subcategory, strftime('%m', date) AS month, SUM(value) AS total
            FROM transactions
            WHERE type = ? AND user_id = ? AND strftime('%Y', date) = ?
            GROUP BY category, subcategory, month
            ORDER BY category, subcategory, month;
        """

        rows = FINANCE_DB.fetch_query(query, (db_type, FINANCE_DB.user_id, selected_year))
        
        logging.info(f"Dados carregados do banco: {rows}")  # Verifique se os dados estão corretos

        pivot = {}
        for category, subcategory, month, total in rows:
            key = (category, subcategory)
            if key not in pivot:
                pivot[key] = {f"{i:02d}": 0.0 for i in range(1, 13)}
            pivot[key][month] = total
        
        logging.info(f"Dados processados para preenchimento: {pivot}")
        return pivot

    def loadDataFromPivot(self, pivot):
        """
        Atualiza a tabela mantendo a estrutura de meses e garantindo que os valores sejam exibidos corretamente.
        """
        month_names = [calendar.month_abbr[i] for i in range(1, 13)]
        headers = ["Categoria", "Subcategoria"] + month_names

        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(pivot))

        for rowIndex, ((category, subcategory), month_totals) in enumerate(pivot.items()):
            self.table.setItem(rowIndex, 0, QTableWidgetItem(category))
            self.table.setItem(rowIndex, 1, QTableWidgetItem(subcategory))

            for j, month in enumerate([f"{i:02d}" for i in range(1, 13)]):
                value = month_totals.get(month, 0.0)
                item = QTableWidgetItem(f"{value:.2f}")
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(rowIndex, 2 + j, item)

        # Ajusta automaticamente a largura das colunas de Categoria e Subcategoria
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)

        # Define uma largura mínima para evitar truncamento
        self.table.setColumnWidth(0, 150)  # Categoria
        self.table.setColumnWidth(1, 180)  # Subcategoria

        logging.info("Tabela preenchida com os dados atualizados.")

    def getSelectedYear(self):
        """
        Obtém o ano configurado pelo usuário na aba de Configurações.
        """
        try:
            row = FINANCE_DB.fetch_query("SELECT selected_year FROM app_settings LIMIT 1")
            if row and row[0][0]:
                logging.info(f"Ano selecionado: {row[0][0]}")
                return row[0][0]
        except Exception as e:
            logging.error("Erro ao carregar o ano selecionado: %s", e)

        return str(datetime.now().year)  # Retorna o ano atual como fallback


    def delayedUpdate(self):
        """
        Aguarda um pequeno tempo antes de chamar updateTableData para garantir que o banco de dados foi atualizado.
        """
        QTimer.singleShot(100, self.updateTableData)  # Aguarda 100ms antes de atualizar
