"""
Project:     Coursework
Name:        src/coursework/web/submission.py
Author:      Ian Kollipara <ian.kollipara@cune.edu>
Date:        2025-08-05
Description: Coursework Submission Views
"""

from __future__ import annotations

import pathlib
import shutil
import tempfile
import typing as t

import flask
import flask_login
import flask_wtf
import rich.console
import wtforms
from flask import views
from flask_wtf import file as flask_file
from wtforms import validators as v

from coursework import runner

if t.TYPE_CHECKING:
    from werkzeug.datastructures import FileStorage

    from coursework.loaders import Configuration
    from coursework.web.auth import User

bp = flask.Blueprint("submission", __name__, url_prefix="")

### Forms ###


class AssignmentSubmissionForm(flask_wtf.FlaskForm):
    """Form used for submitting an assignment."""

    files = flask_file.MultipleFileField(
        label="Submission File", validators=[flask_file.FileRequired("A file must be submitted.")]
    )


### Views ###


@bp.get("/")
@flask_login.login_required
def courses():
    config: Configuration = flask.current_app.config["coursework_config"]
    user: User = flask_login.current_user

    user_courses = [course for course in config.courses.values() if user.name in course.students]

    return flask.render_template("submission/courses.html", courses=user_courses)


@bp.get("/<string:course_name>/")
@flask_login.login_required
def course(course_name: str):
    config: Configuration = flask.current_app.config["coursework_config"]
    user: User = flask_login.current_user
    course_ = config.courses.get(course_name, None)

    if not course_:
        flask.flash(f"Course {course_name} does not exist!")
        return flask.redirect(flask.url_for("submission.courses"))

    if user.name not in course_.students:
        flask.flash(f"You are not a member of {course_name}!")
        return flask.redirect(flask.url_for("submission.courses"))

    def already_submitted(assignment: Configuration.Assignment):
        return (
            pathlib.Path(config.submission.format(student=user.name, course=course_.name, assignment=assignment.name))
            .absolute()
            .exists()
        )

    return flask.render_template("submission/course.html", course=course_, already_submitted=already_submitted)


@bp.get("/<string:course_name>/<string:assignment_name>")
@flask_login.login_required
def course_assignment(course_name: str, assignment_name: str):
    config: Configuration = flask.current_app.config["coursework_config"]
    user: User = flask_login.current_user
    course_ = config.courses.get(course_name, None)

    if not course_:
        flask.flash(f"Course {course_name} does not exist!")
        return flask.redirect(flask.url_for("submission.courses"))

    if user.name not in course_.students:
        flask.flash(f"You are not a member of {course_name}!")
        return flask.redirect(flask.url_for("submission.courses"))

    if assignment_name not in course_.assignments:
        flask.flash(f"{assignment_name} is not a real assignment!")
        return flask.redirect(flask.url_for("submission.course", course_name=course_name))

    assignment = course_.assignments[assignment_name]
    form = AssignmentSubmissionForm()

    save_path = pathlib.Path(
        config.submission.format(student=user.name, course=course_.name, assignment=assignment.name)
    ).absolute()

    return flask.render_template(
        "submission/course_assignment.html",
        assignment=assignment,
        course=course_,
        form=form,
        already_submitted=save_path.exists(),
    )


@bp.post("/<string:course_name>/<string:assignment_name>/submit/")
@flask_login.login_required
def assignment_submit(course_name: str, assignment_name: str):
    config: Configuration = flask.current_app.config["coursework_config"]
    user: User = flask_login.current_user
    course_ = config.courses.get(course_name, None)

    if not course_:
        flask.flash(f"Course {course_name} does not exist!")
        return flask.redirect(flask.url_for("submission.courses"))

    if user.name not in course_.students:
        flask.flash(f"You are not a member of {course_name}!")
        return flask.redirect(flask.url_for("submission.courses"))

    if assignment_name not in course_.assignments:
        flask.flash(f"{assignment_name} is not a real assignment!")
        return flask.redirect(flask.url_for("submission.course", course_name=course_name))

    assignment = course_.assignments[assignment_name]
    form = AssignmentSubmissionForm()

    if form.validate_on_submit():
        save_path = pathlib.Path(
            config.submission.format(student=user.name, course=course_.name, assignment=assignment.name)
        ).absolute()
        with user.as_root():
            if save_path.exists():
                shutil.rmtree(save_path)

        files: list[FileStorage] = form.files.data
        filepaths = []
        console = rich.console.Console(record=True)
        with user.as_root():
            with tempfile.TemporaryDirectory() as d:
                temp_dir = pathlib.Path(d)
                for file in files:
                    temp_path = temp_dir / file.filename
                    temp_path.parent.mkdir(parents=True, exist_ok=True)
                    file.save(temp_path)
                    filepaths.append(temp_path)

                runner_ = runner.get_runner_by_name(assignment.test.runner)
                result = runner_(user.to_core(), config, course_, assignment, filepaths).run(console)

                save_path.mkdir(parents=True, exist_ok=True)
                result.to_pickle((save_path / ".runner-output"))

                for file in filepaths:
                    shutil.copy2(file.absolute(), save_path / file.name)

        return flask.render_template(
            "submission/results.html",
            output=console.export_html(),
            course_name=course_name,
            result=result,
            assignment_name=assignment_name,
        )

    print(form.errors)
    return flask.redirect("submission.course_assignment", course_name=course_name, assignment_name=assignment_name)
