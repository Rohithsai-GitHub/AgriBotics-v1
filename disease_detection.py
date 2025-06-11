import tensorflow as tf
import numpy as np
from PIL import Image
import os
import logging
from inference_sdk import InferenceHTTPClient

class DiseaseDetector:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("Roboflow API key is required")
        
        self.client = InferenceHTTPClient(
            api_url="https://classify.roboflow.com",
            api_key=api_key
        )
        self.model_id = "level-of-disease-in-leaf/1"

    def preprocess_image(self, image_path):
        # Load and preprocess the image
        img = Image.open(image_path).convert('RGB')
        img = img.resize(self.image_size)
        img = np.array(img)
        img = tf.keras.applications.resnet50.preprocess_input(img)
        img = np.expand_dims(img, axis=0)
        return img
        
    def detect_disease(self, image_path):
        try:
            # Validate image file
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
                
            # Make prediction using Roboflow API
            result = self.client.infer(image_path, model_id=self.model_id)
            
            if not result or 'predictions' not in result:
                raise ValueError("Invalid response from Roboflow API")
                
            predictions = result.get('predictions', {})
            
            # Get the disease with highest confidence
            disease_name = next(iter(predictions))
            confidence = predictions[disease_name]['confidence']
            
            disease_data = {
                'disease': disease_name,
                'confidence': round(confidence * 100, 2),
                'treatment': self._get_treatment_recommendation(disease_name)
            }
            
            logging.debug(f"Detected disease: {disease_name} with {disease_data['confidence']}% confidence")
            return disease_data
            
        except Exception as e:
            logging.error(f"Disease detection error: {str(e)}")
            raise Exception(f"Error in disease detection: {str(e)}")

    def _get_treatment_recommendation(self, disease_name):
        recommendations = {
            'Septoria': "Remove infected leaves. Apply fungicide. Improve air circulation.",
            'Healthy': "Plant appears healthy. Continue regular maintenance.",
            'Leaf_Spot': "Remove infected leaves. Apply copper-based fungicide.",
            'Blight': "Remove infected parts. Apply appropriate fungicide. Improve drainage.",
            'Default': "Consult a plant specialist for proper treatment."
        }
        return recommendations.get(disease_name, recommendations['Default'])