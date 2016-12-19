
import unittest

from nose.tools import assert_raises

from sasparse import SASDoc
from sasparse.parse import ParseNode, TopLevel


class TestTopLevel(unittest.TestCase):

    _multiprocess_can_split_ = True

    def test_error_tag_notfound(self):
        assert_raises(Exception, TopLevel.from_parsetree, ParseNode.make_with_invalid_tag())


class TestParseDoesntCrash(unittest.TestCase):

    _multiprocess_can_split_ = True

    def test_empty_doc(self):
        SASDoc.from_string('')

    def test_empty_stmt(self):
        SASDoc.from_string(';')

    def test_ParseNode_comment_dump(self):
        SASDoc.from_string('*;').dump()

    def test_parseerror_str(self):
        assert_raises(Exception, SASDoc.from_string, '"')

    def test_parseerror_child(self):
        assert_raises(Exception, SASDoc.from_string, '1 2 3"')

    def test_parse_array(self):
        SASDoc.from_file('corpus/test-parse-array.sas')

    def test_parse_control(self):
        SASDoc.from_file('corpus/test-parse-control.sas')

    def test_parse_data(self):
        SASDoc.from_file('corpus/test-parse-data.sas')

    def test_parse_do(self):
        SASDoc.from_file('corpus/test-parse-do.sas')

    def test_parse_drop(self):
        SASDoc.from_file('corpus/test-parse-drop.sas')

    def test_parse_filename(self):
        SASDoc.from_file('corpus/test-parse-filename.sas')

    def test_parse_libname(self):
        SASDoc.from_file('corpus/test-parse-libname.sas')

    def test_parse_macros(self):
        SASDoc.from_file('corpus/test-parse-macros.sas')

    def test_parse_ods(self):
        print(SASDoc.from_file('corpus/test-parse-ods.sas'))

    def test_parse_options(self):
        SASDoc.from_file('corpus/test-parse-options.sas')

    def test_parse_proc_cimport(self):
        SASDoc.from_file('corpus/test-parse-proc-cimport.sas')

    def test_parse_proc_datasets(self):
        SASDoc.from_file('corpus/test-parse-proc-datasets.sas')

    def test_parse_proc_export(self):
        SASDoc.from_file('corpus/test-parse-proc-export.sas')

    def test_parse_proc_format(self):
        SASDoc.from_file('corpus/test-parse-proc-format.sas')

    def test_parse_proc_freq(self):
        SASDoc.from_file('corpus/test-parse-proc-freq.sas')

    def test_parse_proc_gmap(self):
        SASDoc.from_file('corpus/test-parse-proc-gmap.sas')

    def test_parse_proc_gremove(self):
        SASDoc.from_file('corpus/test-parse-proc-gremove.sas')

    def test_parse_proc_import(self):
        print(SASDoc.from_file('corpus/test-parse-proc-import.sas'))

    def test_parse_proc_means(self):
        SASDoc.from_file('corpus/test-parse-proc-means.sas')

    def test_parse_print(self):
        SASDoc.from_file('corpus/test-parse-proc-print.sas')

    def test_parse_proc_rank(self):
        SASDoc.from_file('corpus/test-parse-proc-rank.sas')

    def test_parse_proc_report(self):
        SASDoc.from_file('corpus/test-parse-proc-report.sas')

    def test_parse_proc_sgpanel(self):
        SASDoc.from_file('corpus/test-parse-proc-sgpanel.sas')

    def test_parse_proc_sql_select(self):
        SASDoc.from_file('corpus/test-parse-proc-sql-select.sas')

    def test_parse_proc_sort(self):
        SASDoc.from_file('corpus/test-parse-proc-sort.sas')

    def test_parse_proc_transpose(self):
        SASDoc.from_file('corpus/test-parse-proc-transpose.sas')

    def test_parse_proc_template(self):
        SASDoc.from_file('corpus/test-parse-proc-template.sas')

    def test_parse_proc_univariate(self):
        SASDoc.from_file('corpus/test-parse-proc-univariate.sas')

    def test_parse_signon(self):
        SASDoc.from_file('corpus/test-parse-signon.sas')

    def test_parse_title(self):
        SASDoc.from_file('corpus/test-parse-title.sas')

    def test_parse_toplevel(self):
        SASDoc.from_file('corpus/test-parse-toplevel.sas')

    def test_parse_var(self):
        SASDoc.from_file('corpus/test-parse-var.sas')

    def test_parse_sql_create_table(self):
        SASDoc.from_file('corpus/test-parse-sql-create-table.sas')

    def test_parse_sql_create_view(self):
        SASDoc.from_file('corpus/test-parse-sql-create-view.sas')

    def test_parse_sql_sas_nonstandard(self):
        SASDoc.from_file('corpus/test-parse-sql-nonstandard.sas')

    def test_nocrash_bene_characteristics(self):
        SASDoc.from_file('corpus/AC001_P03_Q01_20160628_S01.sas')


class TestDMRCorpus(unittest.TestCase):

    _multiprocess_can_split_ = True

    def test_nocrash_snf_profiles(self):
        SASDoc.from_file('corpus/snf-profiles.sas')

    def test_nocrash_hospital_profiles(self):
        SASDoc.from_file('corpus/hospital-profiles.sas')

    def test_nocrash_awvcclfv6(self):
        SASDoc.from_file('corpus/awvcclfv6.sas')
