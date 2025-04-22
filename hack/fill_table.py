#!/usr/bin/env python3


def fill_table(input_file, output_file):
    with open(input_file, "r") as f:
        lines = f.readlines()

    # Skip the header and separator rows
    header = lines[0]
    separator = lines[1]
    data_rows = lines[2:]

    # Initialize variables to store the last non-empty values
    last_lobe = ""
    last_gyrus = ""

    # Process each data row
    processed_rows = []
    for row in data_rows:
        columns = row.split("|")

        # Check if we have enough columns
        if len(columns) >= 4:
            # Get the lobe and gyrus values (columns 1 and 2, after splitting)
            lobe = columns[1].strip()
            gyrus = columns[2].strip()

            # If lobe is empty, use the last non-empty lobe
            if not lobe:
                columns[1] = last_lobe
            else:
                last_lobe = lobe

            # If gyrus is empty, use the last non-empty gyrus
            if not gyrus:
                columns[2] = last_gyrus
            else:
                last_gyrus = gyrus

            # Reconstruct the row
            processed_row = "|".join(columns)
            processed_rows.append(processed_row)
        else:
            # If the row doesn't have enough columns, keep it as is
            processed_rows.append(row)

    # Write the processed data to the output file
    with open(output_file, "w") as f:
        f.write(header)
        f.write(separator)
        f.writelines(processed_rows)


if __name__ == "__main__":
    fill_table("hack/bn_246_table.md", "hack/bn_246_table_filled.md")
