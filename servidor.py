#  Implementação de um chat básico:
#  ○ Deve ter no mínimo 3 clientes;
#  ○ Deverá ter dois códigos diferentes, o do servidor e do cliente;
#  ○ O Cliente terá um menu onde ele irá escolher o que ele deseja fazer:
# ■ Escutar até receber uma mensagem, depois ele volta para o menu;
#  ■ Apenas escutar mensagens e mostrar na tela;
#  ■ Sair.
#  ■ Mandar mensagem para 1 cliente informando a qual cliente que ele deseja mandar a
# mensagem;
#  ■ Enviar mensagem e escutar a resposta e depois voltar ao menu;
#  ○ O servidor deverá censurar mensagens indevidas (as palavras são definidas pelo grupo).
#  ○ Caso o cliente mande 3 mensagens indevidas no período de 1 minuto, ele deve ser banido e as
# mensagens dele não serão mais transmitidas.
import socket
import datetime

BUFFER = 1024
HOST = "127.0.0.1"
PORT = 9000
PALAVRAS_BANIDA = [
    "buceta",
    "caralho",
    "pika",
    "rolao",
    "cachorra",
    "safada",
    "vagabunda",
    "pih da moiangaba",
    "puta",
    "tijolinho",
    "amigo de o3",
    "Emilly",
]
NMR_CLIENTES = 2


class TratamentoDeMensagem:
    def is_palavrao(self, message):
        return message.lower() in [i.lower() for i in PALAVRAS_BANIDA]

    def msg_censurada(self, message: str) -> str:
        for palavra in PALAVRAS_BANIDA:
            if palavra in message:
                message = message.replace(palavra, "*" * len(palavra))
        return message

class Cliente:
    def __init__(self, cliente_socket, cliente_addrs) -> None:
        self.cliente_socket: socket.socket = cliente_socket
        self.cliente_addrs = cliente_addrs
        self.data_palavroes: list[datetime.datetime] = []
        self.tratamento_msg = TratamentoDeMensagem()

    def add_data_palavroes(self, message):
        if self.tratamento_msg.is_palavrao(message):
            self.data_palavroes.append(datetime.datetime.now())

    def palavroes_falados(self):
        fim = datetime.datetime.now()
        inicio = fim - datetime.timedelta(minutes=1)
        palavroes = len([data for data in self.data_palavroes if inicio <= data <= fim])
        print(palavroes)
        return palavroes >= 3

class Servidor:

    def __init__(self):
        self.addr = (HOST, PORT)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._clientes: dict[str, Cliente] = {}
        self.banidos: list[str] = []
        self.tratamento_de_mensagem = TratamentoDeMensagem()

    def init(self):
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(self.addr)
        self.server_socket.listen(NMR_CLIENTES)

    @property
    def clientes(self):
        return self._clientes

    def is_banned(self, cliente_addrs):
        is_ok = False
        
        if cliente_addrs[0] in [cliente for cliente in self.banidos]:
            is_ok = True
            
        return is_ok

    def is_suport_connect(self):
        is_ok = True
        if len(self.clientes) >= NMR_CLIENTES:
            is_ok = False
        return is_ok

    def __add_clientes(self, cliente_addrs, cliente_socket, user_name) -> bool:
        is_add = True
        if user_name in self.clientes:
            is_add = False
        else:
            self.clientes[user_name] = Cliente(cliente_socket, cliente_addrs)
        return is_add

    def connect_user(self):
        client_socket, client_addr = self.server_socket.accept()
        name = client_socket.recv(BUFFER).decode()

        if self.is_banned(client_addr):
            client_socket.send("disconnected: Voce foi banido!".encode())
            client_socket.close()

        elif not self.is_suport_connect():
            client_socket.send("disconnected: Servidor cheio!".encode())
            client_socket.close()

        else:
            if not (self.__add_clientes(client_addr, client_socket, name)):
                client_socket.send("disconnected: Nome em uso!".encode())
                client_socket.close()
            else:
                client_socket.send("connected: conectado!".encode())

    def handle_client(self, cliente_send: Cliente, name_send):
        try:
            cliente_send.cliente_socket.settimeout(2)
            msg_recebida: str = cliente.cliente_socket.recv(BUFFER).decode()
            cliente_send.cliente_socket.settimeout(None)

            if msg_recebida == "":
                raise ConnectionResetError

            nome_recebido, mensagem = msg_recebida.split(", ", 1)
            cliente_send.add_data_palavroes(mensagem)
            
            mensagem = self.tratamento_de_mensagem.msg_censurada(mensagem)
            for nome_cliente, cliente_destino in self.clientes.items():
                if nome_cliente == nome_recebido:
                    if cliente_send.palavroes_falados():
                        self.banidos.append(cliente_send.cliente_addrs[0])
                        
                        cliente_send.cliente_socket.send("banned".encode())
                        print(f"Cliente {cliente_send.cliente_addrs[0]} foi banido.")
                        raise ConnectionAbortedError
                        
                    cliente_destino.cliente_socket.send(mensagem.encode())

        except socket.timeout:
            print(f"Tempo limite excedido para o cliente {cliente.cliente_addrs}.")

        except (ConnectionResetError, ConnectionAbortedError):
            print(f"Cliente {cliente.cliente_addrs} desconectado.")
            self.clientes.pop(name_send)

if __name__ == "__main__":
    servidor = Servidor()
    servidor.init()

    while True:
        if servidor.is_suport_connect():
            print("Adicione um cliente para continuar")
            servidor.connect_user()
            continue

        try:
            for name, cliente in servidor.clientes.items():
                servidor.handle_client(cliente, name)
        except RuntimeError:
            print("Alerta: Um cliente foi desconectado.")
