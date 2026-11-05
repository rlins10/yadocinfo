"""Seleção e coordenação do provedor de interpretação."""

from yadocinfo.ai.ollama import OllamaProvider


def get_provider(config: dict):
    """Retorna a implementação de IA definida na configuração."""
    provider = config["ai"].get("provider", "ollama")
    if provider == "ollama":
        return OllamaProvider()
    raise ValueError(f"Provedor não implementado: {provider}")
