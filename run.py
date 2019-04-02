from edwin import create_app, socketio


while True:
    try:
        app = create_app()

        socketio.run(app, debug=True, use_reloader=False)
    except:
        print("restarting")
