
import unittest

from nose.tools import assert_raises

from sasparse import SASDoc
from sasparse.parse import ParseNode, TopLevel


class TestParseCorpus_CMS_HCC2017(unittest.TestCase):

    _multiprocess_can_split_ = True

    '''
    def test_parseerror_child(self):
        assert_raises(Exception, SASDoc.from_string, '1 2 3"')
    '''

    def test_parse_select(self):
        SASDoc.from_string('''
SELECT;
WHEN(&SEX='2') _AGESEX  = 1;
OTHERWISE;
END;
        ''')

    def test_parse_AGESEXV2(self):
        SASDoc.from_file('corpus/cms/CMS-HCC software V2216.79.O2 2/AGESEXV2.TXT')

    def test_parse_SCOREVAR(self):
        SASDoc.from_file('corpus/cms/CMS-HCC software V2216.79.O2 2/SCOREVAR.TXT')

    def test_parse_V221602M(self):
        SASDoc.from_file('corpus/cms/CMS-HCC software V2216.79.O2 2/V2216O2M.TXT')

    def test_parse_V221602P(self):
        SASDoc.from_file('corpus/cms/CMS-HCC software V2216.79.O2 2/V2216O2P.TXT')

    def test_parse_V22H79H1(self):
        SASDoc.from_file('corpus/cms/CMS-HCC software V2216.79.O2 2/V22H79H1.TXT')

    def test_parse_V22H79L1(self):
        SASDoc.from_file('corpus/cms/CMS-HCC software V2216.79.O2 2/V22H79L1.TXT')

    def test_parse_V22I0ED1(self):
        SASDoc.from_file('corpus/cms/CMS-HCC software V2216.79.O2 2/V22I0ED1.TXT')

    def test_parse_V22I9ED1(self):
        SASDoc.from_file('corpus/cms/CMS-HCC software V2216.79.O2 2/V22I9ED1.TXT')

