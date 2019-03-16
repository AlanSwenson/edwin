from edwin import create_app, socketio

from flask_socketio import SocketIO

app = create_app()
# socketio = SocketIO(app, async_mode="eventlet")


# 'app' originates from the line 'app = Flask(__name__)'
socketio.run(app, debug=True, use_reloader=False)
