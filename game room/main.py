import random
import time
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, emit
from string import ascii_uppercase

app = Flask(__name__)
app.secret_key = "thisisasupersecretkey"
socketio = SocketIO(app)
rooms = {}

def generate_unique_code(length=4):
    while True:
        code = "".join(random.choice(ascii_uppercase) for _ in range(length))
        if code not in rooms:
            return code

def msg():
    return random.randint(100000, 999999)

def first():
    name="Palak"
    return name

@app.route("/", methods=["GET", "POST"])
def home():
    session.clear()
    if request.method == "POST":
        name = first()
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)
        play = request.form.get("play", False)
        spectate = request.form.get("spectate", False)
        browse_rooms = request.form.get("browse_rooms", False)

        if not name:
            return render_template("home.html", error="Please enter a name.", code=code, name=name)

        if join and not code:
            return render_template("home.html", error="Please enter a room code.", code=code, name=name)

        if browse_rooms:
            return redirect(url_for("browse_spectate"))

        if create:
            room = generate_unique_code()
            rooms[room] = {"members": [], "messages": [], "timer_started": False}
            rooms[room]["members"].append(name)
        elif play:
            room = next((r for r in rooms if len(rooms[r]["members"]) == 1), None)
            if not room:
                room = generate_unique_code()
                rooms[room] = {"members": [], "messages": [], "timer_started": False}
            rooms[room]["members"].append(name)
        elif code in rooms and len(rooms[code]["members"]) < 2:
            room = code
            rooms[room]["members"].append(name)
        elif spectate:
            if code not in rooms:
                return render_template("home.html", error="Room does not exist.", code=code, name=name)
            session["spectator"] = True
            room = code
        elif code in rooms and len(rooms[code]["members"]) < 2:
            room = code
            rooms[room]["members"].append(name)            
        else:
            return render_template("home.html", error="Room does not exist or is full.", code=code, name=name)
        
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))
    
    return render_template("home.html")

@app.route("/browse")
def browse_spectate():
    name = first()
    session["name"] = name
    
    # Filter rooms that have active games or are waiting for players
    available_rooms = {}
    for code, room_data in rooms.items():
        # Only show rooms with at least one player
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
    name = session.get("name", first())
    
    if code not in rooms:
        return redirect(url_for("browse_spectate"))
    
    session["spectator"] = True
    session["room"] = code
    session["name"] = name
    
    return redirect(url_for("room"))

@app.route("/play")
def room():
    room = session.get("room")
    is_spectator = session.get("spectator", False)

    if not room or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    if not is_spectator and len(rooms[room]["members"]) > 2:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"], players=rooms[room]["members"], spectator=is_spectator)

@socketio.on("connect")
def handle_connect():
    room = session.get("room")
    name = session.get("name")
    is_spectator = session.get("spectator", False)

    if not room or room not in rooms:
        return

    join_room(room)  # Everyone joins the main room

    if is_spectator:
        # Create a spectator-specific room
        spectator_room = f"{room}_spectators"
        join_room(spectator_room)
        
        # Add to spectator count if not already tracked
        if "spectator_count" not in rooms[room]:
            rooms[room]["spectator_count"] = 0
        rooms[room]["spectator_count"] += 1
        
        # Notify everyone about new spectator (optional)
        emit("spectator_joined", {"count": rooms[room]["spectator_count"]}, room=room)
    else:
        # Track player socket IDs
        if "player_sids" not in rooms[room]:
            rooms[room]["player_sids"] = {}
        rooms[room]["player_sids"][name] = request.sid
        
        # Update player list for everyone
        emit("update_players", {"players": rooms[room]["members"]}, room=room)
        
        # Start the game timer if both players are connected
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
        # Decrease spectator count
        if "spectator_count" in rooms[room]:
            rooms[room]["spectator_count"] -= 1
            emit("spectator_left", {"count": rooms[room]["spectator_count"]}, room=room)
    else:
        # Handle player disconnect
        if name in rooms[room]["members"]:
            rooms[room]["members"].remove(name)
            if "player_sids" in rooms[room] and name in rooms[room]["player_sids"]:
                del rooms[room]["player_sids"][name]
            
            # Update player list
            emit("update_players", {"players": rooms[room]["members"]}, room=room)
            
            # End game if one player leaves
            if len(rooms[room]["members"]) < 2 and rooms[room].get("game_started", False):
                emit("player_left", {"message": f"{name} has left the game"}, room=room)

@socketio.on("message")
def handle_message(data):
    room = session.get("room")
    name = session.get("name")
    is_spectator = session.get("spectator", False)

    if not room or room not in rooms:
        return

    if is_spectator:
        return  # Spectators can't send messages

    if not rooms[room].get("game_started", False):
        return

    message = data["message"]
    result = check(message)
    
    # Store message in room history (optional)
    rooms[room]["messages"].append({"name": name, "message": result})
    
    # Check if this is a valid answer
    if result == "Valid" and not rooms[room].get("winner", None):
        # Record winner and time
        elapsed_time = rooms[room].get("elapsed_time", 0)
        rooms[room]["winner"] = name
        rooms[room]["winning_time"] = elapsed_time
        
        # Stop the timer
        rooms[room]["game_over"] = True
        
        # Announce winner to everyone
        winner_message = f"{name} wins! Time: {elapsed_time} seconds"
        socketio.emit("game_over", {"message": winner_message}, room=room)
        
        # Set a timer to clean up the room after a delay
        socketio.start_background_task(cleanup_room, room, 30)  # 30 second delay before removing room
    
    # 1. Send to the sender as "You"
    emit("message", {"name": "You", "message": result}, room=request.sid)
    
    # 2. Broadcast to all spectators in the room
    emit("message", {"name": name, "message": result}, room=f"{room}_spectators")

def start_timer(room):
    # Countdown before game starts
    for i in range(10, 0, -1):
        socketio.emit("update_timer", {"time": i}, room=room)
        time.sleep(1)
    
    secret_number = msg()
    rooms[room]["game_started"] = True
    socketio.emit("game_start", {"message": f"Game Started! Your secret code: {secret_number}"}, room=room)

    # Count-up timer starting from 0
    elapsed_time = 0
    rooms[room]["elapsed_time"] = elapsed_time
    
    while elapsed_time <= 300:  # Still limiting to 300 seconds (5 minutes)
        # Check if game has already been won
        if rooms.get(room, {}).get("game_over", False):
            break
            
        socketio.emit("update_game_timer", {"time": elapsed_time}, room=room)
        time.sleep(1)
        elapsed_time += 1
        rooms[room]["elapsed_time"] = elapsed_time

    # If time's up and no winner yet
    if room in rooms and not rooms[room].get("winner", None):
        socketio.emit("game_over", {"message": "Time's up! Game Over! No winner."}, room=room)
        # Set a timer to clean up the room after a delay
        socketio.start_background_task(cleanup_room, room, 30)  # 30 second delay

def cleanup_room(room, delay):
    # Wait for the specified delay
    time.sleep(delay)
    # Remove the room if it still exists
    if room in rooms:
        rooms.pop(room, None)
   
def check(message):
    if message.isdigit():
        return f"Valid"
    else:
        return "Invalid"

if __name__ == "__main__":
    socketio.run(app, debug=True)