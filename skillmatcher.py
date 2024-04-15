import os
import json
from pprint import pprint

def read_json_files(directory):
    json_data = []
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r') as json_file:
                data = json.load(json_file)
                json_data.append(data)
    return json_data

def match_candidates_to_job(parsed_resumes, job_description):
    matched_candidates = []
    for resume in parsed_resumes:
        if set(resume['skills']).issuperset(job_description['skills_required']):
            if any(exp in resume['experience'] for exp in job_description['experience_required']):
                matched_candidates.append(resume['name'])
    return matched_candidates

def main():
    # Read JSON files from the directory
    resumes_dir = 'D:\\resumes'
    parsed_resumes = read_json_files(resumes_dir)

    # Sample job description data
    job_description_data = {
        'title': 'Data Scientist',
        'skills_required': ['python', 'machine learning', 'data analysis'],
        'experience_required': ['data science', 'machine learning'],
        'competencies_required': {'teamwork': ['collaboration', 'communication']},
        'measurable_results_expected': {'revenue growth': ['increase sales']}
    }

    # Match candidates to job description
    matched_candidates = match_candidates_to_job(parsed_resumes, job_description_data)

    print("Matched Candidates:")
    pprint(matched_candidates)

if __name__ == "__main__":
    main()
