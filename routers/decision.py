from calendar import monthrange
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Expense, Income, SavingsGoal, User
from schemas import DecisionRequest, DecisionResponse
from security import get_current_user

router = APIRouter()

@router.post("/buy", response_model=DecisionResponse)
def analyze_purchase(
    request: DecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if request.price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le prix de l'achat doit être supérieur à zéro."
        )

    # 1. Calcul du solde disponible actuel
    total_income = sum(i.amount for i in db.query(Income).filter(Income.user_id == current_user.id).all())
    total_expense = sum(e.amount for e in db.query(Expense).filter(Expense.user_id == current_user.id).all())
    total_saved = sum(
        goal.current_amount
        for goal in db.query(SavingsGoal).filter(SavingsGoal.user_id == current_user.id).all()
    )
    solde_actuel = total_income - total_expense - total_saved

    # 2. Calcul du nombre de jours restants dans le mois
    today = datetime.now()
    days_in_month = monthrange(today.year, today.month)[1]
    days_remaining = max((days_in_month - today.day) + 1, 1)

    # 3. Calculs d'impact
    budget_quotidien_actuel = round(max(solde_actuel / days_remaining, 0), 2)
    solde_apres_achat = solde_actuel - request.price
    budget_quotidien_apres_achat = round(max(solde_apres_achat / days_remaining, 0), 2)

    # 4. Arbre de décision / Logique métier
    if request.price > solde_actuel:
        verdict = "RED"
        title = "Achat déconseillé 🚫"
        message = (
            f"Tu n'as pas assez d'argent disponible ({solde_actuel:.2f} MRU) "
            f"pour acheter '{request.item_name}' à {request.price:.2f} MRU."
        )
    elif request.price > (solde_actuel * 0.4):
        verdict = "ORANGE"
        title = "Attention, achat risqué ⚠️"
        message = (
            f"Cet achat représente plus de 40% de ton argent disponible. "
            f"Ton budget quotidien passera de {budget_quotidien_actuel:.2f} MRU à {budget_quotidien_apres_achat:.2f} MRU par jour."
        )
    else:
        verdict = "GREEN"
        title = "Achat possible ! ✅"
        message = (
            f"Cet achat respecte ton budget. Il te restera {solde_apres_achat:.2f} MRU "
            f"({budget_quotidien_apres_achat:.2f} MRU par jour) jusqu'à la fin du mois."
        )

    return DecisionResponse(
        item_name=request.item_name,
        price=request.price,
        verdict=verdict,
        title=title,
        message=message,
        solde_actuel=solde_actuel,
        solde_apres_achat=solde_apres_achat,
        budget_quotidien_actuel=budget_quotidien_actuel,
        budget_quotidien_apres_achat=budget_quotidien_apres_achat
    )