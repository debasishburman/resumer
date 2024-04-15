import io
import os
import re
import nltk
import spacy
import pandas as pd
import docx2txt
from spacy.matcher import Matcher
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.tree import ParentedTree
import multiprocessing as mp
import pprint
import json




def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as fh:
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            resource_manager = PDFResourceManager()
            fake_file_handle = io.StringIO()
            converter = TextConverter(resource_manager, fake_file_handle, codec='utf-8', laparams=LAParams())
            page_interpreter = PDFPageInterpreter(resource_manager, converter)
            page_interpreter.process_page(page)

            text = fake_file_handle.getvalue()
            yield text

            converter.close()
            fake_file_handle.close()

def extract_text_from_doc(doc_path):
    temp = docx2txt.process(doc_path)
    text = [line.replace('\t', ' ') for line in temp.split('\n') if line]
    return ' '.join(text)

def extract_text(file_path, extension):
    text = ''
    if extension == '.pdf':
        for page in extract_text_from_pdf(file_path):
            text += ' ' + page
    elif extension == '.docx' or extension == '.doc':
        text = extract_text_from_doc(file_path)
    return text

def extract_entity_sections(text):
    text_split = [i.strip() for i in text.split('\n')]
    entities = {}
    key = False
    for phrase in text_split:
        if len(phrase) == 1:
            p_key = phrase
        else:
            p_key = set(phrase.lower().split()) & set(RESUME_SECTIONS)
        try:
            p_key = list(p_key)[0]
        except IndexError:
            pass
        if p_key in RESUME_SECTIONS:
            entities[p_key] = []
            key = p_key
        elif key and phrase.strip():
            entities[key].append(phrase)
    return entities

def extract_email(text):
    email = re.findall(r"[^@|\s\t\n]+@[^@]+\.[^@|\s\t\n]+", text)
    if email:
        try:
            return email[0].split()[0].strip(';')
        except IndexError:
            return None

def extract_name(nlp_text):
    nlp = spacy.load('en_core_web_sm')
    matcher = Matcher(nlp.vocab)
    pattern = [{'POS': 'PROPN'}, {'POS': 'PROPN'}]
    matcher.add('NAME', [pattern])
    doc = nlp(nlp_text)
    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        return span.text

def extract_mobile_number(text):
    phone = re.findall(re.compile(r'(?:(?:\+?([1-9]|[0-9][0-9]|[0-9][0-9][0-9])\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([0-9][1-9]|[0-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?'), text)
    if phone:
        number = ''.join(phone[0])
        if len(number) > 10:
            return '+' + number
        else:
            return number

def extract_skills(nlp_text, noun_chunks):
    tokens = [token.text for token in nlp_text if not token.is_stop]
    data = pd.read_csv(os.path.join(os.path.dirname(__file__), 'skills.csv'))
    skills = list(data.columns.values)
    skillset = []
    for token in tokens:
        if token.lower() in skills:
            skillset.append(token)
    for token in noun_chunks:
        token = token.text.lower().strip()
        if token in skills:
            skillset.append(token)
    return [i.capitalize() for i in set([i.lower() for i in skillset])]

def cleanup(token, lower=True):
    if lower:
        token = token.lower()
    return token.strip()

def extract_education(nlp_text):
    edu = {}
    for index, text in enumerate(nlp_text):
        for tex in text.split():
            tex = re.sub(r'[?|$|.|!|,]', r'', tex)
            if tex.upper() in EDUCATION and tex not in STOPWORDS:
                edu[tex] = text + nlp_text[index]
    education = []
    for key in edu.keys():
        year = re.search(re.compile(YEAR), edu[key])
        if year:
            education.append((key, ''.join(year.group(0))))
        else:
            education.append(key)
    return education

def extract_experience(resume_text):
    wordnet_lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))
    word_tokens = nltk.word_tokenize(resume_text)
    filtered_sentence = [w for w in word_tokens if not w in stop_words and wordnet_lemmatizer.lemmatize(w) not in stop_words]
    sent = nltk.pos_tag(filtered_sentence)
    cp = nltk.RegexpParser('P: {<NNP>+}')
    cs = cp.parse(sent)
    test = []
    for vp in ParentedTree.fromstring(str(cs)).subtrees(filter=lambda x: x.label()=='P'):
        test.append(" ".join([i[0] for i in vp.leaves() if len(vp.leaves()) >= 2]))
    x = [x[x.lower().index('experience') + 10:] for i, x in enumerate(test) if x and 'experience' in x.lower()]
    return x

def extract_competencies(text, experience_list):
    experience_text = ' '.join(experience_list)
    competency_dict = {}
    for competency in COMPETENCIES.keys():
        for item in COMPETENCIES[competency]:
            if string_found(item, experience_text):
                if competency not in competency_dict.keys():
                    competency_dict[competency] = [item]
                else:
                    competency_dict[competency].append(item)
    return competency_dict

def extract_measurable_results(text, experience_list):
    experience_text = ' '.join([text[:len(text) // 2 - 1] for text in experience_list])
    mr_dict = {}
    for mr in MEASURABLE_RESULTS.keys():
        for item in MEASURABLE_RESULTS[mr]:
            if string_found(item, experience_text):
                if mr not in mr_dict.keys():
                    mr_dict[mr] = [item]
                else:
                    mr_dict[mr].append(item)
    return mr_dict

def string_found(string1, string2):
    if re.search(r"\b" + re.escape(string1) + r"\b", string2):
        return True
    return False

class ResumeParser(object):
    def __init__(self, resume):
        self.__nlp = spacy.load('en_core_web_sm')  # Load spaCy model inside the class
        self.__details = {
            'name': None,
            'email': None,
            'mobile_number': None,
            'skills': None,
            'education': None,
            'experience': None,
            'competencies': None,
            'measurable_results': None
        }
        self.__resume = resume
        self.__text_raw = extract_text(self.__resume, os.path.splitext(self.__resume)[1])
        self.__text = ' '.join(self.__text_raw.split())
        self.__get_basic_details()

    def get_extracted_data(self):
        return self.__details

    def __get_basic_details(self):
        name = extract_name(self.__text)
        email = extract_email(self.__text)
        mobile = extract_mobile_number(self.__text)
        skills = extract_skills(self.__nlp(self.__text), self.__nlp(self.__text).noun_chunks)
        edu = extract_education([sent.text.strip() for sent in self.__nlp(self.__text).sents])
        experience = extract_experience(self.__text)
        entities = extract_entity_sections(self.__text_raw)
        self.__details['name'] = name
        self.__details['email'] = email
        self.__details['mobile_number'] = mobile
        self.__details['skills'] = skills
        self.__details['education'] = edu
        self.__details['experience'] = experience
        try:
            self.__details['competencies'] = extract_competencies(self.__text_raw, entities['experience'])
            self.__details['measurable_results'] = extract_measurable_results(self.__text_raw, entities['experience'])
        except KeyError:
            self.__details['competencies'] = []
            self.__details['measurable_results'] = []
        return

def resume_result_wrapper(resume):
    parser = ResumeParser(resume)
    extracted_data = parser.get_extracted_data()

    # Save extracted data to a JSON file
    json_filename = os.path.splitext(resume)[0] + '_extracted.json'
    with open(json_filename, 'w') as json_file:
        json.dump(extracted_data, json_file, indent=4)

    return extracted_data

if __name__ == '__main__':
    pool = mp.Pool(mp.cpu_count())

    resumes = []
    data = []
    for root, directories, filenames in os.walk('D:\\resumes'):
        for filename in filenames:
            file = os.path.join(root, filename)
            resumes.append(file)

    results = [pool.apply_async(resume_result_wrapper, args=(x,)) for x in resumes]

    results = [p.get() for p in results]

    pprint.pprint(results)

# Constants and data for processing resumes
NAME_PATTERN      = [{'POS': 'PROPN'}, {'POS': 'PROPN'}]

# Education (Upper Case Mandatory)
EDUCATION         = [
                    'BE','B.E.', 'B.E', 'BS', 'B.S', 'ME', 'M.E', 'M.E.', 'MS', 'M.S', 'BTECH', 'MTECH',
                    'SSC', 'HSC', 'CBSE', 'ICSE', 'X', 'XII'
                    ]

NOT_ALPHA_NUMERIC = r'[^a-zA-Z\d]'

NUMBER            = r'\d+'

# For finding date ranges
MONTHS_SHORT      = r'(jan)|(feb)|(mar)|(apr)|(may)|(jun)|(jul)|(aug)|(sep)|(oct)|(nov)|(dec)'
MONTHS_LONG       = r'(january)|(february)|(march)|(april)|(may)|(june)|(july)|(august)|(september)|(october)|(november)|(december)'
MONTH             = r'(' + MONTHS_SHORT + r'|' + MONTHS_LONG + r')'
YEAR              = r'(((20|19)(\d{2})))'

STOPWORDS         = set(stopwords.words('english'))

RESUME_SECTIONS = [
                    'accomplishments',
                    'experience',
                    'education',
                    'interests',
                    'projects',
                    'professional experience',
                    'publications',
                    'skills',
                ]

COMPETENCIES = {
    'teamwork': [
        'supervised',
        'facilitated',
        'planned',
        'plan',
        'served',
        'serve',
        'project lead',
        'managing',
        'managed',
        'lead ',
        'project team',
        'team',
        'conducted',
        'worked',
        'gathered',
        'organized',
        'mentored',
        'assist',
        'review',
        'help',
        'involve',
        'share',
        'support',
        'coordinate',
        'cooperate',
        'contributed'
    ],
    'communication': [
        'addressed',
        'collaborated',
        'conveyed',
        'enlivened',
        'instructed',
        'performed',
        'presented',
        'spoke',
        'trained',
        'author',
        'communicate',
        'define',
        'influence',
        'negotiated',
        'outline',
        'proposed',
        'persuaded',
        'edit',
        'interviewed',
        'summarize',
        'translate',
        'write',
        'wrote',
        'project plan',
        'clear communication',
        'written communication',
        'verbal communication',
        'communication skills'
    ],
    'analytical': [
        'analyzed',
        'assembled',
        'assessed',
        'audited',
        'budgeted',
        'calculated',
        'computed',
        'conceived',
        'concluded',
        'consulted',
        'critiqued',
        'derived',
        'developed',
        'evaluated',
        'forecasted',
        'inferred',
        'interpreted',
        'investigated',
        'judged',
        'measured',
        'modeled',
        'quantified',
        'researched',
        'scrutinized',
        'studied',
        'surveyed',
        'systematized',
        'validated',
        'analysis',
        'analytical skills',
        'problem-solving',
        'problem-solving skills'
    ],
    'organizational': [
        'arranged',
        'cataloged',
        'catalogued',
        'classified',
        'collected',
        'compiled',
        'dispatched',
        'executed',
        'implemented',
        'monitored',
        'operated',
        'organized',
        'prepared',
        'processed',
        'scheduled',
        'systematized',
        'organize',
        'organizational skills',
        'organizing',
        'planning'
    ],
    'technical': [
        'administered',
        'built',
        'constructed',
        'designed',
        'developed',
        'engineered',
        'fabricated',
        'installed',
        'maintained',
        'operated',
        'overhauled',
        'programmed',
        'regulated',
        'repaired',
        'troubleshot',
        'troubleshoot',
        'technical skills',
        'programming skills',
        'coding',
        'developing'
    ],
    'leadership': [
        'directed',
        'delegated',
        'empowered',
        'facilitated',
        'guided',
        'hired',
        'hosted',
        'launched',
        'motivated',
        'oversaw',
        'presided',
        'recruited',
        'supervised',
        'leadership skills',
        'leadership experience',
        'leading teams',
        'team leadership',
        'managing teams',
        'team management',
        'managing projects',
        'project management'
    ],
    'creative': [
        'conceptualized',
        'created',
        'designed',
        'fashioned',
        'illustrated',
        'improved',
        'increased',
        'innovated',
        'initiated',
        'integrated',
        'revamped',
        'transformed',
        'creativity',
        'creative thinking',
        'design skills',
        'innovation',
        'innovative solutions'
    ],
    'problem solving': [
        'addressed',
        'analyzed',
        'clarified',
        'conceived',
        'conceptualized',
        'diagnosed',
        'formulated',
        'identified',
        'resolved',
        'solved',
        'troubleshoot',
        'problem-solving',
        'problem-solving skills'
    ],
    'customer focus': [
        'attended',
        'consolidated',
        'customized',
        'delivered',
        'demonstrated',
        'ensured',
        'exceeded',
        'facilitated',
        'fulfilled',
        'generated',
        'insured',
        'interacted',
        'maintained',
        'provided',
        'responded',
        'served',
        'serviced',
        'supported',
        'customer focus',
        'customer service',
        'customer satisfaction'
    ]
}

MEASURABLE_RESULTS = {
    'revenue growth': [
        'increased revenue',
        'boosted sales',
        'expanded market share',
        'generated profits',
        'accelerated growth',
        'maximized profits',
        'achieved revenue targets',
        'met sales goals',
        'exceeded sales targets'
    ],
    'cost reduction': [
        'decreased expenses',
        'lowered costs',
        'saved money',
        'cut overhead',
        'eliminated waste',
        'optimized resources',
        'improved efficiency',
        'streamlined operations'
    ],
    'productivity improvement': [
        'enhanced productivity',
        'improved workflow',
        'increased output',
        'boosted efficiency',
        'streamlined processes',
        'optimized performance',
        'reduced downtime',
        'improved turnaround times'
    ],
    'customer satisfaction': [
        'enhanced customer experience',
        'improved client relations',
        'increased customer retention',
        'resolved customer issues',
        'addressed customer concerns',
        'boosted customer loyalty',
        'exceeded customer expectations',
        'enhanced service levels'
    ],
    'project delivery': [
        'delivered projects on time',
        'met project deadlines',
        'achieved project milestones',
        'completed projects within budget',
        'ensured project quality',
        'managed project risks',
        'implemented project improvements',
        'executed project plans'
    ],
    'team performance': [
        'boosted team morale',
        'improved team collaboration',
        'facilitated team communication',
        'mentored team members',
        'developed team skills',
        'optimized team processes',
        'aligned team objectives',
        'enhanced team productivity'
    ]
}
