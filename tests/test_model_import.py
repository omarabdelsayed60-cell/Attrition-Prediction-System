import sys

print("Testing imports...")
try:
    from sklearn.tree import DecisionTreeClassifier
    print("DecisionTreeClassifier: OK")
except Exception as e:
    print(f"DecisionTreeClassifier Error: {e}")

try:
    from sklearn.ensemble import RandomForestClassifier
    print("RandomForestClassifier: OK")
except Exception as e:
    print(f"RandomForestClassifier Error: {e}")

try:
    from sklearn.ensemble import GradientBoostingClassifier
    print("GradientBoostingClassifier: OK")
except Exception as e:
    print(f"GradientBoostingClassifier Error: {e}")

try:
    import shap
    print("SHAP: OK")
except Exception as e:
    print(f"SHAP Error: {e}")
