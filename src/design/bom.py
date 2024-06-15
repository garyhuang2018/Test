
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QLabel, QVBoxLayout, QWidget
import pandas as pd


def excel_col(num):
    print('excel col method')
    """ Convert a zero-indexed column number to an Excel column letter (e.g., 0 -> 'A'). """
    letters = ''
    while num >= 0:
        num, remainder = divmod(num, 26)
        letters = chr(65 + remainder) + letters
        num -= 1
    return letters


class ExcelFileReader(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('BOM位号检查器')
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.label = QLabel('选择一个BOM的Excel文件', self)
        layout.addWidget(self.label)

        self.button = QPushButton('打开', self)
        self.button.clicked.connect(self.showFileDialog)
        layout.addWidget(self.button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def showFileDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly

        file_name, _ = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xlsx);;All Files (*)", options=options)

        if file_name:
            self.readExcelFile(file_name)

    def readExcelFile(self, file_name):
        try:
            # df = pd.read_excel(file_name)
            # Load the Excel file
            df = pd.read_excel(file_name, engine='openpyxl', skiprows=1)
            self.label.setText(f"Excel file loaded:\n{file_name}\n\nData Preview:\n{df.head()}")

            # Print out the column names to see what pandas is recognizing
            print("Column names in the Excel file:", df.columns.tolist())

            # Ensure the specific header exists
            if '新位号或备注' not in df.columns or '数量' not in df.columns:
                print("Required columns do not exist in the Excel file.")
                return

            # Print out the content of the column
            print("Contents of '新位号或备注':")
            print(df['新位号或备注'])

            # Check for empty rows and print their indices
            empty_rows = df['新位号或备注'].isna()
            if empty_rows.any():
                print("Empty rows at indices:", empty_rows[empty_rows].index.tolist())

            # Count occurrences of each tag number, considering comma-separated values
            def count_unique_tags(cell):
                if pd.isna(cell) or not isinstance(cell, str):
                    return 0  # Return 0 for non-string or NaN cells
                tags = cell.split(',')
                filtered_tags = [tag.strip() for tag in tags if tag.strip()]
                unique_tags = set(filtered_tags)  # Use a set to remove duplicates
                return len(unique_tags)

            df['统计位号数量'] = df['新位号或备注'].apply(count_unique_tags)

            # Manually explode the tags for older pandas versions
            all_tags = df['新位号或备注'].dropna().apply(lambda x: pd.Series(x.split(','))).stack().reset_index(drop=True)
            all_tags = all_tags[all_tags.str.strip() != '']
            tag_counts = all_tags.value_counts()

            df['位号重复'] = df['新位号或备注'].apply(
                lambda x: any(tag_counts[tag.strip()] > 1 for tag in x.split(',') if tag.strip()) if isinstance(x,
                                                                                                                str) else False)

            # Compare computed tag counts with column '数量'
            df['位号数量不匹配'] = df['统计位号数量'] != df['数量']

            # Save the modified DataFrame back to Excel using xlsxwriter
            writer = pd.ExcelWriter(file_name, engine='xlsxwriter')
            df.to_excel(writer, index=False, sheet_name='Sheet1')

            # Get the xlsxwriter workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets['Sheet1']

            # Define a format for mismatched cells
            format_red = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006', })
            format_num = workbook.add_format({'num_format': '0'})  # Format for long numbers

            # Apply the number format to the 'e' column
            e_col_letter = excel_col(df.columns.get_loc('组件编码'))
            worksheet.set_column(f'{e_col_letter}:{e_col_letter}', None, format_num)

            # Determine the Excel column letter for '位号数量不匹配'
            mismatch_col = excel_col(df.columns.get_loc('位号数量不匹配'))

            # Determine the Excel column letter for '位号重复'
            duplicate_col = excel_col(df.columns.get_loc('位号重复'))

            # Apply the format to the mismatched cells
            worksheet.conditional_format(f'{mismatch_col}1:{mismatch_col}{len(df) + 1}', {
                'type': 'cell',
                'criteria': '==',
                'value': 'TRUE',
                'format': format_red
            })

            # Apply the format to the duplicated cells
            worksheet.conditional_format(f'{duplicate_col}1:{duplicate_col}{len(df) + 1}', {
                'type': 'cell',
                'criteria': '==',
                'value': 'TRUE',
                'format': format_red
            })

            self.label.setText(f"不匹配行:\n{mismatch_col}\n\n重复行:\n{duplicate_col}")
            writer.save()
            print("Updated Excel file with tag counts and duplicate status, mismatches highlighted.")
        except Exception as e:
            self.label.setText(f"Failed to read the Excel file:\n{str(e)}")


def main():
    app = QApplication(sys.argv)
    ex = ExcelFileReader()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
