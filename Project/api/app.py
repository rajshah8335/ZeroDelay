"""
Flask Application Entry Point.

Initializes the Flask app, registers blueprints, and starts the server.
No business logic lives here — only app configuration and startup.
"""

from flask import Flask
from flask_cors import CORS

from api.routes import api_bp
import config


def create_app() -> Flask:
    """Application factory — creates and configures the Flask app."""
    app = Flask(__name__)

    # Enable CORS for frontend integration
    CORS(app)

    # Register API blueprint
    app.register_blueprint(api_bp)

    # Root endpoint
    @app.route("/")
    def index():
        return {
            "service": "Smart Multi-Modal Supply Chain Optimizer",
            "version": "1.0.0",
            "endpoints": {
                "POST /api/routes": "Optimize shipping routes",
                "GET /api/cities": "List supported cities",
                "GET /api/disruptions": "List active disruptions",
                "GET /api/health": "Health check",
            }
        }

    return app


if __name__ == "__main__":
    app = create_app()
    print("\n🚀 Smart Supply Chain Optimizer — Starting...")
    print(f"   Server: http://localhost:{config.FLASK_PORT}")
    print(f"   Debug: {config.FLASK_DEBUG}")
    print(f"   Gemini API: {'configured' if config.GEMINI_API_KEY else 'not set (using fallback)'}")
    print()
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG,
    )
