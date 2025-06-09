from flask import Flask, render_template, request, redirect, flash, url_for
from git import Repo
import os
from git import Repo
import subprocess

app = Flask(__name__)
app.secret_key = 'sua-chave-secreta'
BASE_REPOS_DIR = 'repos'


def get_repos():
    if not os.path.exists(BASE_REPOS_DIR):
        os.makedirs(BASE_REPOS_DIR)
    return [d for d in os.listdir(BASE_REPOS_DIR) if os.path.isdir(os.path.join(BASE_REPOS_DIR, d))]


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        repo_url = request.form['repo_url']
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        repo_path = os.path.join(BASE_REPOS_DIR, repo_name)

        if os.path.exists(repo_path):
            flash('Repositório já existe.', 'warning')
        else:
            try:
                Repo.clone_from(repo_url, repo_path)
                flash('Repositório clonado com sucesso!', 'success')
            except Exception as e:
                flash(f'Erro ao clonar: {str(e)}', 'danger')

    repos = get_repos()
    return render_template('index.html', repos=repos)


@app.route('/commit', methods=['POST'])
def commit():
    repo = request.form['repo']
    file_name = request.form['file_name']
    file_content = request.form['file_content']
    commit_msg = request.form['commit_msg']
    repo_path = os.path.join(BASE_REPOS_DIR, repo)

    file_path = os.path.join(repo_path, file_name)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(file_content)

    r = Repo(repo_path)
    r.git.add(file_name)
    r.index.commit(commit_msg)
    try:
        r.remotes.origin.push()
        flash(f'{file_name} enviado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao fazer push: {str(e)}', 'danger')
    return redirect('/')


@app.route("/status", methods=["POST"])
def status():
    repo_name = request.form["repo"]
    repo_path = os.path.join("repos", repo_name)
    repo = Repo(repo_path)

    # Detectar arquivos modificados (staged ou unstaged)
    changed = repo.index.diff(None)
    changed_files = [item.a_path for item in changed if item.change_type != 'D']

    # Detectar arquivos deletados
    deleted_files = [item.a_path for item in changed if item.change_type == 'D']

    # Detectar arquivos novos (untracked)
    untracked_files = repo.untracked_files

    # Combinar arquivos modificados + novos
    all_files_to_commit = changed_files + untracked_files

    # Gerar previews dos arquivos (limitado para performance)
    previews = {}
    for file in all_files_to_commit:
        file_path = os.path.join(repo_path, file)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    previews[file] = f.read()[:500]  # limite de 500 caracteres
            except Exception as e:
                previews[file] = f"Erro ao ler o arquivo: {e}"

    return render_template(
    "index.html",
    repos=get_repos(),  # <- aqui o ajuste
    selected_repo=repo_name,
    changed_files=all_files_to_commit,
    deleted_files=deleted_files,
    previews=previews
)


@app.route('/commit-status', methods=['POST'])
def commit_status():
    repo_name = request.form['repo']
    commit_msg = request.form['commit_msg']
    selected_files = request.form.getlist('files')

    repo_path = os.path.join(BASE_REPOS_DIR, repo_name)
    repo = Repo(repo_path)

    if not selected_files:
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect('/')

    repo.index.add(selected_files)
    repo.index.commit(commit_msg)
    try:
        repo.remotes.origin.push()
        flash('Alterações enviadas com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao fazer push: {str(e)}', 'danger')
    return redirect('/')


@app.route("/branch/switch", methods=["POST"])
def switch_branch():
    repo = Repo(os.path.join(BASE_REPOS_DIR, request.form["repo"]))
    target = request.form["target_branch"]
    try:
        repo.git.checkout(target)
        flash(f'Trocado para o branch {target}', 'success')
    except Exception as e:
        flash(f'Erro ao trocar branch: {str(e)}', 'danger')
    return redirect("/")


@app.route("/branch/create", methods=["POST"])
def create_branch():
    repo = Repo(os.path.join(BASE_REPOS_DIR, request.form["repo"]))
    new_branch = request.form["new_branch"]
    try:
        repo.git.checkout('-b', new_branch)
        flash(f'Branch {new_branch} criado e ativado.', 'success')
    except Exception as e:
        flash(f'Erro ao criar branch: {str(e)}', 'danger')
    return redirect("/")


@app.route("/branch/merge", methods=["POST"])
def merge_branch():
    repo = Repo(os.path.join(BASE_REPOS_DIR, request.form["repo"]))
    source = request.form["merge_from"]
    try:
        repo.git.merge(source)
        flash(f'Branch {source} mesclado com sucesso.', 'success')
    except Exception as e:
        flash(f'Erro ao fazer merge: {str(e)}', 'danger')
    return redirect("/")


@app.route("/history", methods=["POST"])
def history():
    repo_name = request.form["repo"]
    repo_path = os.path.join(BASE_REPOS_DIR, repo_name)
    if not os.path.exists(repo_path):
        flash('Repositório não encontrado.', 'danger')
        return redirect('/')

    repo = Repo(repo_path)
    commits = list(repo.iter_commits('HEAD', max_count=20))
    return render_template('log.html', commits=commits, repo_name=repo_name)


#criação de repositorio
def criar_repositorio_com_gh(repo_name, github_user, is_private, base_path):
    repo_path = os.path.join(base_path, repo_name)

    if os.path.exists(repo_path):
        flash(f"O diretório {repo_path} já existe.", "warning")
        return False

    try:
        # Cria o diretório local e inicializa com um README
        os.makedirs(repo_path)
        with open(os.path.join(repo_path, "README.md"), "w", encoding="utf-8") as f:
            f.write(f"# {repo_name}\n\nRepositório criado com GitHub CLI.")

        # Inicializa repositório Git local
        subprocess.run(["git", "init"], cwd=repo_path, check=True)
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "commit inicial"], cwd=repo_path, check=True)

        # Monta comando do GitHub CLI
        visibility = "--private" if is_private else "--public"
        subprocess.run(
            ["gh", "repo", "create", f"{github_user}/{repo_name}", visibility, "--source=.", "--remote=origin", "--push"],
            cwd=repo_path,
            check=True
        )

        flash(f"Repositório '{repo_name}' criado e enviado ao GitHub com sucesso!", "success")
        return True

    except subprocess.CalledProcessError as e:
        flash(f"Erro ao executar comando: {e}", "danger")
    except Exception as e:
        flash(f"Erro geral: {e}", "danger")
    return False

@app.route('/create-repo', methods=['POST'])
def create_repo():
    repo_name = request.form.get('repo_name').strip()
    base_path = request.form.get('base_path').strip()
    github_user = request.form.get('github_user').strip()
    is_private = bool(request.form.get('private'))

    criar_repositorio_com_gh(repo_name, github_user, is_private, base_path)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
