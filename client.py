import socket
import threading
import random
import time

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.bind(("0.0.0.0", random.randint(8000, 9000)))
key = "mysecretkey" 
server_ip = input("Enter the server IP address: ")
username = input("Enter your username: ")
password = input("Enter your password: ")

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
            encrypted_message, _ = client.recvfrom(1024)
            decrypted_message = rc4_encrypt_decrypt(key, encrypted_message.decode())
            print(decrypted_message)
        except Exception as e:
            print(f"Receive error: {e}")
            break

t = threading.Thread(target=receive)
t.start()

login_message = f"/login {username} {password}"
client.sendto(rc4_encrypt_decrypt(key, login_message).encode(), (server_ip, 9999))
print(f"Welcome, {username}!")

while True:
    chatroom = input("Enter chatroom name (or 'exit' to quit): ")
    if chatroom.lower() == "exit":
        client.close()
        break
    room_password = input("Enter chatroom password: ")
    join_message = f"/join {chatroom} {room_password}"
    client.sendto(rc4_encrypt_decrypt(key, join_message).encode(), (server_ip, 9999))

    while True:
        message = input("")
        if message == "!q":
            print("Leaving chatroom...")
            break
        elif message == "/history":
            client.sendto(rc4_encrypt_decrypt(key, "/history").encode(), (server_ip, 9999))
        else:
            timestamp = time.strftime('%H:%M:%S')
            encrypted_message = rc4_encrypt_decrypt(key, f"[{timestamp}] {username}: {message}")
            client.sendto(encrypted_message.encode(), (server_ip, 9999))
