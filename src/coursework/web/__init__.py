"""
Coursework Web Interface
"""

from os import environ

import flask
import flask_login

from coursework import loaders


def bootstrap_app():
    app = flask.Flask(__name__)
    login_manager = flask_login.LoginManager()

    app.config.from_prefixed_env()
    with open(environ["COURSEWORK_CONFIG"], "rb") as f:
        app.config["coursework_config"] = loaders.Configuration.from_toml(f)

    print(app.config)

    from coursework.web import auth
    from coursework.web import submission

    login_manager.init_app(app)

    @app.context_processor
    def inject_user():
        return {"user": flask_login.current_user}

    @login_manager.user_loader
    def load_user(user_id):
        if app.config["DEBUG"]:
            return auth.User(name="ian", role="student")

        user = auth.User(name=user_id, role="student")
        if user.is_active:
            return user

    app.register_blueprint(auth.bp)
    app.register_blueprint(submission.bp)

    if app.config["DEBUG"]:

        @app.get("/login")
        def test_login():
            flask_login.login_user(auth.User(name="ian", role="student"))
            return flask.redirect("/")

    return app
