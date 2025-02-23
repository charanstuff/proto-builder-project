from agents.developer import developer

class ModificationHandler:
    def request_changes(self, feature_request):
        prompt = f"Modify the current prototype to include: {feature_request}"
        return developer.generate(prompt)

mod_handler = ModificationHandler()
