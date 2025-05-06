import argparse


def read_first_n_lines(filename, n=20):
    """
    Read the first n lines from a file.

    Args:
        filename (str): Path to the file to read
        n (int): Number of lines to read (default: 20)

    Returns:
        list: List containing the first n lines from the file
    """
    try:
        # Open the file and read the first n lines
        with open(filename, "r") as file:
            lines = [file.readline().strip() for _ in range(n)]
            # Remove any empty lines that might occur if the file has fewer than n lines
            lines = [line for line in lines if line]

        print(f"Successfully read {len(lines)} lines from {filename}")
        return lines

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []


def save_lines_to_file(lines, output_file):
    """
    Save lines to an output file without any row numbers or formatting.

    Args:
        lines (list): Lines to save
        output_file (str): Path to the output file
    """
    try:
        with open(output_file, "w") as file:
            for line in lines:
                file.write(f"{line}\n")
        print(f"Successfully saved {len(lines)} lines to {output_file}")
    except Exception as e:
        print(f"Error saving to file: {e}")


if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Read lines from a text file.")
    parser.add_argument(
        "--file", type=str, default="simple.txt", help="Path to the text file"
    )
    parser.add_argument("--lines", type=int, default=20, help="Number of lines to read")
    parser.add_argument("--output", type=str, help="Path to save the output (optional)")
    args = parser.parse_args()

    # Read the file using command-line arguments
    lines = read_first_n_lines(args.file, args.lines)

    # Display the lines
    print("\nFile contents:")
    for line in lines:
        print(line)

    # Save to output file if specified
    if args.output:
        save_lines_to_file(lines, args.output)
