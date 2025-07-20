from .app import create_app
import os

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("CHATBOT_PORT", "8001"))
    app.run(host="0.0.0.0", port=port)
