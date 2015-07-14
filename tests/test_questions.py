import unittest
import datetime

from nose.tools import *  # noqa

from za_parliament_scrapers.questions import QuestionAnswerScraper


class QuestionAnswerScraperTest(unittest.TestCase):
    def setUp(self):
        self.scraper = QuestionAnswerScraper()

    def test_simple(self):
        assert_equal(self.scraper.details_from_name("RNW1143-131127"), {
            'code': 'RNW1143-131127',
            'date': datetime.date(2013, 11, 27),
            'house': 'N',
            'oral_number': None,
            'type': None,
            'written_number': '1143',
            'year': 2013,
        })

    def test_extract_from_document(self):
        text, html = self.scraper.extract_content_from_document("tests/fixtures/RNW126-150302.docx")

        assert_equal(u'36/1/4/1/201500010\n\nNATIONAL ASSEMBLY\n\n\n\nFOR WRITTEN REPLY\n\n\n\nQUESTION 126\n\n\n\nDATE OF PUBLICATION IN INTERNAL QUESTION PAPER: 12 FEBRUARY 2015 \n\n(INTERNAL QUESTION PAPER NO 1-2015)\n\n\n\n126. Ms D Kohler (DA) to ask the Minister of Police:\n\nWith reference to the reply to question 228 on 18 March 2014, (a) how much discontinued ammunition is still in circulation in the SA Police Service in each province and (b) what action is to be taken to remove this ammunition from use?\n\nNW131E\n\nREPLY:\n\nTotal discontinued ammunition still in circulation in the SA Police Service:\n\n\n\nPROVINCE\n\nPREVIOUS QUANTITY\n\nCURRENT QUANTITY\n\nWestern Cape\n\n68,542\n\n74,627\n\nEastern Cape\n\n538,937\n\n594,806\n\nNorthern Cape\n\n104,459\n\n38,326\n\nFree State\n\n410,981\n\n135,065\n\nKwaZulu-Natal\n\n523,978\n\n228,164\n\nNorth West\n\n233,850\n\n24,120\n\nMpumalanga\n\n296,479\n\n92,676\n\nLimpopo\n\n35,080\n\n10,446\n\nGauteng\n\n71,764\n\n63,209\n\nHead Office Divisions\n\n2,061,456\n\n1,704,286\n\nTOTAL:  \n\n4,345,526\n\n2,965,725\n\nThis ammunition may only be used for training purposes. However, this ammunition is still in use by Specialized Units within the SAPS for training, ballistic testing of firearms and IBIS test firing purposes. \n\nAn instruction to withdraw all such ammunition was issued from the Divisional Commissioner, Supply Chain Management on 12 September 2006, which also instructed that such ammunition may not be issued any longer as from this date.\n\nRecently another instruction in regard was issued by the Divisional Commissioner, Supply Chain Management to all Provisional Commissioners and Divisional Commissioners to immediately withdraw all non-standard, obsolete and unserviceable ammunition not in use, from their respective provinces and divisions.\n\nAll non-standard, obsolete and unserviceable ammunition is being sent on a continuous basis to the Ammunition Store at the Division Supply Chain Management for disposal and this is being monitored to ensure compliance.\n\n\n\n\n\n\n\n\n\n', text)

        assert_equal(u'<p><strong>36/1/4/1/2015</strong><strong>00010</strong></p><p><strong>NATIONAL ASSEMBLY</strong></p><p><strong>FOR WRITTEN REPLY</strong></p><p><strong>QUESTION 126</strong></p><p><strong>DATE OF PUBLICATION IN INTERNAL QUESTION PAPER</strong><strong>: 12 FEBRUARY 2015</strong><strong> </strong></p><p><strong>(INTERNAL QUESTION PAPER NO </strong><strong>1</strong><strong>-2015)</strong></p><p><strong>126. </strong><strong>Ms D Kohler (DA) to </strong><strong>ask</strong><strong> the Minister of Police:</strong></p><p>With reference to the reply to question 228 on 18 March 2014, (a) how much discontinued ammunition is still in circulation in the SA Police Service in each province and (b) what action is to be taken to remove this ammunition from use?</p><p>NW131E</p><p><strong>REPLY:</strong></p><ol><li>Total discontinued ammunition still in circulation in the SA Police Service:</li></ol><table><tr><td><p><strong>PROVINCE</strong></p></td><td><p><strong>PREVIOUS QUANTITY</strong></p></td><td><p><strong>CURRENT QUANTITY</strong></p></td></tr><tr><td><p>Western Cape</p></td><td><p>68,542</p></td><td><p>74,627</p></td></tr><tr><td><p>Eastern Cape</p></td><td><p>538,937</p></td><td><p>594,806</p></td></tr><tr><td><p>Northern Cape</p></td><td><p>104,459</p></td><td><p>38,326</p></td></tr><tr><td><p>Free State</p></td><td><p>410,981</p></td><td><p>135,065</p></td></tr><tr><td><p>KwaZulu-Natal</p></td><td><p>523,978</p></td><td><p>228,164</p></td></tr><tr><td><p>North West</p></td><td><p>233,850</p></td><td><p>24,120</p></td></tr><tr><td><p>Mpumalanga</p></td><td><p>296,479</p></td><td><p>92,676</p></td></tr><tr><td><p>Limpopo</p></td><td><p>35,080</p></td><td><p>10,446</p></td></tr><tr><td><p>Gauteng</p></td><td><p>71,764</p></td><td><p>63,209</p></td></tr><tr><td><p>Head Office Divisions</p></td><td><p>2,061,456</p></td><td><p>1,704,286</p></td></tr><tr><td><p><strong>TOTAL:  </strong></p></td><td><p><strong>4,345,526</strong></p></td><td><p><strong>2,965,725</strong></p></td></tr></table><p>This ammunition may only be used for training purposes. However, this ammunition is still in use by Specialized Units within the SAPS for training, ballistic testing of firearms and IBIS test firing purposes. </p><ol><li>An instruction to withdraw all such ammunition was issued from the Divisional Commissioner, Supply Chain Management on 12 September 2006, which also instructed that such ammunition may not be issued any longer as from this date.</li></ol><p>Recently another instruction in regard was issued by the Divisional Commissioner, Supply Chain Management to all Provisional Commissioners and Divisional Commissioners to immediately withdraw all non-standard, obsolete and unserviceable ammunition not in use, from their respective provinces and divisions.</p><p>All non-standard, obsolete and unserviceable ammunition is being sent on a continuous basis to the Ammunition Store at the Division Supply Chain Management for disposal and this is being monitored to ensure compliance.</p>', html)
