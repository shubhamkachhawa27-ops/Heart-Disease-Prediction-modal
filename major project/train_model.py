import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import os

def load_data(filepath):
    print(f"Loading data from {filepath}...")
    try:
        df = pd.read_csv(filepath)
        return df
    except FileNotFoundError:
        print(f"Error: Could not find {filepath}. Please ensure the dataset is saved at this path.")
        exit(1)

def preprocess_data(df):
    print("Preprocessing data...")
    # Handle missing values
    df = df.dropna()
    
    # Separate features (X) and target (y)
    X = df.drop('target', axis=1)
    y = df['target']
    
    # Scale numerical features using StandardScaler
    continuous_features = ['age', 'trestbps', 'chol', 'thalach', 'oldpeak']
    scaler = StandardScaler()
    X_scaled = X.copy()
    X_scaled[continuous_features] = scaler.fit_transform(X[continuous_features])
    
    return X_scaled, y, scaler

def evaluate_model(y_true, y_pred, model_name):
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred)
    rec = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)
    return {'Model': model_name, 'Accuracy': acc, 'Precision': prec, 'Recall': rec, 'F1-score': f1}

def train_and_evaluate(X_train, X_test, y_train, y_test):
    print("Training models...")
    models = {
        'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000),
        'Decision Tree': DecisionTreeClassifier(random_state=42),
        'Random Forest': RandomForestClassifier(random_state=42, n_estimators=100)
    }
    
    results = []
    trained_models = {}
    
    # Train each model and gather metrics
    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        metrics = evaluate_model(y_test, y_pred, name)
        results.append(metrics)
        trained_models[name] = model
        
    results_df = pd.DataFrame(results)
    print("\n--- Model Evaluation Results ---")
    print(results_df.to_string(index=False))
    print("--------------------------------\n")
    
    return results_df, trained_models

def main():
    # Ensure save directory exists
    os.makedirs('models', exist_ok=True)
    
    # 1. Load Data
    data_path = 'data/heart.csv'
    df = load_data(data_path)
    
    # 2. Preprocess
    X, y, scaler = preprocess_data(df)
    
    # 3. Train-Test Split (80% training, 20% testing)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 4 & 5. Model Training & Evaluation
    results_df, trained_models = train_and_evaluate(X_train, X_test, y_train, y_test)
    
    # 6. Select Best Model
    # Determine the best model by taking the one with highest Accuracy (and then F1-score)
    best_model_name = results_df.sort_values(by=['Accuracy', 'F1-score'], ascending=False).iloc[0]['Model']
    print(f"Selected Best Model based on performance: {best_model_name}")
    
    best_model = trained_models[best_model_name]
    
    # 7. Save Model and Scaler
    print("\nSaving the best model and matching scaler...")
    # We save as 'rf_model.pkl' to maintain direct frontend API compatibility without needing UI changes
    joblib.dump(best_model, 'models/rf_model.pkl') 
    joblib.dump(scaler, 'models/scaler.pkl')
    print("Training pipeline completed! Output artifacts secured in the 'models' directory.")

if __name__ == "__main__":
    main()
