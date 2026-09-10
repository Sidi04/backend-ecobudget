from calendar import monthrange
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from database import get_db
from models import Expense, Income, SavingsGoal, User
from schemas import (
    ExpenseCreate, ExpenseResponse,
    IncomeCreate, IncomeResponse,
    BudgetBreakdownResponse, CategoryBreakdownItem
)
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

# --- REVENUS ---
@router.post("/incomes", response_model=IncomeResponse, status_code=status.HTTP_201_CREATED)
def add_income(
    income_data: IncomeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if income_data.amount < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le montant du revenu ne peut pas être négatif."
        )
    
    new_income = Income(**income_data.model_dump(), user_id=current_user.id)
    db.add(new_income)
    db.commit()
    db.refresh(new_income)
    return new_income

@router.get("/incomes", response_model=List[IncomeResponse])
def get_incomes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Income).filter(Income.user_id == current_user.id).all()

@router.put("/incomes/{income_id}", response_model=IncomeResponse)
def update_income(
    income_id: int,
    income_data: IncomeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    income = db.query(Income).filter(
        Income.id == income_id,
        Income.user_id == current_user.id
    ).first()

    if not income:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Revenu non trouvé."
        )
    balance_after_update = (
        _get_available_balance(db, current_user.id)
        - income.amount
        + income_data.amount
    )
    if balance_after_update < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette modification rendrait le solde disponible négatif."
        )

    income.source_type = income_data.source_type
    income.amount = income_data.amount
    income.note = income_data.note

    db.commit()
    db.refresh(income)
    return income

@router.delete("/incomes/{income_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_income(
    income_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    income = db.query(Income).filter(
        Income.id == income_id,
        Income.user_id == current_user.id
    ).first()

    if not income:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Revenu non trouvé."
        )

    balance_after_delete = _get_available_balance(db, current_user.id) - income.amount
    if balance_after_delete < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce revenu ne peut pas être supprimé : le solde disponible deviendrait négatif."
        )

    db.delete(income)
    db.commit()
    return None

# --- DÉPENSES ---
@router.post("/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def add_expense(
    expense_data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    balance_after_expense = _get_available_balance(db, current_user.id) - expense_data.amount
    if balance_after_expense < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le solde disponible est insuffisant pour cette dépense."
        )

    new_expense = Expense(**expense_data.model_dump(), user_id=current_user.id)
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense

@router.get("/expenses", response_model=List[ExpenseResponse])
def get_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Expense).filter(Expense.user_id == current_user.id).all()

@router.put("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    expense_data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).first()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dépense non trouvée."
        )

    balance_after_update = (
        _get_available_balance(db, current_user.id)
        + expense.amount
        - expense_data.amount
    )
    if balance_after_update < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le solde disponible est insuffisant pour cette dépense."
        )

    expense.category = expense_data.category
    expense.amount = expense_data.amount
    expense.description = expense_data.description

    db.commit()
    db.refresh(expense)
    return expense

@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).first()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dépense non trouvée."
        )

    db.delete(expense)
    db.commit()
    return None

# --- FONCTION : "IL ME RESTE COMBIEN ?" ---
@router.get("/remaining")
def get_remaining_budget(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Total des revenus
    total_income = sum(i.amount for i in db.query(Income).filter(Income.user_id == current_user.id).all())

    # Total des dépenses
    total_expense = sum(e.amount for e in db.query(Expense).filter(Expense.user_id == current_user.id).all())

    # Total déjà mis de côté sur les objectifs d'épargne : cet argent n'est
    # ni une dépense, ni disponible pour de nouveaux achats, donc il doit
    # sortir du solde disponible sans polluer la répartition par catégorie
    # de dépenses.
    total_saved = sum(
        g.current_amount
        for g in db.query(SavingsGoal).filter(SavingsGoal.user_id == current_user.id).all()
    )

    solde_disponible = total_income - total_expense - total_saved

    # Calcul du nombre de jours restants dans le mois actuel
    today = datetime.now()
    days_in_month = monthrange(today.year, today.month)[1]
    days_remaining = (days_in_month - today.day) + 1  # Inclut aujourd'hui

    daily_budget = solde_disponible / days_remaining if days_remaining > 0 and solde_disponible > 0 else 0

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "total_saved": total_saved,
        "solde_disponible": solde_disponible,
        "days_remaining_in_month": days_remaining,
        "daily_budget_recommended": round(daily_budget, 2)
    }

# --- RÉPARTITION DES DÉPENSES PAR CATÉGORIE ---
def _parse_month_param(month: Optional[str]) -> tuple[int, int]:
    """Valide et parse le paramètre 'month' au format YYYY-MM.
    Retourne (année, mois). Utilise le mois courant si non fourni."""
    if month is None:
        today = datetime.now()
        return today.year, today.month

    parts = month.split("-")
    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le paramètre 'month' doit être au format YYYY-MM, ex: 2026-09."
        )

    try:
        year, month_num = int(parts[0]), int(parts[1])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le paramètre 'month' doit être au format YYYY-MM, ex: 2026-09."
        )

    if not (1 <= month_num <= 12):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le mois doit être compris entre 01 et 12."
        )

    return year, month_num


@router.get("/breakdown", response_model=BudgetBreakdownResponse)
def get_expense_breakdown(
    month: Optional[str] = Query(
        None,
        description="Mois au format YYYY-MM (ex: 2026-09). Par défaut, le mois en cours."
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    year, month_num = _parse_month_param(month)

    start_date = datetime(year, month_num, 1)
    last_day = monthrange(year, month_num)[1]
    end_date = datetime(year, month_num, last_day, 23, 59, 59)

    rows = (
        db.query(Expense.category, func.sum(Expense.amount).label("total"))
        .filter(
            Expense.user_id == current_user.id,
            Expense.date >= start_date,
            Expense.date <= end_date
        )
        .group_by(Expense.category)
        .all()
    )

    total_expense = sum(row.total for row in rows) if rows else 0.0

    categories = [
        CategoryBreakdownItem(
            category=row.category,
            amount=round(row.total, 2),
            percentage=round((row.total / total_expense) * 100, 1) if total_expense > 0 else 0.0
        )
        for row in rows
    ]

    # Tri décroissant : la catégorie qui pèse le plus lourd en premier
    categories.sort(key=lambda c: c.amount, reverse=True)

    return BudgetBreakdownResponse(
        month=f"{year}-{month_num:02d}",
        total_expense=round(total_expense, 2),
        categories=categories
    )