import os

os.environ["SESSION_SECRET_KEY"] = "test_secret_key"
os.environ["POSTGRES_USER"] = "test"
os.environ["POSTGRES_DATABASE"] = "test"
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_PASSWORD"] = "test"
os.environ["POSTGRES_PORT"] = "5432"
os.environ["SMTP_SERVER"] = "smtp.test.com"
os.environ["SMTP_PORT"] = "587"
os.environ["SMTP_USERNAME"] = "test@test.com"
os.environ["SMTP_PASSWORD"] = "password"
os.environ["SMTP_FROM_EMAIL"] = "noreply@test.com"
os.environ["SMTP_FROM_NAME"] = "Test App"
os.environ["FRONTEND_URL"] = "http://localhost:3000"

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone, timedelta
from jose import jwt
import json

from backend.services.auth_service import AuthService
from backend.services.email_service import EmailService
from backend.services.event_service import EventService
from backend.services.qr_service import QRGenerator
from backend.services.rsvp_service import RSVPService

from backend.graphql_api.types import RegisterInput, LoginInput, EventInput, RSVPInput
from backend.schemas.rsvp_schema import RSVPStatus
from backend.schemas.event_schema import EventCategory


class TestAuthService:
    def test_verify_password(self):
        plain_password = "testpass123"
        hashed_password = AuthService.get_password_hash(plain_password)
        assert AuthService.verify_password(plain_password, hashed_password)
        assert not AuthService.verify_password("wrongpass", hashed_password)

    def test_get_password_hash(self):
        password = "testpass123"
        hashed = AuthService.get_password_hash(password)
        assert hashed != password
        assert hashed.startswith("$2b$")

    def test_create_access_token(self):
        email = "test@example.com"
        token = AuthService.create_access_token(email)
        payload = jwt.decode(token, key="", options={"verify_signature": False})
        assert payload["sub"] == email
        assert payload["type"] == "access"

    def test_create_refresh_token(self):
        email = "test@example.com"
        token, expires_at = AuthService.create_refresh_token(email)
        assert isinstance(token, str)
        assert expires_at > datetime.now(timezone.utc)
        payload = jwt.decode(token, key="", options={"verify_signature": False})
        assert payload["type"] == "refresh"

    @patch("backend.services.auth_service.settings")
    def test_decode_token(self, mock_settings):
        mock_settings.SESSION_SECRET_KEY = "test_secret_key"
        mock_settings.ALGORITHM = "HS256"
        payload = {
            "sub": "test@example.com",
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        }
        token = jwt.encode(payload, "test_secret_key", algorithm="HS256")
        decoded = AuthService.decode_token(token)
        assert decoded["sub"] == "test@example.com"

    def test_validate_token_payload(self):
        valid_payload = {"sub": "test@example.com", "type": "access"}
        assert (
            AuthService._validate_token_payload(valid_payload, "access")
            == "test@example.com"
        )
        with pytest.raises(ValueError):
            AuthService._validate_token_payload(
                {"sub": "x", "type": "refresh"}, "access"
            )
        with pytest.raises(ValueError):
            AuthService._validate_token_payload(
                {"sub": None, "type": "access"}, "access"
            )

    @pytest.mark.asyncio
    @patch("backend.services.auth_service.UserRepository")
    @patch(
        "backend.services.auth_service.AuthService._send_email_verification_otp",
        new_callable=AsyncMock,
    )
    async def test_register_success(self, mock_send_otp, mock_user_repo):
        # Use a non-disposable email to pass Pydantic validation
        mock_user_repo.get_by_email = AsyncMock(return_value=None)
        mock_user_repo.create = AsyncMock(return_value=Mock(id=1))
        register_data = RegisterInput(
            name="Test User", email="test@valid.com", password="testpass123"
        )
        result = await AuthService.register(register_data)
        assert "Registration successful" in result

    @pytest.mark.asyncio
    @patch("backend.services.auth_service.UserRepository")
    async def test_register_existing_email(self, mock_user_repo):
        mock_user_repo.get_by_email = AsyncMock(return_value=Mock(id=1))
        with pytest.raises(ValueError):
            await AuthService.register(
                RegisterInput(name="Test", email="test@example.com", password="pass")
            )

    @pytest.mark.asyncio
    @patch("backend.services.auth_service.UserRepository")
    @patch("backend.services.auth_service.RefreshTokenRepository")
    async def test_login_success(self, mock_refresh_repo, mock_user_repo):
        hashed_password = AuthService.get_password_hash("testpass123")
        mock_user = Mock(
            id=1,
            email="test@valid.com",
            password=hashed_password,
            is_deleted=False,
            is_active=True,
        )
        mock_user_repo.get_by_email = AsyncMock(return_value=mock_user)
        mock_user_repo.update = AsyncMock()
        mock_refresh_repo.invalidate_all_for_user = AsyncMock()
        mock_refresh_repo.create = AsyncMock()
        result = await AuthService.login(
            LoginInput(email="test@valid.com", password="testpass123")
        )
        assert result.user.email == "test@valid.com"

    @pytest.mark.asyncio
    @patch("backend.services.auth_service.UserRepository")
    async def test_login_invalid_credentials(self, mock_user_repo):
        mock_user_repo.get_by_email = AsyncMock(return_value=None)
        with pytest.raises(ValueError):
            await AuthService.login(LoginInput(email="x", password="y"))


class TestEmailService:
    @patch("backend.services.email_service.EmailService._load_template")
    @patch(
        "backend.services.email_service.EmailService.send_email", new_callable=AsyncMock
    )
    @patch("backend.services.email_service.UserRepository")
    @pytest.mark.asyncio
    async def test_send_email_otp(
        self, mock_user_repo, mock_send_email, mock_load_template
    ):
        mock_user_repo.get_by_id = AsyncMock(
            return_value=Mock(name="Test", email="test@example.com")
        )
        mock_template = Mock()
        mock_template.render.return_value = "<html>OTP</html>"
        mock_load_template.return_value = mock_template
        mock_send_email.return_value = True
        result = await EmailService.send_email_otp(1, "123456")
        assert result is True

    @patch("backend.services.email_service.smtplib.SMTP_SSL")
    @pytest.mark.asyncio
    async def test_send_email_success(self, mock_smtp):
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        result = await EmailService.send_email("to@example.com", "Subject", "Body")
        assert result is True
        mock_server.login.assert_called_once()


class TestEventService:
    @pytest.mark.asyncio
    @patch("backend.services.event_service.EventRepository")
    @patch("backend.services.event_service.TicketRepository")
    async def test_create_event_free(self, mock_ticket_repo, mock_event_repo):
        mock_event_repo.create = AsyncMock(return_value=Mock(id=1))
        mock_ticket_repo.create = AsyncMock()
        with patch.object(
            EventService,
            "get_event_by_id",
            new_callable=AsyncMock,
            return_value="event_obj",
        ):
            event_data = EventInput(
                title="Test",
                description="Desc",
                category=EventCategory.SPORTS,
                location="Loc",
                venue_address="Addr",
                start_date=datetime.now(timezone.utc),
                end_date=datetime.now(timezone.utc),
                timezone="UTC",
                max_attendees=100,
                is_free=True,
            )
            result = await EventService.create_event(event_data, 1)
            assert result == "event_obj"


class TestQRGenerator:
    def test_generate_rsvp_qr_success(self):
        qr_code = QRGenerator.generate_rsvp_qr(1, 1)
        assert qr_code.startswith("data:image/png;base64,")

    def test_generate_rsvp_qr_invalid_input(self):
        with pytest.raises(ValueError):
            QRGenerator.generate_rsvp_qr(0, 1)

    def test_decode_qr_data_success(self):
        data = {"user_id": 1, "event_id": 2, "type": "rsvp_checkin"}
        json_data = json.dumps(data)
        assert QRGenerator.decode_qr_data(json_data) == data

    def test_validate_rsvp_qr_data_success(self):
        valid_data = {"user_id": 1, "event_id": 2, "type": "rsvp_checkin"}
        assert QRGenerator.validate_rsvp_qr_data(valid_data)


class TestRSVPService:
    @pytest.mark.asyncio
    @patch("backend.services.rsvp_service.EventRepository")
    @patch("backend.services.rsvp_service.TicketRepository")
    @patch("backend.services.rsvp_service.RSVPRepository")
    @patch("backend.services.rsvp_service.QRGenerator")
    @patch("backend.services.rsvp_service.EmailService")
    async def test_create_rsvp_success(
        self, mock_email, mock_qr, mock_rsvp_repo, mock_ticket_repo, mock_event_repo
    ):
        mock_event_repo.get_by_id = AsyncMock(return_value=Mock(id=1))
        mock_ticket_repo.get_by_id = AsyncMock(
            return_value=Mock(event_id=1, quantity_sold=0, quantity_total=10)
        )
        mock_rsvp_repo.get_by_user_and_event = AsyncMock(return_value=None)
        mock_qr.generate_rsvp_qr.return_value = "qr_code_data"
        mock_rsvp_repo.create = AsyncMock(
            return_value=Mock(
                id=1,
                event_id=1,
                user_id=1,
                ticket_id=1,
                status=RSVPStatus.CONFIRMED,
                qr_code="qr_code_data",
            )
        )
        mock_ticket_repo.increment_sold_count = AsyncMock()
        mock_email.send_rsvp_confirmation = AsyncMock()
        result = await RSVPService.create_rsvp(RSVPInput(event_id=1, ticket_id=1), 1)
        assert result.qr_code == "qr_code_data"
