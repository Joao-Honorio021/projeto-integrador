"""Bootstrap explícito, sem credenciais administrativas padrão."""
from getpass import getpass
from .database import Session
from .models import User
from .core.security import password_hash
from .repositories.sql_repository import insert, user_by_email

def main():
    name=input('Nome: ').strip()
    email=input('E-mail: ').strip().lower()
    password=getpass('Senha (mínimo 12 caracteres): ')
    if len(name)<2 or '@' not in email or len(password)<12:
        raise SystemExit('Dados inválidos')
    if password!=getpass('Confirme a senha: '):raise SystemExit('Senhas diferentes')
    with Session.begin() as db:
        if user_by_email(db,email):raise SystemExit('Usuário já existente; nenhuma alteração realizada')
        insert(db,User,nome=name,email=email,senha_hash=password_hash.hash(password),perfil='administrador',ativo=True)
    print('Administrador criado.')
if __name__=='__main__':main()
