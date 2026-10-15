import pickle

from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

# carregando dataset

iris = load_iris()
X = iris.data
y = iris.target

print(f"""
Informações do Dataset: 
{("-") * 93}
Features: {iris.feature_names}
Classes: {list(iris.target_names)}
Total amostras: {len(X)}
Shape dos dados: {X.shape}
""")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=41
)


print(f"""
Divisão dos dados: 
{("-") * 45}
Treino: {len(X_train)} amostras
Teste: {len(X_test)} amostras
""")

# treinando modelo

modelo = RandomForestClassifier(n_estimators=100, random_state=41)
modelo.fit(X_train, y_train)

# avaliando

y_pred = modelo.predict(X_test)
acuracia = accuracy_score(y_test, y_pred)

print(f"""Modelo treinado com sucesso
Acurácia no teste: {acuracia: .2%}""")


# salvando com pkl

with open("modelo_iris.pkl", "wb") as f:
    pickle.dump(modelo, f)

# salvando nome das classes para usar na API

with open("classes_iris.pkl", "wb") as f:
    pickle.dump(list(iris.target_names), f)

print("salvo com sucesso")
