import os
import re

def save_results(search_type, search_value, text):

    safe_value= re.sub(r'[^\w\-]', '_', search_value.strip())
    base_filename = f"{search_type}_{safe_value}"

    folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "extracted_data")
    os.makedirs(folder, exist_ok=True)  # create folder if it doesn't exist

    counter = 1
    filename = os.path.join(folder, f"{base_filename}{counter}.txt")

    while os.path.exists(filename):
        counter += 1
        filename = os.path.join(folder, f"{base_filename}{counter}.txt")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)

    return os.path.basename(filename) 