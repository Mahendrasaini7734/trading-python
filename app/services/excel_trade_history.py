from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.excel_trade_model import ExcelTrade


class ExcelTradeHistoryService:

    def list_trades(
        self,
        db: Session,
        status: Optional[str] = None,
        symbol: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:

        q = db.query(ExcelTrade)

        if status:
            q = q.filter(ExcelTrade.status == status.upper().strip())

        if symbol:
            q = q.filter(ExcelTrade.symbol.ilike(f"%{symbol.strip()}%"))

        total_count = q.count()

        # ✅ Latest always top
        q = q.order_by(ExcelTrade.created_at.desc())

        rows = q.offset(offset).limit(limit).all()

        data = []

        for index, r in enumerate(rows):
            data.append({
                "id": offset + index + 1,   # ✅ Correct Pagination ID
                "db_id": r.id,
                "symbol": r.symbol,
                "action": r.action,
                "quantity": r.quantity,
                "trigger_price": r.trigger_price,
                "sl_price": r.sl_price,
                "status": r.status,
                "order_id": r.order_id,
                "created_at": r.created_at,
            })

        return {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "data": data,
        }
