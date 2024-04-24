Resumer - Parsing Resumes for  ML

This code defines a comprehensive Python script for parsing resumes and extracting key information. Here's a breakdown of its functionalities:

1. Dependencies:

Imports necessary libraries like io, os, re, nltk, spacy, pandas, docx2txt, libraries for PDF text extraction (pdfminer), and libraries for multiprocessing (multiprocessing).

2. Text Extraction Functions:

extract_text_from_pdf(pdf_path): Iterates through pages of a PDF file and extracts text using TextConverter.
extract_text_from_doc(doc_path): Uses docx2txt to extract text from DOCX files.
extract_text(file_path, extension): Calls the appropriate text extraction function based on the file extension (PDF or DOCX/DOC).

3. Entity and Section Extraction:

extract_entity_sections(text): Splits text by newline, identifies potential sections ('Education', 'Experience', etc.) based on keywords, and stores them in a dictionary.

4. Basic Details Extraction:

extract_email(text): Uses regular expressions to find email addresses.
extract_name(nlp_text): Uses spaCy's Matcher to identify names (two consecutive proper nouns).
extract_mobile_number(text): Uses regular expressions to find mobile phone numbers.

5. Skills Extraction:

extract_skills(nlp_text, noun_chunks):
Uses spaCy to identify tokens that are not stop words.
Reads a CSV file containing skills list.
Finds matches between tokens and skills in the CSV or noun chunks in the text.
Returns a list of unique capitalized skills.

6. Education Extraction:

extract_education(nlp_text):
Iterates over sentences in the text.
Identifies keywords related to education (e.g., BE, B.Tech, etc.) using regular expressions.
Attempts to find years using another regular expression.
Returns a list of education entries (degree and year if found).

7. Experience Extraction:

extract_experience(resume_text):
Uses WordNetLemmatizer and stop words list for text cleaning.
Performs part-of-speech tagging with spaCy.
Uses a chunk parser to identify phrases containing the word "experience".
Returns a list of experience descriptions extracted from these phrases.

8. Competencies and Measurable Results:

extract_competencies(text, experience_list):
Iterates through a competency dictionary where keys are competency categories and values are lists of keywords.
Searches the experience descriptions for these keywords and builds a dictionary mapping categories to found keywords.
extract_measurable_results(text, experience_list):
Similar to extract_competencies, but focuses on keywords related to measurable results (e.g., increased revenue, reduced costs).

9. ResumeParser Class:

This class takes a resume file path as input.
Loads a spaCy language model for NLP tasks.
Initializes an empty dictionary to store extracted details (name, email, skills, etc.).
Calls text extraction functions based on file extension.
Calls functions to extract various details like name, email, skills, education, experience, competencies, and measurable results.
Provides a method get_extracted_data to access the extracted information dictionary.

10. Multiprocessing for Resume Processing:

The script uses multiprocessing.Pool to parallelize resume parsing across multiple CPU cores.
It iterates through a directory containing resumes and creates a list of file paths.
The resume_result_wrapper function takes a resume path, creates a ResumeParser object, extracts data, saves it to a JSON file, and returns the extracted data.
The script uses pool.apply_async to run resume_result_wrapper asynchronously for each resume.
Finally, it retrieves results from all asynchronous tasks and prints them using pprint.

11. Constants and Data:

The script defines various constants and data structures used for text processing:
NAME_PATTERN: Pattern for identifying names (two consecutive proper nouns).
EDUCATION: List of education keywords (e.g., BE, B.Tech, etc.).
NOT_ALPHA_NUMERIC: Regular expression for non-alphanumeric characters.
NUMBER: Regular expression for numbers.
MONTHS_SHORT, MONTHS_LONG: Regular expressions for month names (short and long format).
