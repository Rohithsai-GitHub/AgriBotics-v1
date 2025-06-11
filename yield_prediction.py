import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os

class CropYieldPredictor:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.crop_types = None
        self.countries = None
    
    def load_and_merge_data(self, dataset_path):
        """Load and merge data from different CSV files"""
        # Load rainfall data
        rainfall_df = pd.read_csv(os.path.join(dataset_path, 'rainfall.csv'))
        
        # Load pesticides data
        pesticides_df = pd.read_csv(os.path.join(dataset_path, 'pesticides.csv'))
        pesticides_df = pesticides_df[pesticides_df['Element'] == 'Pesticides Use']
        pesticides_df = pesticides_df.rename(columns={'Value': 'pesticides_tonnes'})
        
        # Load yield data (assuming you have a yield.csv)
        yield_df = pd.read_csv(os.path.join(dataset_path, 'yield.csv'))
        
        # Merge datasets
        df = pd.merge(rainfall_df, pesticides_df[['Area', 'Year', 'pesticides_tonnes']], 
                     on=['Area', 'Year'], how='left')
        df = pd.merge(df, yield_df, on=['Area', 'Year'], how='left')
        
        # Fill missing values
        df['pesticides_tonnes'] = df['pesticides_tonnes'].fillna(df.groupby('Area')['pesticides_tonnes'].transform('mean'))
        
        # Add temperature data (you might want to add actual temperature data if available)
        df['avg_temp'] = 25  # Default temperature, replace with actual data if available
        
        return df

    def prepare_data(self, df):
        """Prepare data for training"""
        # Drop rows with missing values
        df = df.dropna()
        
        # Create label encoders for categorical variables
        for col in ['Area', 'Item']:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
            df[col] = self.label_encoders[col].fit_transform(df[col])
        
        # Store unique values
        self.crop_types = self.label_encoders['Item'].classes_ if 'Item' in self.label_encoders else None
        self.countries = self.label_encoders['Area'].classes_
        
        # Select features
        features = ['Area', 'average_rain_fall_mm_per_year', 'pesticides_tonnes', 'avg_temp']
        if 'Item' in df.columns:
            features.append('Item')
            
        X = df[features]
        y = df['hg/ha_yield']
        
        # Scale numerical features
        numerical_features = ['average_rain_fall_mm_per_year', 'pesticides_tonnes', 'avg_temp']
        X[numerical_features] = self.scaler.fit_transform(X[numerical_features])
        
        return X, y

    def train(self, dataset_path='crop_yield_prediction_dataset'):
        """Train the model"""
        try:
            # Load and merge data
            df = self.load_and_merge_data(dataset_path)
            
            # Prepare data
            X, y = self.prepare_data(df)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Initialize and train model
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=20,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
            
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            train_score = self.model.score(X_train, y_train)
            test_score = self.model.score(X_test, y_test)
            
            print(f"Training R2 Score: {train_score:.4f}")
            print(f"Testing R2 Score: {test_score:.4f}")
            
            # Calculate and print RMSE
            y_pred = self.model.predict(X_test)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            print(f"Root Mean Square Error: {rmse:.2f}")
            
            return train_score, test_score
            
        except Exception as e:
            print(f"Error during training: {str(e)}")
            raise

    def predict(self, country, rainfall, pesticides, temperature):
        """Make predictions"""
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
            
        try:
            # Encode country
            country_encoded = self.label_encoders['Area'].transform([country])[0]
            
            # Scale numerical inputs
            numerical_features = np.array([[rainfall, pesticides, temperature]])
            numerical_scaled = self.scaler.transform(numerical_features)
            
            # Create input features
            X = np.array([[
                country_encoded,
                numerical_scaled[0,0],
                numerical_scaled[0,1],
                numerical_scaled[0,2]
            ]])
            
            # Make prediction
            prediction = self.model.predict(X)[0]
            return prediction
            
        except Exception as e:
            print(f"Error during prediction: {str(e)}")
            raise

    def save_model(self, path='crop_yield_model.joblib'):
        """Save the trained model and preprocessing objects"""
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
            
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'crop_types': self.crop_types,
            'countries': self.countries
        }
        joblib.dump(model_data, path)
        
    def load_model(self, path='crop_yield_model.joblib'):
        """Load a trained model and preprocessing objects"""
        model_data = joblib.load(path)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.label_encoders = model_data['label_encoders']
        self.crop_types = model_data['crop_types']
        self.countries = model_data['countries']

# Function to use in Flask app
def predict_crop(nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall):
    model = CropYieldPredictor()
    try:
        model.load_model()
    except:
        # Train model if not already trained
        model.train('crop_yield_prediction_dataset')
        model.save_model()
    
    # Calculate pesticide use from NPK values
    pesticides = (nitrogen + phosphorus + potassium) / 3
    
    # Make prediction
    prediction = model.predict("India", rainfall, pesticides, temperature)
    return float(prediction)

# Test the model if run directly
if __name__ == "__main__":
    predictor = CropYieldPredictor()
    predictor.train('crop_yield_prediction_dataset')
    predictor.save_model()
    
    # Test prediction
    test_prediction = predict_crop(
        nitrogen=100,
        phosphorus=50,
        potassium=75,
        temperature=28,
        humidity=80,
        ph=6.5,
        rainfall=1500
    )
    print(f"Test Prediction: {test_prediction:.2f} hg/ha")
