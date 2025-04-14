import mlrun
from sklearn import ensemble
from sklearn.model_selection import train_test_split
from mlrun.frameworks.sklearn import apply_mlrun

def train(
    dataset: mlrun.DataItem,
    label_column: str = 'target',
    n_estimators: int = 100,
    learning_rate: float = 0.1,
    max_depth: int = 3,
    model_name: str = "breast_cancer_classifier"
):
    
    df = dataset.as_df()
    X = df.drop(label_column, axis =1)
    y = df[label_column]
    
    #train test split
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Pick Model
    model = ensemble.GradientBoostingClassifier(
        n_estimators=n_estimators, learning_rate=learning_rate, max_depth=max_depth)
    
    apply_mlrun(model=model, model_name=model_name, x_test=X_test, y_test=y_test)
    
    model.fit(X_train, y_train)