class ModelManager:
    def __init__(self):
        self.models = {}

    def load_model(self, model_name, model_path):
        # Logic to load the model from the specified path
        pass

    def get_model(self, model_name):
        # Logic to retrieve the loaded model
        pass

    def list_models(self):
        # Logic to return a list of loaded models
        return list(self.models.keys())

    def unload_model(self, model_name):
        # Logic to unload the specified model
        pass

    def clear_models(self):
        # Logic to clear all loaded models
        self.models.clear()