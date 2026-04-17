"""Fire Detection Module — YOLO for fire detection"""
import logging
import base64
import io
import numpy as np
from typing import Optional, Tuple
from ultralytics import YOLO
import cv2
from PIL import Image

logger = logging.getLogger(__name__)


class FireDetector:
    """YOLO-based fire detection"""
    
    def __init__(self, model_path: str = "yolov8m.pt", conf_threshold: float = 0.5):
        """
        Args:
            model_path: Path to YOLO model file
            conf_threshold: Confidence threshold for detections
        """
        try:
            self.model = YOLO(model_path)
            self.conf_threshold = conf_threshold
            logger.info(f"✅ YOLO model loaded: {model_path}")
        except Exception as e:
            logger.error(f"❌ Failed to load YOLO model: {e}")
            raise

    def detect_from_image_data(self, image_data: bytes) -> Tuple[bool, dict, Optional[np.ndarray]]:
        """
        Detect fire from image bytes
        
        Args:
            image_data: Image bytes (JPEG/PNG)
            
        Returns:
            (fire_detected, detections_info, annotated_frame)
        """
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                logger.error("Failed to decode image")
                return False, {"error": "Invalid image"}, None
            
            return self.detect_from_frame(frame)
        
        except Exception as e:
            logger.error(f"Error in detect_from_image_data: {e}")
            return False, {"error": str(e)}, None

    def detect_from_base64(self, base64_str: str) -> Tuple[bool, dict, Optional[np.ndarray]]:
        """
        Detect fire from base64 encoded image
        
        Args:
            base64_str: Base64 encoded image string
            
        Returns:
            (fire_detected, detections_info, annotated_frame)
        """
        try:
            image_data = base64.b64decode(base64_str)
            return self.detect_from_image_data(image_data)
        except Exception as e:
            logger.error(f"Error in detect_from_base64: {e}")
            return False, {"error": str(e)}, None

    def detect_from_frame(self, frame: np.ndarray) -> Tuple[bool, dict, np.ndarray]:
        """
        Detect fire from OpenCV frame
        
        Args:
            frame: OpenCV image (numpy array)
            
        Returns:
            (fire_detected, detections_info, annotated_frame)
        """
        try:
            # Run YOLO inference
            results = self.model(frame, conf=self.conf_threshold)
            result = results[0]
            
            # Parse detections
            detections = []
            fire_detected = False
            
            for box in result.boxes:
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                label = result.names.get(cls_id, f"class_{cls_id}")
                xyxy = [float(x) for x in box.xyxy[0]]
                
                detection = {
                    "class": label,
                    "confidence": round(conf, 4),
                    "bbox": xyxy,  # [x1, y1, x2, y2]
                }
                detections.append(detection)
                
                if "fire" in label.lower():
                    fire_detected = True
                    logger.warning(f"🔥 Fire detected with confidence: {conf:.4f}")
            
            # Annotate frame
            annotated_frame = result.plot()  # YOLO annotates automatically
            
            info = {
                "fire_detected": fire_detected,
                "total_detections": len(detections),
                "detections": detections,
                "frame_shape": frame.shape,
            }
            
            return fire_detected, info, annotated_frame
        
        except Exception as e:
            logger.error(f"Error in detect_from_frame: {e}")
            return False, {"error": str(e)}, None

    def encode_frame_to_base64(self, frame: np.ndarray) -> str:
        """Convert frame to base64 for JSON transmission"""
        try:
            _, buffer = cv2.imencode('.jpg', frame)
            return base64.b64encode(buffer).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding frame: {e}")
            return ""
