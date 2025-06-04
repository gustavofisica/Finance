import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from finance.database import FINANCE_DB  # Agora importado de finance/database.py
from ui.main_window import FinancePanel  # Main window refatorado

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

UI_LABEL_MAIN = "Meu Cofrinho"

def main():
    """
    Ponto de entrada da aplicação. Inicializa o banco, a interface principal e inicia o loop de eventos.
    """
    app = QApplication(sys.argv)
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
