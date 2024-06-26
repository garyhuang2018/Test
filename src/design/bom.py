
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QLabel, QVBoxLayout, QWidget, \
    QInputDialog
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

            # Ask user if they want to skip the first row
            skip_first_row, ok = QInputDialog.getItem(self, "判断列名所在行", "是否跳过Excel表第一行?",
                                                      ["Yes", "No"], 0, False)
            if not ok:
                self.label.setText("Operation cancelled.")
                return

            skip_rows = 1 if skip_first_row == "Yes" else None

            # Load the Excel file with or without skipping the first row
            df = pd.read_excel(file_name, engine='openpyxl', skiprows=skip_rows)
            self.label.setText(f"Excel file loaded:\n{file_name}\n\nData Preview:\n{df.head()}")

            # Check if the specific header exists
            if '新位号或备注' not in df.columns:
                # Prompt user to input the correct column name
                column_name, ok = QInputDialog.getText(self, 'Input Column Name', '输入位号所在列名:')
                if ok and column_name:
                    column_name = column_name.strip()
                else:
                    self.label.setText("Operation cancelled or invalid column name.")
                    return
            else:
                column_name = '新位号或备注'

            # Continue with the rest of the code using the user-provided or default column name
            if column_name not in df.columns:
                self.label.setText("The specified column does not exist in the Excel file.")
                return

            # Print out the content of the column
            print(f"Contents of '{column_name}':")
            print(df[column_name])

            # Check for empty rows and print their indices
            empty_rows = df[column_name].isna()
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

            df['统计位号数量'] = df[column_name].apply(count_unique_tags)

            # Manually explode the tags for older pandas versions
            all_tags = df[column_name].dropna().apply(lambda x: pd.Series(x.split(','))).stack().reset_index(drop=True)
            all_tags = all_tags[all_tags.str.strip() != '']
            tag_counts = all_tags.value_counts()

            df['位号重复'] = df[column_name].apply(
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

            self.label.setText(f"重复位号或数量不匹配的已在excel表中标红，请在excel表中检查")
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
