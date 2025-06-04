from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDateEdit, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, QDate
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class InvestmentFilterDialog(QDialog):
    """
    A dialog that allows users to specify filter criteria for investments,
    returning a dictionary of filters to be used by the main UI code.
    """

    def __init__(self) -> None:
        """Initialize the InvestmentFilterDialog with default fields for filtering."""
        super().__init__()
        self.setWindowTitle("Filter Investments")
        self.setFixedSize(400, 250)
        self._filters: dict[str, str] = {}
        self._init_ui()

    def _init_ui(self) -> None:
        """
        Build and arrange the form fields for selecting filter criteria such as
        asset, type, group, and date range. Provide a submit button to confirm.
        """
        layout = QFormLayout()

        self.assetInput = QLineEdit()
        self.assetInput.setPlaceholderText("e.g. AAPL, BTC")
        layout.addRow("Asset:", self.assetInput)

        self.typeInput = QLineEdit()
        self.typeInput.setPlaceholderText("e.g. Stock, Crypto, Fund")
        layout.addRow("Type:", self.typeInput)

        self.groupInput = QLineEdit()
        self.groupInput.setPlaceholderText("e.g. Tech, Blockchain, Index Fund")
        layout.addRow("Group:", self.groupInput)

        self.startDateInput = QDateEdit()
        self.startDateInput.setCalendarPopup(True)
        self.startDateInput.setDate(QDate.currentDate().addDays(-30))  # Default: 30 days ago
        layout.addRow("Start Date:", self.startDateInput)

        self.endDateInput = QDateEdit()
        self.endDateInput.setCalendarPopup(True)
        self.endDateInput.setDate(QDate.currentDate())  # Default: today
        layout.addRow("End Date:", self.endDateInput)

        # Buttons: OK/Cancel
        buttonLayout = QHBoxLayout()
        okButton = QPushButton("OK")
        okButton.clicked.connect(self._apply_filters)
        cancelButton = QPushButton("Cancel")
        cancelButton.clicked.connect(self.reject)
        buttonLayout.addWidget(okButton)
        buttonLayout.addWidget(cancelButton)

        layout.addRow(buttonLayout)
        self.setLayout(layout)

    def _apply_filters(self) -> None:
        """
        Collect all filter input values and store them in a dictionary.
        Accept the dialog if at least one field is provided.
        """
        asset = self.assetInput.text().strip()
        if asset:
            self._filters["asset"] = asset

        inv_type = self.typeInput.text().strip()
        if inv_type:
            self._filters["type"] = inv_type

        group_type = self.groupInput.text().strip()
        if group_type:
            self._filters["group_type"] = group_type

        start_date = self.startDateInput.date().toString("yyyy-MM-dd")
        end_date = self.endDateInput.date().toString("yyyy-MM-dd")
        if start_date and end_date:
            self._filters["start_date"] = start_date
            self._filters["end_date"] = end_date

        logging.info("Filters applied: %s", self._filters)
        self.accept()

    def get_filters(self) -> dict:
        """
        Return the dictionary of filters collected from user input.
        
        :return: dict with keys like 'asset', 'type', 'group_type', 'start_date', 'end_date'.
        """
        return self._filters
