import socket
import threading
import queue
import time

messages = queue.Queue()
clients = {}  
chatrooms = {} 
users = {} 
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind(("0.0.0.0", 9999))
key = "mysecretkey" 

try:
    with open("chatrooms.txt", "r") as file:
        for line in file:
            room_name, password = line.strip().split(":")
            chatrooms[room_name] = password
except FileNotFoundError:
    pass

try:
    with open("users.txt", "r") as file:
        for line in file:
            username, password = line.strip().split(":")
            users[username] = password
except FileNotFoundError:
    pass

def rc4_encrypt_decrypt(key, text):
    S = list(range(256))
    j = 0
    out = []
    for i in range(256):
        j = (j + S[i] + ord(key[i % len(key)])) % 256
        S[i], S[j] = S[j], S[i]
    i = j = 0
    for char in text:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        K = S[(S[i] + S[j]) % 256]
        out.append(chr(ord(char) ^ K))
    return ''.join(out)

def receive():
    while True:
        try:
            encrypted_message, addr = server.recvfrom(1824)
            message = rc4_encrypt_decrypt(key, encrypted_message.decode())

            if message.startswith("/login"):
                _, username, password = message.split()
                if username in users:
                    if users[username] == password:
                        server.sendto(rc4_encrypt_decrypt(key, "Login successful").encode(), addr)
                    else:
                        server.sendto(rc4_encrypt_decrypt(key, "Incorrect password").encode(), addr)
                else:
                    users[username] = password
                    with open("users.txt", "a") as file:
                        file.write(f"{username}:{password}\n")
                    server.sendto(rc4_encrypt_decrypt(key, "Registered and logged in").encode(), addr)

            elif message.startswith("/join"):
                _, room_name, password = message.split()
                if addr in clients and clients[addr] == room_name:
                    server.sendto(rc4_encrypt_decrypt(key, "Already in this chatroom").encode(), addr)
                elif room_name in chatrooms and chatrooms[room_name] != password:
                    server.sendto(rc4_encrypt_decrypt(key, "Incorrect chatroom password").encode(), addr)
                else:
                    if room_name not in chatrooms:
                        chatrooms[room_name] = password
                        with open("chatrooms.txt", "a") as file:
                            file.write(f"{room_name}:{password}\n")
                    clients[addr] = room_name
                    server.sendto(rc4_encrypt_decrypt(key, f"Joined {room_name}").encode(), addr)
                    print(f"[{time.strftime('%H:%M:%S')}] {addr} joined room {room_name}")

            elif message.startswith("/history"):
                room_name = clients.get(addr)
                if room_name:
                    try:
                        with open(f"{room_name}_chat_history.txt", "r", encoding="utf-8") as file:
                            history = file.readlines()
                        for line in history:
                            decrypted_line = rc4_encrypt_decrypt(key, line.strip())
                            server.sendto(rc4_encrypt_decrypt(key, decrypted_line).encode(), addr)
                    except FileNotFoundError:
                        server.sendto(rc4_encrypt_decrypt(key, "No chat history available for this room.").encode(), addr)

            elif addr in clients:
                room_name = clients[addr]
                messages.put((message, addr, room_name))
        except Exception as e:
            print(f"Receive error: {e}")

def broadcast():
    while True:
        while not messages.empty():
            message, addr, room_name = messages.get()
            if addr in clients:
                encrypted_message = rc4_encrypt_decrypt(key, message).encode()
                with open(f"{room_name}_chat_history.txt", "a", encoding="utf-8") as file:
                    file.write(f"[{time.strftime('%H:%M:%S')}] {encrypted_message.decode('utf-8')}\n")
                for client, client_room in clients.items():
                    if client_room == room_name:
                        try:
                            server.sendto(encrypted_message, client)
                        except Exception as e:
                            print(f"Broadcast error: {e}")
                            del clients[client]


print("Server started, waiting for clients...")

t1 = threading.Thread(target=receive)
t2 = threading.Thread(target=broadcast)
t1.start()
t2.start()
