#!/usr/bin/env python3

import csv


def add_network_column(table_file, csv_file, output_file):
    # Read the CSV file and create a mapping of ROI to Network_nina
    roi_to_network = {}
    with open(csv_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            roi = int(row["ROI"])
            network = row["Network_nina"]
            roi_to_network[roi] = network

    # Read the markdown table
    with open(table_file, "r") as f:
        lines = f.readlines()

    # Process the header and separator rows
    header = lines[0].strip()
    separator = lines[1].strip()

    # Add the new column to the header and separator
    header_parts = header.split("|")
    separator_parts = separator.split("|")

    # Insert the new column before the last column
    header_parts.insert(-1, "Network Nina")
    separator_parts.insert(-1, "------------")

    # Reconstruct the header and separator rows
    new_header = "|".join(header_parts)
    new_separator = "|".join(separator_parts)

    # Process the data rows
    new_lines = [new_header + "\n", new_separator + "\n"]

    for i in range(2, len(lines)):
        line = lines[i].strip()
        parts = line.split("|")

        # Get the Label ID.L and Label ID.R values
        if len(parts) >= 6:  # Ensure the line has enough columns
            try:
                label_id_l = int(parts[4].strip())
                label_id_r = int(parts[5].strip())

                # Get the Network Nina values for both Label IDs
                network_l = roi_to_network.get(label_id_l, "")
                network_r = roi_to_network.get(label_id_r, "")

                # Use the left hemisphere network if available, otherwise use the right
                network = network_l if network_l else network_r

                # Insert the Network Nina value before the last column
                parts.insert(-1, network)

                # Reconstruct the line
                new_line = "|".join(parts)
                new_lines.append(new_line + "\n")
            except ValueError:
                # If conversion to int fails, just add an empty Network Nina column
                parts.insert(-1, "")
                new_line = "|".join(parts)
                new_lines.append(new_line + "\n")
        else:
            # If the line doesn't have enough columns, keep it as is
            new_lines.append(line + "\n")

    # Write the updated table to the output file
    with open(output_file, "w") as f:
        f.writelines(new_lines)


if __name__ == "__main__":
    add_network_column(
        "hack/bn_246_table.md",
        "hack/brainetome_roi_labels_network_groupings.csv",
        "hack/bn_246_table_with_network.md",
    )
