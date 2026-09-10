from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from models import UserType, IncomeSource, ExpenseCategory

# Auth & Profils
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    user_type: UserType
    school_level: Optional[str] = None
    university: Optional[str] = None
    study_level: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    user_type: UserType
    school_level: Optional[str] = None
    university: Optional[str] = None
    study_level: Optional[str] = None

    class Config:
        from_attributes = True

# --- ÉDITION DU PROFIL ---
# Le user_type n'est volontairement pas modifiable ici : basculer entre
# ELEVE et ETUDIANT change les champs pertinents (school_level vs
# university/study_level) et mériterait son propre flux, pas un simple PUT.
class UserUpdate(BaseModel):
    full_name: str = Field(min_length=1, max_length=100)
    school_level: Optional[str] = None
    university: Optional[str] = None
    study_level: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, description="8 caractères minimum.")

# Revenus
class IncomeCreate(BaseModel):
    source_type: IncomeSource
    amount: float = Field(gt=0)
    note: Optional[str] = None

class IncomeResponse(IncomeCreate):
    id: int
    date: datetime
    class Config:
        from_attributes = True

# Dépenses
class ExpenseCreate(BaseModel):
    category: ExpenseCategory
    amount: float = Field(gt=0)
    description: Optional[str] = None

class ExpenseResponse(ExpenseCreate):
    id: int
    date: datetime
    class Config:
        from_attributes = True

# Objectifs d'épargne
class GoalCreate(BaseModel):
    title: str
    target_amount: float = Field(gt=0)

class GoalResponse(GoalCreate):
    id: int
    current_amount: float
    is_completed: bool
    class Config:
        from_attributes = True

# Dans schemas.py
class GoalDeposit(BaseModel):
    amount: float = Field(gt=0)

# --- ASSISTANT "J'ACHÈTE OU PAS ?" ---
class DecisionRequest(BaseModel):
    item_name: str
    price: float = Field(gt=0)

class DecisionResponse(BaseModel):
    item_name: str
    price: float
    verdict: str           # "GREEN", "ORANGE", "RED"
    title: str
    message: str
    solde_actuel: float
    solde_apres_achat: float
    budget_quotidien_actuel: float
    budget_quotidien_apres_achat: float

# --- CONSEILS FINANCIERS ---
class TipResponse(BaseModel):
    id: int
    title: str
    content: str
    category: str
    target_profile: str

# --- RÉPARTITION DES DÉPENSES PAR CATÉGORIE ---
class CategoryBreakdownItem(BaseModel):
    category: ExpenseCategory
    amount: float
    percentage: float

class BudgetBreakdownResponse(BaseModel):
    month: str  # format "YYYY-MM"
    total_expense: float
    categories: List[CategoryBreakdownItem]