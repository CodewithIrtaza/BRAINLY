"""
Brainly API - Escalation Service

Email and Slack notifications for human escalation.
"""
from typing import Any
from uuid import UUID
from resend import Emails

from ..config import get_settings


class EscalationService:
    """Handle human escalation notifications."""

    def __init__(self):
        self.settings = get_settings()
        self.resend = Emails(self.settings.RESEND_API_KEY) if self.settings.RESEND_API_KEY else None

    async def send_escalation_email(
        self,
        workspace_id: UUID,
        conversation_id: UUID,
        transcript: list[dict[str, Any]],
        visitor_info: dict[str, Any] | None = None,
        kb_context: list[dict[str, Any]] | None = None,
    ) -> bool:
        """Send escalation email to workspace owner(s)."""
        if not self.resend or self.settings.ENVIRONMENT == "development":
            print(f"[DEV] Would send escalation email for conversation {conversation_id}")
            return True

        # TODO: Get workspace owner emails from database
        to_emails = ["owner@example.com"]  # Placeholder

        # Build email content
        html_content = self._build_escalation_email(
            conversation_id, transcript, visitor_info, kb_context
        )

        try:
            await self.resend.send({
                "from": self.settings.RESEND_FROM_EMAIL,
                "to": to_emails,
                "subject": f"🚨 Escalation Required - Conversation {str(conversation_id)[:8]}",
                "html": html_content,
            })
            return True
        except Exception as e:
            print(f"Failed to send escalation email: {e}")
            return False

    async def send_slack_notification(
        self,
        conversation_id: UUID,
        transcript: list[dict[str, Any]],
        visitor_info: dict[str, Any] | None = None,
    ) -> bool:
        """Send Slack notification for escalation."""
        if not self.settings.SLACK_WEBHOOK_URL or self.settings.ENVIRONMENT == "development":
            print(f"[DEV] Would send Slack notification for conversation {conversation_id}")
            return True

        import httpx

        blocks = self._build_slack_blocks(conversation_id, transcript, visitor_info)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.settings.SLACK_WEBHOOK_URL,
                    json={"blocks": blocks},
                    timeout=10.0,
                )
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Failed to send Slack notification: {e}")
            return False

    def _build_escalation_email(
        self,
        conversation_id: UUID,
        transcript: list[dict[str, Any]],
        visitor_info: dict[str, Any] | None,
        kb_context: list[dict[str, Any]] | None,
    ) -> str:
        """Build HTML email content for escalation."""
        transcript_html = ""
        for msg in transcript:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            transcript_html += f"<p><strong>{role}:</strong> {content}</p>"

        visitor_html = ""
        if visitor_info:
            visitor_html = f"""
            <h3>Visitor Info</h3>
            <ul>
                <li>Session: {visitor_info.get('session_id', 'N/A')}</li>
                <li>Language: {visitor_info.get('language', 'N/A')}</li>
            </ul>
            """

        context_html = ""
        if kb_context:
            context_html = "<h3>Relevant KB Context</h3><ul>"
            for ctx in kb_context:
                context_html += f"<li>{ctx.get('preview', '')}</li>"
            context_html += "</ul>"

        return f"""
        <html>
        <body>
            <h2>🚨 Human Escalation Required</h2>
            <p><strong>Conversation ID:</strong> {conversation_id}</p>

            {visitor_html}

            <h3>Conversation Transcript</h3>
            {transcript_html}

            {context_html}

            <p>Please respond to the customer via the Brainly dashboard.</p>
        </body>
        </html>
        """

    def _build_slack_blocks(
        self,
        conversation_id: UUID,
        transcript: list[dict[str, Any]],
        visitor_info: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Build Slack message blocks."""
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🚨 Escalation Required"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Conversation:*\n{conversation_id}"},
                    {"type": "mrkdwn", "text": f"*Language:*\n{visitor_info.get('language', 'N/A') if visitor_info else 'N/A'}"},
                ],
            },
            {"type": "divider"},
        ]

        # Add last few messages
        for msg in transcript[-5:]:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:200]
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*{role}:* {content}"},
            })

        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View in Dashboard"},
                    "url": f"https://brainly.ai/conversations/{conversation_id}",
                    "style": "primary",
                }
            ],
        })

        return blocks


def get_escalation_service() -> EscalationService:
    """Get escalation service instance."""
    return EscalationService()