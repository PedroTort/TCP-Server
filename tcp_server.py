import socket
import os
import threading
import hashlib

HOST = '127.0.0.1'  # Endereço do servidor
PORT = 5000         # Porta do servidor

# Função para calcular o hash SHA-256 de um arquivo
def calcular_hash(arquivo):
    hasher = hashlib.sha256()
    with open(arquivo, 'rb') as f:
        while chunk := f.read(4096):
            hasher.update(chunk)
    return hasher.hexdigest()

# Funcao para ler uma linha completa do socket (terminada com '\n')
def recv_linha(conn, buffer):
    while b'\n' not in buffer:
        dados = conn.recv(1024)
        if not dados:
            return None, buffer
        buffer += dados
    linha, buffer = buffer.split(b'\n', 1)
    return linha.decode().strip(), buffer

# Função para lidar com a conexão de um cliente
def handle_client(conn, addr):
    print(f"Nova conexão de {addr}")
    buffer = b"" # Buffer para receber dados
 
    while True:
        try:
            linha, buffer = recv_linha(conn, buffer)
            if linha is None:
                break
            requisicao = linha

            if not requisicao:
                break

            if requisicao.lower() == "sair":
                print(f"Cliente {addr} desconectou.")
                break

            elif requisicao.lower().startswith("arquivo "):
                nome_arquivo = requisicao.split(" ", 1)[1]
                if os.path.exists(nome_arquivo):
                    tamanho = os.path.getsize(nome_arquivo)
                    hash_arquivo = calcular_hash(nome_arquivo)
                    msg_ok= f"OK {nome_arquivo} {tamanho} {hash_arquivo}\n"
                    print(msg_ok.strip())
                    conn.sendall(msg_ok.encode())

                    confirmacao_linha, buffer = recv_linha(conn,buffer)

                    if confirmacao_linha == "OK": # Cliente confirma recebimento, envia o arquivo
                        with open(nome_arquivo, 'rb') as f:
                            while chunk := f.read(4096):
                                conn.sendall(chunk)

                    else:
                        print(f"Cliente {addr} não confirmou recebimento do arquivo.")
                        conn.sendall("NC NAo houve confirmacao do arquivo \n".encode()) 
                else:
                    print(f"Arquivo {nome_arquivo} não encontrado.")
                    conn.sendall("NOK Arquvi nao existe\n".encode())

            elif requisicao.lower().startswith("chat "):
                msg = requisicao[5:].strip()
                resposta = f"CHAT recebido: {msg}\n"
                conn.sendall(resposta.encode()) # Envia confirmação da mensagem
            
            else:
                print(f"Comando desconhecido de {addr}: '{requisicao}'")
                conn.sendall("NOK Comando desconhecido\n".encode())

        except Exception as e:
            print(f"Erro ao lidar com o cliente {addr}: {e}")
            break

    conn.close()

# Função para iniciar o servidor
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Servidor escutando em {HOST}:{PORT}")
    while True:
        conn, addr = server.accept()
        print(f"Conexão aceita de {addr}")
        thread = threading.Thread(target=handle_client, args=(conn,addr))
        thread.start()

if __name__ == "__main__":
    start_server()