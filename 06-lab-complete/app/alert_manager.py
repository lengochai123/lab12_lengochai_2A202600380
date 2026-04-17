"""Alert Manager — Telegram notifications for fire alerts"""
import logging
import requests
import base64
import io
from typing import Optional
import cv2
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertManager:
    """Manage sending alerts via Telegram"""
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat ID to send alerts to
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_base = f"https://api.telegram.org/bot{bot_token}"
        self.last_alert_time = {}  # Prevent alert spam
        
    def send_text_alert(self, message: str, severity: AlertSeverity = AlertSeverity.HIGH) -> bool:
        """
        Send text alert via Telegram
        
        Args:
            message: Alert message
            severity: Alert severity level
            
        Returns:
            True if sent successfully
        """
        try:
            emoji_map = {
                AlertSeverity.LOW: "🟡",
                AlertSeverity.MEDIUM: "🟠",
                AlertSeverity.HIGH: "🔴",
                AlertSeverity.CRITICAL: "🚨",
            }
            
            full_message = f"{emoji_map.get(severity, '⚠️')} [{severity.value}] {message}"
            
            url = f"{self.api_base}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": full_message,
                "parse_mode": "HTML",
            }
            
            response = requests.post(url, json=payload, timeout=5)
            
            if response.status_code == 200:
                logger.info(f"✅ Telegram alert sent: {severity.value}")
                return True
            else:
                logger.error(f"❌ Failed to send alert: {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"Error sending text alert: {e}")
            return False

    def send_photo_alert(
        self,
        message: str,
        image_data: bytes,
        severity: AlertSeverity = AlertSeverity.CRITICAL
    ) -> bool:
        """
        Send photo alert via Telegram
        
        Args:
            message: Alert message caption
            image_data: Image bytes (JPEG/PNG)
            severity: Alert severity level
            
        Returns:
            True if sent successfully
        """
        try:
            emoji_map = {
                AlertSeverity.LOW: "🟡",
                AlertSeverity.MEDIUM: "🟠",
                AlertSeverity.HIGH: "🔴",
                AlertSeverity.CRITICAL: "🚨",
            }
            
            caption = f"{emoji_map.get(severity, '⚠️')} [{severity.value}]\n{message}"
            
            url = f"{self.api_base}/sendPhoto"
            files = {'photo': ('alert.jpg', image_data)}
            payload = {
                "chat_id": self.chat_id,
                "caption": caption,
                "parse_mode": "HTML",
            }
            
            response = requests.post(url, data=payload, files=files, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✅ Photo alert sent: {severity.value}")
                return True
            else:
                logger.error(f"❌ Failed to send photo: {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"Error sending photo alert: {e}")
            return False

    def frame_to_jpeg_bytes(self, frame: np.ndarray) -> bytes:
        """Convert OpenCV frame to JPEG bytes"""
        try:
            _, buffer = cv2.imencode('.jpg', frame)
            return buffer.tobytes()
        except Exception as e:
            logger.error(f"Error converting frame: {e}")
            return b""

    def send_fire_alert(
        self,
        detections: dict,
        annotated_frame: Optional[np.ndarray] = None,
        llm_analysis: Optional[str] = None
    ) -> bool:
        """
        Send comprehensive fire alert with detections and LLM analysis
        
        Args:
            detections: Detection info from FireDetector
            annotated_frame: Frame with bounding boxes
            llm_analysis: LLM analysis text
            
        Returns:
            True if sent successfully
        """
        try:
            # Build message
            total_detections = detections.get("total_detections", 0)
            message_lines = [
                f"🔥 <b>FIRE ALERT DETECTED!</b>",
                f"Detections: {total_detections}",
            ]
            
            if llm_analysis:
                message_lines.append(f"\n<b>Analysis:</b>\n{llm_analysis}")
            
            message = "\n".join(message_lines)
            
            # Send photo if available
            if annotated_frame is not None:
                image_bytes = self.frame_to_jpeg_bytes(annotated_frame)
                return self.send_photo_alert(
                    message,
                    image_bytes,
                    severity=AlertSeverity.CRITICAL
                )
            else:
                return self.send_text_alert(message, severity=AlertSeverity.CRITICAL)
        
        except Exception as e:
            logger.error(f"Error sending fire alert: {e}")
            return False
