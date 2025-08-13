import qrcode
from io import BytesIO
import base64
import json
from qrcode.constants import ERROR_CORRECT_L
from typing import Dict


class QRGenerator:

    @staticmethod
    def generate_rsvp_qr(user_id: int, event_id: int) -> str:
        """Generate QR code for RSVP check-in"""
        if user_id <= 0 or event_id <= 0:
            raise ValueError("user_id and event_id must be positive integers")

        qr_data = {"user_id": user_id, "event_id": event_id, "type": "rsvp_checkin"}

        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )

            qr.add_data(json.dumps(qr_data, separators=(",", ":")))
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Convert to base64 string
            buffered = BytesIO()
            img.save(buffered, "PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

            return f"data:image/png;base64,{img_str}"
        except Exception as e:
            raise RuntimeError(f"Failed to generate QR code: {str(e)}") from e

    @staticmethod
    def decode_qr_data(qr_data: str) -> Dict:
        """Decode QR code data"""
        if not qr_data or not isinstance(qr_data, str):
            return {}

        try:
            decoded_data = json.loads(qr_data)
            # Validate the expected structure
            if isinstance(decoded_data, dict) and "type" in decoded_data:
                return decoded_data
            return {}
        except (json.JSONDecodeError, TypeError):
            return {}

    @staticmethod
    def validate_rsvp_qr_data(qr_data: Dict) -> bool:
        """Validate that QR code data has the expected RSVP structure"""
        required_fields = ["user_id", "event_id", "type"]

        return (
            isinstance(qr_data, dict)
            and all(field in qr_data for field in required_fields)
            and qr_data.get("type") == "rsvp_checkin"
            and isinstance(qr_data.get("user_id"), int)
            and isinstance(qr_data.get("event_id"), int)
            and qr_data["user_id"] > 0
            and qr_data["event_id"] > 0
        )
