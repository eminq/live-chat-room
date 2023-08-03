from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase
from datetime import datetime 

app = Flask(__name__)
app.config["SECRET_KEY"] = "whateverkey"
socketio = SocketIO(app)

rooms = {}

def get_date_time():
    date = datetime.now()
    return f"{date.month}/{date.day}/{date.year}, {date.hour}:{date.minute}:{date.second}"



def generate_room_code(len):
    while True:
        code = ""
        for _ in range(len):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break

    return code


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == "POST":
        name = request.form.get('name')
        code = request.form.get('code')
        join = request.form.get('join', False)
        create = request.form.get('create', False)

        if not name:
            return render_template('index.html', error = 'Please enter a name!', code=code, name=name)
        
        if join != False and not code:
            return render_template('index.html', error = 'Please enter a code!', code=code, name=name)
        
        room = code
        if create != False:
            room = generate_room_code(4)
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template('index.html', error="Room does not exist.", code=code, name=name)
        
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template('index.html')


@app.route('/room')
def room():
    room = session.get('room')
    if room is None or session.get('name') is None or room not in rooms:
        return redirect(url_for('index'))
    return render_template('room.html', code=room, messages=rooms[room]["messages"])


@socketio.on('message')
def message(data):
    room = session.get('room')
    if room not in rooms:
        return
    content = {
        "name" : session.get('name'),
        "message": data["message"],
        "date": data["date"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f'{session.get("name")} said: {data["message"]}')

@socketio.on('connect')
def connect(auth):
    room = session.get('room')
    name = session.get('name')
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"name":name, "message":"has entered the room", "date": get_date_time()}, to=room)
    rooms[room]["members"] += 1
    print(f'{name} joined room {room}')

@socketio.on('disconnect')
def disconnect():
    room = session.get('room')
    name = session.get('name')

    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            print('room deleted')
            del rooms[room]

    send({"name":name, "message":"has left the room", "date": get_date_time()}, to=room)
    print(f'{name} has left room {room}')

if __name__ == "__main__":
    socketio.run(app, debug=True)

