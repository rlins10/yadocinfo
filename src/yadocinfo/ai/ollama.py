"""Cliente HTTP para a API local de chat do Ollama."""

import json

import httpx

from yadocinfo.ai.base import AIProvider, Interpretation


class OllamaProvider(AIProvider):
    """Envia texto e, opcionalmente, imagens para um modelo servido pelo Ollama."""

    def interpret(self, text: str, images: list[str], metadata: dict, config: dict) -> Interpretation:
        """Solicita uma descrição JSON ao Ollama e valida a resposta recebida."""
        settings = config["ai"]
        prompt = (
            "Analise o conteúdo documental fornecido. Não invente informações ausentes. "
            "Responda exclusivamente com JSON válido, sem markdown, usando as chaves: "
            "document_type, subject, description, keywords (lista), entities (lista), dates (lista). "
            "A descrição deve ser objetiva, útil para localizar o documento em uma pesquisa futura. "
            "Identifique datas somente quando estiverem explícitas.\n\n"
            f"Metadados conhecidos: {json.dumps(metadata, ensure_ascii=False)}\n\n"
            f"Conteúdo extraído:\n{text[:int(settings.get('max_chars', 24000))]}"
        )
        message = {"role": "user", "content": prompt}
        if images and settings.get("input_mode") in {"vision", "auto"}:
            message["images"] = images[:int(settings.get("max_pages", 8))]
        payload = {
            "model": settings.get("model", "gemma4:12b"),
            "messages": [message],
            "stream": False,
            "format": "json",
            "options": {"temperature": float(settings.get("temperature", 0.1))},
        }
        endpoint = settings.get("endpoint", "http://localhost:11434").rstrip("/")
        with httpx.Client(timeout=float(settings.get("timeout", 300))) as client:
            response = client.post(f"{endpoint}/api/chat", json=payload)
            response.raise_for_status()
        content = response.json().get("message", {}).get("content", "")
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Ollama não retornou JSON válido: {content[:500]}") from exc
        return Interpretation(
            document_type=str(data.get("document_type", "")),
            subject=str(data.get("subject", "")),
            description=str(data.get("description", "")),
            keywords=[str(x) for x in data.get("keywords", [])],
            entities=[str(x) for x in data.get("entities", [])],
            dates=[str(x) for x in data.get("dates", [])],
        )
