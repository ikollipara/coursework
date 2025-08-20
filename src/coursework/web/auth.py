"""
Project:     Coursework
Name:        src/coursework/web/auth.py
Author:      Ian Kollipara <ian.kollipara@cune.edu>
Date:        2025-08-05
Description: Authentication Setup
"""

from __future__ import annotations

import contextlib
import http
import typing as t

import flask
import flask_login
import flask_wtf
from flask import views
from onelogin.saml2 import auth
from onelogin.saml2 import constants
from onelogin.saml2 import idp_metadata_parser
from onelogin.saml2 import settings

from coursework import loaders

if t.TYPE_CHECKING:
    from flask import Request


bp = flask.Blueprint("auth", __name__, url_prefix="/accounts")

### Classes ###


class User(loaders.User, flask_login.UserMixin):
    """This is custom version of the Coursework user that is compatible with Flask Login."""

    def get_id(self):
        return self.name

    def to_core(self):
        return loaders.User(name=self.name, role=self.role)


### Forms ###


class LoginForm(flask_wtf.FlaskForm):
    """Form for submitting a login request.

    The Form contains no fields, since its just used for
    CSRF validation.
    """


### Views ###


class SAMLMixin:
    """
    Mixin class to provide SAML-related helper functions.
    """

    timeout = 60 * 4  # 4 Minutes
    """The timeout to use when fetching from the metadata url."""

    @property
    def metadata_url(self):
        """Get the idP Metadata Url."""
        return flask.current_app.config["METADATA_URL"]

    def _prepare_request(self):
        """Prepare the saml related request."""
        return {
            "https": "on" if flask.request.scheme == "https" else "off",
            "http_host": flask.request.host,
            "script_name": f"{flask.request.root_path}{flask.request.path}",
            "get_data": flask.request.args.copy(),
            "post_data": flask.request.form.copy(),
        }

    def _build_saml_config(self):
        """Build the SAML configuration."""

        idp_data = idp_metadata_parser.OneLogin_Saml2_IdPMetadataParser.parse_remote(
            self.metadata_url, timeout=self.timeout
        )

        return {
            "debug": flask.current_app.config["DEBUG"] == 1,
            "sp": {
                "entityId": flask.url_for("auth.cune_saml_metadata", _external=True),
                "assertionConsumerService": {
                    "url": flask.url_for("auth.cune_saml_acs", _external=True),
                    "binding": constants.OneLogin_Saml2_Constants.BINDING_HTTP_POST,
                },
                "singleLogoutService": {
                    "url": flask.url_for("auth.cune_saml_logout", _external=True),
                    "binding": constants.OneLogin_Saml2_Constants.BINDING_HTTP_REDIRECT,
                },
            },
            "security": {
                "logoutRequestSigned": False,
                "logoutResponseSigned": False,
            },
        } | idp_data

    def _configure_auth(self):
        """Configure the SAML auth. Available under `self._auth`."""

        req = self._prepare_request()
        config = self._build_saml_config()
        self._auth = auth.OneLogin_Saml2_Auth(req, config)


class DispatchByMethdoMixin(views.View):
    def dispatch_request(self):
        method = flask.request.method

        return getattr(self, method.lower())()


class MetadataView(SAMLMixin, DispatchByMethdoMixin, views.View):
    """View for SAML Metadata. The url scheme mirrors django-allauth."""

    def get(self):
        config = self._build_saml_config()

        saml_settings = settings.OneLogin_Saml2_Settings(settings=config, sp_validation_only=True)
        metadata = saml_settings.get_sp_metadata()
        errors = saml_settings.validate_metadata(metadata)

        if len(errors) > 0:
            response = flask.make_response({"errors": errors})
            response.status_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
            response.content_type = "application/json"
            return response

        response = flask.make_response(metadata)
        response.content_type = "text/xml"
        response.status_code = http.HTTPStatus.OK
        return response


bp.add_url_rule("/saml/cune/metadata/", view_func=MetadataView.as_view("cune_saml_metadata"))


class ACSView(SAMLMixin, views.View):
    """SAML ACS View for Login."""

    methods = ["GET", "POST"]

    REQUEST_ID_PARAM = "AuthNRequestID"

    def dispatch_request(self):
        errors = []
        error_reason = None
        self._configure_auth()
        print(self._prepare_request())
        with self._request_id():
            try:
                self._auth.process_response(self._request_id)

            except auth.OneLogin_Saml2_Error as e:
                errors = ["error"]
                error_reason = str(e)
                if not errors:
                    errors = self._auth.get_errors()

            if errors:
                error_reason = self._auth.get_last_error_reason() or error_reason
                response = flask.make_response(
                    flask.render_template("errors/saml_login_error.html", errors=errors, error_reason=error_reason)
                )
                response.status_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
                return response

        user = User(name=self._auth.get_nameid().split("@")[0], role="student")
        flask_login.login_user(user)
        next = flask.request.args.get("next")

        return flask.redirect(next or flask.url_for("submission.courses"))

    @contextlib.contextmanager
    def _request_id(self):
        try:
            self._request_id = flask.session.get(self.REQUEST_ID_PARAM, default=None)
            yield
        finally:
            if self.REQUEST_ID_PARAM in flask.session:
                del flask.session[self.REQUEST_ID_PARAM]


bp.add_url_rule("/saml/cune/acs/", view_func=ACSView.as_view("cune_saml_acs"))


class SLSView(SAMLMixin, DispatchByMethdoMixin, views.View):
    decorators = [flask_login.login_required]
    methods = ["GET", "POST", "HEAD", "OPTIONS"]

    def post(self):
        self._configure_auth()
        return flask.redirect(
            self._auth.logout(flask.url_for("auth.cune_saml_logout", _external=True), flask_login.current_user.get_id())
        )

    def get(self):
        self._configure_auth()
        request_id = flask.session["LogoutRequestID"] if "LogoutRequestID" in flask.session else None

        def force_logout():
            """Callback used by Python3-Saml."""
            flask_login.logout_user()

        redirect_to = None
        error_reason = None
        try:
            redirect_to = self._auth.process_slo(
                request_id=request_id,
                delete_session_cb=force_logout,
                keep_local_session=not flask_login.current_user.is_authenticated,
            )
        except auth.OneLogin_Saml2_Error as e:
            error_reason = str(e)
        errors = self._auth.get_errors()

        if errors:
            error_reason = self._auth.get_last_error_reason() or error_reason

            response = flask.make_response(error_reason)
            response.status_code = http.HTTPStatus.BAD_REQUEST
            response.content_type = "text/plain"
            return response

        redirect_to = redirect_to or flask.url_for("auth.cune_saml_login")
        return flask.redirect(redirect_to)

    head = get
    options = get


bp.add_url_rule("/saml/cune/sls/", view_func=SLSView.as_view("cune_saml_logout"))


class LoginView(SAMLMixin, views.View):
    """Login View for the application."""

    methods = ["GET", "POST"]

    def dispatch_request(self):
        form = LoginForm()
        self._configure_auth()
        form = LoginForm()
        if form.validate_on_submit():
            return flask.redirect(self._auth.login())

        return flask.render_template("auth/login.html", form=form)


bp.add_url_rule("/saml/cune/login/", view_func=LoginView.as_view("cune_saml_login"))
