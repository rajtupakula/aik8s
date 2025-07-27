class Sidebar:
    def __init__(self):
        self.system_status = {
            "Kubernetes API": "✅",
            "LLM": "🔧 Offline Mode",
            "Components": {
                "Remediation": "✅",
                "Forecasting": "✅",
                "GlusterFS": "✅"
            }
        }

    def display_status(self):
        # Code to render the system status in the sidebar
        pass

    def quick_actions(self):
        actions = [
            "🔍 Scan for Issues",
            "📊 Generate Report",
            "🏥 Health Check"
        ]
        # Code to render quick actions in the sidebar
        pass

    def render(self):
        self.display_status()
        self.quick_actions()