import os
import json
import pandas as pd
import magic
from PyPDF2 import PdfFileReader
import zipfile
import shutil

def read_file(file_path):
    mime = magic.Magic(mime=True)
    file_type = mime.from_file(file_path)

    if file_type == 'text/csv' or file_type == 'application/vnd.ms-excel':
        df = pd.read_csv(file_path, encoding='ISO-8859-1', sheet_name=None)
    elif file_type == 'application/json':
        with open(file_path, 'r', encoding='ISO-8859-1') as f:
            json_data = json.load(f)
        df = pd.json_normalize(json_data)
    elif file_type == 'application/x-stata':
        df = pd.read_stata(file_path)
    elif file_type == 'text/plain':
        with open(file_path, 'r', encoding='ISO-8859-1') as f:
            content = f.read()
        df = pd.DataFrame({'text': [content]})
    elif file_type == 'application/pdf':
        with open(file_path, 'rb') as f:
            pdf = PdfFileReader(f)
            content = ''
            for i in range(pdf.getNumPages()):
                content += pdf.getPage(i).extractText()
        df = pd.DataFrame({'text': [content]})
    elif file_type == 'application/zip':
        # Extract the zip file to a temporary directory
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            extract_dir = os.path.join(os.path.dirname(file_path), 'extracted')
            zip_ref.extractall(extract_dir)
        
        # Read all supported files within the zip file
        supported_extensions = ('.csv', '.xls', '.xlsx', '.json', '.dta', '.txt', '.pdf')
        supported_files = [f for f in os.listdir(extract_dir) if f.endswith(supported_extensions)]
        data_dict = {}
        for supported_file in supported_files:
            supported_file_path = os.path.join(extract_dir, supported_file)
            data_dict.update(read_file(supported_file_path))
        df = pd.DataFrame(data_dict)
        
        # Remove the temporary directory
        shutil.rmtree(extract_dir)
    else:
        raise ValueError(f'Unsupported file type: {file_type}')

    return df.to_dict()


def convert_to_oims(file_paths):
    data_dict = {}
    for file_path in file_paths:
        data_dict.update(read_file(file_path))
    return json.dumps(data_dict)

# def convert_to_oims(file_paths):
#     data_dict = {}
#     for file_path in file_paths:
#         data_dict.update(read_file(file_path))
    
#     # Remove keys that start with an underscore
#     data_dict = {k: v for k, v in data_dict.items() if not k.startswith('_')}
    
#     # Reorder keys alphabetically
#     data_dict = {k: data_dict[k] for k in sorted(data_dict)}
    
#     return json.dumps(data_dict)

# Example usage:
file_paths = ['uploads/LTE Metadata Checklist.xlsx', 'uploads/tic_2000_train_data.csv']
oims_data = convert_to_oims(file_paths)

with open('foresight.json', 'w') as f:
    f.write(oims_data)
