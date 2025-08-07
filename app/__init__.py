from flask import Flask

def create_app():
    app = Flask(
        __name__, 
        static_folder="static",          # ścieżka względem folderu app/
        template_folder="templates"      # ścieżka względem folderu app/
    )

    from app.routes import main
    app.register_blueprint(main)

    return app

