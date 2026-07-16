from flask import Flask
from config import Config
from app.infrastructure.db.connection import init_db, close_db
from app.interfaces.auth.routes import auth_bp
from app.interfaces.agenda.routes import agenda_bp
from app.interfaces.profissionais.routes import profissionais_bp
from app.interfaces.procedimentos.routes import procedimentos_bp
from app.interfaces.pacientes.routes import pacientes_bp
from app.interfaces.configuracoes.routes import configuracoes_bp
from app.interfaces.publico.routes import publico_bp


def create_app(config=None):
    app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
    app.config.from_object(Config)

    if config:
        app.config.update(config)

    app.teardown_appcontext(close_db)

    app.register_blueprint(auth_bp)
    app.register_blueprint(agenda_bp)
    app.register_blueprint(profissionais_bp)
    app.register_blueprint(procedimentos_bp)
    app.register_blueprint(pacientes_bp)
    app.register_blueprint(configuracoes_bp)
    app.register_blueprint(publico_bp)

    with app.app_context():
        init_db()

    if not app.config.get('TESTING'):
        from app.infrastructure.scheduler import start_scheduler
        start_scheduler(app)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)
