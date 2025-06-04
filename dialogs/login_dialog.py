from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton
from PyQt5.QtCore import Qt

class LoginDialog(QDialog):
    """Simple login dialog with username and password fields."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setFixedSize(300, 150)
        layout = QFormLayout(self)

        self.usernameEdit = QLineEdit()
        self.passwordEdit = QLineEdit()
        self.passwordEdit.setEchoMode(QLineEdit.Password)

        layout.addRow("Usuário:", self.usernameEdit)
        layout.addRow("Senha:", self.passwordEdit)

        self.submitBtn = QPushButton("Entrar")
        self.submitBtn.clicked.connect(self.accept)
        layout.addWidget(self.submitBtn)

    def getCredentials(self):
        return self.usernameEdit.text(), self.passwordEdit.text()
