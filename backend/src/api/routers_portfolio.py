from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_db
from src.api.schemas import PortfolioItemIn, PortfolioItemOut
from src.models.extras import PortfolioItem
from src.models.user import User

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


# PUBLIC_INTERFACE
@router.get("", response_model=list[PortfolioItemOut], summary="List my portfolio")
def list_portfolio(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(PortfolioItem).filter(PortfolioItem.user_id == user.id).all()
    return [PortfolioItemOut(id=i.id, title=i.title, description=i.description, url=i.url) for i in items]


# PUBLIC_INTERFACE
@router.post("", response_model=PortfolioItemOut, summary="Create portfolio item")
def create_portfolio(payload: PortfolioItemIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = PortfolioItem(user_id=user.id, title=payload.title, description=payload.description, url=payload.url)
    db.add(item)
    db.flush()
    return PortfolioItemOut(id=item.id, title=item.title, description=item.description, url=item.url)


# PUBLIC_INTERFACE
@router.put("/{item_id}", response_model=PortfolioItemOut, summary="Update portfolio item")
def update_portfolio(
    item_id: int,
    payload: PortfolioItemIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(PortfolioItem).filter(PortfolioItem.id == item_id, PortfolioItem.user_id == user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    item.title = payload.title
    item.description = payload.description
    item.url = payload.url
    return PortfolioItemOut(id=item.id, title=item.title, description=item.description, url=item.url)


# PUBLIC_INTERFACE
@router.delete("/{item_id}", summary="Delete portfolio item")
def delete_portfolio(item_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(PortfolioItem).filter(PortfolioItem.id == item_id, PortfolioItem.user_id == user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    return {"status": "ok"}
