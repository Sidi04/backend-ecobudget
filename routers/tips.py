from typing import List
from fastapi import APIRouter, Depends
from models import User
from schemas import TipResponse
from security import get_current_user

router = APIRouter()

# Base de conseils embarquée
TIPS_DATABASE = [
    {
        "id": 1,
        "title": "Comment économiser son argent de poche ?",
        "content": "Met de côté 10% à 20% dès que tu le reçois avant de commencer à dépenser.",
        "category": "Épargne",
        "target_profile": "ELEVE"
    },
    {
        "id": 2,
        "title": "Distinguer les besoins des envies",
        "content": "Un besoin est essentiel (ex: transport, fournitures). Une envie est un plaisir secondaire (ex: snack, jeu).",
        "category": "Éducation",
        "target_profile": "ALL"
    },
    {
        "id": 3,
        "title": "Gérer sa bourse universitaire",
        "content": "Divise ta bourse en 3 parts : 50% pour tes dépenses obligatoires, 30% pour tes loisirs, 20% en épargne d'urgence.",
        "category": "Budget",
        "target_profile": "ETUDIANT"
    },
    {
        "id": 4,
        "title": "Éviter les achats impulsifs",
        "content": "Avant d'acheter un objet non essentiel, applique la règle des 24 heures : attends une journée complète pour voir si tu en as vraiment besoin.",
        "category": "Conseil",
        "target_profile": "ALL"
    },
    {
        "id": 5,
        "title": "Se fixer un objectif d'épargne mensuel",
        "content": "Choisis un petit montant fixe à mettre de côté chaque mois, même 500 MRU. La régularité compte plus que le montant au début.",
        "category": "Épargne",
        "target_profile": "ALL"
    },
    {
        "id": 6,
        "title": "Suivre ses dépenses chaque jour",
        "content": "Prends 2 minutes chaque soir pour noter ce que tu as dépensé. Tu repères beaucoup plus vite les petites fuites d'argent répétées.",
        "category": "Budget",
        "target_profile": "ALL"
    },
    {
        "id": 7,
        "title": "Repérer les abonnements oubliés",
        "content": "Relis une fois par mois la liste de tes abonnements (musique, jeux, forfaits). Résilie ceux que tu n'utilises plus vraiment.",
        "category": "Budget",
        "target_profile": "ALL"
    },
    {
        "id": 8,
        "title": "Profiter des réductions étudiantes",
        "content": "Beaucoup de services (transport, logiciels, culture) offrent des tarifs réduits avec une carte étudiante. Vérifie avant de payer plein tarif.",
        "category": "Conseil",
        "target_profile": "ETUDIANT"
    },
    {
        "id": 9,
        "title": "Un job étudiant compatible avec les études",
        "content": "Si tu cherches un revenu complémentaire, privilégie un rythme flexible (quelques heures par semaine) plutôt qu'un emploi qui empiète sur tes cours.",
        "category": "Éducation",
        "target_profile": "ETUDIANT"
    },
    {
        "id": 10,
        "title": "Mettre de côté l'argent reçu en cadeau",
        "content": "Plutôt que de dépenser immédiatement un cadeau en argent, verse au moins la moitié sur un de tes objectifs d'épargne.",
        "category": "Épargne",
        "target_profile": "ELEVE"
    },
    {
        "id": 11,
        "title": "Comparer avant d'acheter",
        "content": "Pour un achat de plus de 1000 MRU, compare au moins deux endroits ou vendeurs différents avant de te décider.",
        "category": "Conseil",
        "target_profile": "ALL"
    },
    {
        "id": 12,
        "title": "Se constituer une petite réserve d'urgence",
        "content": "Avant de viser des objectifs plus ambitieux, essaie d'avoir de côté l'équivalent d'une semaine de dépenses courantes pour les imprévus.",
        "category": "Épargne",
        "target_profile": "ALL"
    },
    {
        "id": 13,
        "title": "Ne pas prêter sans limite claire",
        "content": "Si tu prêtes de l'argent à un proche, fixe un montant maximum que tu es prêt à ne jamais revoir. Ça évite les tensions et les mauvaises surprises.",
        "category": "Conseil",
        "target_profile": "ALL"
    },
    {
        "id": 14,
        "title": "Utiliser le suivi par catégorie",
        "content": "Regarde régulièrement quelle catégorie de dépense pèse le plus dans ton budget. C'est souvent là qu'il y a le plus facile à ajuster.",
        "category": "Budget",
        "target_profile": "ALL"
    },
]

@router.get("/", response_model=List[TipResponse])
def get_financial_tips(current_user: User = Depends(get_current_user)):
    # Filtrage selon le profil de l'utilisateur connecté
    user_tips = [
        tip for tip in TIPS_DATABASE
        if tip["target_profile"] in ["ALL", current_user.user_type]
    ]
    return user_tips