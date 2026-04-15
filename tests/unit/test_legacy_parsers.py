"""Tests unitarios de parsers legacy F6: COBOL, PL/I, RPG, JCL, Natural, copybook resolver, registry."""
from __future__ import annotations
from pathlib import Path

import pytest

from oraculo.polyglot.L2_antlr.cobol_parser import parse_cobol
from oraculo.polyglot.L2_antlr.pli_parser import parse_pli
from oraculo.polyglot.L3_patterns.rpg_parser import parse_rpg
from oraculo.polyglot.L3_patterns.jcl_parser import parse_jcl
from oraculo.polyglot.L3_patterns.natural_parser import parse_natural
from oraculo.polyglot.resolvers.copybook_resolver import CopybookResolver, CopybookIndex
from oraculo.polyglot.parser_registry import parse_file, supported_languages
from oraculo.polyglot.dispatcher import ParserLevel


COBOL_SAMPLE = """\
000100 IDENTIFICATION DIVISION.
000200 PROGRAM-ID. CALCPAGO.
000300 ENVIRONMENT DIVISION.
000400 DATA DIVISION.
000500 WORKING-STORAGE SECTION.
000600 01  WS-TOTAL PIC 9(7)V99.
000700 01  WS-NOMBRE PIC X(30).
000800 PROCEDURE DIVISION.
000900     MAIN-PARA.
001000         PERFORM CALC-TOTAL
001100         PERFORM DISPLAY-RESULT
001200         STOP RUN.
001300     CALC-TOTAL.
001400         MOVE 100 TO WS-TOTAL.
001500     DISPLAY-RESULT.
001600         DISPLAY WS-TOTAL.
001700         COPY DATECOPY.
"""

PLI_SAMPLE = """\
MAINPROC: PROC OPTIONS(MAIN);
    DCL TOTAL FIXED DEC(7,2);
    DCL NAME CHAR(30);
    CALL CALC_TOTAL;
    CALL DISPLAY_RESULT;
END MAINPROC;

CALC_TOTAL: PROC;
    TOTAL = 100;
END CALC_TOTAL;
%INCLUDE DATEUTIL;
"""

RPG_SAMPLE = """\
     H DFTACTGRP(*NO)
     D total           S              7P 2
     D name            S             30A
     C                   EXSR      CalcTot
     C                   EXSR      Display
     C     CalcTot       BEGSR
     C                   EVAL      total = 100
     C                   ENDSR
     C     Display       BEGSR
     C                   DSPLY               total
     C                   ENDSR
"""

RPG_FREE_SAMPLE = """\
**FREE
DCL-S total Packed(7:2);
DCL-S name Char(30);
DCL-DS orderRec;
  orderNum Int(10);
END-DS;
DCL-PROC CalcTotal;
  total = 100;
END-PROC;
/COPY QRPGLESRC/DATEUTIL
"""

JCL_SAMPLE = """\
//PAYROLL  JOB (ACCT),'PAYROLL RUN',CLASS=A
//*  PAYROLL PROCESSING JOB
//STEP1    EXEC PGM=COBPAY01
//INFILE   DD DSN=PAYROLL.INPUT,DISP=SHR
//OUTFILE  DD DSN=PAYROLL.OUTPUT,DISP=(NEW,CATLG)
//STEP2    EXEC PROC=RPTPROC
//SYSPRINT DD SYSOUT=*
//         INCLUDE MEMBER=JCLINC01
"""

NATURAL_SAMPLE = """\
* Natural program for payroll
DEFINE DATA
LOCAL
1 #TOTAL (P7.2)
1 #NAME  (A30)
PARAMETER
1 #INPUT-AMT (P7.2)
END-DEFINE
*
PERFORM CALC-TOTAL
CALLNAT 'DATEUTIL' #TOTAL
*
DEFINE SUBROUTINE CALC-TOTAL
  #TOTAL := 100
END-SUBROUTINE
END
"""


class TestCobolParser:
    def test_program_id(self):
        result = parse_cobol(COBOL_SAMPLE)
        assert result.program_id == "CALCPAGO"

    def test_divisions(self):
        result = parse_cobol(COBOL_SAMPLE)
        names = [d.name for d in result.divisions]
        assert "IDENTIFICATION" in names
        assert "PROCEDURE" in names
        assert len(result.divisions) >= 3

    def test_paragraphs(self):
        result = parse_cobol(COBOL_SAMPLE)
        para_names = [p.name for p in result.paragraphs]
        assert "MAIN-PARA" in para_names
        assert "CALC-TOTAL" in para_names

    def test_perform_targets(self):
        result = parse_cobol(COBOL_SAMPLE)
        assert "CALC-TOTAL" in result.perform_targets
        assert "DISPLAY-RESULT" in result.perform_targets

    def test_copy_statements(self):
        result = parse_cobol(COBOL_SAMPLE)
        assert "DATECOPY" in result.copy_statements

    def test_variables(self):
        result = parse_cobol(COBOL_SAMPLE)
        var_names = [v.name for v in result.variables]
        assert "WS-TOTAL" in var_names

    def test_empty_input(self):
        result = parse_cobol("")
        assert result.line_count == 0
        assert len(result.divisions) == 0


class TestPliParser:
    def test_procedures(self):
        result = parse_pli(PLI_SAMPLE)
        names = [p.name for p in result.procedures]
        assert "MAINPROC" in names
        assert "CALC_TOTAL" in names

    def test_call_targets(self):
        result = parse_pli(PLI_SAMPLE)
        assert "CALC_TOTAL" in result.call_targets
        assert "DISPLAY_RESULT" in result.call_targets

    def test_includes(self):
        result = parse_pli(PLI_SAMPLE)
        assert "DATEUTIL" in result.includes

    def test_variables(self):
        result = parse_pli(PLI_SAMPLE)
        names = [v.name for v in result.variables]
        assert "TOTAL" in names


class TestRpgParser:
    def test_fixed_format_subroutines(self):
        result = parse_rpg(RPG_SAMPLE)
        sr_names = [s.name for s in result.subroutines]
        assert "CALCTOT" in sr_names or "CalcTot" in sr_names

    def test_exsr_targets(self):
        result = parse_rpg(RPG_SAMPLE)
        assert any("CALCTOT" in t.upper() for t in result.exsr_targets)

    def test_spec_counts(self):
        result = parse_rpg(RPG_SAMPLE)
        assert "D" in result.spec_counts or "C" in result.spec_counts

    def test_free_format(self):
        result = parse_rpg(RPG_FREE_SAMPLE)
        assert result.is_free_format
        assert len(result.variables) >= 2
        assert len(result.data_structures) >= 1

    def test_free_format_procedures(self):
        result = parse_rpg(RPG_FREE_SAMPLE)
        proc_names = [p.name for p in result.procedures]
        assert "CalcTotal" in proc_names

    def test_copy_members(self):
        result = parse_rpg(RPG_FREE_SAMPLE)
        assert len(result.copy_members) >= 1


class TestJclParser:
    def test_job_name(self):
        result = parse_jcl(JCL_SAMPLE)
        assert result.job_name == "PAYROLL"

    def test_steps(self):
        result = parse_jcl(JCL_SAMPLE)
        assert len(result.steps) >= 2
        assert result.steps[0].program == "COBPAY01"

    def test_dd_statements(self):
        result = parse_jcl(JCL_SAMPLE)
        dd_names = [d.name for d in result.dd_statements]
        assert "INFILE" in dd_names
        assert "OUTFILE" in dd_names

    def test_programs_called(self):
        result = parse_jcl(JCL_SAMPLE)
        assert "COBPAY01" in result.programs_called

    def test_includes(self):
        result = parse_jcl(JCL_SAMPLE)
        assert "JCLINC01" in result.includes

    def test_proc_step(self):
        result = parse_jcl(JCL_SAMPLE)
        proc_steps = [s for s in result.steps if s.is_proc]
        assert len(proc_steps) >= 1


class TestNaturalParser:
    def test_define_data(self):
        result = parse_natural(NATURAL_SAMPLE)
        assert result.has_define_data

    def test_local_variables(self):
        result = parse_natural(NATURAL_SAMPLE)
        assert "#TOTAL" in result.local_variables
        assert "#NAME" in result.local_variables

    def test_parameters(self):
        result = parse_natural(NATURAL_SAMPLE)
        assert "#INPUT-AMT" in result.parameters

    def test_subroutines(self):
        result = parse_natural(NATURAL_SAMPLE)
        names = [s.name for s in result.subroutines]
        assert "CALC-TOTAL" in names

    def test_perform_targets(self):
        result = parse_natural(NATURAL_SAMPLE)
        assert "CALC-TOTAL" in result.perform_targets

    def test_callnat_targets(self):
        result = parse_natural(NATURAL_SAMPLE)
        assert "DATEUTIL" in result.callnat_targets


class TestCopybookResolver:
    def test_build_index(self, tmp_path: Path):
        copydir = tmp_path / "copybooks"
        copydir.mkdir()
        (copydir / "DATECOPY.cpy").write_text("01 WS-DATE PIC X(10).")
        (copydir / "COMMON.cpy").write_text("01 WS-STATUS PIC X(2).")

        resolver = CopybookResolver(search_paths=[copydir])
        count = resolver.build_index()
        assert count == 2

    def test_resolve_found(self, tmp_path: Path):
        copydir = tmp_path / "copybooks"
        copydir.mkdir()
        (copydir / "DATECOPY.cpy").write_text("01 WS-DATE.")

        resolver = CopybookResolver(search_paths=[copydir])
        path = resolver.resolve("DATECOPY", language="cobol")
        assert path is not None
        assert path.name == "DATECOPY.cpy"

    def test_resolve_not_found(self, tmp_path: Path):
        resolver = CopybookResolver(search_paths=[tmp_path])
        resolver.build_index()
        assert resolver.resolve("NONEXISTENT") is None

    def test_resolve_all(self, tmp_path: Path):
        copydir = tmp_path / "copies"
        copydir.mkdir()
        (copydir / "A.cpy").write_text("data")
        (copydir / "B.cpy").write_text("data")

        resolver = CopybookResolver(search_paths=[copydir])
        results = resolver.resolve_all(["A", "B", "MISSING"])
        resolved = [r for r in results if r.resolved_path]
        assert len(resolved) == 2

    def test_copybook_index(self):
        idx = CopybookIndex()
        idx.add("test", Path("/tmp/test.cpy"))
        assert idx.count() == 1
        assert idx.resolve("TEST") is not None  # case insensitive


class TestParserRegistry:
    def test_supported_languages(self):
        langs = supported_languages()
        assert langs["cobol"] == "L2"
        assert langs["rpg"] == "L3"
        assert langs["python"] == "L1"
        assert len(langs) >= 25

    def test_parse_cobol_via_registry(self):
        result = parse_file(Path("test.cob"), COBOL_SAMPLE, ParserLevel.L2_ANTLR, "cobol")
        assert hasattr(result, "program_id")
        assert result.program_id == "CALCPAGO"

    def test_parse_rpg_via_registry(self):
        result = parse_file(Path("test.rpg"), RPG_SAMPLE, ParserLevel.L3_PATTERNS, "rpg")
        assert hasattr(result, "subroutines")

    def test_parse_jcl_via_registry(self):
        result = parse_file(Path("test.jcl"), JCL_SAMPLE, ParserLevel.L3_PATTERNS, "jcl")
        assert hasattr(result, "job_name")

    def test_fallback_to_skeleton(self):
        result = parse_file(Path("test.txt"), "some text content", ParserLevel.L4_LEXICAL, "unknown")
        assert isinstance(result, list)
