import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib

# Dummy training data
df = pd.DataFrame({
    'hours': [1, 2, 3, 4, 5, 6],
    'difficulty': [1, 2, 3, 4, 5, 6],
    'priority':[2, 3, 4, 6, 7, 9]
})

X = df[['hours', 'difficulty']]
y = df['priority']

model = LinearRegression()
model.fit(X, y)

# Save model
joblib.dump(model, 'model.pkl')
print("Model trained and saved as model.pkl")





