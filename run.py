import sys
import os
from markdown_converter import MarkdownConverter

def main():
    if len(sys.argv) < 2:
        print("Usage: python run.py <input_markdown_file>")
        sys.exit(1)
    input_file = sys.argv[1]
    if not os.path.isfile(input_file):
        print(f"Input file '{input_file}' does not exist.")
        sys.exit(1)
    os.makedirs("outputs/images", exist_ok=True)
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join("outputs", f"{base_name}.html")
    converter = MarkdownConverter(image_dir="outputs/images")
    converter.convert_file(input_file, output_file)
    print(f"Conversion completed! Output: {output_file}")

if __name__ == "__main__":
    main()