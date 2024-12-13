from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, EmailStr

# ESQUEMA PARA TABELA USUARIO
class UserCreate(BaseModel):
    username: str
    pwd: str
    email: EmailStr
    role_id: int
    is_active: bool = True

    class Config:
        orm_mode = True

class MessageResponse(BaseModel):
    message: str

    class Config:
        orm_mode = True

# ESQUEMA PARA TABELA PACIENTE 
class PatientCreate(BaseModel):
    UserBdID: int

    class Config:
        orm_mode = True

# ESQUEMA PARA TABELA DOUTOR
class DoctorCreate(BaseModel):
    UserBdID: int

    class Config:
        orm_mode = True

class TokenData(BaseModel):
    #access_token: str
    #token_type: str
    #email: str
    role: int
    id: int