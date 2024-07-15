from flask import Flask, request, jsonify
from flask_cors import CORS
import fitz  
import joblib 
import nltk  
from nltk.corpus import stopwords
import spacy  
import re 
from sklearn.metrics.pairwise import cosine_similarity 
import json
import difflib

app = Flask(__name__)
CORS(app)

# Load the trained model and the TF-IDF vectorizer from disk
model = joblib.load('./ensemble_model.pkl')
vectorizer = joblib.load('./ensemble_model_tfidf_vectorizer.pkl')

# Load spaCy model for English
nlp = spacy.load("en_core_web_sm")

# Download stopwords from nltk if not already downloaded
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += page.get_text("text")
    return text

# Function to split text into paragraphs
def split_text_into_paragraphs(text):
    # paragraphs = re.split(r'\n\d+\.\s\xa0|\n\xa0', text)
    paragraphs = re.split(r'\n \n', text)
    paragraphs = [para.strip() for para in paragraphs if para.strip()]
    return paragraphs

# Function to clean and preprocess text
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = " ".join([word for word in text.split() if word not in stop_words])
    doc = nlp(text)
    text = " ".join([token.lemma_ for token in doc])
    return text

# Function to annotate paragraphs with predicted clause types
def annotate_paragraphs(paragraphs):
    annotated_paragraphs = []
    for paragraph in paragraphs:
        cleaned_paragraph = clean_text(paragraph)
        paragraph_vector = vectorizer.transform([cleaned_paragraph])
        clause_type = model.predict(paragraph_vector)
        annotated_paragraphs.append((paragraph, clause_type[0].capitalize()))
    return annotated_paragraphs

# Function to calculate cosine similarity between two texts
def calculate_similarity(text1, text2):
    cleaned_text1 = clean_text(text1)
    cleaned_text2 = clean_text(text2)
    vector1 = vectorizer.transform([cleaned_text1])
    vector2 = vectorizer.transform([cleaned_text2])
    similarity = cosine_similarity(vector1, vector2)[0][0]
    return similarity

def highlight_mismatches(text1, text2):
    words1 = text1.split()
    words2 = text2.split()
    
    differ = difflib.Differ()
    diff = list(differ.compare(words1, words2))
    
    highlighted_text1 = ""
    highlighted_text2 = ""
    for word in diff:
        if word.startswith('  '):
            highlighted_text1 += word[2:] + " "
            highlighted_text2 += word[2:] + " "
        elif word.startswith('- '):
            highlighted_text1 += f"<mark>{word[2:]}</mark> "
        elif word.startswith('+ '):
            highlighted_text2 += f"<mark>{word[2:]}</mark> "
            
    return highlighted_text1.strip(), highlighted_text2.strip()

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'pdf1' not in request.files or 'pdf2' not in request.files:
        return jsonify({'message': 'Please upload both PDF files.'}), 400

    pdf1 = request.files['pdf1']
    pdf2 = request.files['pdf2']

    try:
        # Extract text from the PDF
        first_contract_text = extract_text_from_pdf(pdf1)
        second_contract_text = extract_text_from_pdf(pdf2)

        # Split text into paragraphs
        first_contract_paragraphs = split_text_into_paragraphs(first_contract_text)
        second_contract_paragraphs = split_text_into_paragraphs(second_contract_text)

        # Annotate paragraphs with predicted clause types
        annotated_first_contract_paragraphs = annotate_paragraphs(first_contract_paragraphs)
        annotated_second_contract_paragraphs = annotate_paragraphs(second_contract_paragraphs)

        similar_paragraphs = []
        max_len_first = len(annotated_first_contract_paragraphs)
        max_len_second = len(annotated_second_contract_paragraphs)

        # Calculate similarities and create a list of all paragraphs in serial order
        for idx1 in range(max_len_first):
            for idx2 in range(max_len_second):
                similarity = calculate_similarity(annotated_first_contract_paragraphs[idx1][0], annotated_second_contract_paragraphs[idx2][0])
                highlighted_text1, highlighted_text2 = highlight_mismatches(annotated_first_contract_paragraphs[idx1][0], annotated_second_contract_paragraphs[idx2][0])
                if similarity > 0.5:
                    similar_paragraphs.append((idx1 + 1, highlighted_text1, annotated_first_contract_paragraphs[idx1][1], idx2 + 1, highlighted_text2, annotated_second_contract_paragraphs[idx2][1], similarity))

        # Add paragraphs from the first contract that have no matches
        for idx1 in range(max_len_first):
            if not any(pair[0] == idx1 + 1 for pair in similar_paragraphs):
                similar_paragraphs.append((idx1 + 1, annotated_first_contract_paragraphs[idx1][0], annotated_first_contract_paragraphs[idx1][1], None, None, None, None))

        # Sort the list to maintain serial order
        similar_paragraphs.sort(key=lambda x: (x[0] if x[0] is not None else float('inf'), x[2] if x[2] is not None else float('inf')))
        
        # Add paragraphs from the second contract that have no matches
        second_non_matched_paras = []
        for idx2 in range(max_len_second):
            if not any(pair[3] == idx2 + 1 for pair in similar_paragraphs):
                second_non_matched_paras.append((None, None, None, idx2 + 1, annotated_second_contract_paragraphs[idx2][0], annotated_second_contract_paragraphs[idx2][1], None))
                
        for index in range(len(second_non_matched_paras)):
            inserted = False
            for i in range(len(similar_paragraphs)):
                # Skip if similar_paragraphs[i][2] is None
                if similar_paragraphs[i][3] is None:
                    continue
        
                # Insert if the current item's index is less than the one in similar_paragraphs
                if second_non_matched_paras[index][3] < similar_paragraphs[i][3]:
                    similar_paragraphs.insert(i, second_non_matched_paras[index])
                    inserted = True
                    break
    
            # If not inserted, append to the end
            if not inserted:
                similar_paragraphs.append(second_non_matched_paras[index])      
        
        similar_paragraphs_json = json.dumps(similar_paragraphs)
        
        response_data = {
            'message': 'Files processed successfully',
            'similar_paragraphs': similar_paragraphs_json,
        }

        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({'message': f'Error processing files: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
