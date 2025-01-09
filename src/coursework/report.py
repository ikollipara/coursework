"""
report.py
Ian Kollipara <ian.kollipara@cune.edu>
2025-01-07

Creating a report of the code.
"""

from io import BytesIO
from itertools import chain
from pathlib import Path
from typing import BinaryIO
from typing import Iterable

from pygments import highlight
from pygments.formatters import BmpImageFormatter
from pygments.lexers import get_lexer_for_filename
from pygments.styles import get_style_by_name
from pygments.util import ClassNotFound
from reportlab.lib import enums
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ListStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.styles import StyleSheet1
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Flowable
from reportlab.platypus import Image
from reportlab.platypus import ListFlowable
from reportlab.platypus import ListItem
from reportlab.platypus import PageBreak
from reportlab.platypus import Paragraph
from reportlab.platypus import Preformatted
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Spacer

from coursework.models import RunnerResult

styles = StyleSheet1()
styles.add(ParagraphStyle(name="Normal", fontName="Helvetica", fontSize=12, leading=12))
styles.add(
    ParagraphStyle(
        name="Code",
        fontName="Courier",
        fontSize=8,
        leading=8.8,
        firstLineIndent=0,
        leftIndent=0,
        hyphenationLang="",
    )
)
styles.add(
    ParagraphStyle(
        name="Title",
        fontName="Helvetica",
        fontSize=24,
        spaceAfter=20,
        alignment=enums.TA_CENTER,
    )
)
styles.add(
    ParagraphStyle(
        name="Heading",
        fontName="Helvetica",
        fontSize=18,
        spaceAfter=10,
        alignment=enums.TA_LEFT,
    )
)
styles.add(
    ListStyle(
        name="ResultList",
        leftIndent=18,
        bulletType="bullet",
        bulletAlign="left",
        bulletFontName="Helvetica",
        bulletFontSize=12,
        bulletDedent="auto",
        bulletDir="ltr",
        start="circle",
    )
)
styles.add(
    ParagraphStyle(
        name="PassedTest",
        parent=styles["Normal"],
        textColor="green",
    )
)
styles.add(ParagraphStyle(name="FailedTest", parent=styles["Normal"], textColor="red"))


def make(result: RunnerResult, files: Iterable[Path] = None, out: BinaryIO = None):
    """Create a new report for the given result."""

    out = out or BytesIO()
    files = files or []

    document = SimpleDocTemplate(
        out,
        pagesize=LETTER,
        rightMargin=inch / 2,
        leftMargin=inch / 2,
        topMargin=inch / 2,
        bottomMargin=inch / 2,
    )

    document.build([*_title_page(result), *list(chain.from_iterable(_code_page(file, document) for file in files))])

    return out


def _title_page(result: RunnerResult) -> list[Flowable]:
    """Create a title page for the report."""

    success_points = sum(r.points for r in result.test_case_results if r.was_successful)

    return [
        Paragraph("Coursework Report", styles["Heading"]),
        Spacer(1, 30),
        Paragraph(f"Course: <b>{result.course.name}</b>", styles["Heading"]),
        Paragraph(f"Assignment: <b>{result.assignment.name}</b>", styles["Heading"]),
        Paragraph(f"Student: <b>{result.user.name}</b>", styles["Heading"]),
        Paragraph(
            f"Total Score: <b>{success_points}/{result.assignment.total_points} ({success_points/result.assignment.total_points:0.0f}%)</b>",
            styles["Heading"],
        ),
        Spacer(1, 30),
        *_student_scores(result),
        PageBreak(),
    ]


def _student_scores(result: RunnerResult) -> list[Flowable]:
    """Create the list of student scores."""

    return [
        ListFlowable(
            [
                ListItem(
                    Paragraph(
                        f"{test_case_result.name} ({test_case_result.points})",
                        style=styles["PassedTest" if test_case_result.was_successful else "FailedTest"],
                    ),
                    bulletColor="green" if test_case_result.was_successful else "red",
                )
                for test_case_result in result.test_case_results
            ],
            style=styles["ResultList"],
        )
    ]


def _code_page(file: Path, doc: SimpleDocTemplate) -> list[Flowable]:
    """Create code pages."""

    try:
        # Reset the file position to the start, thus making sure all text is grabbed.
        img_buffer = BytesIO()
        highlight(
            file.read_bytes(),
            get_lexer_for_filename(file.name),
            BmpImageFormatter(style=get_style_by_name("xcode")),
            img_buffer,
        )
        reader = ImageReader(img_buffer)
        iw, ih = reader.getSize()
        aspect = ih / float(iw)
        code = Image(img_buffer, width=inch * 4, height=(inch * 4 * aspect), hAlign="LEFT")
    except ClassNotFound:
        # Reset the file position to the start, thus making sure all text is grabbed.
        code = Preformatted(file.read_text(), styles["Code"], maxLineLength=80)

    return [
        Paragraph(file.name, styles["Heading"]),
        Spacer(1, 20),
        code,
        PageBreak(),
    ]
