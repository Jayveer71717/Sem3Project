import mysql.connector
from flask import Flask, render_template

import admin
import auth
import db
import student
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(student.bp)

    app.jinja_env.globals["csrf_token"] = auth.csrf_token

    @app.errorhandler(400)
    def bad_request(e):
        return render_template("error.html", code=400, title="Request not accepted",
                               message=getattr(e, "description", "")), 400

    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("error.html", code=403, title="Access denied",
                               message="Your account does not have permission to view this page."), 403

    @app.errorhandler(mysql.connector.Error)
    def db_error(e):
        app.logger.exception("MySQL error: %s", e)
        return render_template("error.html", code=503, title="Database unavailable",
                               message=f"MySQL error {getattr(e, 'errno', '?')}: {e}"), 503

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("error.html", code=404, title="Page not found",
                               message="The page you requested does not exist."), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True,port=5001)
