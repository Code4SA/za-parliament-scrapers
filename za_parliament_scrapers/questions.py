import os
import re
import datetime

import mammoth


def strip_dict(d):
    """
    Return a new dictionary, like d, but with any string value stripped

    >>> d = {'a': ' foo   ', 'b': 3, 'c': '   bar'}
    >>> result = strip_dict(d)
    >>> type(result)
    <type 'dict'>
    >>> sorted(result.items())
    [('a', 'foo'), ('b', 3), ('c', 'bar')]
    """
    return dict((k, v.strip() if hasattr(v, 'strip') else v) for k, v in d.iteritems())


class QuestionAnswerScraper(object):
    """ Parses answer documents from parliament.
    """

    DOCUMENT_NAME_REGEX = re.compile(r'^R(?P<house>[NC])(?:O(?P<president>D?P)?(?P<oral_number>\d+))?(?:W(?P<written_number>\d+))?-+(?P<date_string>\d{6})$')
    BAR_REGEX = re.compile(r'^_+$', re.MULTILINE)

    QUESTION_RE = re.compile(
        ur"""
          (?P<intro>
            (?:(?P<number1>\d+)\.?\s+)?         # Question number
            [-a-zA-z]+\s+(?P<askedby>[-\w\s]+?) # Name of question asker, dropping the title
            \s*\((?P<party>[-\w\s]+)\)?
            \s+to\s+ask\s+the\s+
            (?P<questionto>[-\w\s(),:.]+)[:.]
            [-\u2013\w\s(),\[\]/]*?
          )                                     # Intro
          (?P<translated>\u2020)?\s*(</b>|\n)\s*
          (?P<question>.*?)\s*                  # The question itself.
          (?:(?P<identifier>(?P<house>[NC])(?P<answer_type>[WO])(?P<id_number>\d+)E)|\n|$) # Number 2
        """,
        re.UNICODE | re.VERBOSE | re.DOTALL)

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
            raise ValueError("bad document name %s" % name)
        document_data = match.groupdict()

        document_data['code'] = os.path.splitext(name)[0]

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
        except:
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
        >>> qn = u'144. Mr D B Feldman (COPE-Gauteng) to ask the Minister of Defence and Military Veterans: </b>Whether the deployment of the SA National Defence Force soldiers to the Central African Republic and the Democratic Republic of Congo is in line with our international policy with regard to (a) upholding international peace, (b) the promotion of constitutional democracy and (c) the respect for parliamentary democracy; if not, why not; if so, what are the (i) policies which underpin South African foreign policy and (ii) further relevant details? CW187E'
        >>> match = QuestionAnswerScraper.QUESTION_RE.match(qn)
        >>> match.groups()
        (u'144. Mr D B Feldman (COPE-Gauteng) to ask the Minister of Defence and Military Veterans:', u'144', u'D B Feldman', u'COPE-Gauteng', u'Minister of Defence and Military Veterans', None, u'</b>', u'Whether the deployment of the SA National Defence Force soldiers to the Central African Republic and the Democratic Republic of Congo is in line with our international policy with regard to (a) upholding international peace, (b) the promotion of constitutional democracy and (c) the respect for parliamentary democracy; if not, why not; if so, what are the (i) policies which underpin South African foreign policy and (ii) further relevant details?', u'CW187E', u'C', u'W', u'187')

        # Shows the need for \u2013 (en-dash) and / (in the date) in latter part of the intro
        >>> qn = u'409. Mr M J R de Villiers (DA-WC) to ask the Minister of Public Works: [215] (Interdepartmental transfer \u2013 01/11) </b>(a) What were the reasons for a cut back on the allocation for the Expanded Public Works Programme to municipalities in the 2013-14 financial year and (b) what effect will this have on (i) job creation and (ii) service delivery? CW603E'
        >>> match = QuestionAnswerScraper.QUESTION_RE.match(qn)
        >>> match.groups()
        (u'409. Mr M J R de Villiers (DA-WC) to ask the Minister of Public Works: [215] (Interdepartmental transfer \u2013 01/11)', u'409', u'M J R de Villiers', u'DA-WC', u'Minister of Public Works', None, u'</b>', u'(a) What were the reasons for a cut back on the allocation for the Expanded Public Works Programme to municipalities in the 2013-14 financial year and (b) what effect will this have on (i) job creation and (ii) service delivery?', u'CW603E', u'C', u'W', u'603')

        # Cope with missing close bracket
        >>> qn = u'1517. Mr W P Doman (DA to ask the Minister of Cooperative Governance and Traditional Affairs:</b> Which approximately 31 municipalities experienced service delivery protests as referred to in his reply to oral question 57 on 10 September 2009? NW1922E'
        >>> match = QuestionAnswerScraper.QUESTION_RE.match(qn)
        >>> match.groups()
        (u'1517. Mr W P Doman (DA to ask the Minister of Cooperative Governance and Traditional Affairs:', u'1517', u'W P Doman', u'DA', u'Minister of Cooperative Governance and Traditional Affairs', None, u'</b>', u'Which approximately 31 municipalities experienced service delivery protests as referred to in his reply to oral question 57 on 10 September 2009?', u'NW1922E', u'N', u'W', u'1922')

        # Check we cope with no space before party in parentheses
        >>> qn = u'1569. Mr M Swart(DA) to ask the Minister of Finance: </b>Test question? NW1975E'
        >>> match = QuestionAnswerScraper.QUESTION_RE.match(qn)
        >>> match.groups()
        (u'1569. Mr M Swart(DA) to ask the Minister of Finance:', u'1569', u'M Swart', u'DA', u'Minister of Finance', None, u'</b>', u'Test question?', u'NW1975E', u'N', u'W', u'1975')

        # Check we cope with a dot after the askee instead of a colon.
        >>> qn = u'1875. Mr G G Hill-Lewis (DA) to ask the Minister in the Presidency. National Planning </b>Test question? NW2224E'
        >>> match = QuestionAnswerScraper.QUESTION_RE.match(qn)
        >>> match.groups()
        (u'1875. Mr G G Hill-Lewis (DA) to ask the Minister in the Presidency. National Planning', u'1875', u'G G Hill-Lewis', u'DA', u'Minister in the Presidency', None, u'</b>', u'Test question?', u'NW2224E', u'N', u'W', u'2224')

        # Check we cope without a question number
        >>> qn = u'Mr AM Matlhoko (EFF) to ask the Minister of Cooperative Governance and Traditional Affairs: </b>Whether he has an immediate plan to assist?'
        >>> match = QuestionAnswerScraper.QUESTION_RE.match(qn)
        >>> match.groups()
        (u'Mr AM Matlhoko (EFF) to ask the Minister of Cooperative Governance and Traditional Affairs:', None, u'AM Matlhoko', u'EFF', u'Minister of Cooperative Governance and Traditional Affairs', None, u'</b>', u'Whether he has an immediate plan to assist?', None, None, None, None)
        """
        questions = []

        for match in self.QUESTION_RE.finditer(text):
            match_dict = match.groupdict()

            answer_type = match_dict[u'answer_type']
            number1 = match_dict.pop('number1')

            if answer_type == 'O':
                if re.search('(?i)to ask the Deputy President', match_dict['intro']):
                    match_dict[u'dp_number'] = number1
                elif re.search('(?i)to ask the President', match_dict['intro']):
                    match_dict[u'president_number'] = number1
                else:
                    match_dict[u'oral_number'] = number1
            elif answer_type == 'W':
                match_dict[u'written_number'] = number1

            match_dict[u'translated'] = bool(match_dict[u'translated'])
            match_dict[u'questionto'] = match_dict[u'questionto'].replace(':', '')

            # Party isn't actually stored in the question, so drop it before saving
            # Perhaps we can eventually use it to make sure we have the right person.
            # (and to tidy up the missing parenthesis.)
            match_dict.pop(u'party')

            questions.append(match_dict)

        return questions

    def extract_answer_from_html(self, html):
        """ Extract the answer portion from a chunk of HTML
        """
        # TODO: implement
        return html
