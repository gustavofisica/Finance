from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QDateTimeEdit, QComboBox, QLineEdit,
    QHBoxLayout, QRadioButton, QButtonGroup, QPushButton,
    QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox
)

from PyQt5.QtCore import QDateTime, Qt, pyqtSignal
import logging
from finance.database import FINANCE_DB  # Import corrigido

logging.basicConfig(level=logging.INFO)

# =====================================================
# Constantes para padronização de transações e categorias
# =====================================================
TRANSACTION_TYPE_INCOME = "Income"
TRANSACTION_TYPE_EXPENSE = "Expense"

DB_TRANSACTION_TYPE_INCOME = "Receitas"
DB_TRANSACTION_TYPE_EXPENSE = "Despesas"

DB_CATEGORY_TYPE_INCOME = "Receita"
DB_CATEGORY_TYPE_EXPENSE = "Despesa"


class AddTransactionDialog(QDialog):
    """
    Diálogo que permite adicionar uma nova transação.
    O construtor recebe 'Income' ou 'Expense',
    mas salvamos como 'Receitas' ou 'Despesas' no banco,
    e usamos 'Receita' ou 'Despesa' para filtrar as categorias.
    """
    transactionUpdated = pyqtSignal()
    def __init__(self, transaction_type):
        """
        :param transaction_type: 'Income' (para receitas) ou 'Expense' (para despesas)
        """
        super().__init__()
        self.transactionType = transaction_type  # "Income" ou "Expense"
        self.setWindowTitle(f"Adicionar {transaction_type}")
        self.setGeometry(300, 300, 400, 300)
        self.init_ui()
    
    def _get_rank_count(self) -> int:
        """
        Tenta buscar a configuração de rank. Se não existir, retorna 5 como padrão.
        """
        result = FINANCE_DB.fetch_query("SELECT rank_count FROM app_settings LIMIT 1")
        if result and result[0][0]:
            return result[0][0]
        return 5

    def init_ui(self):
        layout = QFormLayout()

        # Campo de Data/Hora
        self.dateInput = QDateTimeEdit()
        self.dateInput.setCalendarPopup(True)
        self.dateInput.setDateTime(QDateTime.currentDateTime())

        # Campos de Categoria e Subcategoria
        self.categoryInput = QComboBox()
        self.load_categories_by_type()

        self.subcategoryInput = QComboBox()
        self.categoryInput.currentIndexChanged.connect(self.load_subcategories)
        self.load_subcategories()

        # Campo de Valor
        self.valueInput = QLineEdit("0.00")
        self.valueInput.setAlignment(Qt.AlignRight)

        # Seleção de Moeda
        self.currencyInput = QComboBox()
        self.currencyInput.addItems(["BRL", "USD", "EUR", "GBP"])

        # Seleção de Rank com RadioButtons
        self.rankGroup = QButtonGroup()
        rankLayout = QHBoxLayout()
        rank_count = self._get_rank_count()
        for i in range(1, rank_count + 1):
            btn = QRadioButton(str(i))
            self.rankGroup.addButton(btn, i)
            rankLayout.addWidget(btn)

        layout.addRow("Data/Hora:", self.dateInput)
        layout.addRow("Categoria:", self.categoryInput)
        layout.addRow("Subcategoria:", self.subcategoryInput)
        layout.addRow("Valor:", self.valueInput)
        layout.addRow("Moeda:", self.currencyInput)
        layout.addRow("Rank:", rankLayout)

        self.submitButton = QPushButton("Adicionar Transação")
        self.submitButton.clicked.connect(self.add_transaction)
        layout.addRow(self.submitButton)

        self.setLayout(layout)

    def load_categories_by_type(self):
        """
        Carrega as categorias de 'categories_config' utilizando o tipo apropriado:
        mapeia "Income" para DB_CATEGORY_TYPE_INCOME e "Expense" para DB_CATEGORY_TYPE_EXPENSE.
        """
        self.categoryInput.clear()
        dbType = DB_CATEGORY_TYPE_INCOME if self.transactionType == TRANSACTION_TYPE_INCOME else DB_CATEGORY_TYPE_EXPENSE

        rows = FINANCE_DB.fetch_query(
            "SELECT DISTINCT category FROM categories_config WHERE type = ?",
            (dbType,)
        )

        if not rows:
            self.categoryInput.addItem("Outros")
        else:
            for (cat,) in rows:
                self.categoryInput.addItem(cat)

    def load_subcategories(self):
        """
        Carrega as subcategorias correspondentes ao tipo definido.
        """
        self.subcategoryInput.clear()
        dbType = DB_CATEGORY_TYPE_INCOME if self.transactionType == TRANSACTION_TYPE_INCOME else DB_CATEGORY_TYPE_EXPENSE
        selectedCategory = self.categoryInput.currentText()

        rows = FINANCE_DB.fetch_query(
            "SELECT subcategory FROM categories_config WHERE type = ? AND category = ?",
            (dbType, selectedCategory)
        )

        if not rows:
            self.subcategoryInput.addItem("Geral")
        else:
            for (subcat,) in rows:
                self.subcategoryInput.addItem(subcat)

    def add_transaction(self):
        """
        Insere o registro na tabela 'transactions'.
        Mapeia "Income" para DB_TRANSACTION_TYPE_INCOME e "Expense" para DB_TRANSACTION_TYPE_EXPENSE.
        Se for Expense, o valor é negativado se estiver positivo.
        """
        dateString = self.dateInput.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        category = self.categoryInput.currentText()
        subcategory = self.subcategoryInput.currentText().strip()

        try:
            rawValue = float(self.valueInput.text().replace(",", "."))
        except ValueError:
            rawValue = 0.0

        currency = self.currencyInput.currentText()
        valueBrl = FINANCE_DB.convert_to_brl(rawValue, currency)

        if self.transactionType == TRANSACTION_TYPE_EXPENSE and valueBrl > 0:
            valueBrl = -valueBrl

        rank = self.rankGroup.checkedId() if self.rankGroup.checkedId() != -1 else 0
        dbType = DB_TRANSACTION_TYPE_INCOME if self.transactionType == TRANSACTION_TYPE_INCOME else DB_TRANSACTION_TYPE_EXPENSE

        FINANCE_DB.execute_query(
            """
            INSERT INTO transactions (type, date, category, subcategory, value, rank)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (dbType, dateString, category, subcategory, valueBrl, rank)
        )

        self.transactionUpdated.emit()  # 🔔 Emite sinal de atualização
        self.close()

class EditTransactionDialog(QDialog):
    transactionUpdated = pyqtSignal()
    def __init__(self, transaction_type, selected_month, selected_year):
        """
        Diálogo que permite editar todas as transações de um determinado mês e ano.

        :param transaction_type: "Receitas" ou "Despesas"
        :param selected_month: String representando o mês no formato "MM"
        :param selected_year: String representando o ano no formato "YYYY"
        """
        super().__init__()
        self.transactionType = transaction_type
        self.selectedMonth = selected_month
        self.selectedYear = selected_year
        self.setWindowTitle(f"Editar {transaction_type} - {selected_month}/{selected_year}")
        self.setGeometry(300, 300, 600, 400)
        self.initUI()
        self.loadTransactionData()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Criar tabela para exibir todas as transações do mês selecionado
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Data", "Categoria", "Subcategoria", "Valor"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        # Botão de salvar alterações
        self.saveButton = QPushButton("Salvar Alterações")
        self.saveButton.clicked.connect(self.saveChanges)
        layout.addWidget(self.saveButton)

        # Botão para excluir transação selecionada
        self.deleteButton = QPushButton("Excluir Selecionado")
        self.deleteButton.clicked.connect(self.deleteSelectedTransaction)
        layout.addWidget(self.deleteButton)

        self.setLayout(layout)

    def loadTransactionData(self):
        """
        Carrega todas as transações do banco de dados para o mês e ano selecionados.
        """
        logging.info(f"Carregando transações de {self.selectedMonth}/{self.selectedYear} para {self.transactionType}")

        dbType = "Receitas" if self.transactionType == "Income" else "Despesas"
        query = """
            SELECT id, date, category, subcategory, value 
            FROM transactions
            WHERE type = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ?
            ORDER BY date ASC
        """
        rows = FINANCE_DB.fetch_query(query, (dbType, self.selectedMonth, self.selectedYear))

        self.table.setRowCount(len(rows))

        for rowIndex, (transaction_id, date, category, subcategory, value) in enumerate(rows):
            self.table.setItem(rowIndex, 0, QTableWidgetItem(str(transaction_id)))
            self.table.setItem(rowIndex, 1, QTableWidgetItem(date))
            self.table.setItem(rowIndex, 2, QTableWidgetItem(category))
            self.table.setItem(rowIndex, 3, QTableWidgetItem(subcategory))
            self.table.setItem(rowIndex, 4, QTableWidgetItem(f"{value:.2f}"))

    def saveChanges(self):
        """
        Salva todas as edições feitas na tabela e emite um sinal para atualizar a view.
        """
        logging.info(f"Salvando alterações para as transações de {self.selectedMonth}/{self.selectedYear}")

        for row in range(self.table.rowCount()):
            transaction_id = self.table.item(row, 0).text()
            date = self.table.item(row, 1).text()
            category = self.table.item(row, 2).text()
            subcategory = self.table.item(row, 3).text()
            value = float(self.table.item(row, 4).text().replace(",", "."))

            FINANCE_DB.execute_query(
                """
                UPDATE transactions
                SET date = ?, category = ?, subcategory = ?, value = ?
                WHERE id = ?
                """,
                (date, category, subcategory, value, transaction_id)
            )

        logging.info("Alterações salvas com sucesso.")
        self.transactionUpdated.emit()  # 🔔 Emite sinal de atualização
        self.accept()

    def deleteSelectedTransaction(self):
        """
        Exclui a transação selecionada.
        """
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Erro", "Nenhuma transação selecionada para exclusão.")
            return

        transaction_id = self.table.item(selected_row, 0).text()

        confirmation = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Tem certeza de que deseja excluir a transação {transaction_id}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if confirmation == QMessageBox.Yes:
            FINANCE_DB.execute_query("DELETE FROM transactions WHERE id = ?", (transaction_id,))
            logging.info(f"Transação {transaction_id} excluída com sucesso.")
            self.table.removeRow(selected_row) 
