from edwin import create_app, socketio

app = create_app()

socketio.run(app, debug=True, use_reloader=False)
