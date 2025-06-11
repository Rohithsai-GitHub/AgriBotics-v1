import numpy as np
from sklearn.ensemble import RandomForestClassifier

# Pre-trained model (simplified for demonstration)
model = RandomForestClassifier()

# Dummy data for demonstration
X_train = np.random.rand(100, 7)
y_train = np.random.choice(['rice', 'wheat', 'corn', 'cotton'], 100)
model.fit(X_train, y_train)

def predict_crop(nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall):
    """
    Predict crop based on soil and environmental parameters
    """
    try:
        features = np.array([[
            float(nitrogen),
            float(phosphorus),
            float(potassium),
            float(temperature),
            float(humidity),
            float(ph),
            float(rainfall)
        ]])
        
        prediction = model.predict(features)[0]
        return prediction
    except Exception as e:
        raise Exception(f"Prediction error: {str(e)}")
