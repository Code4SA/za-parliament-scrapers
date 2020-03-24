from builtins import str
from builtins import object
import os
import re
import datetime

import mammoth
import bs4


def strip_dict(d):
    """
    Return a new dictionary, like d, but with any string value stripped

    >>> d = {'a': ' foo   ', 'b': 3, 'c': '   bar'}
    >>> result = strip_dict(d)
    >>> type(result)
    <class 'dict'>
    >>> sorted(result.items())
    [('a', 'foo'), ('b', 3), ('c', 'bar')]
    """
    return dict((k, v.strip() if hasattr(v, 'strip') else v) for k, v in d.items())


class QuestionAnswerScraper(object):
    """ Parses answer documents from parliament.
    """

    DOCUMENT_NAME_REGEX = re.compile(r'^R(?P<house>[NC])(?:O(?P<president>D?P)?(?P<oral_number>\d+))?(?:W(?P<written_number>\d+))?-+(?P<date_string>(\d{6}|\d{4}-\d{2}-\d{2}))$')
    BAR_REGEX = re.compile(r'^_+$', re.MULTILINE)

    QUESTION_RE = re.compile(
        r"""
          (?P<intro>
            (?:(?P<number1>\d+)\.?\s+)?         # Question number
            (?P<askedby>[-\w\s]+?)              # Name of question asker
            \s*\((?P<party>[-\w\s]+)\)?
            \s+(?:to\s+ask|asked)\s+the\s+
            (?P<questionto>[-\w\s(),:.]+)[:.]
            [-\u2013\w\s(),\[\]/]*?
          )                                     # Intro
          (?P<translated>\u2020)?\s*(</b>|\n)\s*
          (?P<question>.*?)\s*                  # The question itself.
          (?:(?P<identifier>(?P<house>[NC])(?P<answer_type>[WO])(?P<id_number>\d+)E)|\n|$) # Number 2
        """,
        re.UNICODE | re.VERBOSE | re.DOTALL)

    REPLY_RE = re.compile(r'^reply:?', re.IGNORECASE | re.MULTILINE)

    def details_from_name(self, name):
        """ Return a map with details from the document name:

        * :code +str+: document code
        * :date +datetime+: question date
        * :year +int+: year portion of the date
        * :type +str+: 'O' for oral, or 'W' for written
        * :house +str+: 'N' for NA, C for NCOP
        * :oral_number +str+: oral number (may be null)
        * :written_number +str+: written number (may be null)
        * :president_number +str+: president question number if this is question for the president (may be null)
        * :deputy_president_number +str+: deputy president question number if this is question for the deputy president (may be null)
        """
        match = self.DOCUMENT_NAME_REGEX.match(name)
        if not match:
            r'^R(?P<house>[NC])(?:O(?P<president>D?P)?(?P<oral_number>\d+))?(?:W(?P<written_number>\d+))?-+(?P<date_string>\d{6})$'
            message = (
                ("Bad document name '%s'. " % name) +
                "Document name needs to be in the form: 'R<house><O or W><number>-<last two digits of year><two-digit month><two-digit day>'. " +
                "For example, 'RNW1143-131127.docx' or 'RNW190-200303.docx'."
            )
            raise ValueError(message)
        document_data = match.groupdict()

        code = os.path.splitext(name)[0].split('-', 1)[0]
        # remove starting 'R'
        document_data['code'] = code[1:]

        # The President and vice Deputy President have their own
        # oral question sequences.
        president = document_data.pop('president')
        if president == 'P':
            document_data['president_number'] = document_data.pop('oral_number')
        if president == 'DP':
            document_data['deputy_president_number'] = document_data.pop('oral_number')

        if document_data.get('oral_number'):
            document_data['type'] = 'O'
        elif document_data.get('written_number'):
            document_data['type'] = 'W'
        else:
            document_data['type'] = None

        date = document_data.pop('date_string')
        try:
            document_data['date'] = datetime.datetime.strptime(date, '%y%m%d').date()
        except Exception:
            try:
                document_data['date'] = datetime.datetime.strptime(date, '%Y-%m-%d').date()
            except Exception:
                raise ValueError("problem converting date %s" % date)
        document_data['year'] = document_data['date'].year

        document_data = strip_dict(document_data)
        return document_data

    def extract_content_from_document(self, filename):
        """ Extract content from a .docx file and return a (text, html) tuple.
        """
        ext = os.path.splitext(filename)[1]
        if ext == '.docx':
            with open(filename, "rb") as f:
                html = mammoth.convert_to_html(f).value
                text = mammoth.extract_raw_text(f).value
            return (text, html)
        else:
            # TODO: handle .doc
            raise ValueError("Can only handle .docx files, but got %s" % ext)

    def extract_questions_from_text(self, text):
        """ Find and return a list of questions in this text.

        Returns a list of dicts:

        * :answer_type +str+: 'W' for written or 'O' for oral
        * :askedby +str+: initial and name of person doing the asking
        * :house +str+: house, N for NA, C for NCOP
        * :id_number +str+: the id number of this question
        * :identifier +str+: the identifier of this question
        * :intro +str+: the preamble/introduction to this question
        * :question +str+: the actual text of the question
        * :questionto +str+: who the question is being asked of, generally a Minister
        * :written_number +str+: the written number of the question

        # Checks for QUESTION_RE

        # Shows the need for - in the party
        >>> qn = '144. Mr D B Feldman (COPE-Gauteng) to ask the Minister of Defence and Military Veterans: </b>Whether the deployment of the SA National Defence Force soldiers to the Central African Republic and the Democratic Republic of Congo is in line with our international policy with regard to (a) upholding international peace, (b) the promotion of constitutional democracy and (c) the respect for parliamentary democracy; if not, why not; if so, what are the (i) policies which underpin South African foreign policy and (ii) further relevant details? CW187E'
        >>> match = QuestionAnswerScraper.QUESTION_RE.match(qn)
        >>> match.groups()
        ('144. Mr D B Feldman (COPE-Gauteng) to ask the Minister of Defence and Military Veterans:', '144', 'Mr D B Feldman', 'COPE-Gauteng', 'Minister of Defence and Military Veterans', None, '</b>', 'Whether the deployment of the SA National Defence Force soldiers to the Central African Republic and the Democratic Republic of Congo is in line with our international policy with regard to (a) upholding international peace, (b) the promotion of constitutional democracy and (c) the respect for parliamentary democracy; if not, why not; if so, what are the (i) policies which underpin South African foreign policy and (ii) further relevant details?', 'CW187E', 'C', 'W', '187')

        # Shows the need for \u2013 (en-dash) and / (in the date) in latter part of the intro
        >>> qn = '409. Mr M J R de Villiers (DA-WC) to ask the Minister of Public Works: [215] (Interdepartmental transfer \u2013 01/11) </b>(a) What were the reasons for a cut back on the allocation for the Expanded Public Works Programme to municipalities in the 2013-14 financial year and (b) what effect will this have on (i) job creation and (ii) service delivery? CW603E'
        >>> match = QuestionAnswerScraper.QUESTION_RE.match(qn)
        >>> match.groups()
        ('409. Mr M J R de Villiers (DA-WC) to ask the Minister of Public Works: [215] (Interdepartmental transfer \u2013 01/11)', '409', 'Mr M J R de Villiers', 'DA-WC', 'Minister of Public Works', None, '</b>', '(a) What were the reasons for a cut back on the allocation for the Expanded Public Works Programme to municipalities in the 2013-14 financial year and (b) what effect will this have on (i) job creation and (ii) service delivery?', 'CW603E', 'C', 'W', '603')

        # Cope with missing close bracket
        >>> qn = '1517. Mr W P Doman (DA to ask the Minister of Cooperative Governance and Traditional Affairs:</b> Which approximately 31 municipalities experienced service delivery protests as referred to in his reply to oral question 57 on 10 September 2009? NW1922E'
        >>> match = QuestionAnswerScraper.QUESTION_RE.match(qn)
        >>> match.groups()
        ('1517. Mr W P Doman (DA to ask the Minister of Cooperative Governance and Traditional Affairs:', '1517', 'Mr W P Doman', 'DA', 'Minister of Cooperative Governance and Traditional Affairs', None, '</b>', 'Which approximately 31 municipalities experienced service delivery protests as referred to in his reply to oral question 57 on 10 September 2009?', 'NW1922E', 'N', 'W', '1922')

        # Check we cope with no space before party in parentheses
        >>> qn = '1569. Mr M Swart(DA) to ask the Minister of Finance: </b>Test question? NW1975E'
        >>> match = QuestionAnswerScraper.QUESTION_RE.match(qn)
        >>> match.groups()
        ('1569. Mr M Swart(DA) to ask the Minister of Finance:', '1569', 'Mr M Swart', 'DA', 'Minister of Finance', None, '</b>', 'Test question?', 'NW1975E', 'N', 'W', '1975')

        # Check we cope with a dot after the askee instead of a colon.
        >>> qn = '1875. Mr G G Hill-Lewis (DA) to ask the Minister in the Presidency. National Planning </b>Test question? NW2224E'
        >>> match = QuestionAnswerScraper.QUESTION_RE.match(qn)
        >>> match.groups()
        ('1875. Mr G G Hill-Lewis (DA) to ask the Minister in the Presidency. National Planning', '1875', 'Mr G G Hill-Lewis', 'DA', 'Minister in the Presidency', None, '</b>', 'Test question?', 'NW2224E', 'N', 'W', '2224')

        # Check we cope without a question number
        >>> qn = 'Mr AM Matlhoko (EFF) to ask the Minister of Cooperative Governance and Traditional Affairs: </b>Whether he has an immediate plan to assist?'
        >>> match = QuestionAnswerScraper.QUESTION_RE.match(qn)
        >>> match.groups()
        ('Mr AM Matlhoko (EFF) to ask the Minister of Cooperative Governance and Traditional Affairs:', None, 'Mr AM Matlhoko', 'EFF', 'Minister of Cooperative Governance and Traditional Affairs', None, '</b>', 'Whether he has an immediate plan to assist?', None, None, None, None)
        """
        questions = []

        for match in self.QUESTION_RE.finditer(text):
            match_dict = match.groupdict()

            answer_type = match_dict['answer_type']
            number1 = match_dict.pop('number1')

            if answer_type == 'O':
                if re.search('(?i)to ask the Deputy President', match_dict['intro']):
                    match_dict['dp_number'] = number1
                elif re.search('(?i)to ask the President', match_dict['intro']):
                    match_dict['president_number'] = number1
                else:
                    match_dict['oral_number'] = number1
            elif answer_type == 'W':
                match_dict['written_number'] = number1

            match_dict['translated'] = bool(match_dict['translated'])
            match_dict['questionto'] = match_dict['questionto'].replace(':', '')
            match_dict['questionto'] = self.correct_minister_title(match_dict['questionto'])

            questions.append(match_dict)

        return questions

    def correct_minister_title(self, minister_title):
        corrections = {
            "Minister President of the Republic":
                "President of the Republic",
            "Minister in The Presidency National Planning Commission":
                "Minister in the Presidency: National Planning Commission",
            "Minister in the Presidency National Planning Commission":
                "Minister in the Presidency: National Planning Commission",
            "Questions asked to the Minister in The Presidency National Planning Commission":
                "Minister in the Presidency: National Planning Commission",
            "Minister in the Presidency. National Planning Commission":
                "Minister in the Presidency: National Planning Commission",
            "Minister in The Presidency": "Minister in the Presidency",
            "Minister in The Presidency Performance Monitoring and Evaluation as well as Administration in the Presidency":
                "Minister in the Presidency: Performance Monitoring and Evaluation as well as Administration in the in the Presidency",
            "Minister in the Presidency Performance , Monitoring and Evaluation as well as Administration in the Presidency":
                "Minister in the Presidency: Performance Monitoring and Evaluation as well as Administration in the in the Presidency",
            "Minister in the Presidency Performance Management and Evaluation as well as Administration in the Presidency":
                "Minister in the Presidency: Performance Monitoring and Evaluation as well as Administration in the in the Presidency",
            "Minister in the Presidency Performance Monitoring and Administration in the Presidency":
                "Minister in the Presidency: Performance Monitoring and Evaluation as well as Administration in the in the Presidency",
            "Minister in the Presidency Performance Monitoring and Evaluation as well Administration in the Presidency":
                "Minister in the Presidency: Performance Monitoring and Evaluation as well as Administration in the in the Presidency",
            "Minister in the Presidency Performance Monitoring and Evaluation as well as Administration":
                "Minister in the Presidency: Performance Monitoring and Evaluation as well as Administration in the in the Presidency",
            "Minister in the Presidency Performance Monitoring and Evaluation as well as Administration in the Presidency":
                "Minister in the Presidency: Performance Monitoring and Evaluation as well as Administration in the in the Presidency",
            "Minister in the Presidency, Performance Monitoring and Evaluation as well as Administration in the Presidency":
                "Minister in the Presidency: Performance Monitoring and Evaluation as well as Administration in the in the Presidency",
            "Minister in the PresidencyPerformance Monitoring and Evaluation as well as Administration in the Presidency":
                "Minister in the Presidency: Performance Monitoring and Evaluation as well as Administration in the in the Presidency",
            "Minister of Women in The Presidency":
                "Minister of Women in the Presidency",
            "Minister of Agriculture, Fisheries and Forestry":
                "Minister of Agriculture, Forestry and Fisheries",
            "Minister of Minister of Agriculture, Forestry and Fisheries":
                "Minister of Agriculture, Forestry and Fisheries",
            "Minister of Agriculture, Foresty and Fisheries":
                "Minister of Agriculture, Forestry and Fisheries",
            "Minister of Minister of Basic Education":
                "Minister of Basic Education",
            "Minister of Basic Transport":
                "Minister of Transport",
            "Minister of Communication":
                "Minister of Communications",
            "Minister of Cooperative Government and Traditional Affairs":
                "Minister of Cooperative Governance and Traditional Affairs",
            "Minister of Defence and MilitaryVeterans":
                "Minister of Defence and Military Veterans",
            "Minister of Heath":
                "Minister of Health",
            "Minister of Higher Education":
                "Minister of Higher Education and Training",
            "Minister of Minister of International Relations and Cooperation":
                "Minister of International Relations and Cooperation",
            "Minister of Justice and Constitutional development":
                "Minister of Justice and Constitutional Development",
            "Minister of Justice and Constitutional Developoment":
                "Minister of Justice and Constitutional Development",
            "Minister of Mining":
                "Minister of Mineral Resources",
            "Minister of Public Enterprise":
                "Minister of Public Enterprises",
            "Minister of the Public Service and Administration":
                "Minister of Public Service and Administration",
            "Minister of Public Work":
                "Minister of Public Works",
            "Minister of Rural Development and Land Affairs":
                "Minister of Rural Development and Land Reform",
            "Minister of Minister of Rural Development and Land Reform":
                "Minister of Rural Development and Land Reform",
            "Minister of Rural Development and Land Reform Question":
                "Minister of Rural Development and Land Reform",
            "Minister of Rural Development and Land Reforms":
                "Minister of Rural Development and Land Reform",
            "Minister of Rural Development and Land reform":
                "Minister of Rural Development and Land Reform",
            "Minister of Sport and Recreaton":
                "Minister of Sport and Recreation",
            "Minister of Sports and Recreation":
                "Minister of Sport and Recreation",
            "Minister of Water and Enviromental Affairs":
                "Minister of Water and Environmental Affairs",
            "Minister of Women, Children andPeople with Disabilities":
                "Minister of Women, Children and People with Disabilities",
            "Minister of Women, Children en People with Disabilities":
                "Minister of Women, Children and People with Disabilities",
            "Minister of Women, Children and Persons with Disabilities":
                "Minister of Women, Children and People with Disabilities",
            "Minister of Women, Youth, Children and People with Disabilities":
                "Minister of Women, Children and People with Disabilities",
            "Higher Education and Training":
                "Minister of Higher Education and Training",
            "Minister Basic Education":
                "Minister of Basic Education",
            "Minister Health":
                "Minister of Health",
            "Minister Labour":
                "Minister of Labour",
            "Minister Public Enterprises":
                "Minister of Public Enterprises",
            "Minister Rural Development and Land Reform":
                "Minister of Rural Development and Land Reform",
            "Minister Science and Technology":
                "Minister of Science and Technology",
            "Minister Social Development":
                "Minister of Social Development",
            "Minister Trade and Industry":
                "Minister of Trade and Industry",
            "Minister in Communications":
                "Minister of Communications",
            "Minister of Arts and Culture 102. Mr D J Stubbe (DA) to ask the Minister of Arts and Culture":
                "Minister of Arts and Culture",
        }

        # the most common error is the inclusion of a hyphen (presumably due to
        # line breaks in the original document). No ministers have a hyphen in
        # their title so we can do a simple replace.
        minister_title = minister_title.replace('-', '')

        # correct mispellings of 'minister'
        minister_title = minister_title.replace('Minster', 'Minister')

        # it is also common for a minister to be labelled "minister for" instead
        # of "minister of"
        minister_title = minister_title.replace('Minister for', 'Minister of')

        # remove any whitespace
        minister_title = minister_title.strip()

        # apply manual corrections
        minister_title = corrections.get(minister_title, minister_title)

        return minister_title

    def extract_answer_from_html(self, html):
        """ Extract the answer portion from a chunk of HTML

        We look for a P tag with text of 'REPLY' and return strip everything before that.
        """
        if html.strip().startswith('<'):
            soup = bs4.BeautifulSoup(html, 'html.parser')

            for p in soup.find_all('p'):
                if self.REPLY_RE.match(p.text):
                    for el in list(p.previous_elements):
                        if isinstance(el, bs4.element.Tag):
                            el.decompose()
                    p.decompose()
                    break

            return str(soup)
        else:
            # plain text
            match = self.REPLY_RE.search(html)
            if match:
                return html[match.end(0):]

        return html
