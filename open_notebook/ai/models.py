from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mistralai import ChatMistralAI
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from loguru import logger

from open_notebook.domain.models import Settings
from open_notebook.exceptions import ConfigurationError, InvalidInputError


class ModelProvider(ABC):
    """Abstract base class for AI model providers."""
    
    @abstractmethod
    def get_client(self, model_name: str, temperature: float = 0.7, max_tokens: int = 4000) -> BaseChatModel:
        """Get a configured client for the provider."""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models for this provider."""
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the provider is properly configured."""
        pass


class OpenAIProvider(ModelProvider):
    """OpenAI model provider."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def get_client(self, model_name: str, temperature: float = 0.7, max_tokens: int = 4000) -> BaseChatModel:
        return ChatOpenAI(
            api_key=self.api_key,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def get_available_models(self) -> List[str]:
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo"
        ]
    
    def is_configured(self) -> bool:
        return bool(self.api_key)


class AnthropicProvider(ModelProvider):
    """Anthropic model provider."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def get_client(self, model_name: str, temperature: float = 0.7, max_tokens: int = 4000) -> BaseChatModel:
        return ChatAnthropic(
            api_key=self.api_key,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def get_available_models(self) -> List[str]:
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]
    
    def is_configured(self) -> bool:
        return bool(self.api_key)


class GeminiProvider(ModelProvider):
    """Google Gemini model provider."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def get_client(self, model_name: str, temperature: float = 0.7, max_tokens: int = 4000) -> BaseChatModel:
        return ChatGoogleGenerativeAI(
            google_api_key=self.api_key,
            model=model_name,
            temperature=temperature,
            max_output_tokens=max_tokens
        )
    
    def get_available_models(self) -> List[str]:
        return [
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-pro"
        ]
    
    def is_configured(self) -> bool:
        return bool(self.api_key)


class MistralProvider(ModelProvider):
    """Mistral AI model provider."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def get_client(self, model_name: str, temperature: float = 0.7, max_tokens: int = 4000) -> BaseChatModel:
        return ChatMistralAI(
            api_key=self.api_key,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def get_available_models(self) -> List[str]:
        return [
            "mistral-large-latest",
            "mistral-medium-latest",
            "mistral-small-latest",
            "open-mistral-7b",
            "open-mixtral-8x7b",
            "open-mixtral-8x22b"
        ]
    
    def is_configured(self) -> bool:
        return bool(self.api_key)


class GroqProvider(ModelProvider):
    """Groq model provider."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def get_client(self, model_name: str, temperature: float = 0.7, max_tokens: int = 4000) -> BaseChatModel:
        return ChatGroq(
            api_key=self.api_key,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def get_available_models(self) -> List[str]:
        return [
            "mixtral-8x7b-32768",
            "llama2-70b-4096",
            "llama3-70b-8192",
            "llama3-8b-8192",
            "gemma-7b-it"
        ]
    
    def is_configured(self) -> bool:
        return bool(self.api_key)


class ModelManager:
    """Manages AI models and providers."""
    
    def __init__(self):
        self.settings = Settings.load()
        self.providers: Dict[str, ModelProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available providers based on configured API keys."""
        if self.settings.openai_api_key:
            self.providers["openai"] = OpenAIProvider(self.settings.openai_api_key)
        
        if self.settings.anthropic_api_key:
            self.providers["anthropic"] = AnthropicProvider(self.settings.anthropic_api_key)
        
        if self.settings.gemini_api_key:
            self.providers["gemini"] = GeminiProvider(self.settings.gemini_api_key)
        
        if self.settings.mistral_api_key:
            self.providers["mistral"] = MistralProvider(self.settings.mistral_api_key)
        
        if self.settings.groq_api_key:
            self.providers["groq"] = GroqProvider(self.settings.groq_api_key)
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """Get all available models grouped by provider."""
        models = {}
        for provider_name, provider in self.providers.items():
            if provider.is_configured():
                models[provider_name] = provider.get_available_models()
        return models
    
    def get_model_client(self, model_name: str, temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> BaseChatModel:
        """Get a configured model client."""
        # Determine provider from model name
        provider_name = self._get_provider_for_model(model_name)
        
        if not provider_name or provider_name not in self.providers:
            raise ConfigurationError(f"No configured provider found for model: {model_name}")
        
        provider = self.providers[provider_name]
        if not provider.is_configured():
            raise ConfigurationError(f"Provider {provider_name} is not properly configured")
        
        # Use provided values or fall back to settings defaults
        temp = temperature if temperature is not None else self.settings.default_temperature
        tokens = max_tokens if max_tokens is not None else self.settings.max_tokens
        
        return provider.get_client(model_name, temp, tokens)
    
    def _get_provider_for_model(self, model_name: str) -> Optional[str]:
        """Determine which provider a model belongs to."""
        for provider_name, provider in self.providers.items():
            if model_name in provider.get_available_models():
                return provider_name
        return None
    
    def get_configured_providers(self) -> List[str]:
        """Get list of configured provider names."""
        return [name for name, provider in self.providers.items() if provider.is_configured()]
    
    def is_model_available(self, model_name: str) -> bool:
        """Check if a model is available and configured."""
        provider_name = self._get_provider_for_model(model_name)
        return (provider_name is not None and 
                provider_name in self.providers and 
                self.providers[provider_name].is_configured())
    
    def chat_completion(self, messages: List[Dict[str, str]], model_name: Optional[str] = None, **kwargs) -> str:
        """Get a chat completion from the specified model."""
        model = model_name or self.settings.default_model
        
        try:
            client = self.get_model_client(model, **kwargs)
            
            # Convert messages to LangChain format
            langchain_messages = []
            for message in messages:
                role = message.get("role", "user")
                content = message.get("content", "")
                
                if role == "system":
                    langchain_messages.append(SystemMessage(content=content))
                elif role == "user":
                    langchain_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    langchain_messages.append(AIMessage(content=content))
                else:
                    # Default to user message
                    langchain_messages.append(HumanMessage(content=content))
            
            response = client.invoke(langchain_messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Error in chat completion: {str(e)}")
            raise
    
    def refresh_settings(self):
        """Refresh settings and reinitialize providers."""
        self.settings = Settings.load()
        self.providers.clear()
        self._initialize_providers()


# Global model manager instance
model_manager = ModelManager()
