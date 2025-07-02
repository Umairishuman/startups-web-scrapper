import json

def filter_failed_founders(input_filename="indiResults.json"):
    """
    Reads a JSON file, removes entries where 'founder_name' is "Failed",
    and writes the updated data back to the same file.

    Args:
        input_filename (str): The name of the JSON file to process.
    """
    try:
        # Read the existing data from the JSON file
        with open(input_filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Ensure data is a list (or handle single object case if needed)
        if not isinstance(data, list):
            print(f"Warning: The JSON in '{input_filename}' is not a list. Attempting to process as a single object.")
            data = [data] # Wrap it in a list to make it iterable

        # Filter out entries where 'founder_name' is "Failed"
        # We create a new list containing only the entries that do NOT have "Failed" as founder_name
        filtered_data = [
            item for item in data
            if item.get('founder_name') != "Failed"
        ]

        # Write the filtered data back to the JSON file
        with open(input_filename, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, indent=4, ensure_ascii=False)

        print(f"Successfully filtered '{input_filename}'. Entries with 'founder_name': 'Failed' have been removed.")

    except FileNotFoundError:
        print(f"Error: The file '{input_filename}' was not found.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{input_filename}'. Please ensure it's valid JSON.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Call the function to execute the script
# Make sure your 'inidResults.json' file is in the same directory as this script,
# or provide the full path to the file.
filter_failed_founders()
