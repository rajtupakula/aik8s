# Configuration settings for AI models

MODEL_CONFIGS = {
    "llama-3.1-8b-instruct": {
        "max_tokens": 8192,
        "temperature": 0.7,
        "top_p": 0.9,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
        "description": "High performance model for general tasks."
    },
    "llama-3.1-70b-instruct": {
        "max_tokens": 32768,
        "temperature": 0.5,
        "top_p": 0.95,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
        "description": "Maximum quality model for complex analysis."
    },
    "mistral-7b-instruct-v0.3": {
        "max_tokens": 4096,
        "temperature": 0.8,
        "top_p": 0.9,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
        "description": "Ultra-fast responses for quick queries."
    },
    "codellama-34b-instruct": {
        "max_tokens": 16384,
        "temperature": 0.6,
        "top_p": 0.9,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
        "description": "Specialized for Kubernetes and code analysis."
    }
}