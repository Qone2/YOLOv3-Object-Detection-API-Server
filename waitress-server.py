from waitress import serve
import app

# serve(app, host="0.0.0.0", port=5000)
serve(app, port=5000)
