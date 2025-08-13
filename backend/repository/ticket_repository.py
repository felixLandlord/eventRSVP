from typing import Optional, List
from sqlalchemy.sql import select, update as sql_update, delete as sql_delete, func
from backend.schemas.ticket_schema import TicketCreate, TicketUpdate  # , TicketType
from backend.core.database import db
from backend.models.ticket_model import Ticket


class TicketRepository:

    @staticmethod
    async def create(ticket_data: TicketCreate) -> Ticket:
        async with db as session:
            ticket = Ticket(**ticket_data.model_dump())
            session.add(ticket)
            await db.commit_rollback()
            await session.refresh(ticket)
            return ticket

    @staticmethod
    async def get_by_id(ticket_id: int) -> Optional[Ticket]:
        async with db as session:
            stmt = select(Ticket).where(Ticket.id == ticket_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    @staticmethod
    async def get_by_event(event_id: int) -> List[Ticket]:
        async with db as session:
            stmt = (
                select(Ticket)
                .where(Ticket.event_id == event_id)
                .order_by(Ticket.price.asc())
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def get_all() -> List[Ticket]:
        async with db as session:
            stmt = select(Ticket)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def update(ticket_id: int, ticket_data: TicketUpdate) -> Optional[Ticket]:
        async with db as session:
            stmt = select(Ticket).where(Ticket.id == ticket_id)
            result = await session.execute(stmt)
            ticket = result.scalars().first()

            if not ticket:
                return None

            for field, value in ticket_data.model_dump(exclude_unset=True).items():
                if hasattr(ticket, field) and value is not None:
                    setattr(ticket, field, value)

            await db.commit_rollback()
            await session.refresh(ticket)
            return ticket

    @staticmethod
    async def delete(ticket_id: int) -> bool:
        async with db as session:
            stmt = sql_delete(Ticket).where(Ticket.id == ticket_id)
            result = await session.execute(stmt)
            await db.commit_rollback()
            return result.rowcount > 0

    @staticmethod
    async def increment_sold_count(ticket_id: int) -> bool:
        async with db as session:
            stmt = (
                sql_update(Ticket)
                .where(Ticket.id == ticket_id)
                .values(quantity_sold=Ticket.quantity_sold + 1)
            )
            result = await session.execute(stmt)
            await db.commit_rollback()
            return result.rowcount > 0

    @staticmethod
    async def decrement_sold_count(ticket_id: int) -> bool:
        async with db as session:
            stmt = (
                sql_update(Ticket)
                .where(Ticket.id == ticket_id)
                .values(quantity_sold=func.greatest(Ticket.quantity_sold - 1, 0))
            )
            result = await session.execute(stmt)
            await db.commit_rollback()
            return result.rowcount > 0

    @staticmethod
    async def get_available_tickets(event_id: int) -> List[Ticket]:
        """Get tickets that are still available for sale"""
        async with db as session:
            stmt = (
                select(Ticket)
                .where(
                    Ticket.event_id == event_id,
                    Ticket.quantity_sold < Ticket.quantity_total,
                )
                .order_by(Ticket.price.asc())
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def get_sold_out_tickets(event_id: int) -> List[Ticket]:
        """Get tickets that are sold out"""
        async with db as session:
            stmt = select(Ticket).where(
                Ticket.event_id == event_id,
                Ticket.quantity_sold >= Ticket.quantity_total,
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def get_ticket_sales_summary(event_id: int) -> dict:
        """Get sales summary for an event"""
        async with db as session:
            stmt = select(
                func.sum(Ticket.quantity_sold).label("total_sold"),
                func.sum(Ticket.quantity_total).label("total_available"),
                func.sum(Ticket.quantity_sold * Ticket.price).label("total_revenue"),
                func.count(Ticket.id).label("ticket_types"),
            ).where(Ticket.event_id == event_id)

            result = await session.execute(stmt)
            row = result.first()

            if not row:
                return {
                    "total_sold": 0,
                    "total_available": 0,
                    "total_revenue": 0.0,
                    "ticket_types": 0,
                    "availability_percentage": 0,
                }

            return {
                "total_sold": row.total_sold or 0,
                "total_available": row.total_available or 0,
                "total_revenue": float(row.total_revenue or 0),
                "ticket_types": row.ticket_types or 0,
                "availability_percentage": (
                    (row.total_sold / row.total_available * 100)
                    if row.total_available and row.total_available > 0
                    else 0
                ),
            }

    @staticmethod
    async def check_ticket_availability(ticket_id: int, quantity: int = 1) -> bool:
        """Check if requested quantity is available for a ticket"""
        async with db as session:
            stmt = select(Ticket).where(Ticket.id == ticket_id)
            result = await session.execute(stmt)
            ticket = result.scalars().first()

            if not ticket:
                return False

            return (ticket.quantity_total - ticket.quantity_sold) >= quantity

    @staticmethod
    async def bulk_create_tickets(
        tickets_data: List[TicketCreate],
    ) -> List[Ticket]:
        """Create multiple tickets at once"""
        async with db as session:
            tickets = [Ticket(**t.model_dump()) for t in tickets_data]
            session.add_all(tickets)
            await db.commit_rollback()

            for ticket in tickets:
                await session.refresh(ticket)

            return tickets

    @staticmethod
    async def delete_event_tickets(event_id: int) -> bool:
        """Delete all tickets for an event"""
        async with db as session:
            stmt = sql_delete(Ticket).where(Ticket.event_id == event_id)
            result = await session.execute(stmt)
            await db.commit_rollback()
            return result.rowcount > 0
