from game import generate_random_number, is_valid_solution
import time
import random
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_socketio import SocketIO, join_room, emit
from string import ascii_uppercase
from db import store, valid_user, can_register, create_table, getname, fetch_user_by_email, update_user_score
from app import fetch_data


app = Flask(__name__)
app.secret_key = "thisisasupersecretkey"
socketio = SocketIO(app)
rooms = {}
create_table()

# uid =None

@app.route("/", methods=["GET", "POST"])
def first():
    # session.clear()
    if request.method == "POST":
        register = request.form.get("register", False)
        login = request.form.get("login", False)
        
        if register != False:
            return redirect(url_for('register'))  
        if login != False:
            return redirect(url_for('login'))  
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    # global uid
    if request.method == "POST":
        name = request.form["name"]
        password = request.form["password"]
        email = request.form["email"]
        # uid=get_uid(email)
        if store(name, email, password)==True:
                session["name"] = name
                session["email"] = email
                session.pop("spectator", None)
                return redirect(url_for('home')) 
        else:
            flash("user already exists")
            return redirect(url_for('login')) 
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if valid_user(email, password):
            name = getname(email)
            session["name"] = name
            session["email"] = email
            session.pop("spectator", None)
            return redirect(url_for('home')) 
        else:
            flash("wrong email or password")
            return render_template("login.html", error="Invalid credentials.")
    return render_template("login.html")


def generate_unique_code(length=4):
    while True:
        code = "".join(random.choice(ascii_uppercase) for _ in range(length))
        if code not in rooms:
            return code

def get_user_room(username):
    for room_code, room_data in rooms.items():
        if username in room_data["members"]:
            return room_code
    return None

@app.route("/home", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = session.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)
        play = request.form.get("play", False)
        spectate = request.form.get("spectate", False)
        browse_rooms = request.form.get("browse_rooms", False)
        

        if request.form.get("leaderboard"):
            print("Leaderboard clicked!")
            return redirect(url_for("leaderboard"))

        if request.form.get("profile"):
            print("profile clicked!")
            return redirect(url_for("profile"))
        
        if request.form.get("rule"):
            print("profile clicked!")
            return redirect(url_for("rule"))



        if join or create or play:
            session.pop("spectator", None)

        if not name:
            return render_template("home.html", error="Please enter a name.", code=code, name=name)

        if join and not code:
            return render_template("home.html", error="Please enter a room code.", code=code, name=name)

        if browse_rooms:
            return redirect(url_for("browse_spectate"))
        
        existing_room = get_user_room(name)
        if existing_room:
            flash("You are already playing in another room.")
            session["room"] = existing_room
            return redirect(url_for("room"))

        if create:
            room = generate_unique_code()
            rooms[room] = {"members": [], "messages": [], "timer_started": False}
            rooms[room]["members"].append(name)
        elif play:
            room = next((r for r in rooms if len(rooms[r]["members"]) == 1 and name not in rooms[r]["members"]), None)
            if not room:
                room = generate_unique_code()
                rooms[room] = {"members": [], "messages": [], "timer_started": False}
            rooms[room]["members"].append(name)
        elif code in rooms and len(rooms[code]["members"]) < 2:
            if name not in rooms[code]["members"]:
                room = code
                rooms[room]["members"].append(name)
            else:
                room = code
        elif spectate:
            if code not in rooms:
                return render_template("home.html", error="Room does not exist.", code=code, name=name)
            session["spectator"] = True
            room = code
        else:
            return render_template("home.html", error="Room does not exist or is full.", code=code, name=name)

        session["room"] = room
        return redirect(url_for("room"))
    
    return render_template("home.html")

@app.route('/leaderboard')
def leaderboard():
    data, error = fetch_data()
    if error:
        return error, 500
    return render_template('leaderboard.html', leaderboard=data)

@app.route('/profile')
def profile():
    email = session.get("email")  # get email from session
    print("🔎 Session email:", email)
    if not email:
        return redirect(url_for('login'))  # Redirect if not logged in

    user, error = fetch_user_by_email(email)  # use your existing function
    if error:
        return f"Error: {error}", 500
    if user is None:
        return "User not found", 404

    return render_template('profile.html', user=user)

@app.route('/rule')
def rule():
    return render_template("rule.html")

@app.route("/browse")
def browse_spectate():
    name = session.get("name")
    if not name:
        return redirect(url_for('login'))
    
    available_rooms = {}
    for code, room_data in rooms.items():
        if len(room_data["members"]) > 0:
            status = "Waiting" if len(room_data["members"]) < 2 else "In Progress"
            available_rooms[code] = {
                "players": room_data["members"],
                "status": status,
                "player_count": len(room_data["members"])
            }
    
    return render_template("browse_rooms.html", rooms=available_rooms)

@app.route("/spectate/<code>")
def spectate_room(code):
    name = session.get("name")
    
    if not name:
        return redirect(url_for("login"))
    
    if code not in rooms:
        return redirect(url_for("browse_spectate"))
    
    session["spectator"] = True
    session["room"] = code
    
    return redirect(url_for("room"))

@app.route("/play")
def room():
    room = session.get("room")
    is_spectator = session.get("spectator", False)
    name = session.get("name")

    if not room or name is None or room not in rooms:
        return redirect(url_for("home"))

    if not is_spectator and len(rooms[room]["members"]) > 2:
        return redirect(url_for("home"))
    
    if not is_spectator and name not in rooms[room]["members"]:
        if len(rooms[room]["members"]) >= 2:
            return redirect(url_for("home"))
        rooms[room]["members"].append(name)

    return render_template("room.html", code=room, messages=rooms[room]["messages"], players=rooms[room]["members"], spectator=is_spectator)

@socketio.on("connect")
def handle_connect():
    room = session.get("room")
    name = session.get("name")
    is_spectator = session.get("spectator", False)

    if not room or room not in rooms:
        return

    join_room(room)  

    if is_spectator:
        spectator_room = f"{room}_spectators"
        join_room(spectator_room)
        
        if "spectator_count" not in rooms[room]:
            rooms[room]["spectator_count"] = 0
        rooms[room]["spectator_count"] += 1
        
        emit("spectator_joined", {"count": rooms[room]["spectator_count"]}, room=room)
    else:
        if "player_sids" not in rooms[room]:
            rooms[room]["player_sids"] = {}
        rooms[room]["player_sids"][name] = request.sid
        
        if name not in rooms[room]["members"]:
            rooms[room]["members"].append(name)
        
        emit("update_players", {"players": rooms[room]["members"]}, room=room)
        
        if len(rooms[room]["members"]) == 2 and not rooms[room]["timer_started"]:
            rooms[room]["timer_started"] = True
            socketio.start_background_task(start_timer, room)

@socketio.on("disconnect")
def handle_disconnect():
    room = session.get("room")
    name = session.get("name")
    is_spectator = session.get("spectator", False)
    
    if not room or room not in rooms:
        return
        
    if is_spectator:
        if "spectator_count" in rooms[room]:
            rooms[room]["spectator_count"] -= 1
            emit("spectator_left", {"count": rooms[room]["spectator_count"]}, room=room)
    else:
        if name in rooms[room]["members"]:
            rooms[room]["members"].remove(name)
            if "player_sids" in rooms[room] and name in rooms[room]["player_sids"]:
                del rooms[room]["player_sids"][name]
            
            emit("update_players", {"players": rooms[room]["members"]}, room=room)
            
            if len(rooms[room]["members"]) < 2 and rooms[room].get("game_started", False):
                emit("player_left", {"message": f"{name} has left the game"}, room=room)

# Add this near the top of your app.py file
from db import update_user_score

# Then modify your handle_message function to update the database when a player wins
@socketio.on("message")
def handle_message(data):
    room = session.get("room")
    name = session.get("name")
    is_spectator = session.get("spectator", False)
    email = session.get("email")  # Get the player's email from the session

    if not room or room not in rooms:
        return

    if is_spectator:
        return 

    if not rooms[room].get("game_started", False):
        return

    message = data["message"]
    result = check(message)
    score = data.get("score", 0)  # Get the submitted score from data
    
    rooms[room]["messages"].append({"name": name, "message": result})
    
    if result.startswith("Valid") and not rooms[room].get("winner", None):
        elapsed_time = rooms[room].get("elapsed_time", 0)
        rooms[room]["winner"] = name
        rooms[room]["winning_time"] = elapsed_time
        rooms[room]["winning_score"] = score  # Store the winning score
        
        rooms[room]["game_over"] = True
        
        winner_message = f"{name} wins! Time: {elapsed_time} seconds"
        socketio.emit("game_over", {"message": winner_message, "winner": name}, room=room)
        
        # Update the winner's score in the database
        if email:
            update_user_score(email, score)
        
        socketio.start_background_task(cleanup_room, room, 30)
    
    emit("message", {"name": "You", "message": result}, room=request.sid)
    
    for player, sid in rooms[room].get("player_sids", {}).items():
        if sid != request.sid:
            emit("message", {"name": name, "message": result}, room=sid)
    
    emit("message", {"name": name, "message": result}, room=f"{room}_spectators")
    
def start_timer(room):
    if room not in rooms:
        return
        
    for i in range(10, 0, -1):
        socketio.emit("update_timer", {"time": i}, room=room)
        time.sleep(1)
    
    secret_number = generate_random_number()
    rooms[room]["game_started"] = True
    socketio.emit("game_start", {"message": f"Game Started! Your 6 digit code: {secret_number}"}, room=room)

    elapsed_time = 0
    rooms[room]["elapsed_time"] = elapsed_time
    
    while elapsed_time <= 600:  
        if room not in rooms or rooms.get(room, {}).get("game_over", False):
            break
            
        socketio.emit("update_game_timer", {"time": elapsed_time}, room=room)
        time.sleep(1)
        elapsed_time += 1
        rooms[room]["elapsed_time"] = elapsed_time

    if room in rooms and not rooms[room].get("winner", None):
        socketio.emit("game_over", {"message": "Time's up! Game Over! No winner."}, room=room)
        socketio.start_background_task(cleanup_room, room, 30) 

def cleanup_room(room, delay):
    time.sleep(delay)
    
    if room in rooms:
        rooms.pop(room, None)
   
def check(message):
    if is_valid_solution(message):
        return f"Valid, {message}"
    else:
        return f"Invalid, {message}"

if __name__ == "__main__":
    socketio.run(app, debug=True)

# from app import app2

# if __name__ == "__main__":
#     app2.run(debug=True)

    