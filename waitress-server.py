from waitress import serve
from paste.translogger import TransLogger
import app

if __name__ == "__main__":
    # serve(app.app, host="0.0.0.0", port=5000)
    # serve(app.app, port=5000)
    serve(TransLogger(app.app, setup_console_handler=False), port=5000)
