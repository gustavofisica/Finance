# settings_dialog.py

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QHBoxLayout, QPushButton, QMessageBox
import logging
from finance.database import FINANCE_DB

class DomainDialog(QDialog):
    """
    Diálogo genérico para inserir ou editar registros em uma tabela de domínio.
    """
    def __init__(self, title, table, column, current_value=None, record_id=None, parent=None):
        """
        :param title: Título da janela (ex.: "Ativo", "Tipo de Investimento", "Grupo")
        :param table: Nome da tabela de domínio (ex.: "assets", "investment_types", "groups")
        :param column: Nome da coluna que armazena o valor (ex.: "name")
        :param current_value: Valor atual para edição (None para inserir)
        :param record_id: ID do registro para edição (None para inserir)
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.table = table
        self.column = column
        self.record_id = record_id
        self.current_value = current_value
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        formLayout = QFormLayout()
        self.valueInput = QLineEdit()
        if self.current_value:
            self.valueInput.setText(self.current_value)
        formLayout.addRow("Valor:", self.valueInput)
        layout.addLayout(formLayout)
        btnLayout = QHBoxLayout()
        self.saveButton = QPushButton("Salvar")
        self.saveButton.clicked.connect(self.save)
        self.cancelButton = QPushButton("Cancelar")
        self.cancelButton.clicked.connect(self.reject)
        btnLayout.addWidget(self.saveButton)
        btnLayout.addWidget(self.cancelButton)
        layout.addLayout(btnLayout)
    
    def save(self):
        value = self.valueInput.text().strip()
        if not value:
            QMessageBox.warning(self, "Aviso", "O valor não pode ser vazio.")
            return
        try:
            if self.record_id:
                FINANCE_DB.execute_query(
                    f"UPDATE {self.table} SET {self.column} = ? WHERE id = ?",
                    (value, self.record_id)
                )
            else:
                FINANCE_DB.execute_query(
                    f"INSERT INTO {self.table} ({self.column}) VALUES (?)",
                    (value,)
                )
            self.accept()
        except Exception as e:
            logging.error("Erro ao salvar registro em %s: %s", self.table, e)
            QMessageBox.critical(self, "Erro", f"Erro ao salvar registro: {e}")

class AssetDialog(DomainDialog):
    def __init__(self, current_value=None, record_id=None, parent=None):
        super().__init__("Ativo", "assets", "name", current_value, record_id, parent)

class InvestmentTypeDialog(DomainDialog):
    def __init__(self, current_value=None, record_id=None, parent=None):
        super().__init__("Tipo de Investimento", "investment_types", "name", current_value, record_id, parent)

class GroupDialog(DomainDialog):
    def __init__(self, current_value=None, record_id=None, parent=None):
        super().__init__("Grupo", "groups", "name", current_value, record_id, parent)
