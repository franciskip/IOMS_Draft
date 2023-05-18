from flask import Flask, render_template, request, send_file, send_from_directory
import os
import json
import PyPDF2
import pandas as pd
import xlrd

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['JSON_FOLDER'] = os.path.join(os.getcwd(), 'json')
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'csv', 'xlsx', 'xls', 'json', 'pdf', 'dta', 'jpg', 'jpeg', 'png', 'gif', 'doc', 'docx', 'ppt', 'pptx', 'zip', 'rar', 'tar', 'gz', '7z'])

# Function to convert Excel file to DataFrame
def read_excel_file(file):
    # Add custom logic to handle variations in Excel file format if needed
    return pd.read_excel(file, engine='openpyxl')

# Function to convert CSV file to DataFrame
def read_csv_file(file):
    # Add custom logic to handle variations in CSV file format if needed
    return pd.read_csv(file)

# Function to convert text file to DataFrame
def read_text_file(file):
    # Add custom logic to handle variations in text file format if needed
    try:
        with open(file, 'r') as f:
            lines = f.readlines()
        return pd.DataFrame({'data': lines})
    except UnicodeDecodeError:
        return None  # Unable to read the file as text


# Function to convert JSON file to DataFrame
def read_json_file(file):
    # Add custom logic to handle variations in JSON file format if needed
    with open(file, 'r') as f:
        data = json.load(f)
    return pd.DataFrame(data)

# Function to convert PDF file to DataFrame
import PyPDF2
def read_pdf_file(file):
    # Add custom logic to handle variations in PDF file format if needed
    with open(file, 'rb') as f:
        pdf_reader = PyPDF2.PdfReader(f)
        num_pages = len(pdf_reader.pages)
        text = ''
        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
    return pd.DataFrame({'data': text.split('\n')})


def convert_to_oims(data_files, stata_files):
    metadata = {
        'data_description': [],
        'stata_data': []
    }

    for data_file in data_files:
        if data_file:
            # Save the data file to the upload folder
            data_file_path = os.path.join(app.config['UPLOAD_FOLDER'], data_file.filename)
            data_file.save(data_file_path)

            # Check if data file is provided
            data_description = read_file(data_file_path)

            if data_description is not None:
                metadata['data_description'].extend(data_description.to_dict(orient='records'))

    for stata_file in stata_files:
        if stata_file:
            # Save the stata file to the upload folder
            stata_file_path = os.path.join(app.config['UPLOAD_FOLDER'], stata_file.filename)
            stata_file.save(stata_file_path)

            # Check if stata file is provided
            stata_data = read_file(stata_file_path)

            if stata_data is not None:
                metadata['stata_data'].extend(stata_data.to_dict(orient='records'))

    return metadata



# Determine the file format and read the file as DataFrame
def read_file(file):
    file_extension = file.split('.')[-1].lower()
    if file_extension in ['xlsx', 'xls']:
        return read_excel_file(file)
    elif file_extension == 'csv':
        return read_csv_file(file)
    elif file_extension == 'txt':
        return read_text_file(file)
    elif file_extension == 'json':
        return read_json_file(file)
    elif file_extension == 'pdf':
        return read_pdf_file(file)
    elif file_extension == 'dta':
        return read_stata_file(file)
    else:
        return None  # Unsupported file format


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tag_data', methods=['POST'])
def tag_data():
    data_files = request.files.getlist('data_file')
    stata_files = request.files.getlist('stata_file')

    # Validate file extensions for all files
    for data_file in data_files:
        if not allowed_file(data_file.filename):
            return "Invalid file extension for data file. Only TXT, CSV, XLSX, XLS, JSON, PDF, DTA, JPG, JPEG, PNG, GIF, DOC, DOCX, PPT, PPTX, ZIP, RAR, TAR, GZ, and 7Z files are allowed."

    for stata_file in stata_files:
        if not allowed_file(stata_file.filename):
            return "Invalid file extension for stata file. Only TXT, CSV, XLSX, XLS, JSON, PDF, DTA, JPG, JPEG, PNG, GIF, DOC, DOCX, PPT, PPTX, ZIP, RAR, TAR, GZ, and 7Z files are allowed."

    # Combine data files and stata files into OIMS metadata
    metadata = convert_to_oims(data_files, stata_files)

    # Save the metadata as a JSON file
    json_filename = 'metadata.json'
    json_file_path = os.path.join(app.config['JSON_FOLDER'], json_filename)

    with open(json_file_path, 'w') as f:
        json.dump(metadata, f, indent=4)

    # Return the JSON file as a download response
    return send_file(json_file_path, as_attachment=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

if __name__ == '__main__':
    app.run(debug=True)
