import strawberry

from backend.services.auth_service import AuthService
from backend.services.event_service import EventService
from backend.services.rsvp_service import RSVPService
from backend.graphql_api.types import (
    AuthType,
    EventType,
    RSVPType,
    RegisterInput,
    LoginInput,
    EventInput,
    RSVPInput,
    VerifyEmailInput,
    ForgotPasswordInput,
    ResetPasswordInput,
    ChangePasswordInput,
    ResendOTPInput,
)
from backend.permissions.auth_permissions import IsAuthenticated
from typing import Optional


@strawberry.type
class Mutation:

    @strawberry.mutation
    async def register(self, user_data: RegisterInput) -> str:
        return await AuthService.register(user_data)

    @strawberry.mutation
    async def login(self, login_data: LoginInput) -> AuthType:
        return await AuthService.login(login_data)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def create_event(self, info, event_data: EventInput) -> Optional[EventType]:
        user = info.context["current_user"]
        return await EventService.create_event(event_data, user.id)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def update_event(self, info, event_id: int, event_data: EventInput) -> str:
        user = info.context["current_user"]
        return await EventService.update_event(event_id, event_data, user.id)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def delete_event(self, info, event_id: int) -> str:
        user = info.context["current_user"]
        return await EventService.delete_event(event_id, user.id)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def create_rsvp(self, info, rsvp_data: RSVPInput) -> RSVPType:
        user = info.context["current_user"]
        return await RSVPService.create_rsvp(rsvp_data, user.id)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def cancel_rsvp(self, info, rsvp_id: int) -> str:
        user = info.context["current_user"]
        return await RSVPService.cancel_rsvp(rsvp_id, user.id)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def check_in_attendee(self, info, rsvp_id: int) -> str:
        user = info.context["current_user"]
        return await RSVPService.check_in_attendee(rsvp_id, user.id)

    @strawberry.mutation
    async def verify_email(self, verify_data: VerifyEmailInput) -> str:
        return await AuthService.verify_email(verify_data)

    @strawberry.mutation
    async def resend_email_otp(self, resend_data: ResendOTPInput) -> str:
        return await AuthService.resend_email_otp(resend_data)

    @strawberry.mutation
    async def forgot_password(self, forgot_data: ForgotPasswordInput) -> str:
        return await AuthService.forgot_password(forgot_data)

    @strawberry.mutation
    async def reset_password(self, reset_data: ResetPasswordInput) -> str:
        return await AuthService.reset_password(reset_data)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def change_password(self, info, change_data: ChangePasswordInput) -> str:
        user = info.context["current_user"]
        return await AuthService.change_password(change_data, user.id)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def delete_account(self, info) -> str:
        user = info.context["current_user"]
        return await AuthService.delete_account(user.id)

    @strawberry.mutation
    async def refresh_tokens(self, refresh_token: str) -> AuthType:
        return await AuthService.refresh_tokens(refresh_token)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def validate_qr_code(self, info, qr_data: str, event_id: int) -> str:
        from backend.services.qr_service import QRGenerator

        decoded_data = QRGenerator.decode_qr_data(qr_data)
        if not QRGenerator.validate_rsvp_qr_data(decoded_data):
            raise ValueError("Invalid QR code")

        if decoded_data.get("event_id") != event_id:
            raise ValueError("QR code is for a different event")

        user = info.context["current_user"]
        return await RSVPService.check_in_attendee(decoded_data["user_id"], user.id)
