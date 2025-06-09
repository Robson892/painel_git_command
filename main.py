import os
from git import Repo

# 1. Clonar o repositório (se ainda não existir)
repo_url = 'https://github.com/robson892/analisador-de-curriculos.git'
local_path = 'meu-repositorio'

if not os.path.exists(local_path):
    print("Clonando o repositório...")
    repo = Repo.clone_from(repo_url, local_path)
else:
    print("Repositório já clonado.")
    repo = Repo(local_path)

# 2. Criar um novo arquivo
arquivo_novo = os.path.join(local_path, 'arquivo_teste.txt')
with open(arquivo_novo, 'w') as f:
    f.write('Este é um teste de commit com GitPython.')

# 3. Adicionar o arquivo ao staging
repo.git.add('arquivo_teste.txt')

# 4. Commitar
repo.index.commit("Adiciona arquivo_teste.txt via GitPython")

# 5. Push (envio para o repositório remoto)
try:
    origin = repo.remote(name='origin')
    origin.push()
    print("Push realizado com sucesso!")
except Exception as e:
    print("Erro ao enviar para o repositório remoto:", str(e))
