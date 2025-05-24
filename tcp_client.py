import socket
import hashlib
import time

HOST = '127.0.0.1'  # Endereço do servidor
PORT = 5000         # Porta do servidor

# Função para calcular o hash SHA-256 de um arquivo
def calcular_hash(arquivo):
    hasher = hashlib.sha256()
    with open(arquivo, 'rb') as f:
        while chunk := f.read(4096):
            hasher.update(chunk)
    return hasher.hexdigest()

# Lê uma linha completa da conexão (até '\n')
def recv_linha(conn, buffer):
    while b'\n' not in buffer:
        dados = conn.recv(1024)
        if not dados:
            return None, buffer
        buffer += dados
    linha, buffer = buffer.split(b'\n', 1)
    return linha.decode().strip(), buffer

# Função principal do cliente
def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    buffer = b""

    while True:
        comando = input("Digite um comando (sair / arquivo <nome.ext> / chat <msg>): ")
        client.sendall((comando + '\n').encode())

        if comando.lower() == "sair":
            break

        elif comando.lower().startswith("arquivo "):
            resposta, buffer = recv_linha(client, buffer)
            if resposta is None:
                print("[ERRO] Conexão fechada inesperadamente.")
                break

            if resposta.startswith("OK"):
                _, nome_arquivo, tamanho, hash_servidor = resposta.split()
                tamanho = int(tamanho)
                print(f"[DEBUG] Recebendo arquivo: {nome_arquivo} ({tamanho} bytes, hash: {hash_servidor})")
                client.sendall("OK\n".encode())

                timestamp = int(time.time())
                caminho_arquivo = f"{nome_arquivo}_{timestamp}"

                with open(caminho_arquivo, 'wb') as f:
                    recebido = 0
                    while recebido < tamanho:
                        chunk = client.recv(min(4096, tamanho - recebido))
                        if not chunk:
                            print("[DEBUG] Conexão fechada antes do esperado")
                            break
                        f.write(chunk)
                        recebido += len(chunk)
                    print(f"[DEBUG] Total bytes recebidos: {recebido}")

                hash_cliente = calcular_hash(caminho_arquivo)
                print(f"[DEBUG] Hash do arquivo recebido: {hash_cliente}")
                print(f"[DEBUG] Hash esperado: {hash_servidor}")

                if hash_cliente.strip() == hash_servidor.strip():
                    print(f"Arquivo {nome_arquivo} recebido com sucesso e verificado.")
                else:
                    print(f"Erro: Hash do arquivo recebido não confere. Esperado: {hash_servidor}, Recebido: {hash_cliente}")

            else:
                # Pode ser "NOK Comando desconhecido" ou "NOK Arquivo nao existe"
                print(resposta)

        elif comando.lower().startswith("chat "):
            linha, buffer = recv_linha(client, buffer)
            if linha:
                print(linha)
            else:
                print("Erro ao receber mensagem do servidor.")

        else:
            # Não imprime nada local, só espera resposta do servidor
            linha, buffer = recv_linha(client, buffer)
            if linha:
                print(linha)
            else:
                print("Erro ao receber mensagem do servidor.")

    client.close()

if __name__ == "__main__":
    start_client()
