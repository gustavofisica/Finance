from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QComboBox, QSpinBox, QLineEdit,
    QPushButton, QHBoxLayout, QButtonGroup, QToolButton, QTreeWidget, QTreeWidgetItem,
    QTabWidget, QLabel, QInputDialog
)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon, QFont
from finance.database import FINANCE_DB
from dialogs.settings_dialog import AssetDialog, InvestmentTypeDialog, GroupDialog
import logging
from datetime import datetime

class SettingsView(QWidget):
    """
    Gerencia as configurações em abas: Configurações Gerais, Taxas de Câmbio,
    Categorias e Domínio de Investimentos.
    """
    def __init__(self, settings_label):
        super().__init__()
        self.settings_label = settings_label
        self.editCategoryId = None
        self.initUI()
        self._loadExchangeSettings()
    
    def initUI(self):
        mainLayout = QVBoxLayout(self)
        
        self.titleLabel = QLabel(self.settings_label)
        self.titleLabel.setFont(QFont("Arial", 22, QFont.Bold))
        mainLayout.addWidget(self.titleLabel, alignment=Qt.AlignCenter)
        
        self.tabWidget = QTabWidget()
        self.tabWidget.addTab(self._createGeneralTab(), "Configurações Gerais")
        self.tabWidget.addTab(self._createExchangeTab(), "Taxas de Câmbio")
        self.tabWidget.addTab(self._createCategoryTab(), "Categorias")
        self.tabWidget.addTab(self._createInvestmentDomainTab(), "Investimentos")
        mainLayout.addWidget(self.tabWidget)
        
        self.saveButton = QPushButton("Salvar Tudo")
        self.saveButton.clicked.connect(self.saveSettings)
        mainLayout.addWidget(self.saveButton)
        self.setLayout(mainLayout)
    
    def _createGeneralTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        groupGeneral = QGroupBox("Moeda, Rankings e Ano")
        formLayout = QFormLayout()

        self.currencyInput = QComboBox()
        self.currencyInput.addItems(["BRL", "USD", "EUR", "GBP"])

        self.rankCountInput = QSpinBox()
        self.rankCountInput.setRange(3, 10)
        self.rankCountInput.setValue(5)

        self.yearInput = QComboBox()
        current_year = datetime.now().year
        self.yearInput.addItems([str(year) for year in range(current_year, current_year - 10, -1)])

        formLayout.addRow("Moeda Padrão:", self.currencyInput)
        formLayout.addRow("Número de Rankings:", self.rankCountInput)
        formLayout.addRow("Ano dos Dados:", self.yearInput)

        groupGeneral.setLayout(formLayout)
        layout.addWidget(groupGeneral)
        return widget
    
    def _createExchangeTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        groupExchange = QGroupBox("Editar Taxas de Câmbio")
        formLayout = QFormLayout()
        self.exchangeInputs = {}
        for currency in ["BRL", "USD", "EUR", "GBP"]:
            lineEdit = QLineEdit()
            lineEdit.setPlaceholderText("Informe a taxa...")
            self.exchangeInputs[currency] = lineEdit
            formLayout.addRow(f"{currency}:", lineEdit)
        groupExchange.setLayout(formLayout)
        layout.addWidget(groupExchange)
        
        self.updateExchangeBtn = QPushButton("Atualizar Taxas Automaticamente")
        self.updateExchangeBtn.clicked.connect(self._updateExchangeAutomatic)
        layout.addWidget(self.updateExchangeBtn)
        return widget
    
    def _createCategoryTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        groupCategory = QGroupBox("Adicionar e Editar Categorias")
        catLayout = QVBoxLayout()
        
        formLayout = QFormLayout()
        self.typeButtonGroup = QButtonGroup(self)
        self.incomeBtn = QToolButton()
        self.incomeBtn.setText("Receita")
        self.incomeBtn.setCheckable(True)
        self.incomeBtn.setIcon(QIcon("assets/icons/income.png"))
        self.incomeBtn.setIconSize(QSize(48,48))
        self.incomeBtn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.incomeBtn.setFixedSize(96,96)
        self.expenseBtn = QToolButton()
        self.expenseBtn.setText("Despesa")
        self.expenseBtn.setCheckable(True)
        self.expenseBtn.setIcon(QIcon("assets/icons/expense.png"))
        self.expenseBtn.setIconSize(QSize(48,48))
        self.expenseBtn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.expenseBtn.setFixedSize(96,96)
        self.typeButtonGroup.addButton(self.incomeBtn)
        self.typeButtonGroup.addButton(self.expenseBtn)
        self.incomeBtn.setChecked(True)
        
        hLayout = QHBoxLayout()
        hLayout.addWidget(self.incomeBtn)
        hLayout.addWidget(self.expenseBtn)
        formLayout.addRow("Tipo de Transação:", hLayout)
        
        self.categoryInput = QLineEdit()
        self.categoryInput.setPlaceholderText("Ex.: Salário")
        self.subcategoryInput = QLineEdit()
        self.subcategoryInput.setPlaceholderText("Ex.: Mensal")
        formLayout.addRow("Categoria:", self.categoryInput)
        formLayout.addRow("Subcategoria:", self.subcategoryInput)
        catLayout.addLayout(formLayout)
        
        btnLayout = QHBoxLayout()
        self.addCatBtn = QPushButton("Adicionar Categoria/Subcategoria")
        self.addCatBtn.clicked.connect(self.addCategory)
        self.editCatBtn = QPushButton("Editar Categoria")
        self.editCatBtn.clicked.connect(self.editCategory)
        self.deleteCatBtn = QPushButton("Remover Categoria")
        self.deleteCatBtn.clicked.connect(self.deleteCategory)
        self.saveEditBtn = QPushButton("Salvar Edição")
        self.saveEditBtn.clicked.connect(self.updateCategory)
        self.cancelEditBtn = QPushButton("Cancelar Edição")
        self.cancelEditBtn.clicked.connect(self.cancelEdit)
        self.saveEditBtn.setVisible(False)
        self.cancelEditBtn.setVisible(False)
        btnLayout.addWidget(self.addCatBtn)
        btnLayout.addWidget(self.editCatBtn)
        btnLayout.addWidget(self.deleteCatBtn)
        btnLayout.addWidget(self.saveEditBtn)
        btnLayout.addWidget(self.cancelEditBtn)
        catLayout.addLayout(btnLayout)
        
        self.categoryTree = QTreeWidget()
        self.categoryTree.setColumnCount(3)
        self.categoryTree.setHeaderLabels(["Tipo", "Categoria", "Subcategoria"])
        self.categoryTree.itemDoubleClicked.connect(self.editCategory)
        catLayout.addWidget(self.categoryTree)
        
        groupCategory.setLayout(catLayout)
        layout.addWidget(groupCategory)
        self.loadCategoryTree()
        return widget

    def _createInvestmentDomainTab(self):
        """
        Cria a aba para gerenciar os dados de domínio dos investimentos:
        Ativos, Tipos de Investimento e Grupos.
        As entradas "novo ..." foram removidas; as operações serão realizadas por diálogos modais.
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Grupo de Ativos
        groupAssets = QGroupBox("Ativos")
        assetLayout = QVBoxLayout(groupAssets)
        self.assetList = QTreeWidget()
        self.assetList.setHeaderLabels(["Ativo"])
        assetButtons = QHBoxLayout()
        self.addAssetBtn = QPushButton("Adicionar")
        self.addAssetBtn.clicked.connect(self.addAsset)
        self.editAssetBtn = QPushButton("Editar")
        self.editAssetBtn.clicked.connect(self.editAsset)
        self.deleteAssetBtn = QPushButton("Excluir")
        self.deleteAssetBtn.clicked.connect(self.deleteAsset)
        assetButtons.addWidget(self.addAssetBtn)
        assetButtons.addWidget(self.editAssetBtn)
        assetButtons.addWidget(self.deleteAssetBtn)
        assetLayout.addWidget(self.assetList)
        assetLayout.addLayout(assetButtons)
        
        # Grupo de Tipos de Investimento
        groupTypes = QGroupBox("Tipos de Investimento")
        typeLayout = QVBoxLayout(groupTypes)
        self.typeList = QTreeWidget()
        self.typeList.setHeaderLabels(["Tipo"])
        typeButtons = QHBoxLayout()
        self.addTypeBtn = QPushButton("Adicionar")
        self.addTypeBtn.clicked.connect(self.addType)
        self.editTypeBtn = QPushButton("Editar")
        self.editTypeBtn.clicked.connect(self.editType)
        self.deleteTypeBtn = QPushButton("Excluir")
        self.deleteTypeBtn.clicked.connect(self.deleteType)
        typeButtons.addWidget(self.addTypeBtn)
        typeButtons.addWidget(self.editTypeBtn)
        typeButtons.addWidget(self.deleteTypeBtn)
        typeLayout.addWidget(self.typeList)
        typeLayout.addLayout(typeButtons)
        
        # Grupo de Grupos
        groupGroups = QGroupBox("Grupos")
        groupsLayout = QVBoxLayout(groupGroups)
        self.groupList = QTreeWidget()
        self.groupList.setHeaderLabels(["Grupo"])
        groupButtons = QHBoxLayout()
        self.addGroupBtn = QPushButton("Adicionar")
        self.addGroupBtn.clicked.connect(self.addGroup)
        self.editGroupBtn = QPushButton("Editar")
        self.editGroupBtn.clicked.connect(self.editGroup)
        self.deleteGroupBtn = QPushButton("Excluir")
        self.deleteGroupBtn.clicked.connect(self.deleteGroup)
        groupButtons.addWidget(self.addGroupBtn)
        groupButtons.addWidget(self.editGroupBtn)
        groupButtons.addWidget(self.deleteGroupBtn)
        groupsLayout.addWidget(self.groupList)
        groupsLayout.addLayout(groupButtons)
        
        layout.addWidget(groupAssets)
        layout.addWidget(groupTypes)
        layout.addWidget(groupGroups)
        
        self.loadAssetData()
        self.loadTypeData()
        self.loadGroupData()
        
        return widget

    def _updateExchangeAutomatic(self):
        try:
            logging.info("Atualizando taxas de câmbio...")
            FINANCE_DB.update_exchange_rates()
            QTimer.singleShot(200, self._loadExchangeSettings)
        except Exception as e:
            logging.error("Erro ao atualizar taxas de câmbio automaticamente: %s", e)
    
    def _loadExchangeSettings(self):
        try:
            rows = FINANCE_DB.fetch_query("""
                SELECT currency, rate, date 
                FROM exchange 
                ORDER BY date DESC
            """)
            for currency, rate, date in rows:
                if currency in self.exchangeInputs:
                    self.exchangeInputs[currency].setText(f"{rate:.4f} (Atualizado: {date})")
            logging.info("Taxas de câmbio carregadas com sucesso.")
        except Exception as e:
            logging.error("Erro ao carregar taxas de câmbio: %s", e)
    
    def loadCategoryTree(self):
        self.categoryTree.clear()
        try:
            rows = FINANCE_DB.fetch_query("SELECT id, type, category, subcategory FROM categories_config")
            for cat_id, cat_type, category, subcategory in rows:
                item = QTreeWidgetItem([cat_type, category, subcategory])
                item.setData(0, Qt.UserRole, cat_id)
                self.categoryTree.addTopLevelItem(item)
            self.categoryTree.expandAll()
        except Exception as e:
            logging.error("Erro ao carregar categorias: %s", e)
    
    def addCategory(self):
        cat_type = "Receita" if self.incomeBtn.isChecked() else "Despesa"
        category = self.categoryInput.text().strip()
        subcategory = self.subcategoryInput.text().strip()
        if category and subcategory:
            FINANCE_DB.execute_query(
                "INSERT INTO categories_config (type, category, subcategory) VALUES (?, ?, ?)",
                (cat_type, category, subcategory)
            )
            self.loadCategoryTree()
            self.categoryInput.clear()
            self.subcategoryInput.clear()
    
    def editCategory(self, item=None, column=None):
        if not item:
            item = self.categoryTree.currentItem()
        if item:
            self.editCategoryId = item.data(0, Qt.UserRole)
            cat_type = item.text(0)
            category = item.text(1)
            subcategory = item.text(2)
            if cat_type == "Receita":
                self.incomeBtn.setChecked(True)
            else:
                self.expenseBtn.setChecked(True)
            self.categoryInput.setText(category)
            self.subcategoryInput.setText(subcategory)
            self.addCatBtn.setVisible(False)
            self.editCatBtn.setVisible(False)
            self.deleteCatBtn.setVisible(False)
            self.saveEditBtn.setVisible(True)
            self.cancelEditBtn.setVisible(True)
    
    def updateCategory(self):
        cat_type = "Receita" if self.incomeBtn.isChecked() else "Despesa"
        category = self.categoryInput.text().strip()
        subcategory = self.subcategoryInput.text().strip()
        if self.editCategoryId and category and subcategory:
            FINANCE_DB.execute_query(
                "UPDATE categories_config SET type = ?, category = ?, subcategory = ? WHERE id = ?",
                (cat_type, category, subcategory, self.editCategoryId)
            )
            self.loadCategoryTree()
            self.cancelEdit()
    
    def deleteCategory(self):
        item = self.categoryTree.currentItem()
        if item:
            cat_id = item.data(0, Qt.UserRole)
            FINANCE_DB.execute_query("DELETE FROM categories_config WHERE id = ?", (cat_id,))
            self.loadCategoryTree()
    
    def cancelEdit(self):
        self.editCategoryId = None
        self.categoryInput.clear()
        self.subcategoryInput.clear()
        self.addCatBtn.setVisible(True)
        self.editCatBtn.setVisible(True)
        self.deleteCatBtn.setVisible(True)
        self.saveEditBtn.setVisible(False)
        self.cancelEditBtn.setVisible(False)
    
    def saveSettings(self):
        selectedCurrency = self.currencyInput.currentText()
        rankCount = self.rankCountInput.value()
        selectedYear = self.yearInput.currentText()

        FINANCE_DB.execute_query("DELETE FROM app_settings")
        FINANCE_DB.execute_query(
            "INSERT INTO app_settings (currency, rank_count, selected_year) VALUES (?, ?, ?)",
            (selectedCurrency, rankCount, selectedYear)
        )

        FINANCE_DB.execute_query("DELETE FROM exchange")
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info("Current date for exchange insertion: %s", current_date)
        for currency, lineEdit in self.exchangeInputs.items():
            try:
                rate = float(lineEdit.text().split()[0].replace(",", "."))
            except ValueError:
                rate = 1.0
            FINANCE_DB.execute_query(
                "INSERT INTO exchange (currency, rate, date) VALUES (?, ?, ?)",
                (currency, rate, current_date)
            )

        logging.info("Configurações salvas com sucesso!")
    
    def loadSettings(self):
        try:
            row = FINANCE_DB.fetch_query("SELECT currency, rank_count, selected_year FROM app_settings LIMIT 1")
            if row:
                currency, rank_count, selected_year = row[0]
                self.currencyInput.setCurrentText(currency)
                self.rankCountInput.setValue(rank_count)
                available_years = [self.yearInput.itemText(i) for i in range(self.yearInput.count())]
                if selected_year and selected_year in available_years:
                    self.yearInput.setCurrentText(str(selected_year))
        except Exception as e:
            logging.error("Erro ao carregar configurações: %s", e)


    # Métodos para gerenciar o domínio de investimentos

    def loadAssetData(self):
        self.assetList.clear()
        try:
            rows = FINANCE_DB.fetch_query("SELECT id, name FROM assets")
            for row in rows:
                item = QTreeWidgetItem([row[1]])
                item.setData(0, Qt.UserRole, row[0])
                self.assetList.addTopLevelItem(item)
        except Exception as e:
            logging.error("Erro ao carregar ativos: %s", e)

    def addAsset(self):
        from dialogs.settings_dialog import AssetDialog
        dialog = AssetDialog()
        if dialog.exec_():
            self.loadAssetData()

    def editAsset(self):
        item = self.assetList.currentItem()
        if item:
            from dialogs.settings_dialog import AssetDialog
            record_id = item.data(0, Qt.UserRole)
            current_name = item.text(0)
            dialog = AssetDialog(current_value=current_name, record_id=record_id)
            if dialog.exec_():
                self.loadAssetData()

    def deleteAsset(self):
        item = self.assetList.currentItem()
        if item:
            asset_id = item.data(0, Qt.UserRole)
            try:
                FINANCE_DB.execute_query("DELETE FROM assets WHERE id = ?", (asset_id,))
                self.loadAssetData()
            except Exception as e:
                logging.error("Erro ao excluir ativo: %s", e)

    def loadTypeData(self):
        self.typeList.clear()
        try:
            rows = FINANCE_DB.fetch_query("SELECT id, name FROM investment_types")
            for row in rows:
                item = QTreeWidgetItem([row[1]])
                item.setData(0, Qt.UserRole, row[0])
                self.typeList.addTopLevelItem(item)
        except Exception as e:
            logging.error("Erro ao carregar tipos de investimento: %s", e)

    def addType(self):
        from dialogs.settings_dialog import InvestmentTypeDialog
        dialog = InvestmentTypeDialog()
        if dialog.exec_():
            self.loadTypeData()

    def editType(self):
        item = self.typeList.currentItem()
        if item:
            from dialogs.settings_dialog import InvestmentTypeDialog
            record_id = item.data(0, Qt.UserRole)
            current_name = item.text(0)
            dialog = InvestmentTypeDialog(current_value=current_name, record_id=record_id)
            if dialog.exec_():
                self.loadTypeData()

    def deleteType(self):
        item = self.typeList.currentItem()
        if item:
            type_id = item.data(0, Qt.UserRole)
            try:
                FINANCE_DB.execute_query("DELETE FROM investment_types WHERE id = ?", (type_id,))
                self.loadTypeData()
            except Exception as e:
                logging.error("Erro ao excluir tipo: %s", e)

    def loadGroupData(self):
        self.groupList.clear()
        try:
            rows = FINANCE_DB.fetch_query("SELECT id, name FROM groups")
            for row in rows:
                item = QTreeWidgetItem([row[1]])
                item.setData(0, Qt.UserRole, row[0])
                self.groupList.addTopLevelItem(item)
        except Exception as e:
            logging.error("Erro ao carregar grupos: %s", e)

    def addGroup(self):
        from dialogs.settings_dialog import GroupDialog
        dialog = GroupDialog()
        if dialog.exec_():
            self.loadGroupData()

    def editGroup(self):
        item = self.groupList.currentItem()
        if item:
            from dialogs.settings_dialog import GroupDialog
            record_id = item.data(0, Qt.UserRole)
            current_name = item.text(0)
            dialog = GroupDialog(current_value=current_name, record_id=record_id)
            if dialog.exec_():
                self.loadGroupData()

    def deleteGroup(self):
        item = self.groupList.currentItem()
        if item:
            group_id = item.data(0, Qt.UserRole)
            try:
                FINANCE_DB.execute_query("DELETE FROM groups WHERE id = ?", (group_id,))
                self.loadGroupData()
            except Exception as e:
                logging.error("Erro ao excluir grupo: %s", e)

    def saveSettings(self):
        selectedCurrency = self.currencyInput.currentText()
        rankCount = self.rankCountInput.value()
        selectedYear = self.yearInput.currentText()

        FINANCE_DB.execute_query("DELETE FROM app_settings")
        FINANCE_DB.execute_query(
            "INSERT INTO app_settings (currency, rank_count, selected_year) VALUES (?, ?, ?)",
            (selectedCurrency, rankCount, selectedYear)
        )

        FINANCE_DB.execute_query("DELETE FROM exchange")
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info("Current date for exchange insertion: %s", current_date)
        for currency, lineEdit in self.exchangeInputs.items():
            try:
                rate = float(lineEdit.text().split()[0].replace(",", "."))
            except ValueError:
                rate = 1.0
            FINANCE_DB.execute_query(
                "INSERT INTO exchange (currency, rate, date) VALUES (?, ?, ?)",
                (currency, rate, current_date)
            )

        logging.info("Configurações salvas com sucesso!")
    
    def loadSettings(self):
        try:
            row = FINANCE_DB.fetch_query("SELECT currency, rank_count, selected_year FROM app_settings LIMIT 1")
            if row:
                currency, rank_count, selected_year = row[0]
                self.currencyInput.setCurrentText(currency)
                self.rankCountInput.setValue(rank_count)
                available_years = [self.yearInput.itemText(i) for i in range(self.yearInput.count())]
                if selected_year and selected_year in available_years:
                    self.yearInput.setCurrentText(str(selected_year))
        except Exception as e:
            logging.error("Erro ao carregar configurações: %s", e)
