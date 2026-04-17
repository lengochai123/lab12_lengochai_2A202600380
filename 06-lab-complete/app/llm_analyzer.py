"""LLM Analyzer — Intelligent fire analysis using OpenAI or mock LLM"""
import logging
import base64
import os
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)


class LLMAnalyzer:
    """Analyze fire images using LLM"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-vision"):
        """
        Args:
            api_key: OpenAI API key (if None, uses mock)
            model: LLM model to use
        """
        self.api_key = api_key
        self.model = model
        self.use_mock = not api_key
        
        if not self.use_mock:
            try:
                import openai
                self.client = openai.OpenAI(api_key=api_key)
                logger.info(f"✅ Using OpenAI {model}")
            except ImportError:
                logger.warning("⚠️ openai package not installed, falling back to mock")
                self.use_mock = True
        else:
            logger.info("⚠️ Using mock LLM (no OPENAI_API_KEY)")

    def analyze_frame(
        self,
        frame: np.ndarray,
        detection_info: dict,
        max_tokens: int = 200
    ) -> str:
        """
        Analyze frame with detections using LLM
        
        Args:
            frame: Image frame
            detection_info: Detection info from FireDetector
            max_tokens: Max tokens for response
            
        Returns:
            LLM analysis text
        """
        try:
            if self.use_mock:
                return self._mock_analysis(frame, detection_info)
            else:
                return self._openai_analysis(frame, detection_info, max_tokens)
        
        except Exception as e:
            logger.error(f"Error in analyze_frame: {e}")
            return f"Error: {str(e)}"

    def _openai_analysis(
        self,
        frame: np.ndarray,
        detection_info: dict,
        max_tokens: int = 200
    ) -> str:
        """Call OpenAI GPT-4 Vision for analysis"""
        try:
            import cv2
            import base64
            
            # Encode frame
            _, buffer = cv2.imencode('.jpg', frame)
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Build prompt
            detections_text = "\n".join([
                f"- {d['class']} (confidence: {d['confidence']})"
                for d in detection_info.get("detections", [])
            ])
            
            prompt = f"""You are a fire detection AI expert. Analyze the image and detected objects.

Detected objects:
{detections_text}

Questions:
1. What is the fire risk level? (LOW/MEDIUM/HIGH/CRITICAL)
2. What immediate actions should be taken?
3. Any false positives or concerns?

Provide a brief, actionable analysis."""
            
            # Call OpenAI
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_base64,
                                },
                            },
                        ],
                    }
                ],
            )
            
            analysis = response.content[0].text
            logger.info(f"✅ OpenAI analysis completed")
            return analysis
        
        except Exception as e:
            logger.error(f"Error in OpenAI analysis: {e}")
            return f"Analysis failed: {str(e)}"

    def _mock_analysis(
        self,
        frame: np.ndarray,
        detection_info: dict
    ) -> str:
        """Mock LLM analysis for development"""
        try:
            fire_detected = detection_info.get("fire_detected", False)
            total_detections = detection_info.get("total_detections", 0)
            
            if fire_detected:
                if total_detections >= 3:
                    risk_level = "CRITICAL"
                    actions = "1. Evacuate immediately\n2. Call emergency services\n3. Activate fire suppression"
                elif total_detections >= 2:
                    risk_level = "HIGH"
                    actions = "1. Alert occupants\n2. Prepare evacuation routes\n3. Monitor situation"
                else:
                    risk_level = "MEDIUM"
                    actions = "1. Investigate source\n2. Increase monitoring\n3. Keep fire suppression ready"
            else:
                risk_level = "LOW"
                actions = "1. Continue routine monitoring\n2. No immediate action needed"
            
            analysis = f"""🔍 <b>Fire Analysis (Mock LLM)</b>
            
<b>Risk Level:</b> {risk_level}

<b>Recommended Actions:</b>
{actions}

<b>Note:</b> This is a mock analysis. Deploy with OpenAI API key for real analysis."""
            
            return analysis
        
        except Exception as e:
            logger.error(f"Error in mock analysis: {e}")
            return f"Analysis failed: {str(e)}"
