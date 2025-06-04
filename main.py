import sys
import logging
from PyQt5.QtWidgets import QApplication, QInputDialog, QLineEdit, QMessageBox
from PyQt5.QtGui import QIcon
from finance.database import FINANCE_DB
import hashlib
from ui.main_window import FinancePanel  # Main window refatorado

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

UI_LABEL_MAIN = "Meu Cofrinho"

def login_dialog():
    """Simple username/password prompt that sets FINANCE_DB.user_id."""
    while True:
        username, ok = QInputDialog.getText(None, "Login", "Username:")
        if not ok:
            return False
        password, ok = QInputDialog.getText(
            None, "Login", "Password:", QLineEdit.Password
        )
        if not ok:
            return False
        row = FINANCE_DB.fetch_query(
            "SELECT id, password_hash FROM users WHERE username = ?", (username,)
        )
        if row:
            user_id, pwd_hash = row[0]
            if hashlib.sha256(password.encode()).hexdigest() == pwd_hash:
                FINANCE_DB.user_id = user_id
                return True
            QMessageBox.warning(None, "Login", "Invalid password")
        else:
            pwd_hash = hashlib.sha256(password.encode()).hexdigest()
            cur = FINANCE_DB.execute_query(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, pwd_hash),
            )
            FINANCE_DB.user_id = cur.lastrowid
            return True

def main():
    """
    Ponto de entrada da aplicação. Inicializa o banco, a interface principal e inicia o loop de eventos.
    """
    app = QApplication(sys.argv)

    if not login_dialog():
        return

    panel = FinancePanel(UI_LABEL_MAIN)
    panel.show()
    exit_code = app.exec()
    FINANCE_DB.close()  # Fecha a conexão com o banco ao encerrar
    sys.exit(exit_code)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception("Unhandled exception: %s", e)
        FINANCE_DB.close()
        sys.exit(1)
