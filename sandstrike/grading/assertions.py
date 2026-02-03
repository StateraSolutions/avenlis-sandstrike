"""
Grading assertions for Avenlis.

Provides flexible assertion-based testing for LLM responses.
"""

import json
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass

from .config import GradingConfig, AssertionTypeConfig
from .providers import GradingProvider, GradingResult


@dataclass
class AssertionResult:
    """Result from a grading assertion."""
    assertion_type: str
    pass_result: bool
    score: float
    reason: str
    metadata: Dict[str, Any]
    error: Optional[str] = None


class GradingAssertion(ABC):
    """Base class for grading assertions."""
    
    def __init__(self, config: GradingConfig, assertion_type: str):
        self.config = config
        self.assertion_type = assertion_type
        self.assertion_config = config.get_assertion_config(assertion_type)
        if not self.assertion_config:
            raise ValueError(f"Unknown assertion type: {assertion_type}")
    
    @abstractmethod
    async def evaluate(self, output: str, **kwargs) -> AssertionResult:
        """Evaluate an output using this assertion."""
        pass
    
    def _render_template(self, template: str, **kwargs) -> str:
        """Render template with variables."""
        # Simple template rendering with variable substitution
        rendered = template
        for key, value in kwargs.items():
            placeholder = f"{{{{ {key} }}}}"
            rendered = rendered.replace(placeholder, str(value))
        return rendered
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response."""
        try:
            # Try to parse as JSON directly
            return json.loads(response.strip())
        except json.JSONDecodeError:
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            # If no JSON found, return as text
            return {"text": response}


class LLMRubricAssertion(GradingAssertion):
    """LLM-based rubric evaluation assertion."""
    
    def __init__(self, config: GradingConfig):
        super().__init__(config, "llm_rubric")
    
    async def evaluate(self, output: str, rubric: str, **kwargs) -> AssertionResult:
        """Evaluate output against a rubric using LLM."""
        try:
            # Get provider configuration
            provider_config = self.config.get_provider_config(self.assertion_config.provider)
            if not provider_config:
                raise ValueError(f"Provider not found: {self.assertion_config.provider}")
            
            # Create provider
            from .providers import create_grading_provider
            provider = create_grading_provider(self.assertion_config.provider, provider_config)
            
            # Get prompt template
            prompt_template = self.config.get_prompt_template(self.assertion_config.prompt_template)
            if not prompt_template:
                raise ValueError(f"Prompt template not found: {self.assertion_config.prompt_template}")
            
            # Render prompt
            prompt = self._render_template(prompt_template, output=output, rubric=rubric, **kwargs)
            
            # Grade using provider
            result = await provider.grade(prompt, assertion_type="llm_rubric")
            
            if result.error:
                return AssertionResult(
                    assertion_type=self.assertion_type,
                    pass_result=False,
                    score=0.0,
                    reason="",
                    metadata={"error": result.error},
                    error=result.error
                )
            
            return AssertionResult(
                assertion_type=self.assertion_type,
                pass_result=result.pass_result,
                score=result.score,
                reason=result.reason,
                metadata=result.metadata
            )
            
        except Exception as e:
            return AssertionResult(
                assertion_type=self.assertion_type,
                pass_result=False,
                score=0.0,
                reason="",
                metadata={"error": str(e)},
                error=str(e)
            )


class ClosedQAAssertion(GradingAssertion):
    """Closed question-answering evaluation assertion."""
    
    def __init__(self, config: GradingConfig):
        super().__init__(config, "closed_qa")
    
    async def evaluate(self, output: str, input_question: str, criteria: str, **kwargs) -> AssertionResult:
        """Evaluate if output correctly answers the question."""
        try:
            # Get provider configuration
            provider_config = self.config.get_provider_config(self.assertion_config.provider)
            if not provider_config:
                raise ValueError(f"Provider not found: {self.assertion_config.provider}")
            
            # Create provider
            from .providers import create_grading_provider
            provider = create_grading_provider(self.assertion_config.provider, provider_config)
            
            # Get prompt template
            prompt_template = self.config.get_prompt_template(self.assertion_config.prompt_template)
            if not prompt_template:
                raise ValueError(f"Prompt template not found: {self.assertion_config.prompt_template}")
            
            # Render prompt
            prompt = self._render_template(
                prompt_template, 
                input=input_question, 
                completion=output, 
                criteria=criteria, 
                **kwargs
            )
            
            # Grade using provider
            result = await provider.grade(prompt, assertion_type="closed_qa")
            
            if result.error:
                return AssertionResult(
                    assertion_type=self.assertion_type,
                    pass_result=False,
                    score=0.0,
                    reason="",
                    metadata={"error": result.error},
                    error=result.error
                )
            
            return AssertionResult(
                assertion_type=self.assertion_type,
                pass_result=result.pass_result,
                score=result.score,
                reason=result.reason,
                metadata=result.metadata
            )
            
        except Exception as e:
            return AssertionResult(
                assertion_type=self.assertion_type,
                pass_result=False,
                score=0.0,
                reason="",
                metadata={"error": str(e)},
                error=str(e)
            )


class ClassificationAssertion(GradingAssertion):
    """Classification evaluation assertion."""
    
    def __init__(self, config: GradingConfig):
        super().__init__(config, "classification")
    
    async def evaluate(self, output: str, categories: List[str], **kwargs) -> AssertionResult:
        """Classify output into categories."""
        try:
            # Get provider configuration
            provider_config = self.config.get_provider_config(self.assertion_config.provider)
            if not provider_config:
                raise ValueError(f"Provider not found: {self.assertion_config.provider}")
            
            # Create provider
            from .providers import create_grading_provider
            provider = create_grading_provider(self.assertion_config.provider, provider_config)
            
            # Get prompt template
            prompt_template = self.config.get_prompt_template(self.assertion_config.prompt_template)
            if not prompt_template:
                raise ValueError(f"Prompt template not found: {self.assertion_config.prompt_template}")
            
            # Render prompt
            prompt = self._render_template(
                prompt_template, 
                output=output, 
                categories=", ".join(categories), 
                **kwargs
            )
            
            # Grade using provider
            result = await provider.grade(prompt, assertion_type="classification")
            
            if result.error:
                return AssertionResult(
                    assertion_type=self.assertion_type,
                    pass_result=False,
                    score=0.0,
                    reason="",
                    metadata={"error": result.error},
                    error=result.error
                )
            
            return AssertionResult(
                assertion_type=self.assertion_type,
                pass_result=result.pass_result,
                score=result.score,
                reason=result.reason,
                metadata=result.metadata
            )
            
        except Exception as e:
            return AssertionResult(
                assertion_type=self.assertion_type,
                pass_result=False,
                score=0.0,
                reason="",
                metadata={"error": str(e)},
                error=str(e)
            )


class ModerationAssertion(GradingAssertion):
    """Content moderation evaluation assertion."""
    
    def __init__(self, config: GradingConfig):
        super().__init__(config, "moderation")
    
    async def evaluate(self, output: str, **kwargs) -> AssertionResult:
        """Check if output violates content policies."""
        try:
            # Get provider configuration
            provider_config = self.config.get_provider_config(self.assertion_config.provider)
            if not provider_config:
                raise ValueError(f"Provider not found: {self.assertion_config.provider}")
            
            # Create provider
            from .providers import create_grading_provider
            provider = create_grading_provider(self.assertion_config.provider, provider_config)
            
            # Get prompt template
            prompt_template = self.config.get_prompt_template(self.assertion_config.prompt_template)
            if not prompt_template:
                raise ValueError(f"Prompt template not found: {self.assertion_config.prompt_template}")
            
            # Render prompt
            prompt = self._render_template(prompt_template, output=output, **kwargs)
            
            # Grade using provider
            result = await provider.grade(prompt, assertion_type="moderation")
            
            if result.error:
                return AssertionResult(
                    assertion_type=self.assertion_type,
                    pass_result=False,
                    score=0.0,
                    reason="",
                    metadata={"error": result.error},
                    error=result.error
                )
            
            return AssertionResult(
                assertion_type=self.assertion_type,
                pass_result=result.pass_result,
                score=result.score,
                reason=result.reason,
                metadata=result.metadata
            )
            
        except Exception as e:
            return AssertionResult(
                assertion_type=self.assertion_type,
                pass_result=False,
                score=0.0,
                reason="",
                metadata={"error": str(e)},
                error=str(e)
            )


class RedTeamHarmfulAssertion(GradingAssertion):
    """Red team harmful content detection assertion."""
    
    def __init__(self, config: GradingConfig):
        super().__init__(config, "redteam_harmful")
    
    async def evaluate(self, output: str, **kwargs) -> AssertionResult:
        """Check if output contains harmful content."""
        try:
            # Get provider from kwargs (provider_override) or use default from assertion config
            provider_name = kwargs.get('provider_override') or self.assertion_config.provider
            print(f"[RedTeamHarmfulAssertion] Provider to use: {provider_name}")
            print(f"  From kwargs override: {kwargs.get('provider_override')}")
            print(f"  From assertion config: {self.assertion_config.provider}")
            
            # Get provider configuration
            provider_config = self.config.get_provider_config(provider_name)
            if not provider_config:
                raise ValueError(f"Provider not found: {provider_name}")
            
            # Create provider
            from .providers import create_grading_provider
            print(f"[RedTeamHarmfulAssertion] Creating provider: {provider_name}")
            provider = create_grading_provider(provider_name, provider_config)
            print(f"[RedTeamHarmfulAssertion] Provider created: {type(provider).__name__}")
            
            # Show the grading service URL for debugging
            if hasattr(provider, 'base_url'):
                print(f"[RedTeamHarmfulAssertion] Grading service base URL: {provider.base_url}")
                if provider_name == 'avenlis_copilot':
                    print(f"[RedTeamHarmfulAssertion] Full grading endpoint: {provider.base_url}/llm/grade-response")
            
            # Get prompt template
            prompt_template = self.config.get_prompt_template(self.assertion_config.prompt_template)
            if not prompt_template:
                raise ValueError(f"Prompt template not found: {self.assertion_config.prompt_template}")
            
            # Render prompt
            print(f"[RedTeamHarmfulAssertion] Rendering prompt template")
            prompt = self._render_template(prompt_template, output=output, **kwargs)
            
            # Grade using provider - pass all kwargs including api_key
            print(f"[RedTeamHarmfulAssertion] Calling provider.grade() with kwargs: {list(kwargs.keys())}")
            result = await provider.grade(prompt, assertion_type="redteam_harmful", **kwargs)
            print(f"[RedTeamHarmfulAssertion] Provider returned result: pass={result.pass_result}, score={result.score}")
            
            if result.error:
                return AssertionResult(
                    assertion_type=self.assertion_type,
                    pass_result=False,
                    score=0.0,
                    reason="",
                    metadata={"error": result.error},
                    error=result.error
                )
            
            return AssertionResult(
                assertion_type=self.assertion_type,
                pass_result=result.pass_result,
                score=result.score,
                reason=result.reason,
                metadata=result.metadata
            )
            
        except Exception as e:
            return AssertionResult(
                assertion_type=self.assertion_type,
                pass_result=False,
                score=0.0,
                reason="",
                metadata={"error": str(e)},
                error=str(e)
            )


class RedTeamInjectionAssertion(GradingAssertion):
    """Red team prompt injection detection assertion."""
    
    def __init__(self, config: GradingConfig):
        super().__init__(config, "redteam_injection")
    
    async def evaluate(self, output: str, original_prompt: str, **kwargs) -> AssertionResult:
        """Check if prompt injection was successful."""
        try:
            # Get provider from kwargs (provider_override) or use default from assertion config
            provider_name = kwargs.get('provider_override') or self.assertion_config.provider
            print(f"[RedTeamInjectionAssertion] Provider to use: {provider_name}")
            
            # Get provider configuration
            provider_config = self.config.get_provider_config(provider_name)
            if not provider_config:
                raise ValueError(f"Provider not found: {provider_name}")
            
            # Create provider
            from .providers import create_grading_provider
            print(f"[RedTeamInjectionAssertion] Creating provider: {provider_name}")
            provider = create_grading_provider(provider_name, provider_config)
            
            # Show the grading service URL for debugging
            if hasattr(provider, 'base_url'):
                print(f"[RedTeamInjectionAssertion] Grading service base URL: {provider.base_url}")
                if provider_name == 'avenlis_copilot':
                    print(f"[RedTeamInjectionAssertion] Full grading endpoint: {provider.base_url}/llm/grade-response")
            
            # Get prompt template
            prompt_template = self.config.get_prompt_template(self.assertion_config.prompt_template)
            if not prompt_template:
                raise ValueError(f"Prompt template not found: {self.assertion_config.prompt_template}")
            
            # Render prompt
            prompt = self._render_template(
                prompt_template, 
                output=output, 
                original_prompt=original_prompt, 
                response=output, 
                **kwargs
            )
            
            # Grade using provider - pass all kwargs including grader_intent
            result = await provider.grade(prompt, assertion_type="redteam_injection", **kwargs)
            
            if result.error:
                return AssertionResult(
                    assertion_type=self.assertion_type,
                    pass_result=False,
                    score=0.0,
                    reason="",
                    metadata={"error": result.error},
                    error=result.error
                )
            
            return AssertionResult(
                assertion_type=self.assertion_type,
                pass_result=result.pass_result,
                score=result.score,
                reason=result.reason,
                metadata=result.metadata
            )
            
        except Exception as e:
            return AssertionResult(
                assertion_type=self.assertion_type,
                pass_result=False,
                score=0.0,
                reason="",
                metadata={"error": str(e)},
                error=str(e)
            )


def create_assertion(assertion_type: str, config: GradingConfig) -> GradingAssertion:
    """Create an assertion by type."""
    if assertion_type == "llm_rubric":
        return LLMRubricAssertion(config)
    elif assertion_type == "closed_qa":
        return ClosedQAAssertion(config)
    elif assertion_type == "classification":
        return ClassificationAssertion(config)
    elif assertion_type == "moderation":
        return ModerationAssertion(config)
    elif assertion_type == "redteam_harmful":
        return RedTeamHarmfulAssertion(config)
    elif assertion_type == "redteam_injection":
        return RedTeamInjectionAssertion(config)
    else:
        raise ValueError(f"Unknown assertion type: {assertion_type}")
