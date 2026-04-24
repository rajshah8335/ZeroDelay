"""
Top-level runner for the Smart Supply Chain Optimizer.
This file provides a convenient entry point: `python run.py`
"""

from api.app import create_app
import config

if __name__ == "__main__":
    app = create_app()
    print("\n🚀 Smart Supply Chain Optimizer — Starting...")
    print(f"   Server: http://localhost:{config.FLASK_PORT}")
    print(f"   Debug:  {config.FLASK_DEBUG}")
    print(f"   Gemini: {'✅ configured' if config.GEMINI_API_KEY else '⚠️  not set (fallback mode)'}")
    print()
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG,
    )
