import asyncio
import socket
from select import select


class ClientsDict:
    def __init__(self):
        self.clients_dict = {}
        self.client_without_companion = None

    def append_client(self, client):
        if self.client_without_companion:
            if client is self.client_without_companion:
                return None

            self.clients_dict[client] = self.client_without_companion
            self.clients_dict[self.client_without_companion] = client

            self.client_without_companion = None
            return self.clients_dict[client]

        self.client_without_companion = client
        return None

    def get_companion(self, client):
        try:
            return self.clients_dict[client]
        except KeyError:
            return self.append_client(client)

    def delete_client(self, client):
        companion = self.get_companion(client)
        del self.clients_dict[client]
        del self.clients_dict[companion]
        self.append_client(companion)


async def accept_connection(server):
    client, address = server.accept()
    print(f"Connected from {address}")
    to_monitor.append(client)
    client_dict.append_client(client)


async def receive_message(client):
    data = client.recv(1024)
    print(f"Received data: {data.decode()}")

    if data.decode().strip() in ['', '^Z', 'quit', 'exit']:
        client_dict.delete_client(client)
        to_monitor.remove(client)
        client.close()
    else:
        companion = client_dict.get_companion(client)
        if companion:
            companion.send(f"-----------------------------: {data.decode()}".encode())


async def main(server):
    to_monitor.append(server)

    while True:
        done_sockets, _, _ = select(to_monitor, [], [])

        tasks = []
        for sock in done_sockets:
            if sock is server:
                tasks.append(asyncio.create_task(accept_connection(sock)))
            else:
                tasks.append(asyncio.create_task(receive_message(sock)))

        if tasks:
            await asyncio.gather(*tasks)


if __name__ == '__main__':
    port = 8000

    server_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_.bind(('localhost', port))
    server_.listen()

    to_monitor = []
    client_dict = ClientsDict()

    asyncio.run(main(server_))
