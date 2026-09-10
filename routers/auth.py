from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserType
from schemas import UserCreate, UserResponse, UserUpdate, PasswordChange
from security import get_current_user, get_password_hash, verify_password, create_access_token

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Vérification si l'email existe déjà
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Un compte avec cet email existe déjà."
        )

    # Création du nouvel utilisateur
    hashed_pwd = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_pwd,
        full_name=user_data.full_name,
        user_type=user_data.user_type,
        school_level=user_data.school_level,
        university=user_data.university,
        study_level=user_data.study_level
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Recherche de l'utilisateur par email (form_data.username)
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun compte avec cette email",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Génération du JWT Token
    access_token = create_access_token(data={"sub": str(user.id), "user_type": user.user_type})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "user_type": user.user_type
        }
    }

@router.get("/users/me", response_model=UserResponse)
def read_name_user(
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.put("/users/me", response_model=UserResponse)
def update_profile(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_user.full_name = user_data.full_name

    # On ne met à jour que les champs pertinents pour le type de profil
    # existant — un ELEVE n'a pas d'université, un ETUDIANT n'a pas de
    # niveau scolaire, pas la peine de garder les deux jeux de champs.
    if current_user.user_type == UserType.ELEVE:
        current_user.school_level = user_data.school_level
    else:
        current_user.university = user_data.university
        current_user.study_level = user_data.study_level

    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/users/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le mot de passe actuel est incorrect."
        )

    current_user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    return None