from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QFormLayout, QComboBox,
    QDateEdit, QLineEdit, QMessageBox, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QDate
import logging
from finance.database import FINANCE_DB

logging.basicConfig(level=logging.INFO)

class InsertInvestmentDialog(QDialog):
    """
    Modal para inserir um novo aporte de investimento.
    Se o ativo já tiver um aporte no mesmo mês, o valor será somado ao existente.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inserir Aporte de Investimento")
        self.setFixedSize(400, 250)
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        titulo = QLabel("Inserir Novo Aporte")
        titulo.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(titulo, alignment=Qt.AlignCenter)

        formLayout = QFormLayout()

        # Seleção de Ativo
        self.assetInput = QComboBox()
        assets = FINANCE_DB.fetch_query("SELECT name FROM assets ORDER BY name")
        self.assetInput.addItems([a[0] for a in assets] if assets else [])

        # Seleção de Tipo
        self.typeInput = QComboBox()
        types = FINANCE_DB.fetch_query("SELECT name FROM investment_types ORDER BY name")
        self.typeInput.addItems([t[0] for t in types] if types else [])

        # Seleção de Grupo
        self.groupInput = QComboBox()
        groups = FINANCE_DB.fetch_query("SELECT name FROM groups ORDER BY name")
        self.groupInput.addItems([g[0] for g in groups] if groups else [])

        # Data do Aporte
        self.dateInput = QDateEdit()
        self.dateInput.setCalendarPopup(True)
        self.dateInput.setDate(QDate.currentDate())

        # Valor do Aporte
        self.investedValueInput = QLineEdit()
        self.investedValueInput.setPlaceholderText("Digite o valor do aporte")

        formLayout.addRow("Ativo:", self.assetInput)
        formLayout.addRow("Tipo:", self.typeInput)
        formLayout.addRow("Grupo:", self.groupInput)
        formLayout.addRow("Data:", self.dateInput)
        formLayout.addRow("Valor Aplicado:", self.investedValueInput)
        layout.addLayout(formLayout)

        # Botões
        buttonLayout = QHBoxLayout()
        self.saveButton = QPushButton("Salvar")
        self.saveButton.clicked.connect(self.saveInvestment)
        self.cancelButton = QPushButton("Cancelar")
        self.cancelButton.clicked.connect(self.reject)
        buttonLayout.addWidget(self.saveButton)
        buttonLayout.addWidget(self.cancelButton)
        layout.addLayout(buttonLayout)

        self.setLayout(layout)

    def saveInvestment(self):
        """
        Insere ou atualiza um aporte de investimento no banco de dados.
        Se já houver um aporte no mesmo mês, os valores serão somados.
        """
        try:
            asset = self.assetInput.currentText().strip()
            inv_type = self.typeInput.currentText().strip()
            group = self.groupInput.currentText().strip()
            date = self.dateInput.date().toString("yyyy-MM-dd")

            # Verifica campos obrigatórios
            if not asset or not inv_type or not group:
                QMessageBox.warning(self, "Aviso", "Todos os campos devem ser preenchidos.")
                return

            try:
                invested_value = float(self.investedValueInput.text().replace(",", "."))
                if invested_value <= 0:
                    raise ValueError("O valor aplicado deve ser maior que zero.")
            except ValueError:
                QMessageBox.warning(self, "Aviso", "Digite um valor válido maior que zero.")
                return

            # Obtém os IDs dos domínios
            asset_id = FINANCE_DB._get_or_create("assets", "name", asset)
            type_id = FINANCE_DB._get_or_create("investment_types", "name", inv_type)
            group_id = FINANCE_DB._get_or_create("groups", "name", group)

            # Verifica se já existe um aporte no mesmo mês para esta combinação
            existing = FINANCE_DB.fetch_query(
                """
                SELECT id, invested_value, current_value
                FROM investments
                WHERE asset_id = ? AND type_id = ? AND group_id = ?
                      AND user_id = ? AND strftime('%Y-%m', date) = strftime('%Y-%m', ?)
                """,
                (asset_id, type_id, group_id, FINANCE_DB.user_id, date),
            )

            if existing:
                # Se já existe, soma os valores
                investment_id, current_invested_value, current_balance = existing[0]
                new_invested_value = current_invested_value + invested_value
                new_balance = current_balance + invested_value
                FINANCE_DB.execute_query(
                    """
                    UPDATE investments
                    SET invested_value = ?, current_value = ?
                    WHERE id = ? AND user_id = ?
                    """,
                    (new_invested_value, new_balance, investment_id, FINANCE_DB.user_id),
                )
            else:
                # Insere um novo registro
                FINANCE_DB.execute_query(
                    """
                    INSERT INTO investments (asset_id, type_id, group_id, date, invested_value, current_value, user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (asset_id, type_id, group_id, date, invested_value, invested_value, FINANCE_DB.user_id),
                )

            self.accept()
        except Exception as e:
            logging.error(f"Erro ao inserir aporte: {e}", exc_info=True)
            QMessageBox.critical(self, "Erro", f"Erro ao inserir aporte: {e}")



class EditInvestmentDialog(QDialog):
    """
    Modal para editar ou excluir aportes de investimento.
    Permite carregar os aportes para um ativo e um mês específico, atualizá-los ou excluí-los.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Editar/Excluir Aportes de Investimento")
        self.setFixedSize(600, 400)
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        titulo = QLabel("Editar/Excluir Aportes")
        titulo.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(titulo, alignment=Qt.AlignCenter)

        # Filtros para busca de aportes
        filterLayout = QHBoxLayout()
        self.assetFilter = QComboBox()
        assets = FINANCE_DB.fetch_query("SELECT name FROM assets ORDER BY name")
        self.assetFilter.addItems([a[0] for a in assets] if assets else [])
        self.dateFilter = QDateEdit()
        self.dateFilter.setCalendarPopup(True)
        self.dateFilter.setDate(QDate.currentDate())
        self.loadButton = QPushButton("Carregar")
        self.loadButton.clicked.connect(self.loadAportes)
        filterLayout.addWidget(QLabel("Ativo:"))
        filterLayout.addWidget(self.assetFilter)
        filterLayout.addWidget(QLabel("Data (AAAA-MM):"))
        filterLayout.addWidget(self.dateFilter)
        filterLayout.addWidget(self.loadButton)
        layout.addLayout(filterLayout)

        # Tabela para exibir os aportes
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Data", "Valor Aplicado", "Saldo Atual"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        # Botões de ação
        buttonLayout = QHBoxLayout()
        self.saveButton = QPushButton("Salvar Alterações")
        self.saveButton.clicked.connect(self.saveChanges)
        self.deleteButton = QPushButton("Excluir Selecionado")
        self.deleteButton.clicked.connect(self.deleteSelectedAporte)
        buttonLayout.addWidget(self.saveButton)
        buttonLayout.addWidget(self.deleteButton)
        layout.addLayout(buttonLayout)

        self.setLayout(layout)

    def loadAportes(self):
        """
        Carrega os aportes para o ativo e o mês selecionado.
        Usa o formato "AAAA-MM" para filtrar os registros.
        """
        asset = self.assetFilter.currentText()
        # Formato: "AAAA-MM"
        period = self.dateFilter.date().toString("yyyy-MM")
        asset_id_query = FINANCE_DB.fetch_query("SELECT id FROM assets WHERE name = ?", (asset,))
        if not asset_id_query:
            QMessageBox.warning(self, "Erro", "Ativo não encontrado no banco de dados.")
            return
        asset_id = asset_id_query[0][0]

        rows = FINANCE_DB.fetch_query(
            """
            SELECT id, date, invested_value, current_value
            FROM investments
            WHERE asset_id = ? AND user_id = ? AND strftime('%Y-%m', date) = ?
            ORDER BY date ASC
            """,
            (asset_id, FINANCE_DB.user_id, period),
        )

        if not rows:
            QMessageBox.information(self, "Info", "Nenhum aporte encontrado para esse ativo no período selecionado.")
            self.table.setRowCount(0)
            return

        self.table.setRowCount(len(rows))
        for rowIndex, (inv_id, date, invested_value, current_value) in enumerate(rows):
            self.table.setItem(rowIndex, 0, QTableWidgetItem(str(inv_id)))
            self.table.setItem(rowIndex, 1, QTableWidgetItem(date))
            self.table.setItem(rowIndex, 2, QTableWidgetItem(f"{invested_value:.2f}"))
            self.table.setItem(rowIndex, 3, QTableWidgetItem(f"{current_value:.2f}"))

        QMessageBox.information(self, "Sucesso", f"{len(rows)} aportes carregados com sucesso!")

    def saveChanges(self):
        """
        Salva as alterações feitas nos aportes.
        Atualiza os valores de invested_value e current_value para cada registro editado.
        """
        updated = 0
        for row in range(self.table.rowCount()):
            try:
                inv_id = int(self.table.item(row, 0).text())
                new_invested = float(self.table.item(row, 2).text().replace(",", "."))
                new_balance = float(self.table.item(row, 3).text().replace(",", "."))
                if new_invested <= 0 or new_balance < 0:
                    raise ValueError("Valores inválidos")
            except ValueError:
                QMessageBox.warning(self, "Erro", "Valores inválidos! Insira números positivos.")
                return

            FINANCE_DB.execute_query(
                """
                UPDATE investments
                SET invested_value = ?, current_value = ?
                WHERE id = ? AND user_id = ?
                """,
                (new_invested, new_balance, inv_id, FINANCE_DB.user_id),
            )
            updated += 1

        QMessageBox.information(self, "Sucesso", f"{updated} aportes atualizados com sucesso!")
        self.accept()

    def deleteSelectedAporte(self):
        """
        Exclui o aporte selecionado, removendo também os registros correspondentes na tabela de histórico.
        """
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Erro", "Nenhum aporte selecionado para exclusão.")
            return

        inv_id = int(self.table.item(selected_row, 0).text())
        confirmation = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Tem certeza de que deseja excluir o aporte {inv_id}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if confirmation == QMessageBox.Yes:
            # Exclui registros no histórico primeiro
            FINANCE_DB.execute_query(
                "DELETE FROM investment_history WHERE investment_id = ?",
                (inv_id,),
            )
            # Exclui o investimento principal
            FINANCE_DB.execute_query(
                "DELETE FROM investments WHERE id = ? AND user_id = ?",
                (inv_id, FINANCE_DB.user_id),
            )
            self.table.removeRow(selected_row)
            QMessageBox.information(self, "Sucesso", "Aporte excluído com sucesso.")
