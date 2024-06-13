#
# import pandas as pd
#
#
# def count_and_identify_duplicates(excel_path):
#     # Load the Excel file
#     df = pd.read_excel(excel_path)
#
#     # Print out the column names to see what pandas is recognizing
#     print("Column names in the Excel file:", df.columns.tolist())
#
#     # Ensure the specific header exists (replace 'e' with the actual header name)
#     if 'e' not in df.columns or '数量' not in df.columns:
#         print("Required columns do not exist in the Excel file.")
#         return
#
#     # Print out the content of the column
#     print("Contents of 'e':")
#     print(df['e'])
#
#     # Check for empty rows and print their indices
#     empty_rows = df['e'].isna()
#     if empty_rows.any():
#         print("Empty rows at indices:", empty_rows[empty_rows].index.tolist())
#
#     # Count occurrences of each tag number, considering comma-separated values
#     def count_unique_tags(cell):
#         if pd.isna(cell) or not isinstance(cell, str):
#             return 0  # Return 0 for non-string or NaN cells
#         tags = cell.split(',')
#         filtered_tags = [tag.strip() for tag in tags if tag.strip()]
#         unique_tags = set(filtered_tags)  # Use a set to remove duplicates
#         return len(unique_tags)
#
#     df['Computed Tag Count'] = df['e'].apply(count_unique_tags)
#
#     # Manually explode the tags for older pandas versions
#     all_tags = df['e'].dropna().apply(lambda x: pd.Series(x.split(','))).stack().reset_index(drop=True)
#     all_tags = all_tags[all_tags.str.strip() != '']
#     tag_counts = all_tags.value_counts()
#
#     df['Is Duplicate'] = df['e'].apply(
#         lambda x: any(tag_counts[tag.strip()] > 1 for tag in x.split(',') if tag.strip()) if isinstance(x, str) else False)
#
#     # Compare computed tag counts with column 'd'
#     mismatches = df[df['Computed Tag Count'] != df['数量']]
#     if not mismatches.empty:
#         print("Mismatched rows:")
#         print(mismatches[['数量', 'Computed Tag Count']])
#
#     # Save the modified DataFrame back to Excel
#     df.to_excel(excel_path, index=False)
#     print("Updated Excel file with tag counts and duplicate status.")
#
#
# # Example usage
# count_and_identify_duplicates('test_bom.xlsx')

import pandas as pd
import string

def excel_col(num):
    """ Convert a zero-indexed column number to an Excel column letter (e.g., 0 -> 'A'). """
    letters = ''
    while num >= 0:
        num, remainder = divmod(num, 26)
        letters = chr(65 + remainder) + letters
        num -= 1
    return letters


def count_and_identify_duplicates(excel_path):
    # Load the Excel file
    df = pd.read_excel(excel_path, engine='openpyxl')

    # Print out the column names to see what pandas is recognizing
    print("Column names in the Excel file:", df.columns.tolist())

    # Ensure the specific header exists
    if 'e' not in df.columns or '数量' not in df.columns:
        print("Required columns do not exist in the Excel file.")
        return

    # Print out the content of the column
    print("Contents of 'e':")
    print(df['e'])

    # Check for empty rows and print their indices
    empty_rows = df['e'].isna()
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

    df['Computed Tag Count'] = df['e'].apply(count_unique_tags)

    # Manually explode the tags for older pandas versions
    all_tags = df['e'].dropna().apply(lambda x: pd.Series(x.split(','))).stack().reset_index(drop=True)
    all_tags = all_tags[all_tags.str.strip() != '']
    tag_counts = all_tags.value_counts()

    df['Is Duplicate'] = df['e'].apply(
        lambda x: any(tag_counts[tag.strip()] > 1 for tag in x.split(',') if tag.strip()) if isinstance(x, str) else False)

    # Compare computed tag counts with column '数量'
    df['Mismatch'] = df['Computed Tag Count'] != df['数量']

    # Save the modified DataFrame back to Excel using xlsxwriter
    writer = pd.ExcelWriter(excel_path, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')

    # Get the xlsxwriter workbook and worksheet objects
    workbook  = writer.book
    worksheet = writer.sheets['Sheet1']

    # Define a format for mismatched cells
    format_red = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})

    # Determine the Excel column letter for 'Mismatch'
    mismatch_col = excel_col(df.columns.get_loc('Mismatch'))

    # Apply the format to the mismatched cells
    worksheet.conditional_format(f'{mismatch_col}1:{mismatch_col}{len(df)+1}', {
        'type': 'cell',
        'criteria': '==',
        'value': 'TRUE',
        'format': format_red
    })

    writer.save()
    print("Updated Excel file with tag counts and duplicate status, mismatches highlighted.")


# Example usage
count_and_identify_duplicates('test.xlsx')