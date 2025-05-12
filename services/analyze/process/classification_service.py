from services.analyze.process.ingredient_classifier import IngredientClassifier

class ClassificationService:
    def __init__(self, rules_path: str | None = None):
        self.classifier = IngredientClassifier(rules_path) if rules_path \
                          else IngredientClassifier()

    def classify_ingredients(self, ingredients: list[str], restriction: str | list[str]):
        return self.classifier.classify(ingredients, restriction)
