from services.analyze.process.ingredient_classifier import IngredientClassifier

class ClassificationService:
    def __init__(self):
        self.classifier = IngredientClassifier()

    def classify_ingredients(self, ingredients: list[str], restriction: str) -> list[dict]:
        return self.classifier.classify(ingredients, restriction)
    