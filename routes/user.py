from dotenv import load_dotenv
import os
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2AuthorizationCodeBearer, OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from config.db import conn
from pydantic import BaseModel
from schemas.schema import UserCreate, MessageResponse, TokenData
from cryptography.fernet import Fernet
from config.auth import create_access_token,  decode_access_token

load_dotenv()
key = os.getenv("FERRET_KEY").encode()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://saudeplus-alb-1862619778.us-east-1.elb.amazonaws.com/service1/login")
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

class LoginRequest(BaseModel):
    email: str
    password: str

# OPERACAO POST PARA LOGIN
@user.post("/login")
def login_user(request: LoginRequest):
    try:
        # Verificar se o usuário existe no banco de dados
        query = text("SELECT * FROM UserBd WHERE Email = :email")
        user = conn.execute(query, {"email": request.email}).fetchone()

        if not user:
            raise HTTPException(status_code=400, detail="Email ou senha incorretos.")

        # Descriptografar e verificar a senha
        user_dict = dict(user._mapping)
        decrypted_pwd = Fernet(key).decrypt(user_dict["Pwd"].encode()).decode()  # Descriptografando

        # Verificar se a senha fornecida corresponde à senha descriptografada
        if request.password != decrypted_pwd:
            raise HTTPException(status_code=400, detail="Email ou senha incorretos.")

        # Retornar os dados do usuário
        return {
            "email": user_dict["Email"],
            "role": user_dict["UserRoleID"],
            "id": user_dict["UserBdID"]
        }

    except SQLAlchemyError as e:
        print(str(e))
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
     # Busca o usuário no banco de dados
    user_query = text("SELECT * FROM UserBd WHERE Email = :email")
    user = conn.execute(user_query, {"email": payload["sub"]}).fetchone()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return dict(user._mapping)

#OPERACAO GET PARA USUARIO LOGADO
@user.get("/validate", tags=["Auth"])
async def validate_token(token: str = Depends(oauth2_scheme)):
    """
    Endpoint para validar um token JWT e retornar os dados do usuário.
    """
    user = get_current_user(token)  # Chama a função de validação
    return {
        "id": user["UserBdID"],
        "email": user["Email"],
        "role": user["UserRoleID"],
        "username": user["UserName"]
    }

@user.get("/validate_manual", tags=["Auth"])
def validate_token_manual(token: str):
    """
    Endpoint para validar um token JWT fornecido como query parameter.
    """
    try:
        user = get_current_user(token)  # Chama a função de validação
        return {
            "id": user["UserBdID"],
            "email": user["Email"],
            "role": user["UserRoleID"],
            "username": user["UserName"]
        }
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
