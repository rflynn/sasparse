

SAS_EBNF = r'''
sas          := toplevel*

toplevel     := space          /
                comment        /
                macro          /
                run_stmt       /
                quit_stmt      /
                data_stmt      /
                proc_stmt      /
                title_stmt     /
                ods_stmt       /
                options_stmt   /
                footnote_stmt  /
                delete_stmt    /
                preproc_stmt   /
                if_stmt        /
                do_block       /
                do_over_stmt   /
                do_to_stmt     /
                do_until_stmt  /
                else_stmt      /
                libname_stmt   /
                filename_stmt  /
                assign_stmt    /
                format_stmt    /
                array_stmt     /
                abort_stmt     /
                length_stmt    /
                input_stmt     /
                datalines_stmt /
                put_stmt       /
                var_stmt       /
                drop_stmt      /
                signon_stmt    /
                pattern_stmt   /
                rsubmit_stmt   /
                select_stmt    /
                label_stmt     /
                endrsubmit_stmt/
                waitfor_stmt   /
                toplevel_funcesque_op /
                compute_block  /
                expr_stmt      /
                empty_stmt

preproc_stmt := macrovar, -[;\n]*, (';' / newline)

# some questionable code seems to need this, but is caused breakage?
expr_stmt := sas_value, spacecom*, ';'

empty_stmt   := space*, ';'

macro        := macro_comment  /
                macro_do_block /
                macro_to       /
                macro_def      /
                macro_else     /
                macro_if       /
                macro_then     /
                macro_until    /
                macro_include  /
                macro_global   /
                macro_goto     /
                macro_label    /
                macro_let      /
                macro_local    /
                macro_mend     /
                macro_put      /
                macro_symdel   /
                macro_syslput  /
                macro_call

macro_call_stmt    := macro_call, spaces1*, (';' / newline)
macro_call         := macro_call_builtin /
                      macro_call_udf

macro_call_builtin := macro_emailx   /
                      macro_length   /
                      macro_nrstr    /
                      macro_qsysfunc /
                      macro_scan     /
                      macro_str      /
                      macro_sysfunc

macro_reserved := (kwdo      /
                   kwelse    /
                   kwend     /
                   kwif      /
                   kwinclude /
                   kwglobal  /
                   kwgoto    /
                   kwlabel   /
                   kwlet     /
                   kwlocal   /
                   kwmacro   /
                   kwmend    /
                   kwsymdel), ?-[a-zA-Z0-9_]

# user-defined function; something we don't recognize as a built-in
macro_call_udf     := '%', ?-macro_reserved, identmacro, spaces1?, macro_params?
macro_params       := '(', macro_param_list?, space*, ')'
macro_param_list   := space?, macro_param_def, (space?, ',', space?,  macro_param_def, space?)*, hanging_comma?
hanging_comma      := spacecom?, ','

macro_let          := '%', space?, kwlet, space?, identmacro, space?, '=', space*, macro_let_val?, hanging_comma?, spacecom*, (';' / newline)?
macro_let_val      := non_param_list / sas_expr_list

# SAS has context-dependent list syntax. what a joy for everyone
non_param_list :=  sas_expr_list, (spaces1?, ',', spaces1?, sas_expr_list)+

# XXX: i think this is a custom function? but i can't find a definition,
# and i don't understand the syntax, so just swallow it for now
macro_emailx       := '%', space?, kwemailx, '(', semistmt

macro_length       := '%', space?, kwlength, space*, macro_params

macro_include      := '%', space?, kwinclude, spaces1*, sas_expr_scalar, spaces1*, include_opts?, spaces1*, (';' / newline)
include_opts       := '/', spaces1*, include_opts_list
include_opts_list  := include_opt, (spaces1*, include_opt)*
include_opt        := include_opt_nosource2 /
                      include_opt_source2
include_opt_nosource2 := kwnosource2
include_opt_source2   := kwsource2

macro_do_block     := macro_do, macro_block_stmt*, macro_end
macro_do           := '%', kwdo, spaces1?, (sas_expr / (spaces1?, ';'))
macro_block_stmt   := ?-macro_end, (toplevel / sas_expr / hanging_comma)
# a catch-all for when unhygenic macros break shit...
anything_goes      := [.]

macro_to           := '%', space?, kwto, spaces1?, sas_expr?

macro_def          := '%', space?, kwmacro, spaces1, ident, spaces1?, macro_params?, macro_opts?, spaces1?, ';'
macro_param_def    := macro_param_keyval / macro_param_pos
macro_param_keyval := macro_param_keyval_key, space?, '=', (space?, macro_param_pos)?
macro_param_keyval_key := macro / pseudoident
macro_param_pos    := sas_expr_list
macro_opts         := spaces1?, '/', space*, macro_opts_list
macro_opts_list    := macro_opt, (spacecom*, macro_opt)*
macro_opt          := macro_opt_minoperator
macro_opt_minoperator := kwminoperator

# macro comments may be multi-line,
# whereas program comments in the form *...; must be single-line?
macro_comment   := '%', '*', -';'*, ';'

macro_mend      := '%', space?, kwmend, spaces1?, (ident, spaces1?)?, ';'

macro_global    := '%', kwglobal, spaces1, ident_list?, spacecom*, ';'
macro_local     := '%', kwlocal, spaces1, ident_list?, spacecom*, ';'

macro_goto      := '%', kwgoto, spaces1, ident, spacecom*, ';'
macro_label     := '%', ident,  spaces1?, ':'

macro_if        := '%', space?, kwif,   spaces1?, sas_expr
macro_then      := '%', space?,  kwthen, spaces1?, macro_do_block
macro_else      := '%', space?, kwelse, spaces1?
macro_end       := '%', space?, kwend,  spaces1?, ';'
macro_until     := '%', space?, kwuntil, (spaces1?, '(', spaces1?, sas_expr, spaces1?, ')')?

macro_if_then_end  := macro_if, spaces1?, macro_then
# a catch-all for when unhygenic macros break shit...


macro_scan      := '%', space?, kwscan, scan_params
scan_params     := '(', macro_param_list?, (spacecom*, '.')?, space*, ')'

macro_str       := '%', space?, kwstr, '(', macro_str_str, ')'
macro_str_str   := (regular_str / escaped_chr / balanced_parens)*
regular_str     := -('(' / ')' / '%')+
escaped_chr     := '%', ['"()%]
balanced_parens := '(', (-('(' / ')') / balanced_parens)*, ')'


macro_nrstr     := '%', space?, kwnrstr, '(', macro_nrstr_str, ')'
macro_nrstr_str := (-('(' / ')' / '%')+ / ('%', ['"()&%]) / balanced_parens)*

macro_put       := '%', space?, kwput, spaces1, semistmt

macro_symdel    := '%', space?, kwsymdel, spaces1, pseudoident_list?, spacecom*, ';'

macro_syslput   := '%', space?, kwsyslput, spaces1, sas_identifier, spaces1?, '=', spaces1?, pseudoident_list?, spaces1*, ';'

macro_sysfunc   := '%', space?, kwsysfunc, space*, macro_params
macro_qsysfunc  := '%', space?, kwqsysfunc, space*, macro_params

run_stmt        := kwrun, spacecom*, ';'
quit_stmt       := kwquit, spacecom*, ';'
abort_stmt      := kwabort, spacecom*, ';'

libname_stmt       := libname_clear  /
                      libname_def    /
                      libname_list   /
                      libname_meta   /
                      libname_engine
libname_eos       := ((spaces1?, newline) / (space*, ';'))
libname_clear     := kwlibname, space+, libref, space+, kwclear, libname_eos
libname_list      := kwlibname, space+, libref, space+, kwlist, libname_eos
libname_def       := kwlibname, space+, ident, space*, string, libname_eos
libname_meta      := kwlibname, space+, ident, space*, kwmeta, space*, libname_meta_opts?, libname_eos
libname_meta_opts := libname_meta_opt_libid /
                     libname_meta_opt_library /
                     libname_meta_opt_liburi
libname_meta_opt_libid   := kwlibid,   spacecom*, '=', spacecom*, string
libname_meta_opt_library := kwlibrary, spacecom*, '=', spacecom*, string
libname_meta_opt_liburi  := kwliburi,  spacecom*, '=', spacecom*, string
libname_engine:= kwlibname, space+, ident, space*, ident, space*, string, libname_eos
libref       := kw_all_ / pseudoident / libref_parameterized
libref_parameterized := '[', ident_list, ']'

filename_stmt:= kwfilename, space+, ident, (space?, string)?, (space?, keyval_list)?, space?, ';'

title_stmt   := titlenum / title_
titlenum     := kwtitle, integer, (spaces1*, title_descr)?, spaces1?, (newline / ';')
title_       := kwtitle, (spaces1*, title_descr)?, spaces1?, (';' / newline)
title_descr  := title_opts?, spaces1?, stringparts
title_opts   := title_opt, (space*, title_opt)*
title_opt    := ident, spaces1?, '=', spaces1?, sas_expr_scalar

# an optionally whitespace-sep list of concatenated string-like stuff
stringparts  := stringpart, (space*, stringpart)*
# XXX: i think this came about from a misunderstanding of date literals...
#stringpart   := string / sas_identifier / macrovar
stringpart   := string / macrovar / macrovar

footnote_stmt   := footnote_ / footnotenum
footnote_       := kwfootnote, spaces1?, ';'
footnotenum     := kwfootnote, integer, (spaces1?, string)?, space?, ';'

signon_stmt     := kwsignon, spacecom+, identmacro, spacecom*, ';'

pattern_stmt    := pattern_ / patternnum
pattern_        := kwpattern, spaces1?, ';'
patternnum      := kwpattern, integer, (spaces1?, keyval_list)?, space?, ';'

rsubmit_stmt    := kwrsubmit, spaces1?, semistmt

select_stmt     := select_select_stmt, spacecom*, select_when_list, spacecom*, select_otherwise, spacecom*, select_end
select_select_stmt := kwselect, spacecom*, ';'
select_when_list := select_when_stmt, (spacecom*, select_when_stmt)*
select_when_stmt := kwwhen, spacecom*, '(', sas_expr, ')', spacecom*, assign_stmt
select_otherwise := kwotherwise, spacecom*, ';'
select_end       := kwend, spacecom*, ';'

label_stmt      := kwlabel, spacecom+, keyval_list, spacecom*, ';'

endrsubmit_stmt := kwendrsubmit, spaces1?, ';'

waitfor_stmt    := kwwaitfor, spaces1?, semistmt

delete_stmt     := kwdelete, spaces1?, semistmt

var_stmt        := kwvar, spaces1, (ws_ident_list / macro)

drop_stmt       := kwdrop, spaces1, list_of_list_of_variables, spacecom*, ';'
list_of_list_of_variables := droppable, (spacecom+, droppable)*
droppable       := variable_list / sas_identifier

length_stmt     := kwlength, spacecom*, length_var_spec_list, spacecom*, ';'
length_var_spec_list := length_var_spec, (spacecom*, length_var_spec)*
length_var_spec := length_var_list, spacecom+, (('$', spacecom*)?, integer, '.'?)?
length_var_list := var_list

var_list        := var_ref, (spacecom+, var_ref)*
var_ref         := var_ref_range / ident / macrovar
var_ref_range   := identmacro, '-', identmacro

input_stmt      := kwinput, spacecom+, ident, spacecom*, ';'
datalines_stmt  := kwdatalines, spacecom*, ';', semistmt



if_stmt         := kwif,   spacecom+, sas_expr, spacecom*, then_expr
then_expr       := kwthen, spacecom*, (do_block / assign_stmt / sas_expr)
else_stmt       := kwelse, spacecom+, (if_stmt / do_block / toplevel)
end_stmt        := kwend,  spacecom*, ';'

do_block        := do_stmt, do_block_stmt*, end_stmt
do_stmt         := kwdo, spacecom*, ';'
do_block_stmt   := ?-end_stmt, (toplevel / sas_expr / hanging_comma)

do_over_stmt    := kwdo, spacecom+, kwover, spacecom+, ident, spacecom*, ';', do_block_stmt*, end_stmt

do_to_stmt      := do_to, do_block_stmt*, end_stmt
do_to           := kwdo, spacecom+, ident, spacecom*, '=', spacecom*, sas_value, spacecom+, kwto, spacecom+, sas_value, spacecom*, while_stmt?, spacecom*, ';'
while_stmt      := kwwhile, space?, '(', space?, sas_expr, space?, ')'

do_until_stmt   := do_until, do_block_stmt*, end_stmt
do_until        := kwdo, spacecom+, kwuntil, space?, '(', spacecom*, sas_expr, ')', spacecom*, ';'

compute_block      := compute_stmt, compute_block_stmt*, endcomp_stmt
compute_block_stmt := ?-endcomp_stmt, toplevel
compute_stmt       := kwcompute, spacecom+, pseudoident_list, spacecom*, ';'
endcomp_stmt       := kwendcomp, spacecom*, ';'

assign_stmt     := assignable, spacecom*, '=', spacecom*, sas_expr?, spacecom*, ';'
assignable      := array_access / sas_identifier
array_access    := sas_identifier, array_subscript
# ref: Tip: You can enclose the subscript in braces ({}), brackets ( [ ] ) or parentheses (( )).
array_subscript := ('{', array_dimension, '}') /
                   ('[', array_dimension, ']') /
                   ('(', array_dimension, ')')
array_dimension := '*' / sas_expr

format_stmt     := kwformat, space?, semistmt

# ref: http://support.sas.com/documentation/cdl/en/lrdict/64316/HTML/default/viewer.htm#a000201956.htm
array_stmt      := (kwarray, spacecom+,
                    (array_access / identmacro),
                    (spacecom*, '$', integer?)?,
                    spacecom+, array_initial_values, spacecom*, ';')

array_initial_values := list_of_variables

list_of_variables := variable_list / pseudoident_list

# ref: http://support.sas.com/documentation/cdl/en/lrcon/68089/HTML/default/viewer.htm#p0wphcpsfgx6o7n1sjtqzizp1n39.htm
variable_list := numbered_range_list /
                 name_range_list     /
                 name_prefix_list    /
                 special_SAS_name_list

numbered_range_list   := numbered_range_list_exhaustive / numbered_range_list_dashed
name_range_list       := name_range_all / name_range_numeric / name_range_character
name_prefix_list      := kwof, space+, sas_label
special_SAS_name_list := kw_numeric_ / kw_character_ / kw_all_

numbered_range_list_exhaustive := numbered_identifier, (',', numbered_identifier)+
numbered_range_list_dashed     := numbered_identifier, spacecom*, '-', spacecom*, numbered_identifier
numbered_identifier            := sas_identifier # TODO: verify this ends with a numeric character...

name_range_all       := numbered_identifier, '-',              '-', numbered_identifier
name_range_numeric   := numbered_identifier, '-', kwnumeric,   '-', numbered_identifier
name_range_character := numbered_identifier, '-', kwcharacter, '-', numbered_identifier


put_stmt        := kwput, ?-[a-zA-Z0-9_], semistmt

options_stmt := kwoptions, space, options_opts?, space?, ';'
options_opts := options_opt, (space, options_opt)*
options_opt  := options_opt_bufno       /
                options_opt_bufsize     /
                options_opt_compress    /
                options_opt_dsoptions   /
                options_opt_errors      /
                options_opt_fmterr      /
                options_opt_fmtsearch   /
                options_opt_fullstimer  /
                options_opt_ibufno      /
                options_opt_linesize    /
                options_opt_lrecl       /
                options_opt_mautosource /
                options_opt_memsize     /
                options_opt_metapass    /
                options_opt_metauser    /
                options_opt_mlogic      /
                options_opt_mprint      /
                options_opt_msglevel    /
                options_opt_nocenter    /
                options_opt_nodate      /
                options_opt_nofmterr    /
                options_opt_nomlogic    /
                options_opt_nomprint    /
                options_opt_nosymbolgen /
                options_opt_notes       /
                options_opt_number      /
                options_opt_obs         /
                options_opt_pageno      /
                options_opt_pagesize    /
                options_opt_realmemsize /
                options_opt_replace     /
                options_opt_sastrace    /
                options_opt_sastraceloc /
                options_opt_sortsize    /
                options_opt_source2     / # must be before source
                options_opt_source      /
                options_opt_sumsize     /
                options_opt_symbolgen   /
                options_opt_ubufno      /
                options_opt_ubufsize    /
                options_opt_user        /
                options_opt_validvarname/
                options_opt_varlenchk   /
                options_opt_macro_catchall

options_opt_bufno        := kwbufno,        space?, '=', space?, sas_expr_scalar
options_opt_bufsize      := kwbufsize,      space?, '=', space?, valmemspec
options_opt_compress     := kwcompress,     space?, '=', space?, sas_expr_scalar
options_opt_dsoptions    := kwdsoptions,    space?, '=', space?, sas_expr_scalar
options_opt_errors       := kwerrors,       space?, '=', space?, sas_expr_scalar
options_opt_fmterr       := kwfmterr
options_opt_fmtsearch    := kwfmtsearch,    space?, '=', space?, sas_expr_scalar
options_opt_fullstimer   := kwfullstimer
options_opt_ibufno       := kwibufno,       space?, '=', space?, sas_expr_scalar
options_opt_linesize     := kwlinesize,     space?, '=', space?, sas_expr_scalar
options_opt_lrecl        := kwlrecl,        space?, '=', space?, sas_expr_scalar
options_opt_mautosource  := kwmautosource
options_opt_memsize      := kwmemsize,      space?, '=', space?, valmemspec
options_opt_metapass     := kwmetapass,     space?, '=', space?, sas_expr_scalar
options_opt_metauser     := kwmetauser,     space?, '=', space?, sas_expr_scalar
options_opt_mlogic       := kwmlogic
options_opt_mprint       := kwmprint
options_opt_msglevel     := kwmsglevel,     space?, '=', space?, sas_expr_scalar
options_opt_nocenter     := kwnocenter
options_opt_nodate       := kwnodate
options_opt_nofmterr     := kwnofmterr
options_opt_nomlogic     := kwnomlogic
options_opt_nomprint     := kwnomprint
options_opt_nosymbolgen  := kwnosymbolgen
options_opt_notes        := kwnotes
options_opt_number       := kwnumber
options_opt_obs          := kwobs,          space?, '=', space?, sas_expr_scalar
options_opt_pageno       := kwpageno,       space?, '=', space?, sas_expr_scalar
options_opt_pagesize     := kwpagesize,     space?, '=', space?, valmemspec
options_opt_realmemsize  := kwrealmemsize,  space?, '=', space?, valmemspec
options_opt_replace      := kwreplace
options_opt_sastrace     := kwsastrace,     space?, '=', space?, sas_expr_scalar
options_opt_sastraceloc  := kwsastraceloc,  space?, '=', space?, sas_expr_scalar
options_opt_sortsize     := kwsortsize,     space?, '=', space?, valmemspec
options_opt_source       := kwsource
options_opt_source2      := kwsource2
options_opt_sumsize      := kwsumsize,      space?, '=', space?, sas_expr_scalar
options_opt_symbolgen    := kwsymbolgen
options_opt_ubufno       := kwubufno,       space?, '=', space?, sas_expr_scalar
options_opt_ubufsize     := kwubufsize,     space?, '=', space?, valmemspec
options_opt_user         := kwuser,         space?, '=', space?, sas_expr_scalar
options_opt_validvarname := kwvalidvarname, space?, '=', space?, sas_expr_scalar
options_opt_varlenchk    := kwvarlenchk,    space?, '=', space?, sas_expr_scalar
options_opt_macro_catchall := macrovar


# keywords
kw_all_      := '_all_' / '_ALL_'
kw_character_:= '_character_' / '_CHARACTER_'
kw_numeric_  := '_numeric_' / '_NUMERIC_'
kwabort      := 'abort' / 'ABORT'
kwall        := 'all' / 'ALL'
kwalso       := 'also' / 'ALSO'
kwalter      := 'alter' / 'ALTER'
kwand        := 'and' / 'AND'
kwanno       := 'anno' / 'ANNO'
kwany        := 'any' / 'ANY'
kwarray      := 'array' / 'ARRAY'
kwas         := 'as' / 'AS'
kwasc        := 'asc' / 'ASC'
kwascending  := 'ascending' / 'ASCENDING'
kwavg        := 'avg' / 'AVG'
kwbetween    := 'between' / 'BETWEEN'
kwbufno      := 'bufno' / 'BUFNO'
kwbufsize    := 'bufsize' / 'BUFSIZE'
kwby         := 'by' / 'BY'
kwc          := 'c' / 'C'
kwcalculated := 'calculated' / 'CALCULATED'
kwcall       := 'call' / 'CALL'
kwcase       := 'case' / 'CASE'
kwcat        := 'cat' / 'CAT'
kwcatalog    := 'catalog' / 'CATALOG'
kwcharacter  := 'character' / 'CHARACTER'
kwchoro      := 'choro' / 'CHORO'
kwcimport    := 'cimport' / 'CIMPORT'
kwclass      := 'class' / 'CLASS'
kwclear      := 'clear' / 'CLEAR'
kwclose      := 'close' / 'CLOSE'
kwcntlin     := 'cntlin' / 'CNTLIN'
kwcoalesce   := 'colaesce' / 'COALESCE'
kwcol        := 'col' / 'COL'
kwcolaxis    := 'colaxis' / 'COLAXIS'
kwcolumn     := 'column' / 'COLUMN'
kwcomma      := 'comma' / 'COMMA'
kwcompress   := 'compress' / 'COMPRESS'
kwcompute    := 'compute' / 'COMPUTE'
kwcontains   := 'contains' / 'CONTAINS'
kwcontents   := 'contents' / 'CONTENTS' / 'Contents'
kwcorr       := 'corr' / 'CORR'
kwcorresponding := 'corresponding' / 'CORRESPONDING'
kwcount      := 'count' / 'COUNT'
kwcreate     := 'create' / 'CREATE'
kwcsv        := 'csv' / 'CSV'
kwdata       := 'data' / 'DATA' / 'Data'
kwdatafile   := 'datafile' / 'DATAFILE'
kwdatalines  := 'datalines' / 'DATALINES'
kwdatasets   := 'datasets' / 'DATASETS'
kwdbms       := 'dbms' / 'DBMS'
kwdefine     := 'define' / 'DEFINE'
kwdelete     := 'delete' / 'DELETE'
kwdense      := 'dense' / 'DENSE'
kwdesc       := 'desc' / 'DESC'
kwdescending := 'descending' / 'DESCENDING'
kwdescribe   := 'describe' / 'DESCRIBE'
kwdistinct   := 'distinct' / 'DISTINCT'
kwdo         := 'do' / 'DO'
kwdollar     := 'dollar' / 'DOLLAR'
kwdrop       := 'drop' / 'DROP'
kwdsoptions  := 'dsoptions' / 'DSOPTIONS'
kwdupout     := 'dupout' / 'DUPOUT'
kwelse       := 'else' / 'ELSE'
kwemailx     := 'emailx' / 'EMAILX'
kwend        := 'end' / 'END'
kwendcomp    := 'endcomp' / 'ENDCOMP'
kwendrsubmit := 'endrsubmit' / 'ENDRSUBMIT'
kwerrors     := 'errors' / 'ERRORS'
kwescapechar := 'escapechar' / 'ESCAPECHAR'
kwexcel      := 'excel' / 'EXCEL'
kwexcelxp    := 'excelxp' / 'EXCELXP' / 'ExcelXP'
kwexcept     := 'except' / 'EXCEPT'
kwexists     := 'exists' / 'EXISTS'
kwexport     := 'export' / 'EXPORT'
kwfile       := 'file' / 'FILE'
kwfilename   := 'filename' / 'FILENAME'
kwfmterr     := 'fmterr' / 'FMTERR'
kwfmtlib     := 'fmtlib' / 'FMTLIB'
kwfmtsearch  := 'fmtsearch' / 'FMTSEARCH'
kwfootnote   := 'footnote' / 'Footnote' / 'FOOTNOTE'
kwformat     := 'format' / 'FORMAT'
kwfreq       := 'freq' / 'FREQ'
kwfrom       := 'from' / 'FROM'
kwfull       := 'full' / 'FULL'
kwfullstimer := 'fullstimer' / 'FULLSTIMER'
kwge         := 'ge' / 'GE'
kwglobal     := 'global' / 'GLOBAL'
kwgmap       := 'gmap' / 'GMAP'
kwgoto       := 'goto' / 'GOTO'
kwgraphics   := 'graphics' / 'GRAPHICS'
kwgremove    := 'gremove' / 'GREMOVE'
kwgroup      := 'group' / 'GROUP'
kwgroups     := 'groups' / 'GROUPS'
kwgt         := 'gt' / 'GT'
kwhaving     := 'having' / 'HAVING'
kwhigh       := 'high' / 'HIGH'
kwhistogram  := 'histogram' / 'HISTOGRAM'
kwhtml       := 'html' / 'HTML'
kwibufno     := 'ibufno' / 'IBUFNO'
kwid         := 'id' / 'ID'
kwif         := 'if' / 'IF'
kwimagemap   := 'imagemap' / 'IMAGEMAP'
kwimport     := 'import' / 'IMPORT'
kwin         := 'in' / 'IN'
kwinclude    := 'include' / 'INCLUDE'
kwinfile     := 'infile' / 'INFILE'
kwinformat   := 'informat' / 'INFORMAT'
kwinner      := 'inner' / 'INNER'
kwinput      := 'input' / 'INPUT'
kwinsert     := 'insert' / 'INSERT'
kwintersect  := 'intersect' / 'INTERSECT'
kwinto       := 'into' / 'INTO'
kwis         := 'is' / 'IS'
kwjoin       := 'join' / 'JOIN'
kwkeep       := 'keep' / 'KEEP' / 'Keep'
kwkey        := 'key' / 'KEY'
kwkeylegend  := 'keylegend' / 'KEYLEGEND'
kwkill       := 'kill' / 'KILL'
kwlabel      := 'label' / 'LABEL'
kwle         := 'le' / 'LE'
kwleft       := 'left' / 'LEFT' / 'Left'
kwlength     := 'length' / 'LENGTH'
kwlet        := 'let' / 'LET'
kwlib        := 'lib' / 'LIB'
kwlibid      := 'libid' / 'LIBID'
kwlibname    := 'libname' / 'LIBNAME' / 'Libname'
kwlibrary    := 'library' / 'LIBRARY'
kwliburi     := 'liburi' / 'LIBURI'
kwlike       := 'like' / 'LIKE'
kwlinesize   := 'linesize' / 'LINESIZE'
kwlist       := 'list' / 'LIST'
kwlisting    := 'listing' / 'LISTING'
kwlocal      := 'local' / 'LOCAL'
kwlow        := 'low' / 'LOW'
kwlrecl      := 'lrecl' / 'LRECL'
kwlt         := 'lt' / 'LT'
kwmacro      := 'macro' / 'MACRO'
kwmap        := 'map' / 'MAP'
kwmautosource:= 'mautosource' / 'MAUTOSOURCE'
kwmax        := 'max' / 'MAX'
kwmaxdec     := 'maxdec' / 'MAXDEC'
kwmean       := 'mean' / 'MEAN'
kwmeans      := 'means' / 'MEANS'
kwmemsize    := 'memsize' / 'MEMSIZE'
kwmend       := 'mend' / 'MEND'
kwmerge      := 'merge' / 'MERGE'
kwmeta       := 'meta' / 'META'
kwmetapass   := 'metapass' / 'METAPASS'
kwmetauser   := 'metauser' / 'METAUSER'
kwmin        := 'min' / 'MIN'
kwminimum    := 'minimum' / 'MINIMUM'
kwminoperator:= 'minoperator' / 'MINOPERATOR'
kwmissing    := 'missing' / 'MISSING'
kwmlogic     := 'mlogic' / 'MLOGIC'
kwmodify     := 'modify' / 'MODIFY'
kwmprint     := 'mprint' / 'MPRINT'
kwmsglevel   := 'msglevel' / 'MSGLEVEL'
kwn          := 'n' / 'N'
kwne         := 'ne' / 'NE'
kwnmiss      := 'nmiss' / 'NMISS'
kwno         := 'no' / 'NO'
kwnoautolegend:= 'noautolegend' / 'NOAUTOLEGEND'
kwnocenter   := 'nocenter' / 'NOCENTER'
kwnocol      := 'nocol' / 'NOCOL'
kwnodate     := 'nodate' / 'NODATE'
kwnodupkey   := 'nodupkey' / 'NODUPKEY'
kwnofmterr   := 'nofmterr' / 'NOFMTERR'
kwnofreq     := 'nofreq' / 'NOFREQ'
kwnofs       := 'nofs' / 'NOFS'
kwnolist     := 'nolist' / 'NOLIST'
kwnomiss     := 'nomiss' / 'NOMISS'
kwnomlogic   := 'nomlogic' / 'NOMLOGIC'
kwnomprint   := 'nomprint' / 'NOMPRINT'
kwnoobs      := 'noobs' / 'NOOBS'
kwnopercent  := 'nopercent' / 'NOPERCENT'
kwnoprint    := 'noprint' / 'NOPRINT'
kwnorow      := 'norow' / 'NOROW'
kwnosource2  := 'nosource2' / 'NOSOURCE2'
kwnosymbolgen:= 'nosymbolgen' / 'NOSYMBOLGEN'
kwnot        := 'not' / 'NOT'
kwnotes      := 'notes' / 'NOTES'
kwnow        := 'now' / 'NOW'
kwnowarn     := 'nowarn' / 'NOWARN'
kwnowindows  := 'nowindows' / 'NOWINDOWS'
kwnrstr      := 'nrstr' / 'NRSTR'
kwnull       := 'null' / 'NULL'
kwnullif     := 'nullif' / 'NULLIF'
kwnumber     := 'number' / 'NUMBER'
kwnumeric    := 'numeric' / 'NUMERIC'
kwnway       := 'nway' / 'NWAY'
kwobs        := 'obs' / 'OBS'
kwods        := 'ods' / 'ODS'
kwof         := 'of' / 'OF'
kwoff        := 'off' / 'OFF'
kwon         := 'on' / 'ON' / 'On'
kwoption     := 'option' / 'OPTION'
kwoptions    := 'options' / 'OPTIONS'
kwor         := 'or' / 'OR'
kworder      := 'order' / 'ORDER'
kwotherwise  := 'otherwise' / 'OTHERWISE'
kwout        := 'out' / 'OUT'
kwouter      := 'outer' / 'OUTER'
kwoutfile    := 'outfile' / 'OUTFILE'
kwoutobs     := 'outobs' / 'OUTOBS'
kwoutput     := 'output' / 'OUTPUT'
kwover       := 'over' / 'OVER'
kwp          := 'p'
kwpageno     := 'pageno' / 'PAGENO'
kwpagesize   := 'pagesize' / 'PAGESIZE'
kwpanelby    := 'panelby' / 'PANELBY'
kwpattern    := 'pattern' / 'PATTERN'
kwpercent    := 'percent' / 'PERCENT'
kwplot       := 'plot' / 'PLOT'
kwplots      := 'plots' / 'PLOTS'
kwprefix     := 'prefix' / 'PREFIX'
kwprint      := 'print' / 'PRINT'
kwproc       := 'proc' / 'PROC' / 'Proc'
kwput        := 'put' / 'PUT'
kwpwencode   := 'pwencode' / 'PWENCODE'
kwqsysfunc   := 'qsysfunc' / 'QSYSFUNC'
kwquit       := 'quit' / 'QUIT'
kwrank       := 'rank' / 'RANK'
kwranks      := 'ranks' / 'RANKS'
kwrealmemsize:= 'realmemsize' / 'REALMEMSIZE'
kwrename     := 'rename' / 'RENAME'
kwreplace    := 'replace' / 'REPLACE'
kwreport     := 'report' / 'REPORT'
kwreset      := 'reset' / 'RESET'
kwretain     := 'retain' / 'RETAIN'
kwright      := 'right' / 'RIGHT'
kwrowaxis    := 'rowaxis' / 'ROWAXIS'
kwrsubmit    := 'rsubmit' / 'RSUBMIT'
kwrun        := 'run' / 'RUN' / 'Run'
kwsastrace   := 'sastrace' / 'SASTRACE'
kwsastraceloc:= 'sastraceloc' / 'SASTRACELOC'
kwscan       := 'scan' / 'SCAN'
kwselect     := 'select' / 'SELECT'
kwseparated  := 'separated' / 'SEPARATED'
kwset        := 'set' / 'SET'
kwsgpanel    := 'sgpanel' / 'SGPANEL'
kwsgplot     := 'sgplot' / 'SGPLOT'
kwsignon     := 'signon' / 'SIGNON'
kwsort       := 'sort' / 'SORT'
kwsortsize   := 'sortsize' / 'SORTSIZE'
kwsource     := 'source' / 'SOURCE'
kwsource2    := 'source2' / 'SOURCE2'
kwsplit      := 'split' / 'SPLIT'
kwsql        := 'sql' / 'SQL'
kwstd        := 'std' / 'STD'
kwstderr     := 'stderr' / 'STDERR'
kwstr        := 'str' / 'STR'
kwstyle      := 'style' / 'STYLE'
kwsum        := 'sum' / 'SUM'
kwsumsize    := 'sumsize' / 'SUMSIZE'
kwsymbolgen  := 'symbolgen' / 'SYMBOLGEN'
kwsymdel     := 'symdel' / 'SYMDEL'
kwsymput     := 'symput' / 'SYMPUT'
kwsysfunc    := 'sysfunc' / 'SYSFUNC'
kwsyslput    := 'syslput' / 'SYSLPUT'
kwtable      := 'table' / 'TABLE'
kwtables     := 'tables' / 'TABLES'
kwtagsets    := 'tagsets' / 'TAGSETS'
kwtemplate   := 'template' / 'TEMPLATE'
kwtext       := 'text' / 'TEXT'
kwthen       := 'then' / 'THEN'
kwties       := 'ties' / 'TIES'
kwtitle      := 'title' / 'Title' / 'TITLE'
kwto         := 'to' / 'TO'
kwtranspose  := 'transpose' / 'TRANSPOSE'
kwubufno     := 'ubufno' / 'UBUFNO'
kwubufsize   := 'ubufsize' / 'UBUFSIZE'
kwuniform    := 'uniform' / 'UNIFORM'
kwuniformby  := 'uniformby' / 'UNIFORMBY'
kwunion      := 'union' / 'UNION'
kwunivariate := 'univariate' / 'UNIVARIATE'
kwuntil      := 'until' / 'UNTIL'
kwupdate     := 'update' / 'UPDATE'
kwuser       := 'user' / 'USER'
kwusing      := 'using' / 'USING'
kwvalidate   := 'validate' / 'VALIDATE'
kwvalidvarname := 'validvarname' / 'VALIDVARNAME'
kwvalue      := 'value' / 'VALUE'
kwvar        := 'var' / 'VAR'
kwvarlenchk  := 'varlenchk' / 'VARLENCHK'
kwvbar       := 'vbar' / 'VBAR'
kwview       := 'view' / 'VIEW'
kwvline      := 'vline' / 'VLINE'
kwwaitfor    := 'waitfor' / 'WAITFOR'
kwwidth      := 'width' / 'WIDTH'
kwwhen       := 'when' / 'WHEN'
kwwhere      := 'where' / 'WHERE' / 'Where'
kwwhile      := 'while' / 'WHILE'
kwwrite      := 'write' / 'WRITE'
kwxlsx       := 'xlsx' / 'XLSX'
kwyaxis      := 'yaxis' / 'YAXIS'
kwz          := 'z' / 'Z'


# NOTE: cannot use "spacecom" in expressions, as *...; is ambiguous wrt mult/exp operators
sas_expr              := sas_value / sas_expr_tuple / sql_expr_tuple / comment
sas_value             := sas_expr_binop / sas_expr_scalar / sas_expr_triop
sas_expr_tuple        := '(', space*, sas_expr_list, space*, ')'
sas_expr_list         := sas_expr, (space*, sas_expr)*
sas_expr_binop        := sas_expr_scalar, space*, sas_expr_bin_op_val
sas_expr_triop        := sas_expr_binop, space*, sas_expr_bin_op_val
sas_expr_bin_op_val   := sas_expr_bin_general / sas_op_between
sas_expr_bin_general  := sas_op_bin, space*, sas_expr?
sas_expr_scalar       := (macro           /
                          date_literal    /
                          string          /
                          sas_funcall     /
                          sas_expr_unary  /
                          sas_expr_tuple  /
                          sql_expr_tuple  /
                          proc_block      /
                          fileref_abspath /
                          sas_label       /
                          array_access    /
                          sas_identifier  /
                          sas_val_int_range /
                          number          /
                          sas_brackets)

toplevel_funcesque_op := funcesque_op, space+, sas_expr
funcesque_op          := (kwoutput / kwcall / kwsymput, ?-[a-zA-Z0-9_])

sas_expr_unary        := sas_op_unary, space*, sas_expr
sas_op_unary          := '+' / '-' / '~' / sas_op_unary_not / funcesque_op
sas_op_unary_not      := '^' / 'ˆ' / '¬' / '~' / (kwnot, ?-[a-zA-Z0-9_])

sas_funcall           := sas_funcall_builtin / sas_funcall_udf
sas_funcall_builtin   := sas_funcall_put
sas_funcall_udf       := sas_func_ident, space?, sas_funcall_params
sas_funcall_params    := '(', sas_funcall_param_list?, space*, ')'
sas_funcall_param_list:= sas_funcall_param, (space*, ',', space*, sas_funcall_param)*, hanging_comma?
sas_funcall_param     := sas_expr_list
sas_func_ident        := ident

sas_funcall_put       := kwput, space?, func_put_params
func_put_params       := '(', sas_funcall_param_list?, space*, func_put_param_format?, space*, ')'
func_put_param_format := func_put_format_dollar / sas_format
func_put_format_dollar:= '$', sas_identifier, '.'

# ref: http://support.sas.com/documentation/cdl/en/lrcon/62955/HTML/default/viewer.htm#a000780367.htm
sas_op_bin            := sas_op_bin_arith  /
                         sas_op_bin_cmp    /
                         sas_op_bin_concat /
                         sas_op_bin_logic
sas_op_bin_arith      := '+' / '-' / '**' / '*' / '/'
sas_op_bin_cmp        := '=' / sas_op_bin_cmp_ne / '><' / '<>' / sas_op_bin_cmp_ord / (kwlike, ?-[a-zA-Z0-9_])
sas_op_bin_cmp_ne     := '^=' / '¬=' / '~=' / (kwne, ?-[a-zA-Z0-9_])
sas_op_bin_cmp_ord    := '<=' / '<' / '>=' / '>' / ((kwnot / kwlt / kwle / kwge / kwgt), ?-[a-zA-Z_])
sas_op_bin_concat     := '||' / '¦¦' / '!!'
sas_op_bin_logic      := (sas_op_bin_logic_and /
                          sas_op_bin_logic_or  /
                          sas_op_bin_logic_not /
                          sas_op_bin_is        /
                          sas_op_bin_in        /
                          sas_op_bin_not_in)
sas_op_bin_logic_and  := ('&' / kwand), ?-[a-zA-Z0-9_]
sas_op_bin_logic_or   := [|!¦] / (kwor, ?-[a-zA-Z0-9_])
sas_op_bin_logic_not  := [~^¬] / (kwnot, ?-[a-zA-Z0-9_])
sas_op_bin_is         := kwis, ?-[a-zA-Z0-9_]
sas_op_bin_in         := kwin, ?-[a-zA-Z0-9_]
sas_op_bin_not_in     := kwnot, space+, kwin, ?-[a-zA-Z_]
sas_op_between        := kwbetween, space*, sas_expr_scalar, space*, kwand, space*, sas_expr_scalar

sas_val_int_range     := integer, ':', integer

data_stmt          := kwdata, spacecom+, data_body_sets, spacecom*, ';', data_body?
data_body_sets     := spacecom*, data_body_set, (spacecom*, data_body_set)*
data_body_set      := sas_identifier, spacecom*, data_body_set_opts?
data_body_set_opts := '(', spacecom*, data_body_set_opt_list, spacecom*, ')'
data_body_set_opt_list := data_body_set_opt, (spacecom*, data_body_set_opt)*
data_body_set_opt  := data_body_alter  /
                      data_body_delete /
                      data_body_drop   /
                      data_body_in     /
                      data_body_keep   /
                      data_body_modify /
                      data_body_obs    /
                      data_body_rename /
                      data_body_where  /
                      data_body_write
data_body_alter    := kwalter,  spacecom*, '=', spacecom*, pseudoident_list_kvsafe
data_body_delete   := kwdelete, spacecom*, '=', spacecom*, pseudoident_list_kvsafe
data_body_drop     := kwdrop,   spacecom*, '=', spacecom*, pseudoident_list_kvsafe
data_body_in       := kwin,     spacecom*, '=', spacecom*, pseudoident
data_body_keep     := kwkeep,   spacecom*, '=', spacecom*, pseudoident_list_kvsafe
data_body_modify   := kwmodify, spacecom*, '=', spacecom*, ident, spacecom*, ';'
data_body_obs      := kwobs,    spacecom*, '=', spacecom*, intmax
data_body_rename   := kwrename, spacecom*, '=', spacecom*, '(', spacecom*, keyval_list, spacecom*, ')'
data_body_where    := kwwhere,  spacecom*, '=', spacecom*, sas_expr
data_body_write    := kwwrite,  spacecom*, '=', spacecom*, pseudoident_list_kvsafe

data_body          := spacecom*, data_body_stmt, (spacecom*, data_body_stmt)*
data_body_stmt     := (data_body_stmt_by     /
                       data_body_stmt_drop   /
                       data_body_stmt_if     /
                       data_body_stmt_else   /
                       data_body_stmt_label  /
                       data_body_stmt_keep   /
                       data_body_stmt_merge  /
                       data_body_stmt_rename /
                       data_body_stmt_retain /
                       data_body_stmt_set    /
                       data_body_stmt_where  /
                       toplevel)
data_body_stmt_by     := kwby,     spacecom+, pseudoident_list, spacecom*, ';'
data_body_stmt_drop   := kwdrop,   spacecom+, pseudoident_list, spacecom*, ';'
data_body_stmt_if     := kwif,     spacecom+, sas_expr, spacecom*, ';'
data_body_stmt_else   := kwelse,   spacecom+, sas_expr, spacecom*, ';'
data_body_stmt_label  := kwlabel,  spacecom+, semistmt
data_body_stmt_keep   := kwkeep,   spacecom+, pseudoident_list_kvsafe, spacecom*, ';'
data_body_stmt_merge  := kwmerge,  spacecom+, data_body_sets, spacecom*, ';'
data_body_stmt_rename := kwrename, spacecom+, keyval_list, spacecom*, ';'
data_body_stmt_retain := kwretain, spacecom+, sas_expr_list, spacecom*, ';'
data_body_stmt_set    := kwset,    spacecom*, data_body_sets, spacecom*, ';'
data_body_stmt_where  := kwwhere,  (spacecom*, kwalso)?, spacecom*, sas_expr, spacecom*, ';'


# one filter expr to rule them all
sas_filter_expr     := '(', spacecom*, sas_filter_expr_list, spacecom*, ')'
sas_filter_expr_list:= sas_filter_expr_opt, (spacecom*, sas_filter_expr_opt)*

sas_filter_expr_opt := filter_opt_alter  /
                       filter_opt_delete /
                       filter_opt_drop   /
                       filter_opt_in     /
                       filter_opt_keep   /
                       filter_opt_modify /
                       filter_opt_obs    /
                       filter_opt_rename /
                       filter_opt_where  /
                       filter_opt_write
filter_opt_alter    := kwalter,  spacecom*, '=', spacecom*, pseudoident_list_kvsafe
filter_opt_delete   := kwdelete, spacecom*, '=', spacecom*, pseudoident_list_kvsafe
filter_opt_drop     := kwdrop,   spacecom*, '=', spacecom*, pseudoident_list_kvsafe
filter_opt_in       := kwin,     spacecom*, '=', spacecom*, pseudoident
filter_opt_keep     := kwkeep,   spacecom*, '=', spacecom*, pseudoident_list_kvsafe
filter_opt_modify   := kwmodify, spacecom*, '=', spacecom*, ident, spacecom*, ';'
filter_opt_obs      := kwobs,    spacecom*, '=', spacecom*, intmax
filter_opt_rename   := kwrename, spacecom*, '=', spacecom*, '(', spacecom*, keyval_list, spacecom*, ')'
filter_opt_where    := kwwhere,  spacecom*, '=', spacecom*, sas_expr
filter_opt_write    := kwwrite,  spacecom*, '=', spacecom*, pseudoident_list_kvsafe


proc_block := proc_stmt, space?, (run_stmt / quit_stmt)

proc_stmt    := (proc_catalog   /
                 proc_cimport   /
                 proc_contents  /
                 proc_corr      /
                 proc_datasets  /
                 proc_export    /
                 proc_format    /
                 proc_freq      /
                 proc_gmap      /
                 proc_gremove   /
                 proc_import    /
                 proc_means     /
                 proc_options   /
                 proc_print     /
                 proc_pwencode  /
                 proc_rank      /
                 proc_report    /
                 proc_sgpanel   /
                 proc_sgplot    /
                 proc_sort      /
                 proc_sql       /
                 proc_template  /
                 proc_transpose /
                 proc_univariate)

proc_sgplot          := kwproc, spaces1, kwsgplot, spacecom*, proc_sgplot_opts?, spacecom*, ';', spacecom*, proc_sgplot_body?
proc_sgplot_opts     := proc_sgplot_opt, (space*, proc_sgplot_opt)*
proc_sgplot_opt      := (proc_sgplot_opt_data /
                         proc_sgplot_opt_noautolegend)
proc_sgplot_opt_data        := kwdata, space?, '=', space?, sas_identifier, proc_sgplot_opt_data_expr?
proc_sgplot_opt_data_expr   := spacecom*, '(', spacecom*, proc_sgplot_data_exprs, spacecom*, ')'
proc_sgplot_data_exprs      := proc_sgplot_data_expr, (spacecom*, proc_sgplot_data_expr)*
proc_sgplot_data_expr       := proc_sgplot_data_expr_where
proc_sgplot_data_expr_where := kwwhere, spacecom*, '=', spacecom*, sas_expr
proc_sgplot_opt_noautolegend := kwnoautolegend
proc_sgplot_body     := proc_sgplot_body_stmt, (spacecom*, proc_sgplot_body_stmt)*
proc_sgplot_body_stmt:= (proc_sgplot_by        /
                         proc_sgplot_format    /
                         proc_sgplot_keylegend /
                         proc_sgplot_title     /
                         proc_sgplot_vbar      /
                         proc_sgplot_vline     /
                         proc_sgplot_where     /
                         proc_sgplot_yaxis)
proc_sgplot_by       := kwby, space?, semistmt
proc_sgplot_format   := kwformat, space?, semistmt
proc_sgplot_keylegend:= kwkeylegend, space?, semistmt
proc_sgplot_title    := kwtitle, space?, semistmt
proc_sgplot_vbar     := kwvbar, space?, semistmt
proc_sgplot_vline    := kwvline, space?, semistmt
proc_sgplot_where    := kwwhere, space?, sas_expr, spacecom*, ';'
proc_sgplot_yaxis    := kwyaxis, space?, semistmt


proc_sgpanel         := kwproc, spaces1, kwsgpanel, space?, proc_sgpanel_opts?, space*, ';', spacecom*, proc_sgpanel_body?
proc_sgpanel_opts    := proc_sgpanel_opt, (space*, proc_sgpanel_opt)*
proc_sgpanel_opt     := proc_sgpanel_opt_data
proc_sgpanel_opt_data:= kwdata, space?, '=', space?, sas_identifier
proc_sgpanel_body    := proc_sgpanel_body_stmt, (spacecom*, proc_sgpanel_body_stmt)*
proc_sgpanel_body_stmt := (proc_sgpanel_colaxis   /
                           proc_sgpanel_footnote  /
                           proc_sgpanel_keylegend /
                           proc_sgpanel_panelby   /
                           proc_sgpanel_rowaxis   /
                           proc_sgpanel_title     /
                           proc_sgpanel_vline)
proc_sgpanel_colaxis  := kwcolaxis,   space?, semistmt
proc_sgpanel_footnote := kwfootnote,  integer,semistmt
proc_sgpanel_keylegend:= kwkeylegend, space?, semistmt
proc_sgpanel_panelby  := kwpanelby,   space?, semistmt
proc_sgpanel_rowaxis  := kwrowaxis,   space?, semistmt
proc_sgpanel_title    := kwtitle,     space?, semistmt
proc_sgpanel_vline    := kwvline,     space?, semistmt



proc_catalog          := kwproc, spaces1, kwcatalog, space?, proc_catalog_opts?, space*, ';', spacecom*, proc_catalog_body?
proc_catalog_opts     := proc_catalog_opt, (space*, proc_catalog_opt)*
proc_catalog_opt      := proc_catalog_opt_cat
proc_catalog_opt_cat    := (kwcatalog / kwcat / kwc), space?, '=', space?, (libref, '.')?, catalog
proc_catalog_body       := proc_catalog_body_stmt, (spacecom*, proc_catalog_body_stmt)*
proc_catalog_body_stmt  := proc_catalog_contents / proc_catalog_delete
proc_catalog_contents   := kwcontents, space?, semistmt
proc_catalog_delete     := kwdelete, space?, macrovar, space?, proc_catalog_delete_opts?, space?, ';'
proc_catalog_delete_opts      := '/', space*, proc_catalog_delete_opts_list
proc_catalog_delete_opts_list := 'et=macro'

catalog := catalog_parameterized / pseudoident
catalog_parameterized := '[', ident_list, ']'


# ref: http://support.sas.com/documentation/cdl/en/proc/61895/HTML/default/viewer.htm#a002473368.htm
proc_cimport          := kwproc, spaces1, kwcimport, space?, proc_cimport_opts?, space*, ';', spacecom*, proc_cimport_body?
proc_cimport_opts     := proc_cimport_opt, (space*, proc_cimport_opt)*
proc_cimport_opt      := proc_cimport_opt_data /
                         proc_cimport_opt_infile
proc_cimport_opt_data   := kwdata,   space?, '=', space?, sas_identifier
proc_cimport_opt_infile := kwinfile, space?, '=', space?, sas_identifier
proc_cimport_body       := proc_cimport_body_stmt, (spacecom*, proc_cimport_body_stmt)*
proc_cimport_body_stmt  := 'NOMATCH'


# ref: http://support.sas.com/documentation/cdl/en/proc/61895/HTML/default/viewer.htm#a000085768.htm
proc_contents           := kwproc, spaces1, kwcontents, spaces1?, proc_contents_opts?, space?, ';', proc_contents_body?
proc_contents_opts      := proc_contents_opt, (space?, proc_contents_opt)*
proc_contents_opt       := proc_contents_opt_data  /
                           proc_contents_opt_order /
                           proc_contents_opt_out   /
                           proc_contents_opt_noprint
proc_contents_opt_data  := kwdata,  space?, '=', space?, sas_identifier
proc_contents_opt_order := kworder, space?, '=', space?, ident_list
proc_contents_opt_out   := kwout,   space?, '=', space?, ident_list, space?, proc_contents_opt_out_options?
proc_contents_opt_out_options := '(', space?, kwkeep, space?, '=', space?, 'name', space?, ')'
proc_contents_opt_noprint:= kwnoprint
proc_contents_body      := (comment / space)*

# ref: http://support.sas.com/documentation/cdl/en/procstat/63104/HTML/default/viewer.htm#procstat_corr_sect003.htm
# ref: corr plots http://support.sas.com/documentation/cdl/en/procstat/63104/HTML/default/viewer.htm#procstat_corr_sect034.htm
proc_corr            := kwproc, spacecom+, kwcorr, spacecom+, proc_corr_opts?, spacecom*, ';', spacecom*, proc_corr_body?
proc_corr_opts       := proc_corr_opt, (spacecom*, proc_corr_opt)*
proc_corr_opt        := proc_corr_opt_data   /
                        proc_corr_opt_nomiss /
                        proc_corr_opt_plots
proc_corr_opt_data   := kwdata, space?, '=', space?, ident
proc_corr_opt_nomiss := kwnomiss
# FIXME: this is a crummy hack, i can't figure out the syntax and it's only used once...
proc_corr_opt_plots  := kwplots, space?, '=', ('matrix(histogram) plots (maxpoints=none )')
proc_corr_body       := proc_corr_body_stmt, (spacecom*, proc_corr_body_stmt)*
proc_corr_body_stmt  := proc_corr_var
proc_corr_var        := kwvar, (space, ident)+, ';'

# ref: http://support.sas.com/documentation/cdl/en/proc/61895/HTML/default/viewer.htm#a000393161.htm
proc_datasets          := kwproc, spacecom*, kwdatasets, spacecom*, proc_datasets_opts?, spacecom*, ';', spacecom*, proc_datasets_body?
proc_datasets_opts     := proc_datasets_opt, (spacecom*, proc_datasets_opt)*
proc_datasets_opt      := (proc_datasets_opt_library
                            / proc_datasets_opt_kill
                            / proc_datasets_opt_nolist
                            / proc_datasets_opt_nowarn)
proc_datasets_opt_library:= (kwlibrary / kwlib), space?, '=', space?, identmacro
proc_datasets_opt_nowarn := kwnowarn
proc_datasets_opt_nolist := kwnolist
proc_datasets_opt_kill   := kwkill
proc_datasets_body       := proc_datasets_stmt, (spacecom*, proc_datasets_stmt)*
proc_datasets_stmt       := (proc_datasets_delete
                            / proc_datasets_modify
                            / proc_datasets_rename)
proc_datasets_delete     := kwdelete, space+,  pseudoident_list?, spacecom*, ';'
proc_datasets_modify     := kwmodify, spacecom*, ident, spacecom*, ';'
proc_datasets_rename     := kwrename, spacecom*, keyval_list, spacecom*, ';'

# ref: http://support.sas.com/documentation/cdl/en/procstat/63104/HTML/default/viewer.htm#procstat_freq_sect006.htm
proc_freq           := kwproc, spacecom*, kwfreq, spacecom*, proc_freq_opts, spacecom*, ';', spacecom*, proc_freq_body?
proc_freq_opts      := proc_freq_opt, (spacecom*, proc_freq_opt)*
proc_freq_opt       := proc_freq_opt_data /
                       proc_freq_opt_order /
                       proc_freq_opt_noprint
proc_freq_opt_data  := kwdata,  space?, '=', space?, sas_identifier
proc_freq_opt_order := kworder, space?, '=', space?, sas_identifier
proc_freq_opt_noprint:= kwnoprint
proc_freq_body      := proc_freq_body_stmt, (spacecom*, proc_freq_body_stmt)*
proc_freq_body_stmt := proc_freq_by       /
                       proc_freq_footnote /
                       proc_freq_format   /
                       proc_freq_table    /
                       proc_freq_title    /
                       proc_freq_where    /
                       titlenum           /
                       empty_stmt
proc_freq_by              := kwby, spacecom+, pseudoident_list, spacecom*, ';'
proc_freq_footnote        := kwfootnote, semistmt
proc_freq_format          := kwformat, spacecom+, semistmt
# NOTE: the table syntax has an embedded '*' in it, so you can't match comments, since *...; matches...
proc_freq_table           := (kwtables / kwtable), spacecom+, proc_freq_table_spec, spacecom*, ';'
proc_freq_table_spec      := ws_ident_list, space?, (space?, '*', space?, ws_ident_list)*, proc_freq_table_opts?
proc_freq_table_opts      := spacecom*, '/', spacecom*, proc_freq_table_opts_list
proc_freq_table_opts_list := proc_freq_table_opts_mod, (space, proc_freq_table_opts_mod)*
proc_freq_table_opts_mod  := kwlist / kwmissing /  proc_freq_table_out/ kwnocol / kwnofreq / kwnopercent / kwnorow
proc_freq_table_out       := kwout, spacecom*, '=', spacecom*, sas_identifier
proc_freq_title           := title_
proc_freq_where           := kwwhere, spacecom+, sas_expr?, spacecom*, ';'



proc_gmap          := kwproc, spacecom*, kwgmap, spacecom*, proc_gmap_opts?, spacecom*, ';', spacecom*, proc_gmap_body?
proc_gmap_opts     := proc_gmap_opt, (spacecom*, proc_gmap_opt)*
proc_gmap_opt      := proc_gmap_opt_anno /
                      proc_gmap_opt_data /
                      proc_gmap_opt_map
proc_gmap_opt_anno := kwanno, space?, '=', space?, sas_identifier
proc_gmap_opt_data := kwdata, space?, '=', space?, sas_identifier
proc_gmap_opt_map  := kwmap,  space?, '=', space?, sas_identifier
proc_gmap_body     := proc_gmap_stmt, (spacecom*, proc_gmap_stmt)*
proc_gmap_stmt     := proc_gmap_choro    /
                      proc_gmap_footnote /
                      proc_gmap_format   /
                      proc_gmap_id       /
                      proc_gmap_label    /
                      proc_gmap_title    /
                      proc_gmap_where
proc_gmap_choro    := kwchoro, semistmt
proc_gmap_footnote := kwfootnote, semistmt
proc_gmap_format   := kwformat, semistmt
proc_gmap_id       := kwid, spacecom+, pseudoident_list, spacecom*, ';'
proc_gmap_label    := kwlabel, semistmt
proc_gmap_title    := kwtitle, semistmt
proc_gmap_where    := kwwhere, spacecom*, sas_expr, spacecom*, ';'


proc_gremove          := kwproc, spacecom*, kwgremove, spacecom*, proc_gremove_opts?, spacecom*, ';', spacecom*, proc_gremove_body?
proc_gremove_opts     := proc_gremove_opt, (spacecom*, proc_gremove_opt)*
proc_gremove_opt      := proc_gremove_opt_data /
                         proc_gremove_opt_out
proc_gremove_opt_data := kwdata, space?, '=', space?, sas_identifier
proc_gremove_opt_out  := kwout,  space?, '=', space?, sas_identifier
proc_gremove_body     := proc_gremove_stmt, (spacecom*, proc_gremove_stmt)*
proc_gremove_stmt     := proc_gremove_by /
                         proc_gremove_id
proc_gremove_by       := kwby, spacecom+, pseudoident_list, spacecom*, ';'
proc_gremove_id       := kwid, spacecom+, pseudoident_list, spacecom*, ';'


# ref: http://support.sas.com/documentation/cdl/en/proc/61895/HTML/default/viewer.htm#a000316287.htm
proc_export             := kwproc, spacecom*, kwexport, spacecom*, proc_export_opts?, spacecom*, ';'
proc_export_opts        := proc_export_opt, (spacecom*,  proc_export_opt)*
proc_export_opt         := proc_export_opt_data    /
                           proc_export_opt_dbms    /
                           proc_export_opt_outfile /
                           proc_export_opt_replace
proc_export_opt_data    := kwdata, spaces1?, '=', spaces1?, (sas_expr, proc_export_opt_data_expr?)?
proc_export_opt_data_expr:= spacecom*, '(', spacecom*, kwdrop, spacecom*, '=', spacecom*, sas_expr_list?, spacecom*, ')'
proc_export_opt_dbms    := kwdbms, spaces1?, '=', spaces1?, dbms_opt
dbms_opt                := kwcsv / kwxlsx
proc_export_opt_outfile := kwoutfile, spaces1?, '=', (spaces1?, string)?
proc_export_opt_replace := kwreplace, (spacecom*, ident)?

# XXX: unimplemented
#proc_export_body        := proc_export_body_stmt, (spacecom*,  proc_export_body_stmt)*
#proc_export_body_stmt   := proc_export_data /
#                           proc_export_dbms /
#                           proc_export_outfile /
#                           proc_export_replace
proc_export_dbms        := kwdbms, spaces1?, '=', spaces1?, dbms_opt
proc_export_outfile     := kwoutfile, spaces1?, '=', (spaces1?, fileref)?
proc_export_replace     := kwreplace, (spacecom*, identmacro)?


proc_format             := kwproc, spacecom*, kwformat, spacecom*, proc_format_opts?, spacecom*, ';', spacecom*, proc_format_body?
proc_format_opts        := proc_format_opt, (spacecom*,  proc_format_opt)*
proc_format_opt         := proc_format_opt_cntlin /
                           proc_format_opt_fmtlib /
                           proc_format_opt_library
proc_format_opt_cntlin  := kwcntlin, spacecom*, '=', spacecom*, sas_identifier
proc_format_opt_fmtlib  := kwfmtlib
proc_format_opt_library := kwlibrary, spacecom*, '=', spacecom*, sas_identifier
proc_format_body        := proc_format_stmt, (spacecom*,  proc_format_stmt)*
proc_format_stmt        := proc_format_value
proc_format_value       := kwvalue, spacecom+, semistmt


# ref: http://support.sas.com/documentation/cdl/en/proc/61895/HTML/default/viewer.htm#a000308090.htm
proc_import              := kwproc, spacecom*, kwimport, spacecom*, proc_import_opts?, spacecom*, ';'
proc_import_opts         := proc_import_opt, (spacecom*, proc_import_opt)*
proc_import_opt          := proc_import_opt_datafile /
                            proc_import_opt_dbms     /
                            proc_import_opt_out      /
                            proc_import_opt_replace
proc_import_opt_datafile := kwdatafile, spaces1?, '=', spaces1?, fileref
proc_import_opt_dbms     := kwdbms,     spaces1?, '=', spaces1?, dbms_opt
proc_import_opt_out      := kwout,      spaces1?, '=', proc_import_opt_out_spec?
proc_import_opt_out_spec := spaces1?, fileref, (spacecom*, sas_expr)?
proc_import_opt_replace  := kwreplace, (spacecom*, ident)?
#proc_import_body        := proc_import_body_stmt, (spacecom*,  proc_import_body_stmt)*


# ref: http://support.sas.com/documentation/cdl/en/proc/61895/HTML/default/viewer.htm#a002473537.htm
proc_means           := kwproc, spacecom+,
                        kwmeans, ?-[a-zA-Z_], spacecom*,
                        proc_means_opts?, spacecom*, ';', spacecom*,
                        proc_means_body?
proc_means_opts      := proc_means_opt, (spacecom*, proc_means_opt)*
proc_means_opt       := proc_means_opt_data    /
                        proc_means_opt_maxdec  /
                        proc_means_opt_max     /
                        proc_means_opt_mean    /
                        proc_means_opt_min     /
                        proc_means_opt_nmiss   /
                        proc_means_opt_noprint /
                        proc_means_opt_nway    /
                        proc_means_opt_n       /
                        proc_means_opt_percentile /
                        proc_means_opt_var     /
                        proc_means_opt_stderr  /
                        proc_means_opt_std
proc_means_opt_data    := kwdata, space?, '=', spacecom*, pseudoident_list_kvsafe, proc_means_data_parens?
proc_means_data_parens := spacecom*, '(', spacecom*, kwdrop, spacecom*, '=', spacecom*, sas_expr_list?, spacecom*, ')'
proc_means_opt_maxdec  := kwmaxdec, spacecom*, '=', spacecom*, integer
proc_means_opt_max     := kwmax
proc_means_opt_mean    := kwmean
proc_means_opt_min     := kwmin
proc_means_opt_nmiss   := kwnmiss
proc_means_opt_nway    := kwnway
proc_means_opt_noprint := kwnoprint
proc_means_opt_n       := kwn
proc_means_opt_percentile := kwp, integer, ?-[a-zA-Z0-9_]
proc_means_opt_var     := kwvar
proc_means_opt_std     := kwstd
proc_means_opt_stderr  := kwstderr
proc_means_body        := proc_means_stmt, (spacecom*, proc_means_stmt)*
proc_means_stmt        := proc_means_by     /
                          proc_means_class  /
                          proc_means_format /
                          proc_means_output /
                          proc_means_var    /
                          proc_means_where
proc_means_by        := kwby,     spacecom+, pseudoident_list, spacecom*, ';'
proc_means_class     := kwclass,  spacecom+, pseudoident_list, spacecom*, ';'
proc_means_format    := kwformat, spacecom*, semistmt
proc_means_output    := kwoutput, spacecom*, semistmt
proc_means_var       := kwvar,    space+, pseudoident_list, space*, ';'
proc_means_where     := kwwhere,  space, sas_expr, spacecom*, ';'


proc_options             := kwproc, spacecom*, kwoptions, spacecom*, proc_options_opts?, spacecom*, ';'
proc_options_opts        := proc_options_opt, (spacecom*, proc_options_opt)*
proc_options_opt         := proc_options_opt_group /
                            proc_options_opt_option
proc_options_opt_group   := kwgroup, spaces1?, '=', spaces1?, proc_options_group_ident
proc_options_group_ident := 'memory' / 'performance'
proc_options_opt_option  := kwoption, spaces1?, '=', spaces1?, proc_options_opt_option_ident
proc_options_opt_option_ident := kwmemsize / kwsortsize / kwsumsize


proc_print          := kwproc, spacecom*, kwprint, spacecom*, proc_print_opts?, spacecom*, ';', spacecom*, proc_print_body?
proc_print_opts     := proc_print_opt, (spacecom*, proc_print_opt)*
proc_print_opt      := proc_print_opt_data  /
                       proc_print_opt_label /
                       proc_print_opt_noobs /
                       proc_print_opt_obs   /
                       proc_print_opt_split /
                       proc_print_opt_width
proc_print_opt_data := kwdata, space?, '=', space?, sas_identifier, proc_print_data_paren?
proc_print_opt_label:= kwlabel
proc_print_opt_obs  := (kwno, spacecom+), kwobs
proc_print_opt_noobs:= kwnoobs
proc_print_opt_split:= kwsplit, space?, '=', space?, string
proc_print_opt_width:= (kwwidth, space?, '=', space?, (kwfull / kwminimum / kwuniformby / kwuniform)) / 'U' / 'MIN' / 'UBY'
proc_print_data_paren:= spacecom*, '(', -')'*, ')'
proc_print_body     := proc_print_stmt, (spacecom*, proc_print_stmt)*
proc_print_stmt     := proc_print_format /
                       proc_print_label /
                       proc_print_title /
                       proc_print_where /
                       proc_print_var
proc_print_format   := kwformat, spacecom*, semistmt
proc_print_label    := kwlabel, spacecom*, semistmt
proc_print_title    := kwtitle, spacecom*, string, spacecom*, ';'
proc_print_var      := kwvar, ?-[a-zA-Z0-9_], spacecom*, pseudoident_list, (spacecom*, proc_print_var_opts)?, spacecom*, ';'
proc_print_var_opts := '/', spacecom*, kwstyle, spacecom*, '=', spacecom*, '{', spacecom*, keyval_list, spacecom*, '}'
proc_print_where    := kwwhere, spacecom*, sas_expr?, spacecom*, ';'


proc_pwencode       := kwproc, spaces1, kwpwencode, space+, proc_pwencode_opts, space*, ';'
proc_pwencode_opts  := proc_pwencode_opt, (space*, proc_pwencode_opt)*
proc_pwencode_opt   := proc_pwencode_opt_in  /
                       proc_pwencode_opt_out /
                       proc_pwencode_opt_method
proc_pwencode_opt_in     := kwin,  space?, '=', space?, string
proc_pwencode_opt_out    := kwout, space?, '=', space?, fileref
proc_pwencode_opt_method := kwin,  space?, '=', space?, pwenc_encoding_method
fileref               := fileref_abspath / string / sas_identifier
fileref_abspath       := filepath_unixlike / filepath_windowslike
filepath_unixlike     := '/', [a-zA-z]+, [^;)"']*
filepath_windowslike  := [a-zA-Z], ':', ('/' / [\\]), [a-zA-Z_ /\\-]*
pwenc_encoding_method := 'sas001' / 'sas002' / 'sas003'

# ref: http://support.sas.com/documentation/cdl/en/proc/61895/HTML/default/viewer.htm#a000146840.htm
proc_rank           := kwproc, spaces1, kwrank, spacecom*, proc_rank_opts?, spacecom*, ';', spacecom*, proc_rank_body?
proc_rank_opts      := proc_rank_opt, (spacecom*, proc_rank_opt)*
proc_rank_opt       := proc_rank_opt_data        /
                       proc_rank_opt_descending  /
                       proc_rank_opt_groups      /
                       proc_rank_opt_out         /
                       proc_rank_opt_ties
proc_rank_opt_data  := kwdata, space?, '=', space?, (?-((kwdata / kwgroups / kwout / kwdescending), spacecom*, '='), ident)?
proc_rank_opt_descending := kwdescending
proc_rank_opt_groups:= kwgroups, space?, '=', space?, integer
proc_rank_opt_out   := kwout, space?, '=', space?, (?-((kwdata / kwgroups / kwout / kwdescending), spacecom*, '='), ident)?, (space?, sas_filter_expr)?
proc_rank_opt_ties  := kwties, space?, '=', space?, proc_rank_opt_ties_val
proc_rank_opt_ties_val := (kwhigh / kwlow / kwmean / kwdense), (space, (kwascending / kwdescending))?
proc_rank_body      := proc_rank_stmt, (spacecom*, proc_rank_stmt)*
proc_rank_stmt      := proc_rank_by    /
                       proc_rank_ranks /
                       proc_rank_where /
                       proc_rank_var
proc_rank_by        := kwby, proc_rank_by_var*, space?, ';'
proc_rank_by_var    := spaces1?, kwdescending?, space?, identmacro
proc_rank_ranks     := kwranks, space, semistmt
proc_rank_where     := kwwhere, space, semistmt
proc_rank_var       := kwvar, space, semistmt


proc_report           := kwproc, spaces1, kwreport, spacecom*, proc_report_opts?, spacecom*, ';', spacecom*, proc_report_body?
proc_report_opts      := proc_report_opt, (spacecom*, proc_report_opt)*
proc_report_opt       := proc_report_opt_data  /
                         proc_report_opt_nofs  /
                         proc_report_opt_nowin /
                         proc_report_opt_split
proc_report_opt_data  := kwdata, space?, '=', space?, sas_identifier
proc_report_opt_nofs  := kwnofs
proc_report_opt_nowin := kwnowindows
proc_report_opt_split := kwsplit, space?, '=', space?, string
proc_report_body      := proc_report_stmt, (spacecom*, proc_report_stmt)*
proc_report_stmt      := proc_report_col    /
                         proc_report_define /
                         proc_report_where
proc_report_col       := (kwcolumn / kwcol), spacecom+, semistmt
proc_report_col_def_list := proc_report_col_def, (spacecom*, proc_report_col_def)*
proc_report_col_def   := '(', spacecom*, string, spacecom+, ident_list, spacecom*, ')'
proc_report_define    := kwdefine, spacecom+, semistmt
proc_report_where     := kwwhere,  spacecom+, sas_expr, spacecom*, ';'



# NOTE: this is a catch-all "parse until a semicolon" used as a first pass against scary clauses we can't parse
# once we can actually parse everything, all references to this should be deleted and it should go away
semistmt             := -';'*, ';'

# ref: http://support.sas.com/documentation/cdl/en/proc/61895/HTML/default/viewer.htm#a002294523.htm
proc_sql             := kwproc, spaces1, kwsql, spacecom*, proc_sql_opts?, spacecom*, ';', spacecom*, proc_sql_body
proc_sql_opts        := proc_sql_opt, (spacecom*, proc_sql_opt)*
proc_sql_opt         := proc_sql_opt_outobs  /
                        proc_sql_opt_noprint /
                        proc_sql_opt_nowarn
proc_sql_opt_outobs  := kwoutobs, spacecom*, '=', spacecom*, intmax
proc_sql_opt_noprint := kwnoprint
proc_sql_opt_nowarn  := kwnowarn
intmax               := integer / kwmax

proc_sql_body     := proc_sql_stmt*
proc_sql_stmt     := space_                /
                     sql_comment           /
                     spacesql              /
                     sql_stmt_create_table /
                     sql_stmt_create_view  /
                     sql_expr_select       /
                     proc_sql_query        /
                     comment               /
                     title_stmt            /
                     empty_stmt
proc_sql_query    := space?, sqlstart, space, semistmt

sqlstart          := kwalter    /
                     #kwcreate # parsed for real
                     kwdelete   /
                     kwdescribe /
                     kwdrop     /
                     kwinsert   /
                     kwreset    /
                     #kwselect  /
                     kwupdate   /
                     kwvalidate

space_ := space

sql_comment           := '--', -'\n'*, '\n'

spacesql              := space / commentmulti

# TODO: CTEs...
sql_query_select       := sql_expr_select /
                          sql_query_create_table /
                          sql_query_create_view

sql_stmt_create_table  := sql_query_create_table, spacesql*, ';'
sql_query_create_table := kwcreate, spacesql+,
                          kwtable, spacesql+,
                          sas_sql_ident_expr, spacesql+,
                          (sas_sql_create_table_expr, spacesql*)?,
                          kwas, spacesql+, sql_expr_create_table_as

sql_stmt_create_view   := sql_query_create_view, spacesql*, ';'
sql_query_create_view  := kwcreate, spacesql+,
                          kwview, spacesql+,
                          sas_sql_ident_expr, spacesql+,
                          (sas_sql_create_table_expr, spacesql*)?,
                          kwas, spacesql+, sql_expr_create_table_as

sas_sql_ident_expr    := sql_ident      /
                         sql_stringpart /
                         sas_brackets

sql_expr_create_table_as := sql_stmt_select_parens / sql_expr_select
sql_stmt_select_parens := '(', spacesql*, sql_expr_select, spacesql*, ')'

sas_sql_create_table_expr := '(', spacesql*, sas_sql_create_table_expr_opts, spacesql*, ')'
sas_sql_create_table_expr_opts := sas_sql_create_table_expr_opt, (spacesql*, sas_sql_create_table_expr_opt)*
sas_sql_create_table_expr_opt := sas_sql_create_table_alter_expr /
                                 sas_sql_create_table_drop_expr  /
                                 sas_sql_create_table_keep_expr  /
                                 sas_sql_create_table_rename_expr
sas_sql_create_table_alter_expr  := kwalter,  spacesql*, '=', spacesql*, sas_expr_list?
sas_sql_create_table_drop_expr   := kwdrop,   spacesql*, '=', spacesql*, sas_expr_list?
sas_sql_create_table_keep_expr   := kwkeep,   spacesql*, '=', spacesql*, sas_expr_list?
sas_sql_create_table_rename_expr := kwrename, spacesql*, '=', spacesql*, '(', spacesql*, keyval_list, spacesql*, ')'

sql_expr_select       := kwselect, ?-[a-zA-Z_],
                         sql_sas_expr_alias_list,
                         sql_stmt_into?,
                         sql_stmt_from?,
                         sql_stmt_join_list?,
                         sql_stmt_where?,
                         sql_stmt_groupby?,
                         sql_stmt_having?,
                         sql_stmt_orderby?,
                         sql_stmt_set?
sql_stmt_into         := spacesql*, kwinto, ?-[a-zA-Z_], spacesql*, sql_into_target_list
sql_into_target_list  := sql_into_target_expr, (spacesql*, ',', spacesql*, sql_into_target_expr)*
sql_into_target_expr  := sql_into_target, sql_into_separated?
sql_into_separated    := spacesql*, kwseparated, spacesql+, kwby, spacesql, string
sql_into_target       := sql_into_target_varrange / sql_into_target_var
sql_into_target_varrange := sql_into_target_var, spacesql*, '-', spacesql*, sql_into_target_var
sql_into_target_var      := ':', spacesql*, sql_ident

sql_stmt_from         := spacesql+, kwfrom, ?-[a-zA-Z_], spacesql*, sql_expr_alias_list
sql_stmt_join_list    := (spacesql*, sql_stmt_join)+
sql_stmt_join         := (spacesql*, (sql_stmt_join_mod, spacesql+)?, kwjoin, ?-[a-zA-Z_],
                          spacesql*, sql_joinable, sql_stmt_join_cond?)
sql_stmt_join_mod     := (kwinner /
                          kwouter /
                          (kwfull,  spacesql+, kwinner) /
                          (kwfull,  spacesql+, kwouter) /
                          (kwleft,  spacesql+, kwouter) /
                          (kwright, spacesql+, kwinner) /
                          kwfull /
                          kwleft /
                          kwright), ?-[a-zA-Z_]
sql_stmt_join_cond    := sql_stmt_join_on / sql_stmt_join_using
sql_stmt_join_on      := spacesql*, kwon, spacesql*, sql_expr
sql_stmt_join_using   := spacesql*, kwusing, spacesql*, '(', sql_ident_list, spacesql*, ')'
sql_ident_list        := spacesql*, sql_ident, (spacesql*, ',', spacesql* , sql_ident)*
sql_stmt_where        := spacesql*, kwwhere, ?-[a-zA-Z_], spacesql*, sql_expr
sql_stmt_groupby      := spacesql*, kwgroup, spacesql+, kwby, ?-[a-zA-Z_], spacesql*, sql_expr_list
sql_stmt_having       := spacesql*, kwhaving, ?-[a-zA-Z_], spacesql*, sql_expr
sql_stmt_orderby      := spacesql*, kworder, (spacesql+, kwby, ?-[a-zA-Z_])?, sql_stmt_orderby_list
sql_stmt_orderby_list := spacesql*, sql_stmt_orderby_expr, (spacesql*, ',', spacesql*, sql_stmt_orderby_expr)*
sql_stmt_orderby_expr := sql_expr, (spacesql*, sql_stmt_orderby_dir)?
sql_stmt_orderby_dir  := (sql_stmt_orderby_asc / sql_stmt_orderby_desc), ?-[a-zA-Z_]
sql_stmt_orderby_asc  := kwascending / kwasc
sql_stmt_orderby_desc := kwdescending / kwdesc
sql_stmt_set          := spacesql*, sql_sas_set_op, spacesql*, sql_expr_select
sql_joinable          := sql_expr, (spacesql*, sas_data_exprs_paren)?, spacesql*, sql_alias?
sql_expr_list         := sql_expr, (spacesql*, ',', spacesql*, sql_expr)*

#sql_expr_alias_list   := sql_expr_name, (spacesql*, ',', spacesql*, sql_expr_name)*
sql_expr_alias_list     := sql_expr_alias_item, sql_sas_expr_alias_next*
sql_expr_alias_item     := macro_if_then_end / sql_expr_name
sql_expr_alias_next     := spacesql*, ',', spacesql*, sql_expr_alias_item

#sql_sas_expr_alias_list := spacesql*, sql_sas_expr_name, sql_sas_expr_alias_list_next*
#sql_sas_expr_alias_list_next := spacesql*, (macro_if_then_end / (',', spacesql*, sql_sas_expr_name))

sql_sas_expr_alias_list := spacesql*, sql_sas_expr_alias_item, sql_sas_expr_alias_next*
sql_sas_expr_alias_item := sql_sas_expr_alias_item_macro_pair /
                           sql_sas_expr_alias_item_normal
sql_sas_expr_alias_item_macro_pair := macrovar, spacesql*, ?-sql_reserved, sql_sas_expr_name
sql_sas_expr_alias_item_normal := macro_if_then_end / sql_sas_expr_name
sql_sas_expr_alias_next := sql_sas_expr_alias_next_comma /
                           sql_sas_expr_alias_next_nocomma
sql_sas_expr_alias_next_comma := spacesql*, ',', spacesql*, sql_sas_expr_alias_item
sql_sas_expr_alias_next_nocomma := spacesql*, sql_sas_expr_alias_item


sql_sas_expr_name     := sql_expr_name, sql_sas_column_mods?
sql_sas_column_mods   := spacesql+, sql_sas_column_mod, (spacesql*, sql_sas_column_mod)*

# ref: http://support.sas.com/documentation/cdl/en/proc/61895/HTML/default/viewer.htm#a002473684.htm
sql_sas_column_mod    := sql_sas_format_spec   /
                         sql_sas_informat_spec /
                         sql_sas_label_spec    /
                         sql_sas_length_spec
sql_sas_format_spec   := kwformat,   spacesql*, ('=', spacesql*)?, sas_format
sql_sas_informat_spec := kwinformat, spacesql*, ('=', spacesql*)?, sas_format
sql_sas_label_spec    := kwlabel,    spacesql*, ('=', spacesql*)?, string
sql_sas_length_spec   := kwlength,   spacesql*, ('=', spacesql*)?, integer

sql_expr_name         := sql_expr, (spacesql*, sas_data_exprs_paren)?,
                         (spacesql*, sql_alias)?,
                         (spacesql+, sas_sql_alias_label)?

sas_data_exprs_paren  := spacecom*, '(', spacecom*, sas_data_exprs, spacecom*, ')'
sas_data_exprs        := sas_data_expr, (spacecom*, sas_data_expr)*
sas_data_expr         := sas_data_expr_where
sas_data_expr_where   := kwwhere, spacecom*, '=', spacecom*, sas_expr

sql_alias             := (sql_alias_as / sql_alias_noas), sas_sql_alias_label?
sql_alias_as          := kwas, spacesql+, sql_ident
sql_alias_noas        := ?-sql_forbidden_alias, sql_ident
sas_sql_alias_label   := spacesql*, string

sql_expr              := macro_if_then_end / sql_value / sql_expr_subquery / sql_expr_tuple / sas_expr_tuple / sql_comment
sql_expr_subquery     := '(', spacesql*, sql_query_select, spacesql*, ')', (spacesql*, sql_alias)?
sql_expr_tuple        := '(', spacesql*, sql_expr_list, spacesql*, ')'
sql_value             := sql_expr_binop / sql_expr_scalar
sql_expr_binop        := sql_expr_scalar, spacesql*, sql_expr_bin_op_val
sql_expr_bin_op_val   := sql_expr_bin_general / sql_op_between
sql_expr_bin_general  := sql_op_bin, spacesql*, sql_expr
sql_expr_scalar       := (sql_expr_subquery /
                          sas_expr_tuple    /
                          sql_expr_tuple    /
                          sql_expr_case     /
                          sql_expr_unary    /
                          sql_funcall       /
                          sql_ident         /
                          number            /
                          date_literal      /
                          sql_stringparts   /
                          macro             /
                          sas_brackets), sql_sas_column_mods?
sql_expr_unary         := sql_sas_op_unary, spacesql*, sql_expr
sql_sas_op_unary       := sql_op_unary / sql_sas_op_named
sql_sas_op_named       := kwcalculated / kwdistinct
sql_sas_set_op         := sql_sas_set_except      /
                          sql_sas_set_intersect   /
                          sql_sas_set_union       /
                          sql_sas_set_union_outer
sql_sas_set_except      := kwexcept,    (spacesql+, kwcorresponding)?, (spacesql+, kwall)?
sql_sas_set_intersect   := kwintersect, (spacesql+, kwcorresponding, (spacesql+, kwall)?)?
sql_sas_set_union       := kwunion,     (spacesql+, kwcorresponding)?, (spacesql+, kwall)?
sql_sas_set_union_outer := kwouter,      spacesql+, kwunion, (spacesql+, kwcorresponding)?
sql_expr_case           := kwcase, spacesql+, sql_expr_case_when_list, (spacesql*, sql_expr_case_else)?, spacesql*, kwend
sql_expr_case_when_list := (spacesql*, sql_expr_case_when)+
sql_expr_case_when      := kwwhen, spacesql*, sql_expr, spacesql*, kwthen, spacesql*, sql_expr
sql_expr_case_else      := kwelse, spacesql*, sql_expr

sql_funcall             := sql_funcall_builtin /
                           sas_funcall_builtin /
                           sql_funcall_udf /
                           sas_funcall_udf /
                           macro_call

# XXX: cannot just use sas_funcall, as the parameter syntax can diff? ugh...
sql_funcall_            := sql_ident, sql_funcall_params
sql_funcall_params      := '(', spacesql*, sql_expr_list?, spacesql*, ')'


sql_funcall_builtin     := sql_funcname_builtin, sql_funcall_params
sql_funcname_builtin    := kwany /
                           kwavg /
                           kwcoalesce /
                           kwcount /
                           kwexists /
                           kwmax /
                           kwmin /
                           kwnow /
                           kwnullif /
                           kwsum


sql_funcall_udf         := sql_ident, sql_funcall_params

sql_op_bin              := sql_op_bin_op / sql_op_bin_cmp / sql_op_bin_logic
sql_op_bin_op           := '+' / '-' / '**' / '*' / '/' / '||'
sql_op_bin_cmp          := '=' / '!=' / '~=' / '<>' / '<=' / '<' / '>=' / '>' / (kwne / kwle / kwlt / kwge / kwgt, ?-[a-zA-Z0-9_])
# NOTE: negative lookahead assertion to prevent "SELECT 1 ORDER" from turning into "SELECT 1 [OR]DER..."
sql_op_bin_logic        := (kwand / kwor / kwis / kwin / sql_op_bin_not_in / kwlike / kwcontains), ?-[a-zA-Z0-9_]
sql_op_bin_not_in       := kwnot, spacesql+, (sql_op_bin_in / sql_op_bin_not_in)
sql_op_bin_in           := kwin, ?-[a-zA-Z0-9_]
sql_op_unary            := '+' / '-' / ('~', ?-'=') / (kwnot, ?-[a-zA-Z0-9_])
# XXX: this is a hack to avoid consuming the 'AND'...
sql_op_between          := kwbetween, ?-[a-zA-Z_], spacesql*, sql_expr_scalar, spacesql*, kwand, ?-[a-zA-Z_], spacesql*, sql_value
sql_ident               := sql_star /
                           sql_sas_ident_special /
                           sql_null /
                           #sql_sas_macro_pair /
                          (sql_identmacro, ?-[.a-zA-Z_])

# "foo.bar"
# "foo .bar"
sql_identmacro := identmacro, (spacesql*, '.', spacesql*, identmacro)*

sql_null              := kwnull, ?-[a-zA-Z0-9_]
# XXX: allow a macro to exist in a list without a comma, ugh
sql_sas_macro_pair    := macrovar, spacesql*, ?-sql_reserved, sql_expr_scalar
sql_sas_ident_special := sas_format / ('.', ?-[0-9])
sql_star              := sql_star_dot / sql_dot_star
sql_star_dot          := '*', ('.', sas_identifier)?
sql_dot_star          := (sas_identifier, '.')+, '*'
sql_stringparts       := sql_stringpart, (spacesql*, sql_stringpart)*
sql_stringpart        := ?-sql_reserved, (string / sas_identifier / macrovar)


sql_forbidden_alias   := sql_reserved / kworder

# reserved sql identifiers; disallow juxtaposed aliases
sql_reserved          := (kwalter   /
                          kwand     /
                          kwasc     /
                          #kwas     /
                          kwbetween /
                          kwby      /
                          kwcase    /
                          kwcreate  /
                          kwdelete  /
                          kwdesc    /
                          kwdrop    /
                          kwelse    /
                          kwend     /
                          kwformat  / # FIXME: a hack to support non-standard 'ident formmat=YYMMDD10.' syntax...
                          kwfrom    /
                          kwgroup   /
                          kwhaving  /
                          kwinner   /
                          kwinsert  /
                          kwinto    /
                          #kwin     /
                          kwis      /
                          kwjoin    /
                          kwleft    /
                          kwnot     /
                          kwnull    /
                          kwon      /
                          kworder   / # longer ORDER must precent OR
                          kwor      /
                          kwouter   /
                          kwselect  /
                          kwthen    /
                          kwunion   /
                          kwupdate  /
                          kwusing   /
                          kwwhen    /
                          kwwhere), ?-[a-zA-Z0-9_]

#ref: http://support.sas.com/documentation/cdl/en/proc/61895/HTML/default/viewer.htm#a002473662.htm
proc_sort                := kwproc, spaces1, kwsort, space*, proc_sort_opts?, spacecom*, ';', spacecom*, proc_sort_body?
proc_sort_opts           := proc_sort_opt, (spacecom*, proc_sort_opt)*
proc_sort_opt            := proc_sort_opt_data      /
                            proc_sort_opt_dupout    /
                            proc_sort_opt_out       /
                            proc_sort_opt_nodupekey /
                            proc_sort_opt_parens
proc_sort_opt_data       := kwdata, space?, '=', space?, sas_identifier, proc_sort_opt_data_keep?
proc_sort_opt_data_keep  := space?, '(', space?, kwkeep, space?, '=', space?, ident, (space, ident)*, space?, ')'
proc_sort_opt_dupout     := kwdupout, space?, '=', space?, identmacro
proc_sort_opt_out        := kwout, space?, '=', space?, sas_identifier #, (space, identmacro)*, (space?, proc_sort_opt_out_drop)?
proc_sort_opt_out_drop   := '(', kwdrop, space?, '=', space?,  proc_opt_drop_ident_list?, space?, ')'
proc_opt_drop_ident_list := proc_opt_drop_ident, (space*, proc_opt_drop_ident)*
proc_opt_drop_ident      := pseudoident
proc_sort_opt_parens     := sas_expr
proc_sort_opt_nodupekey  := kwnodupkey
proc_sort_body           := proc_sort_body_stmt, (spacecom*, proc_sort_body_stmt)*
proc_sort_body_stmt      := proc_sort_by / proc_sort_key / proc_sort_where / empty_stmt
proc_sort_by             := kwby, proc_sort_by_var+, spacecom*, ';'
proc_sort_by_var         := spacecom*, kwdescending?, spacecom*, identmacro
proc_sort_key            := kwkey, spaces1, semistmt
proc_sort_where          := kwwhere, spacecom+, sas_expr, spacecom*, ';'


# ref: http://support.sas.com/documentation/cdl/en/proc/61895/HTML/default/viewer.htm#a000063662.htm
proc_template            := kwproc, spaces1, kwtemplate, spacecom*, ';', spacecom*, proc_template_body?
proc_template_body       := proc_template_stmt, (spacecom*, proc_template_stmt)*
proc_template_stmt       := proc_template_list
proc_template_list       := kwlist, spacecom*, ('styles' / 'tagsets'), spacecom*, ';'


# ref: http://support.sas.com/documentation/cdl/en/proc/61895/HTML/default/viewer.htm#a000063662.htm
proc_transpose           := kwproc, spaces1, kwtranspose, spacecom*, proc_transpose_opts?, spacecom*, ';', spacecom*, proc_transpose_body?
proc_transpose_opts      := proc_transpose_opt, (spacecom*, proc_transpose_opt)*
proc_transpose_opt       := proc_transpose_opt_data /
                            proc_transpose_opt_out  /
                            proc_transpose_opt_prefix
proc_transpose_opt_data      := kwdata, space?, '=', space?, sas_identifier, proc_transpose_opt_data_keep?
proc_transpose_opt_data_keep := space?, '(', space?, kwkeep, space?, '=', space?, list_of_variables, space?, ')'
proc_transpose_opt_out       := kwout, space?, '=', space?, sas_identifier, proc_transpose_opt_out_opts?
proc_transpose_opt_prefix    := kwprefix, space?, '=', space?, sas_identifier
proc_transpose_opt_out_opts  := space?, '(', space?, out_opts, space?, ')'
out_opts                     := out_opt, (spacecom*, out_opt)*
out_opt                      := out_opt_drop   /
                                out_opt_rename /
                                out_opt_where
out_opt_drop            := kwdrop,   space?, '=', space?, ident_list_kvsafe
out_opt_out             := kwout,    space?, '=', space?, sas_identifier
out_opt_rename          := kwrename, space?, '=', space?, '(', space?, keyval_list, space?, ')'
out_opt_where           := kwwhere, space?, '=', space?, '(', space?, sas_expr, space?, ')'
proc_transpose_body     := proc_transpose_stmt, (spacecom*, proc_transpose_stmt)*
proc_transpose_stmt     := proc_transpose_by  /
                           proc_transpose_id  /
                           proc_transpose_var /
                           proc_transpose_where
proc_transpose_by       := kwby,    spacecom+, pseudoident_list, spacecom*, ';'
proc_transpose_id       := kwid,    spacecom+, pseudoident_list, spacecom*, ';'
proc_transpose_var      := kwvar,   spacecom+, pseudoident_list, spacecom*, ';'
proc_transpose_where    := kwwhere, spacecom+, sas_expr,         spacecom*, ';'


# ref: http://support.sas.com/documentation/cdl/en/procstat/63104/HTML/default/viewer.htm#procstat_univariate_sect008.htm
proc_univariate      := kwproc, spaces1, kwunivariate, spacecom*, proc_uni_opts, spacecom*, ';', spacecom*, proc_uni_body?
proc_uni_opts        := proc_uni_opt, (spacecom*, proc_uni_opt)*
proc_uni_opt         := proc_uni_opt_data / proc_uni_opt_noprint
proc_uni_opt_data    := kwdata, space?, '=', space?, sas_identifier
proc_uni_opt_noprint := kwnoprint
proc_uni_body        := proc_uni_stmt, (spacecom*, proc_uni_stmt)*
proc_uni_stmt        := proc_uni_class / proc_uni_histogram / proc_uni_var / proc_uni_where
proc_uni_histogram   := kwhistogram, spacecom+, semistmt
proc_uni_class       := kwclass, spacecom+, pseudoident_list, spacecom*, ';'
proc_uni_where       := kwwhere, spaces1, sas_expr, spacecom*, ';'
proc_uni_var         := kwvar, spaces1, semistmt

ods_stmt          := kwods, spacecom+, ods_stmt_opts, spacecom*, ';'
ods_stmt_opts     := ods_stmt_opt?
ods_stmt_opt      := ods_opt_all        /
                     ods_opt_escapechar /
                     ods_opt_excel      /
                     ods_opt_graphics   /
                     ods_opt_html       /
                     ods_opt_listing    /
                     ods_opt_tagsets    /
                     ods_opt_text
ods_opt_all       := kw_all_, spacecom*, kwclose
ods_opt_escapechar:= kwescapechar, spacecom*, '=', spacecom*, string
ods_opt_excel     := kwexcel, spacecom*, ods_excel_opts
ods_excel_opts    := ods_excel_opt, (spacecom*, ods_excel_opt)*
ods_excel_opt     := ods_excel_close   /
                     ods_excel_file    /
                     ods_excel_options /
                     ods_excel_style
ods_excel_close   := kwclose
ods_excel_file    := kwfile,     spacecom*, '=', spacecom*, string
ods_excel_options := kwoptions,  spacecom*, macro_params
ods_excel_style   := kwstyle,    spacecom*, '=', spacecom*, ident
ods_opt_html      := kwhtml,     spacecom*, kwclose
ods_opt_listing   := kwlisting,  spacecom+, kwclose
ods_opt_tagsets   := kwtagsets, '.', ods_opt_tagset
ods_opt_tagset    := ods_tagset_excelxp
ods_tagset_excelxp:= kwexcelxp,  spacecom*, ods_excel_opts
ods_opt_text      := kwtext,     spacecom*, '=', spacecom*, string
ods_opt_graphics  := kwgraphics, spacecom+, ods_graphics_opts
ods_graphics_opts := offon / ods_graphics_slash
ods_graphics_slash:= spacecom*, '/', spacecom*, ods_graphics_reset
ods_graphics_reset:= kwreset,    spacecom*, ods_reset_opts?
ods_reset_opts    := ods_reset_opt, (spacecom*, ods_reset_opt)*
ods_reset_opt     := ods_reset_imagemap / ods_reset_keyval
ods_reset_imagemap:= kwimagemap
ods_reset_keyval  := ident, spacecom*, '=', spacecom*, sas_expr
offon := kwoff / kwon


ws_ident_list       := ws_ident_list_paren / ws_ident_list_bare
ws_ident_list_paren := '(', ws_ident_list, ')'
ws_ident_list_bare  := pseudoident, (space,  pseudoident)*

pseudoident_list_kvsafe := pseudoident_kvsafe, (spacecom*, pseudoident_kvsafe)*
pseudoident_kvsafe      := pseudoident, ?-(spacecom*, '=')

pseudoident_list    := spacecom*, pseudoident, (spacecom*, pseudoident)*
pseudoident         := sas_label / sas_identifier

sas_identifier_list := sas_identifier, (space*, sas_identifier)*
sas_identifier      := sas_label /
                       identmacrodotted /
                       ('.', ?-[a-zA-Z0-9_])

# SAS's ridiculous syntax means we have to know when to stop on a whitespace-delimited tokenlist. ugh...
ident_list_kvsafe   := ident_kvsafe, (spacecom*, ident_kvsafe)*
ident_kvsafe        := ident, ?-(spacecom*, '=')

keyval_list_parens  := '(', spacecom*, keyval_list, spacecom*, ')'
keyval_list         := keyval_item, (spacecom*, keyval_item)*
keyval_item         := identmacro, spacecom*, '=', spacecom*, keyval_val
keyval_val          := pseudoident / string

# ref: http://support.sas.com/documentation/cdl/en/lrdict/64316/HTML/default/viewer.htm#a000204328.htm
sas_label           := identmacro, ':'

identmacrodotted    := identmacro, ('.', identmacro)*
identmacro          := (macrovar / ident / macro_call)+

macromacrovar       := '&', macrovar+, '.'?
# &&x&i.
# &&pr&p..

# macrovars can end with '.', but can also be dotted and not?
# &foo.
# &input._nodupe;
# work.sasmac1.&c___..macro
macrovar     := macromacrovar / macrovar_
macrovar_    := '&', ident , '.'?

ident_list   := ident, (spacecom*, ident)*

ident        := [a-zA-Z_] , [a-zA-Z0-9_]*


number       := float / integer
float        := ([0-9]+, '.', [0-9]*) / ('.', [0-9]+)
integer      := [0-9]+
string       := stringdq / stringsq
stringsq     := "'", strsqtxt, "'"
stringdq     := '"', strdqtxt, '"'
strdqtxt     := (('%', "'"?) / '""' / -'"')*
strsqtxt     := (('%', '"'?) / "''" / -"'")*
spacecom     := space / comment
space        := [ \t\r\n\v\f\u2002\x1a]+
spaces1      := [ \t\v\f\u2002]+
comment      := commentmulti / comment1line
comment1line := "*", -';'*, ';'
commentmulti := '/*', -'*/'*, '*/'
sas_brackets := '[', -']'*, ']'  # XXX: no idea what this is

newline      := [\r\n]+


# some of the weirder datatypes in the SAS zoo

sas_format              := sas_format_date  /
                           sas_format_money /
                           sas_format_str   /
                           sas_format_num   /
                           sas_format_unknown
sas_format_date         := sas_date_format_dt14      / # longer matches first...
                           sas_date_format_date9     /
                           sas_date_format_date7     /
                           sas_date_format_date      /
                           sas_date_format_monname   /
                           sas_date_format_monyy7    /
                           sas_date_format_mmyys     /
                           sas_date_format_mmddyy10  /
                           sas_date_format_mmddyys10 /
                           sas_date_format_mmddyys   /
                           sas_date_format_time20    /
                           sas_date_format_yymmdd10  /
                           sas_date_format_yymms7    /
                           sas_date_format_yyqs9
sas_date_format_dt14     := 'datetime14.' / 'DATETIME14.'
sas_date_format_date9    := 'date9.' / 'DATE9.'
sas_date_format_date7    := 'date7.' / 'DATE7.'
sas_date_format_date     := 'date.' / 'DATE.'
sas_date_format_monname  := 'monname.' / 'MONNAME.'
sas_date_format_monyy7   := 'monyy7.' / 'MONYY7.'
sas_date_format_mmddyy10 := 'mmddyy10.' / 'MMDDYY10.'
sas_date_format_mmddyys10:= 'mmddyys10.' / 'MMDDYYS10.'
sas_date_format_mmddyys  := 'mmddyys.' / 'MMDDYYS.'
sas_date_format_mmyys    := 'mmyys.' / 'MMYYS.'
sas_date_format_time20   := 'time20.' / 'TIME20.'
sas_date_format_yymmdd10 := 'yymmdd10.' / 'YYMMDD10.'
sas_date_format_yymms7   := 'yymms7.' / 'YYMMS7.'
sas_date_format_yyqs9    := 'yyqs9.' / 'YYQS9.'

sas_format_money  := sas_format_dollar
sas_format_dollar := kwdollar, integer, '.', integer?

sas_format_str := sas_format_comma
# ref: http://support.sas.com/documentation/cdl/en/lrdict/64316/HTML/default/viewer.htm#a000200667.htm
sas_format_comma := kwcomma, integer, '.', integer?

sas_format_num := sas_format_numwdot /
                  sas_format_percent /
                  sas_format_zeroes
# ref: http://support.sas.com/documentation/cdl/en/lrdict/64316/HTML/default/viewer.htm#a000205114.htm
sas_format_numwdot := integer, '.', integer?
sas_format_percent := kwpercent, integer, '.', integer?
sas_format_zeroes  := kwz, integer, '.', integer?

# what are these?
sas_format_unknown := sas_format_dualf   /
                      sas_format_eligf   /
                      sas_format_provspf /
                      sas_format_srvcgf
sas_format_eligf := 'eligf.' / 'ELIGF.'
sas_format_dualf := 'dualf.' / 'DUALF.'
sas_format_provspf := '$provspf.' / '$PROVSPF.'
sas_format_srvcgf  := 'srvcgf.' / 'SRVCGF.'

# 64k, 2g, etc
valmemspec   := valkbsize / kwmax
valkbsize    := integer, (('k' / 'm' / 'g'), ?-[a-zA-Z0-9_])

date_literal := string, [dD], ?-[a-zA-Z0-9_]
'''
