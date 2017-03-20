
import os
import unittest

from sasparse import SASDoc


class TestSymIO(unittest.TestCase):

    _multiprocess_can_split_ = True

    @unittest.skipUnless(os.path.exists('corpus/test-symio-001.sas'), '')
    def test_symio_001(self):
        SASDoc.from_file('corpus/test-symio-001.sas')
