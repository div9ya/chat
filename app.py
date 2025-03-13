from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, send

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active disease discussion rooms and their message history
disease_rooms = {}

# Store active private chats (private rooms between two users)
private_rooms = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/private/<sender>/<receiver>")
def private_chat(sender, receiver):
    return render_template("private_chat.html", sender=sender, receiver=receiver)

# Group chat - join the discussion room based on disease
@socketio.on("join_disease_room")
def join_disease(data):
    username = data.get("username")
    disease = data.get("disease")

    if not username or not disease:
        return

    disease = disease.lower()  # Standardize room names
    if disease not in disease_rooms:
        disease_rooms[disease] = {'users': [], 'messages': []}

    join_room(disease)  # Join the room for that disease
    disease_rooms[disease]['users'].append(username)

    # Send the message history to the new user
    for msg in disease_rooms[disease]['messages']:
        send(msg, room=disease)

    send(f"{username} joined the discussion for {disease}.", room=disease)
    print(f"{username} joined {disease} room.")

# Group chat - leave the disease room
@socketio.on("leave_disease_room")
def leave_disease(data):
    username = data.get("username")
    disease = data.get("disease")

    if not username or not disease:
        return

    disease = disease.lower()
    leave_room(disease)  # Leave the disease room

    if disease in disease_rooms and username in disease_rooms[disease]['users']:
        disease_rooms[disease]['users'].remove(username)

    send(f"{username} left the discussion.", room=disease)
    print(f"{username} left {disease} room.")

# Personal message - handle private messages between users
@socketio.on("send_private_message")
def send_private_message(data):
    sender = data.get("sender")
    receiver = data.get("receiver")
    message = data.get("message")

    if not sender or not receiver or not message:
        return

    # Create a private room between sender and receiver
    private_room = f"{sender}_{receiver}" if sender < receiver else f"{receiver}_{sender}"

    # Create the private room if it doesn't exist
    if private_room not in private_rooms:
        private_rooms[private_room] = []

    # Store the private message in the room's history
    private_rooms[private_room].append(f"{sender}: {message}")

    join_room(private_room)  # Join the private room
    send(f"{sender} (private): {message}", room=private_room)
    print(f"{sender} sent a private message to {receiver}")

# Group chat - send a message to the disease room
@socketio.on("send_message")
def send_message(data):
    username = data.get("username")
    disease = data.get("disease")
    message = data.get("message")

    if not username or not disease or not message:
        return

    disease = disease.lower()

    # Store the message in the disease room's history
    if disease not in disease_rooms:
        disease_rooms[disease] = {'users': [], 'messages': []}

    disease_rooms[disease]['messages'].append(f"{username}: {message}")
    
    send(f"{username}: {message}", room=disease)

if __name__ == "__main__":
    socketio.run(app, debug=True)