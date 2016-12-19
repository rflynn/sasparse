
# import unittest

from nose.tools import timed, assert_raises

from sasparse import SASDoc


_multiprocess_can_split_ = True


def recursive_glob(path, pattern, maxitems=None):
    import os
    from fnmatch import fnmatch
    cnt = 0
    for root, directories, filenames in os.walk(path):
        for directory in sorted(directories):
            recursive_glob(root, directory)
        for filename in sorted(filenames):
            if fnmatch(filename, pattern):
                yield os.path.join(root, filename)
                cnt += 1
                if maxitems is not None and cnt >= maxitems:
                    return


_ExpectedFailures = {
    # these files contain either code that is truly broken, incomplete, or just has little chunks of code that i refuse to parse
    # '../../sas/alshadye/.mysnippets/tm_char_loop.sas',  # top-level brackets... maybe?
    '../../sas/alshadye/.mysnippets/tm_overlap_dates.sas',
    '../../sas/alshadye/.mysnippets/tm_sql_merge.sas',  # brackets in SQL
    '../../sas/alshadye/.mysnippets/tm_write_protect.sas',  # raw parameter expr in file: (...)
    '../../sas/alshadye/AA_Provider_Recruit/AA002_Provider_PUF/AA002_P01_PPUF/AA002_P01_20150303/AA002_P01_20150306.sas',  # /* ... unterminated thru EOF
    '../../sas/alshadye/AA_Provider_Recruit/AA002_Provider_PUF/AA002_P01_PPUF/AA002_P01_20150311/AA002_P01_20150311.sas',  # "LEFT OFF HERE..."
    '../../sas/alshadye/AA_Provider_Recruit/AASRC_Source_Data/AASRC_MUPUF/AASRC_MUPUF_Input.sas',  # sql error (no comma after field)
    '../../sas/alshadye/AC_CCLF_Analytical/AC001_Build_Analytical/AC001_P01_Final_Action/AC001_P01_20151103/AC001_P01_20151103.sas',  # "LEFT OFF HERE"...
    '../../sas/alshadye/AC_CCLF_Analytical/AC001_Build_Analytical/AC001_P02_File_Types/BENE_QTR_CHECK_20160706.sas',  # lone %end line 109
    '../../sas/alshadye/AC_CCLF_Analytical/AC001_Build_Analytical/AC001_P03_Bene_Monthly/AC001_P03_Q02_Month_Report/AC001_P03_Q02_20151028/AC001_P03_Q02_20151028_S04.sas',  # "LEFT OFF HERE"...
    '../../sas/alshadye/AC_CCLF_Analytical/AC001_Build_Analytical/AC001_P03_Bene_Monthly/AC001_P03_Q02_Month_Report/AC001_P03_Q02_20151120/AC001_P03_Q02_20151120_S03.sas',  # an insane macro-laden sql query on line 764 that i refuse to implement :(
    '../../sas/alshadye/AC_CCLF_Analytical/AC001_Build_Analytical/AC001_P03_Bene_Monthly/AC001_P03_Q02_Month_Report/AC001_P03_Q02_20160322/Bene-month -cm.sas',  # file just has raw data and comments sitting in it at line 14...
    '../../sas/alshadye/AC_CCLF_Analytical/AC001_Build_Analytical/AC001_P03_Bene_Monthly/AC001_P03_Q03_ACO_Dashboard/AC001_P03_Q03_20151216/AC001_P03_Q03_20151216_S02.sas',  # freeform text in code line 228
    '../../sas/alshadye/AC_CCLF_Analytical/AC001_Build_Analytical/AWS.sas',  # mangled SQL query
    '../../sas/alshadye/AC_CCLF_Analytical/AC001_Build_Analytical/FAC_NONFAC.sas',   # weird syntax: "stmt; [2]" line 290
    '../../sas/alshadye/AC_CCLF_Analytical/AC001_Build_Analytical/FH_ED_INPT.sas',  # syntax error, missing [proc ]sort data...
    '../../sas/alshadye/AC_CCLF_Analytical/AC001_Build_Analytical/Scratch_ancillary_2.sas',  # syntax error line 364, unterminated ;
    '../../sas/alshadye/AC_CCLF_Analytical/AC001_Build_Analytical/Scratch_ancillary_3.sas',  # syntax error line 364, unterminated ;
    '../../sas/alshadye/Aledade_practices_providers.sas',
    '../../sas/alshadye/Assign_pt.sas',
    '../../sas/alshadye/Scratch_Ancillary.sas',  # hanging 'p' line 18
    '../../sas/alshadye/AC_CCLF_Analytical/AC001_Build_Analytical/AC001_P03_Bene_Monthly/AC001_P03_Q03_ACO_Dashboard/AC001_P03_Q03_20151204/AC001_P03_Q03_20151204_S01.sas',  # "LEFT OFF HERE"...
    '../../sas/alshadye/AC_CCLF_Analytical/AC001_Build_Analytical/AC001_P03_Bene_Monthly/AC001_P03_Q02_Month_Report/AC001_P03_Q02_20160304/Check_dashboard.sas',  # raw data inline line 65. is this legal syntax?
    '../../sas/shared/practice report/potentially avoidable hospitalizations.sas',  # SQL sliver: case statement
    '../../sas/alshadye/AA_Provider_Recruit/AA001_Recruit_Lists/AA001_P03_REPORTS/AA001_P03_20150521/AA001_P03_20150521.sas',  # "LEFT OFF HERE"...
    '../../sas/alshadye/AA_Provider_Recruit/AA001_Recruit_Lists/AA001_P02_SITENPI/AA001_P02_20150916/Current_Aledade_Practices.sas',  # file cut off...
    '../../sas/alshadye/AC_CCLF_Analytical/AC001_Build_Analytical/Completion Factor.sas',  # "c" on line 29...
    '../../sas/alshadye/AC_CCLF_Analytical/AC001_Build_Analytical/AC001_P04_Reports/AC001_P04_20150416.sas',  # "LEFT OFF TRYING"...
    '../../sas/alshadye/AA_Provider_Recruit/AA002_Provider_PUF/AA002_P01_PPUF/AA002_P01_20150311/AA002_P01_20150311.sas',  # "LEFT OFF HERE"...
    '../../sas/alshadye/AD_ACO_Rescue/AD001_FL_Primary_Partners/Blah.sas',  # "LEFT OFF HERE"...
}


def test_parse_corpus():
    for sasfilepath in recursive_glob('../../sas', '*.sas', maxitems=500):
        if sasfilepath in _ExpectedFailures:
            yield parsefile_expectedfailure, sasfilepath
        else:
            yield parsefile, sasfilepath


@timed(25)
def parsefile(sasfilepath):
    SASDoc.from_file(sasfilepath)


@timed(10)
def parsefile_expectedfailure(sasfilepath):
    assert_raises(Exception, SASDoc.from_file, sasfilepath)
