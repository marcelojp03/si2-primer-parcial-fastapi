from fastapi import APIRouter

from app.api.deps import ClienteUser, CurrentUser, DbSession
from app.schemas.rating import RatingCreate, RatingRead
from app.services.rating_service import RatingService

router = APIRouter(prefix="/ratings", tags=["ratings"])


@router.post("", response_model=RatingRead, status_code=201)
async def create_rating(data: RatingCreate, session: DbSession, _user: ClienteUser):
    svc = RatingService(session)
    return await svc.create(data)


@router.get("/{rating_id}", response_model=RatingRead)
async def read_rating(rating_id: int, session: DbSession, _current_user: CurrentUser):
    svc = RatingService(session)
    return await svc.get_by_id(rating_id)
