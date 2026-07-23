# Machine Learning Model Documentation

This package documents the three saved trained models and the artifacts required to use them. No retraining is required.

---

## Dropout Model

**Dataset Used:** uci_refined.csv

**Dataset Path:** `C:\Users\LENOVO\OneDrive - JK LAKSHMIPAT UNIVERSITY\Desktop\ml model ss26 hackthone\student-risk-ai\data\raw\uci_refined.csv`

**Number of Samples:** 4405

**Number of Original Features:** 12

**Number of Transformed Features:** 12

**Target Variable:** target (encoded as 0=Graduate, 1=Enrolled, 2=Dropout)

**Algorithm Used:** XGBoost XGBClassifier (multi:softprob)

### Best Hyperparameters

```json
{
  "subsample": 0.7,
  "n_estimators": 300,
  "min_child_weight": 1,
  "max_depth": 3,
  "learning_rate": 0.05,
  "gamma": 1,
  "colsample_bytree": 0.6
}
```

### Evaluation Metrics

- Accuracy: 0.753688989784336
- Precision: 0.6932836807584213
- Recall: 0.6660490529345248
- F1 Score: 0.6740813899821068
- ROC AUC: 0.8634936512960468
- Cross Validation Score: 0.6609642843217797

### Top 10 Most Important Features

- numeric__approved_sem2
- numeric__semester_success_ratio
- numeric__tuition_up_to_date
- numeric__grade_sem2
- numeric__approved_sem1
- numeric__scholarship_holder
- numeric__age
- numeric__average_semester_grade
- numeric__gender
- numeric__academic_performance_index

**SHAP Summary:** `C:\Users\LENOVO\OneDrive - JK LAKSHMIPAT UNIVERSITY\Desktop\ml model ss26 hackthone\student-risk-ai\shap\dropout_summary.png`

**Saved Model Location:** `C:\Users\LENOVO\OneDrive - JK LAKSHMIPAT UNIVERSITY\Desktop\ml model ss26 hackthone\student-risk-ai\models\dropout_model.pkl`

**Saved Preprocessor Location:** `C:\Users\LENOVO\OneDrive - JK LAKSHMIPAT UNIVERSITY\Desktop\ml model ss26 hackthone\student-risk-ai\models\dropout_preprocessor.pkl`

### Expected Input Features

- tuition_up_to_date
- scholarship_holder
- age
- gender
- approved_sem1
- grade_sem1
- approved_sem2
- grade_sem2
- semester_improvement
- academic_performance_index
- semester_success_ratio
- average_semester_grade

**Prediction Output Format:** Class label prediction and multi-class probability vector for [0, 1, 2]

---

## Wellbeing Model

**Dataset Used:** student_mental_health_burnout_1M.csv

**Dataset Path:** `C:\Users\LENOVO\OneDrive - JK LAKSHMIPAT UNIVERSITY\Desktop\ml model ss26 hackthone\student-risk-ai\data\raw\student_mental_health_burnout_1M.csv`

**Number of Samples:** 1000000

**Number of Original Features:** 15

**Number of Transformed Features:** 17

**Target Variable:** risk_level (encoded as 0=Low, 1=Medium, 2=High)

**Algorithm Used:** XGBoost XGBClassifier (multi:softprob)

### Best Hyperparameters

```json
{
  "subsample": 1.0,
  "n_estimators": 100,
  "min_child_weight": 1,
  "max_depth": 5,
  "learning_rate": 0.1,
  "gamma": 3,
  "colsample_bytree": 1.0
}
```

### Evaluation Metrics

- Accuracy: 0.99883
- Precision: 0.9982281264133542
- Recall: 0.9987273945035334
- F1 Score: 0.9984747965886672
- ROC AUC: 0.9999949634640193
- Cross Validation Score: 0.9981972088675529

### Top 10 Most Important Features

- numeric__burnout_score
- numeric__mental_health_index
- numeric__anxiety_score
- numeric__family_expectation
- categorical__gender_Male
- numeric__internet_usage
- categorical__gender_Female
- numeric__exam_pressure
- numeric__financial_risk_index
- numeric__lifestyle_score

**SHAP Summary:** `C:\Users\LENOVO\OneDrive - JK LAKSHMIPAT UNIVERSITY\Desktop\ml model ss26 hackthone\student-risk-ai\shap\wellbeing_summary.png`

**Saved Model Location:** `C:\Users\LENOVO\OneDrive - JK LAKSHMIPAT UNIVERSITY\Desktop\ml model ss26 hackthone\student-risk-ai\models\wellbeing_model.pkl`

**Saved Preprocessor Location:** `C:\Users\LENOVO\OneDrive - JK LAKSHMIPAT UNIVERSITY\Desktop\ml model ss26 hackthone\student-risk-ai\models\wellbeing_preprocessor.pkl`

### Expected Input Features

- age
- gender
- exam_pressure
- academic_performance
- stress_level
- anxiety_score
- physical_activity
- social_support
- internet_usage
- family_expectation
- burnout_score
- mental_health_index
- lifestyle_score
- stress_balance
- financial_risk_index

**Prediction Output Format:** Class label prediction and multi-class probability vector for [0, 1, 2]

---

## Depression Model

**Dataset Used:** Student Depression Dataset.csv

**Dataset Path:** `C:\Users\LENOVO\OneDrive - JK LAKSHMIPAT UNIVERSITY\Desktop\ml model ss26 hackthone\student-risk-ai\data\raw\student_depression\Student Depression Dataset.csv`

**Number of Samples:** 27901

**Number of Original Features:** 15

**Number of Transformed Features:** 48

**Target Variable:** Depression (binary 0/1)

**Algorithm Used:** XGBoost XGBClassifier (binary:logistic)

### Best Hyperparameters

```json
{
  "subsample": 0.7,
  "n_estimators": 100,
  "min_child_weight": 5,
  "max_depth": 3,
  "learning_rate": 0.1,
  "gamma": 0,
  "colsample_bytree": 1.0
}
```

### Evaluation Metrics

- Accuracy: 0.844472316789106
- Precision: 0.8415142018618884
- Recall: 0.8364329311046446
- F1 Score: 0.8386405363561993
- ROC AUC: 0.9193498669909475
- Cross Validation Score: 0.8718416772302245

### Top 10 Most Important Features

- categorical__Have you ever had suicidal thoughts ?_No
- numeric__Academic Pressure
- numeric__Financial Stress
- numeric__satisfaction_index
- categorical__Dietary Habits_Unhealthy
- numeric__Work/Study Hours
- numeric__Age
- categorical__Dietary Habits_Healthy
- numeric__Study Satisfaction
- numeric__sleep_hours

**SHAP Summary:** `C:\Users\LENOVO\OneDrive - JK LAKSHMIPAT UNIVERSITY\Desktop\ml model ss26 hackthone\student-risk-ai\shap\depression_summary.png`

**Saved Model Location:** `C:\Users\LENOVO\OneDrive - JK LAKSHMIPAT UNIVERSITY\Desktop\ml model ss26 hackthone\student-risk-ai\models\depression_model.pkl`

**Saved Preprocessor Location:** `C:\Users\LENOVO\OneDrive - JK LAKSHMIPAT UNIVERSITY\Desktop\ml model ss26 hackthone\student-risk-ai\models\depression_preprocessor.pkl`

### Expected Input Features

- Gender
- Age
- Academic Pressure
- CGPA
- Study Satisfaction
- Dietary Habits
- Degree
- Have you ever had suicidal thoughts ?
- Work/Study Hours
- Financial Stress
- Family History of Mental Illness
- sleep_hours
- family_history
- satisfaction_index
- stress_pressure_ratio

**Prediction Output Format:** Class label prediction and binary probability score for class 1

