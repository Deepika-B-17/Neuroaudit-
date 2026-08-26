"""
Leakage-Free Preprocessing and Pipeline Construction for NeuroAudit ML.

Ensures imputation and standard scaling are strictly encapsulated in sklearn Pipelines
and fitted only on training partitions within cross-validation folds.
"""

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier


def create_classifier(classifier_type: str = "logistic_regression", random_state: int = 42):
    """
    Instantiate standard baseline classifiers with reproducible configurations.

    Parameters
    ----------
    classifier_type : str
        One of 'dummy', 'logistic_regression', 'random_forest'.
    random_state : int
        Deterministic random seed.

    Returns
    -------
    Classifier instance.
    """
    ctype = classifier_type.lower().strip()
    if ctype in ("dummy", "chance"):
        return DummyClassifier(strategy="stratified", random_state=random_state)
    elif ctype in ("logistic_regression", "lr"):
        return LogisticRegression(
            C=1.0,
            solver="lbfgs",
            max_iter=1000,
            random_state=random_state,
        )
    elif ctype in ("random_forest", "rf"):
        return RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=random_state,
            n_jobs=-1,
        )
    else:
        raise ValueError(
            f"Unsupported classifier_type '{classifier_type}'. "
            f"Supported options: 'dummy', 'logistic_regression', 'random_forest'."
        )


def create_ml_pipeline(classifier_type: str = "logistic_regression", random_state: int = 42) -> Pipeline:
    """
    Construct a leakage-free Scikit-Learn Pipeline combining median imputation,
    standard scaling, and the specified classifier.

    Parameters
    ----------
    classifier_type : str
        Classifier algorithm to encapsulate.
    random_state : int
        Deterministic random seed.

    Returns
    -------
    Pipeline
        Unfitted pipeline. When .fit(X_train, y_train) is called, Imputer and
        StandardScaler learn statistics solely from X_train.
    """
    clf = create_classifier(classifier_type, random_state=random_state)
    steps = [
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("classifier", clf),
    ]
    return Pipeline(steps)
