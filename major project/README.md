# Heart Disease Prediction Using Machine Learning Classification Models

A complete, beginner-friendly machine learning project that predicts whether a patient has heart disease based on medical parameters.

## 📌 Project Overview
This project demonstrates an end-to-end Machine Learning pipeline:
1. **Data Preprocessing & EDA**
2. **Model Training & Comparison** (Logistic Regression, Decision Tree, Random Forest, Neural Network)
3. **Hyperparameter Tuning** via GridSearchCV
4. **Interactive Deployment** using Streamlit

## 📂 Folder Structure
```text
project/
│
├── data/
│   └── heart.csv                   <- Place your dataset here
│
├── notebooks/
│   └── Heart_Disease_Prediction.ipynb <- Jupyter notebook for exploration
│
├── models/
│   ├── rf_model.pkl                <- Trained Random Forest model (generated after running train_model.py)
│   └── scaler.pkl                  <- Feature scaler
│
├── app.py                          <- Streamlit UI Application
├── train_model.py                  <- Script to build, evaluate, and save models
├── requirements.txt                <- Required library dependencies
└── README.md                       <- Project documentation (this file)
```

## ⚙️ Installation & Setup

**Step 1: Install Python Dependencies**
Ensure you have Python installed. Then, run the following in your terminal:
```bash
pip install -r requirements.txt
```

**Step 2: Download the Dataset**
Download the dataset using the provided Google Drive link:
[Heart Disease Dataset Link](https://drive.google.com/file/d/1k3Yhgzrgzl9CbdGXuZvK7WgbZ8kVx56I/view)

Save the downloaded CSV file as `heart.csv` strictly inside the `data/` folder.

**Step 3: Train the Models**
Run the training script to evaluate algorithms, generate EDA charts, and save the best model:
```bash
python train_model.py
```
*Outputs such as `correlation_heatmap.png`, `roc_curve.png`, and `feature_importance.png` will be saved in the `data/` folder.*

**Step 4: Run the Streamlit Application**
Launch the simple interactive UI to make real-time predictions:
```bash
streamlit run app.py
```

## 🤖 Models & Evaluation
The `train_model.py` compares the following models:
- **Logistic Regression**
- **Decision Tree Classifier** (Tuned)
- **Random Forest Classifier** (Tuned - chosen as final model)
- **Neural Network (MLPClassifier)**

Evaluation metrics computed: **Accuracy, Precision, Recall, F1-Score**.
The final selected model is persisted to `models/rf_model.pkl`.

## 💻 Tech Stack
- **Data Manipulation**: Pandas, NumPy
- **Machine Learning**: Scikit-Learn
- **Data Visualization**: Matplotlib, Seaborn
- **Web Interface**: Streamlit
