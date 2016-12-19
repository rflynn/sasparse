
import unittest

from sasparse import SASDoc


class TestSymIO(unittest.TestCase):

    _multiprocess_can_split_ = True

    def test_symio_001(self):
        SASDoc.from_file('corpus/test-symio-001.sas')
