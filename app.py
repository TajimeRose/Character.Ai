from flask import Flask, render_template, Response
from config import Config
from routes.chat import chat_bp
from routes.conversations import convo_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(convo_bp, url_prefix="/api")

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/favicon.ico")
    def favicon():
        return Response(status=204)

    return app

if __name__ == "__main__":
    create_app().run(debug=True)
