from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Expense, Income, SavingsGoal, User
from schemas import GoalCreate, GoalResponse, GoalDeposit
from security import get_current_user

router = APIRouter()


def _get_available_balance(db: Session, user_id: int) -> float:
    total_income = sum(
        income.amount
        for income in db.query(Income).filter(Income.user_id == user_id).all()
    )
    total_expense = sum(
        expense.amount
        for expense in db.query(Expense).filter(Expense.user_id == user_id).all()
    )
    total_saved = sum(
        goal.current_amount
        for goal in db.query(SavingsGoal).filter(SavingsGoal.user_id == user_id).all()
    )
    return total_income - total_expense - total_saved

# --- 1. CRÉER UN OBJECTIF D'ÉPARGNE ---
@router.post("/", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    goal_data: GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if goal_data.target_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le montant cible doit être supérieur à zéro."
        )

    new_goal = SavingsGoal(
        **goal_data.model_dump(),
        user_id=current_user.id
    )
    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)
    return new_goal


# --- 2. LISTER TOUS LES OBJECTIFS ---
@router.get("/", response_model=List[GoalResponse])
def get_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(SavingsGoal).filter(SavingsGoal.user_id == current_user.id).all()


# --- 3. ALIMENTER UNE CAGNOTTE (VERSER DE L'ARGENT) ---
@router.post("/{goal_id}/deposit", response_model=GoalResponse)
def deposit_to_goal(
    goal_id: int,
    deposit: GoalDeposit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if deposit.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le montant du versement doit être supérieur à zéro."
        )

    # Récupération de l'objectif
    goal = db.query(SavingsGoal).filter(
        SavingsGoal.id == goal_id,
        SavingsGoal.user_id == current_user.id
    ).first()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objectif non trouvé."
        )

    if deposit.amount > _get_available_balance(db, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le solde disponible est insuffisant pour ce versement."
        )

    # Mise à jour du montant actuel
    goal.current_amount += deposit.amount

    # Vérification si l'objectif est atteint
    if goal.current_amount >= goal.target_amount:
        goal.is_completed = True

    db.commit()
    db.refresh(goal)
    return goal


# --- 4. SUPPRIMER UN OBJECTIF ---
@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    goal = db.query(SavingsGoal).filter(
        SavingsGoal.id == goal_id,
        SavingsGoal.user_id == current_user.id
    ).first()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objectif non trouvé."
        )

    db.delete(goal)
    db.commit()
    return None