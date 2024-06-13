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
#     # Ensure the specific header exists (replace 'YourHeaderHere' with the actual header name)
#     if 'e' not in df.columns:
#         print("Column 'YourHeaderHere' does not exist in the Excel file.")
#         return
#
#     # Print out the content of the column
#     # print("Contents of 'YourHeaderHere':")
#     # print(df['e'])
#
#     # Check for empty rows and print their indices
#     empty_rows = df['e'].isna()
#     if empty_rows.any():
#         print("Empty rows at indices:", empty_rows[empty_rows].index.tolist())
#
#     # Count occurrences of each tag number, considering comma-separated values
#     def count_unique_tags(cell):
#         tags = cell.split(',')
#         unique_tags = set(tags)  # Use a set to remove duplicates
#         return len(unique_tags)
#
#     df['Tag Count'] = df['e'].apply(count_unique_tags)
#
#     # Identify duplicates by checking if any tag appears more than once across all cells
#     all_tags = df['e'].str.split(',').explode().dropna()
#     tag_counts = all_tags.value_counts()
#     df['Is Duplicate'] = df['e'].apply(lambda x: any(tag_counts[tag] > 1 for tag in x.split(',')))
#
#     # Save the modified DataFrame back to Excel
#     df.to_excel(excel_path, index=False)
#     print("Updated Excel file with tag counts and duplicate status.")
#
#
# # Example usage
# count_and_identify_duplicates('test_bom.xls')


import pandas as pd


def count_and_identify_duplicates(excel_path):
    # Load the Excel file
    df = pd.read_excel(excel_path)

    # Print out the column names to see what pandas is recognizing
    print("Column names in the Excel file:", df.columns.tolist())

    # Ensure the specific header exists (replace 'YourHeaderHere' with the actual header name)
    if 'e' not in df.columns:
        print("Column 'e' does not exist in the Excel file.")
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
        # Filter out empty strings
        filtered_tags = [tag.strip() for tag in tags if tag.strip()]
        # filtered_tags = set(tags)  # Use a set to remove duplicates
        print(filtered_tags)
        print(len(filtered_tags))
        return len(filtered_tags)

    df['Tag Count'] = df['e'].apply(count_unique_tags)

    # Manually explode the tags for older pandas versions
    all_tags = df['e'].dropna().apply(lambda x: pd.Series(x.split(','))).stack().reset_index(drop=True)
    all_tags = all_tags[all_tags.str.strip() != '']
    tag_counts = all_tags.value_counts()

    df['Is Duplicate'] = df['e'].apply(
        lambda x: any(tag_counts[tag.strip()] > 1 for tag in x.split(',') if tag.strip()) if isinstance(x,
                                                                                                        str) else False)

    # Save the modified DataFrame back to Excel
    df.to_excel(excel_path, index=False)
    print("Updated Excel file with tag counts and duplicate status.")


# Example usage
count_and_identify_duplicates('test_bom.xls')