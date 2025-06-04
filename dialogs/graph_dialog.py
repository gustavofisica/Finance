from PyQt5.QtWidgets import QDialog, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from database import FINANCE_DB

class InvestmentGraphDialog(QDialog):
    """
    A dialog for visualizing investment data using a simple Matplotlib chart.
    Displays each investment's 'Asset' along the X-axis and a chosen
    data metric (e.g., 'current_value') on the Y-axis.
    """

    def __init__(self):
        """Initialize the InvestmentGraphDialog with a default window size."""
        super().__init__()
        self.setWindowTitle("Investment Graph")
        self.setGeometry(300, 300, 600, 400)
        self._init_ui()

    def _init_ui(self):
        """
        Create and arrange the matplotlib figure canvas in the dialog layout.
        Once created, call the plotting method to display the investment data.
        """
        layout = QVBoxLayout(self)

        # Create a matplotlib Figure and Canvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.setLayout(layout)
        self._plot_investments()

    def _plot_investments(self):
        """
        Query the 'investments' table to retrieve investment data and
        display a bar chart of 'asset' vs. 'current_value'.
        """
        # Use FINANCE_DB to fetch the data instead of creating a new connection.
        rows = FINANCE_DB.fetch_query(
            """
            SELECT a.name, i.current_value
            FROM investments i
            JOIN assets a ON i.asset_id = a.id
            WHERE i.user_id = ?
            ORDER BY a.name
            """,
            (FINANCE_DB.user_id,),
        )

        # Separate data into lists
        assets = [row[0] for row in rows]
        current_values = [row[1] for row in rows]

        # Clear the figure in case it's not empty
        self.figure.clear()

        # Add a subplot to the figure and plot the data
        ax = self.figure.add_subplot(111)
        ax.bar(assets, current_values, color="#2196F3")
        ax.set_title("Investments - Current Value")
        ax.set_xlabel("Assets")
        ax.set_ylabel("Current Value (BRL)")
        ax.tick_params(axis='x', rotation=45)

        # Adjust layout to avoid cutting off labels and render the chart
        self.figure.tight_layout()
        self.canvas.draw()
