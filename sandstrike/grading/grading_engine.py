"""
Grading engine for Avenlis.

Main engine that coordinates grading providers and assertions.
"""

import asyncio
import time
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass

from .config import GradingConfig
from .assertions import GradingAssertion, create_assertion, AssertionResult
from .providers import GradingProvider, create_grading_provider


@dataclass
class GradingRequest:
    """Request for grading an output."""
    output: str
    assertion_type: str
    assertion_params: Dict[str, Any]
    provider_override: Optional[str] = None
    timeout: Optional[float] = None


@dataclass
class GradingResponse:
    """Response from grading engine."""
    request: GradingRequest
    result: AssertionResult
    execution_time: float
    provider_used: str
    metadata: Dict[str, Any]


class GradingEngine:
    """Main grading engine for Avenlis."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize grading engine with configuration."""
        if config_path:
            self.config = GradingConfig.load_from_file(config_path)
        else:
            self.config = GradingConfig._load_default_config()
        
        self._provider_cache: Dict[str, GradingProvider] = {}
    
    def _get_provider(self, provider_name: str) -> GradingProvider:
        """Get or create a grading provider."""
        if provider_name not in self._provider_cache:
            print(f"\n[GradingEngine] Getting provider: {provider_name}")
            provider_config = self.config.get_provider_config(provider_name)
            if not provider_config:
                # For avenlis_copilot, create a default config if not found
                print(f"[GradingEngine] Provider config not found in default configs")
                if provider_name == "avenlis_copilot":
                    import os
                    from .config import GradingProviderConfig
                    base_url = os.getenv('AVENLIS_LLM_URL', 'https://avenlis.staterasolv.com')
                    provider_config = GradingProviderConfig(
                        id="avenlis_copilot",
                        api_key=None,  # Will be passed via kwargs
                        base_url=base_url,
                        timeout=30.0
                    )
                    print(f"[GradingEngine] Created default avenlis_copilot config with base_url: {base_url}")
                else:
                    raise ValueError(f"Provider not found: {provider_name}")
            else:
                print(f"[GradingEngine] Using existing provider config")
                if hasattr(provider_config, 'base_url') and provider_config.base_url:
                    print(f"  Base URL: {provider_config.base_url}")
                if hasattr(provider_config, 'timeout'):
                    print(f"  Timeout: {provider_config.timeout}s")
            
            print(f"[GradingEngine] Creating provider instance...")
            self._provider_cache[provider_name] = create_grading_provider(
                provider_name, provider_config
            )
            print(f"[GradingEngine] Provider '{provider_name}' created successfully")
        else:
            print(f"[GradingEngine] Using cached provider: {provider_name}")
        
        return self._provider_cache[provider_name]
    
    async def grade(self, request: GradingRequest) -> GradingResponse:
        """Grade an output using the specified assertion type."""
        start_time = time.time()
        
        try:
            # Create assertion
            assertion = create_assertion(request.assertion_type, self.config)
            
            # Determine provider to use
            provider_name = request.provider_override
            if not provider_name:
                assertion_config = self.config.get_assertion_config(request.assertion_type)
                provider_name = assertion_config.provider
            
            print(f"GradingEngine: Using provider '{provider_name}' for assertion type '{request.assertion_type}'")
            
            # Pass provider_override to assertion via kwargs
            assertion_params_with_override = dict(request.assertion_params)
            assertion_params_with_override['provider_override'] = provider_name
            print(f"GradingEngine: Added provider_override to assertion params: {provider_name}")
            
            # Execute grading with timeout
            timeout = request.timeout or self.config.error_handling.timeout
            
            try:
                print(f"GradingEngine: Calling assertion.evaluate with output length={len(request.output)}, params keys={list(assertion_params_with_override.keys())}")
                result = await asyncio.wait_for(
                    assertion.evaluate(request.output, **assertion_params_with_override),
                    timeout=timeout
                )
                print(f"GradingEngine: Assertion evaluation completed, result pass={result.pass_result}, score={result.score}")
            except asyncio.TimeoutError:
                result = AssertionResult(
                    assertion_type=request.assertion_type,
                    pass_result=False,
                    score=0.0,
                    reason="Grading timeout",
                    metadata={"error": "timeout"},
                    error="Grading timeout"
                )
            
            execution_time = time.time() - start_time
            
            return GradingResponse(
                request=request,
                result=result,
                execution_time=execution_time,
                provider_used=provider_name,
                metadata={
                    "assertion_type": request.assertion_type,
                    "provider": provider_name,
                    "execution_time": execution_time
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            result = AssertionResult(
                assertion_type=request.assertion_type,
                pass_result=False,
                score=0.0,
                reason=str(e),
                metadata={"error": str(e)},
                error=str(e)
            )
            
            return GradingResponse(
                request=request,
                result=result,
                execution_time=execution_time,
                provider_used="unknown",
                metadata={
                    "assertion_type": request.assertion_type,
                    "error": str(e),
                    "execution_time": execution_time
                }
            )
    
    async def grade_batch(self, requests: List[GradingRequest]) -> List[GradingResponse]:
        """Grade multiple outputs in parallel."""
        tasks = [self.grade(request) for request in requests]
        return await asyncio.gather(*tasks)
    
    async def grade_with_retry(self, request: GradingRequest, max_retries: Optional[int] = None) -> GradingResponse:
        """Grade with retry logic."""
        max_retries = max_retries or self.config.error_handling.max_retries
        retry_delay = self.config.error_handling.retry_delay
        
        last_response = None
        
        for attempt in range(max_retries + 1):
            try:
                response = await self.grade(request)
                
                # If successful or not a retryable error, return
                if not response.result.error or attempt == max_retries:
                    return response
                
                last_response = response
                
                # Wait before retry
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)
                    
            except Exception as e:
                if attempt == max_retries:
                    # Last attempt failed, return error response
                    return GradingResponse(
                        request=request,
                        result=AssertionResult(
                            assertion_type=request.assertion_type,
                            pass_result=False,
                            score=0.0,
                            reason="",
                            metadata={"error": str(e)},
                            error=str(e)
                        ),
                        execution_time=0.0,
                        provider_used="unknown",
                        metadata={"error": str(e)}
                    )
                
                # Wait before retry
                await asyncio.sleep(retry_delay)
        
        return last_response or GradingResponse(
            request=request,
            result=AssertionResult(
                assertion_type=request.assertion_type,
                pass_result=False,
                score=0.0,
                reason="",
                metadata={"error": "Max retries exceeded"},
                error="Max retries exceeded"
            ),
            execution_time=0.0,
            provider_used="unknown",
            metadata={"error": "Max retries exceeded"}
        )
    
    def get_available_assertions(self) -> List[str]:
        """Get list of available assertion types."""
        return list(self.config.assertion_types.keys())
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        return list(self.config.default_graders.keys())
    
    def get_assertion_config(self, assertion_type: str) -> Optional[Dict[str, Any]]:
        """Get configuration for an assertion type."""
        assertion_config = self.config.get_assertion_config(assertion_type)
        if not assertion_config:
            return None
        
        return {
            "description": assertion_config.description,
            "provider": assertion_config.provider,
            "output_format": assertion_config.output_format,
            "required_fields": assertion_config.required_fields,
            "expected_output": assertion_config.expected_output
        }
    
    def get_provider_config(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a provider."""
        provider_config = self.config.get_provider_config(provider_name)
        if not provider_config:
            return None
        
        return {
            "id": provider_config.id,
            "model": provider_config.model,
            "temperature": provider_config.temperature,
            "max_tokens": provider_config.max_tokens,
            "timeout": provider_config.timeout
        }


# Convenience functions for common grading tasks
async def grade_llm_rubric(
    output: str, 
    rubric: str, 
    engine: GradingEngine,
    provider: Optional[str] = None
) -> GradingResponse:
    """Grade output against a rubric using LLM."""
    request = GradingRequest(
        output=output,
        assertion_type="llm_rubric",
        assertion_params={"rubric": rubric},
        provider_override=provider
    )
    return await engine.grade(request)


async def grade_harmful_content(
    output: str, 
    engine: GradingEngine,
    provider: Optional[str] = None
) -> GradingResponse:
    """Check if output contains harmful content."""
    request = GradingRequest(
        output=output,
        assertion_type="redteam_harmful",
        assertion_params={},
        provider_override=provider
    )
    return await engine.grade(request)


async def grade_prompt_injection(
    output: str, 
    original_prompt: str,
    engine: GradingEngine,
    provider: Optional[str] = None
) -> GradingResponse:
    """Check if prompt injection was successful."""
    request = GradingRequest(
        output=output,
        assertion_type="redteam_injection",
        assertion_params={"original_prompt": original_prompt},
        provider_override=provider
    )
    return await engine.grade(request)


async def grade_moderation(
    output: str, 
    engine: GradingEngine,
    provider: Optional[str] = None
) -> GradingResponse:
    """Check if output violates content policies."""
    request = GradingRequest(
        output=output,
        assertion_type="moderation",
        assertion_params={},
        provider_override=provider
    )
    return await engine.grade(request)
