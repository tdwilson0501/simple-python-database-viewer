import sys
import sqlite3
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QTableWidget, QTableWidgetItem,
    QMessageBox, QLabel, QComboBox
)

class DBReader(QWidget):
    def __init__(self):
        super().__init__()
        self.conn = None  # will hold a live connection once opened
        self.tables = []
        
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("SQLite DB Reader")
        self.setGeometry(200, 200, 800, 600)
        
        main_layout = QVBoxLayout()
        
        # -- Row with "Open DB File" button --
        file_button_layout = QHBoxLayout()
        self.open_db_button = QPushButton("Open Database File")
        self.open_db_button.clicked.connect(self.open_file)
        file_button_layout.addWidget(self.open_db_button)
        main_layout.addLayout(file_button_layout)
        
        # -- Row with label and combo to pick which table to load --
        table_selection_layout = QHBoxLayout()
        self.table_label = QLabel("Select table:")
        self.table_combo = QComboBox()
        self.table_combo.addItem("No database loaded")  # initial placeholder
        table_selection_layout.addWidget(self.table_label)
        table_selection_layout.addWidget(self.table_combo)
        
        # A button to load whatever table is selected in the combo
        self.load_table_button = QPushButton("Load Selected Table")
        self.load_table_button.clicked.connect(self.load_selected_table)
        table_selection_layout.addWidget(self.load_table_button)
        
        main_layout.addLayout(table_selection_layout)
        
        # -- TableWidget to display results --
        self.table_widget = QTableWidget()
        main_layout.addWidget(self.table_widget)
        
        self.setLayout(main_layout)
    
    def open_file(self):
        """Prompt the user for a .db file, connect to it, fetch table names."""
        options = QFileDialog.Options()
        db_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select SQLite DB File",
            "",
            "SQLite DB Files (*.db);;All Files (*)",
            options=options
        )
        
        if db_path:
            # Close any existing connection
            if self.conn:
                self.conn.close()
            
            try:
                self.conn = sqlite3.connect(db_path)
                cursor = self.conn.cursor()
                # Get a list of tables, excluding internal sqlite_* tables
                cursor.execute("""
                    SELECT name
                    FROM sqlite_master
                    WHERE type='table'
                      AND name NOT LIKE 'sqlite_%';
                """)
                self.tables = [row[0] for row in cursor.fetchall()]
                
                if not self.tables:
                    QMessageBox.warning(self, "No Tables", 
                                        "No user tables found in the database.")
                else:
                    # Update the combo box with the found tables
                    self.table_combo.clear()
                    for t in self.tables:
                        self.table_combo.addItem(t)
            except Exception as e:
                QMessageBox.critical(self, "Error",
                                     f"Failed to open database: {str(e)}")
                self.conn = None  # reset on failure
    
    def load_selected_table(self):
        """Load the currently selected table from the combo and display it."""
        if not self.conn:
            QMessageBox.warning(self, "No DB", "No database is open yet!")
            return
        
        table_name = self.table_combo.currentText()
        if table_name == "No database loaded":
            return
        
        try:
            # Use pandas to read the entire table
            query = f"SELECT * FROM {table_name};"
            df = pd.read_sql_query(query, self.conn)
            
            # Display in the QTableWidget
            self.display_data(df)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read table: {str(e)}")
    
    def display_data(self, df):
        """Populates the QTableWidget with pandas DataFrame data."""
        self.table_widget.setRowCount(df.shape[0])
        self.table_widget.setColumnCount(df.shape[1])
        self.table_widget.setHorizontalHeaderLabels(df.columns)
        
        for row_idx, row_data in df.iterrows():
            for col_idx, value in enumerate(row_data):
                self.table_widget.setItem(
                    row_idx,
                    col_idx,
                    QTableWidgetItem(str(value))
                )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DBReader()
    window.show()
    sys.exit(app.exec())

