import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Enum, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base

class UserType(str, enum.Enum):
    ELEVE = "ELEVE"
    ETUDIANT = "ETUDIANT"

class IncomeSource(str, enum.Enum):
    ARGENT_DE_POCHE = "ARGENT_DE_POCHE"  # Élève
    CADEAUX = "CADEAUX"                  # Élève
    SAVINGS = "SAVINGS"            # Élève / Étudiant
    BOURSE = "BOURSE"    # Étudiant
    AIDE_FAMILIAL = "AIDE_FAMILIAL"      # Étudiant
    STAGE = "STAGE"      # Étudiant
    AUTRES = "AUTRES"

class ExpenseCategory(str, enum.Enum):
    NOURRITURE = "NOURRITURE"
    TRANSPORT = "TRANSPORT"
    ETUDES = "ETUDES"
    COMMUNICATION = "COMMUNICATION"
    LOISIRS = "LOISIRS"
    ACHATS = "ACHATS"
    AUTRES = "AUTRES"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    user_type = Column(Enum(UserType), nullable=False)

    # Profil Élève
    school_level = Column(String, nullable=True)

    # Profil Étudiant
    university = Column(String, nullable=True)
    study_level = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    #Revenus
    incomes = relationship("Income", back_populates="owner")
    #Depenses
    expenses = relationship("Expense", back_populates="owner")
    #Buts
    goals = relationship("SavingsGoal", back_populates="owner")

class Income(Base):
    __tablename__ = "incomes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    source_type = Column(Enum(IncomeSource), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    note = Column(String, nullable=True)

    owner = relationship("User", back_populates="incomes")

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    category = Column(Enum(ExpenseCategory), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    date = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="expenses")

class SavingsGoal(Base):
    __tablename__ = "savings_goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    is_completed = Column(Boolean, default=False)

    owner = relationship("User", back_populates="goals")