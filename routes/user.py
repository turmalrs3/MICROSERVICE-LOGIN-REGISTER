from dotenv import load_dotenv
import os
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2AuthorizationCodeBearer, OAuth2PasswordRequestForm
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from config.db import conn
from schemas.schema import UserCreate, MessageResponse, TokenData
from cryptography.fernet import Fernet
from config.auth import create_access_token

load_dotenv()
key = os.getenv("FERRET_KEY").encode()

user = APIRouter()

# OPERACAO POST PARA CRIAR UM NOVO USUARIO
@user.post("/createUsers", response_model=MessageResponse)
def create_user(user_data: UserCreate):

    try:
        check_query = text("""
                       SELECT * FROM UserBd WHERE Username = :username OR Email = :email""")
        existing_user = conn.execute(check_query, {
            "username": user_data.username,
            "email": user_data.email
        }).fetchone()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Usuario com este username ou email ja existe."
            )
        
        #inserir user 
        hashed_pwd = Fernet(key).encrypt(user_data.pwd.encode()).decode() #Criptografa a senha
        query_user = text("""
                INSERT INTO UserBd (Username, Pwd, Email, UserRoleID, IsActive) 
                VALUES (:username, :pwd, :email, :role_id, :is_active)""")
        conn.execute(query_user, {
            "username": user_data.username,
            "pwd": hashed_pwd,
            "email": user_data.email,
            "role_id": user_data.role_id,
            "is_active": user_data.is_active
        })

        #recuperar o id do usuario recem criado
        user_id_query = text("SELECT LAST_INSERT_ID() AS user_id")
        user_id_result = conn.execute(user_id_query).fetchone()
        user_id = user_id_result[0]

        #dependendo do role_id adiciona na tabela correspondente(paciente, doutor)
        if user_data.role_id == 1: #paciente
            query_patient = text("INSERT INTO Patient (UserBdID, Email) VALUES (:user_id, :email)")
            conn.execute(query_patient, {"user_id": user_id, "email": user_data.email})

        if user_data.role_id == 4: #doutor
            query_doctor = text("INSERT INTO Doctor (UserBdID, Email) VALUES (:user_id, :email)")
            conn.execute(query_doctor, {"user_id": user_id, "email": user_data.email})

        conn.commit()
        #retornar os dados do usario criado
        return {"message": "Usuario criado com sucesso."}
    
    except SQLAlchemyError as e:
        conn.rollback()
        print(str(e))
        raise HTTPException(status_code=500, detail="Erro ao criar usuário.")
    
# OPERACAO POST PARA LOGIN

@user.post("/login", response_model=TokenData)
def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        # Verificar se o usuário existe no banco de dados
        query = text("SELECT * FROM UserBd WHERE Email = :email")
        user = conn.execute(query, {"email": form_data.username}).fetchone()

        if not user:
            raise HTTPException(status_code=400, detail="Email ou senha incorretos.")

        # Descriptografar e verificar a senha
        user_dict = dict(user._mapping)

        
        decrypted_pwd = Fernet(key).decrypt(user_dict["Pwd"].encode()).decode()  # Descriptografando

        # Verificar se a senha fornecida corresponde à senha descriptografada
        if form_data.password != decrypted_pwd:
            raise HTTPException(status_code=400, detail="Email ou senha incorretos.")

        # Criar o token JWT
        access_token = create_access_token(data={
            "sub": user_dict["Email"],
            "username": user_dict["UserName"],  # Nome correto da chave
            "role": user_dict["UserRoleID"]
        })

        # Retornar os dados do token
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "email": user_dict["Email"],
            "role": user_dict["UserRoleID"],
            "id": user_dict["UserBdID"]
        }

    except SQLAlchemyError as e:
        print(str(e))
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")
