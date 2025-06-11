import os
import logging
from inference_sdk import InferenceHTTPClient

class WeedDetector:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("Roboflow API key is required")
        
        self.client = InferenceHTTPClient(
            api_url="https://detect.roboflow.com",
            api_key=api_key
        )
        self.model_id = "weeds-nxe1w/1"

    def detect_weeds(self, image_path):
        try:
            # Validate image file
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
                
            # Make prediction using Roboflow API
            result = self.client.infer(image_path, model_id=self.model_id)
            
            if not result or 'predictions' not in result:
                raise ValueError("Invalid response from Roboflow API")
                
            predictions = result.get('predictions', [])
            
            # Process predictions
            weed_data = {
                'count': len(predictions),
                'detections': [
                    {
                        'location': {
                            'x': round(p['x'], 2),
                            'y': round(p['y'], 2),
                            'width': round(p['width'], 2),
                            'height': round(p['height'], 2)
                        },
                        'confidence': round(p['confidence'] * 100, 2),
                        'class': p.get('class', 'weed')
                    }
                    for p in predictions
                ],
                'recommendations': self._get_recommendations(len(predictions))
            }
            
            logging.debug(f"Detected {weed_data['count']} weeds in image")
            return weed_data
            
        except Exception as e:
            logging.error(f"Weed detection error: {str(e)}")
            raise Exception(f"Error in weed detection: {str(e)}")

    def _get_recommendations(self, weed_count):
        if weed_count == 0:
            return "No weeds detected. Continue regular monitoring."
        elif weed_count < 5:
            return "Low weed concentration. Consider spot treatment with herbicide."
        elif weed_count < 10:
            return "Moderate weed infestation. Apply targeted herbicide treatment."
        else:
            return "High weed concentration. Immediate widespread treatment recommended."
