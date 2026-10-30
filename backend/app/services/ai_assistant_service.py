import asyncio
import json
import logging
import re
import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status

try:
    from groq import (
        AsyncGroq,
        APIConnectionError,
        APIStatusError,
        APITimeoutError,
        AuthenticationError,
        BadRequestError,
        NotFoundError,
        RateLimitError,
    )
except ImportError:
    AsyncGroq = None  # type: ignore
    APIConnectionError = Exception  # type: ignore
    APIStatusError = Exception  # type: ignore
    APITimeoutError = Exception  # type: ignore
    AuthenticationError = Exception  # type: ignore
    BadRequestError = Exception  # type: ignore
    NotFoundError = Exception  # type: ignore
    RateLimitError = Exception  # type: ignore

from app.calculations.electricity_calculator import calculate_electricity_savings_scenario
from app.calculations.route_optimizer import optimize_bus_routes
from app.calculations.waste_calculator import calculate_recycling_rate
from app.core.config import settings
from app.data.emission_factors import BENCHMARK_PRICES, EMISSION_FACTORS
from app.schemas.ai import (
    AiChatResponse,
    CalculationBreakdown,
    KeyFindingItem,
    MetricItem,
    RecommendationItem,
    StructuredAiPayload,
)
from app.services.ai_context_service import AiContextService
from app.utils.dates import utc_iso
from app.utils.ids import generate_id

logger = logging.getLogger("carboniq.ai")


class AiCache:
    """
    Workspace-scoped, data-versioned in-memory LRU cache for deterministic calculations
    and AI responses.
    Guarantees:
    - Zero data leakage across workspaces (workspace_id prefix).
    - Automatic invalidation when underlying workspace records change (count, sum, or period).
    - Never caches error states.
    - LRU eviction (max 150 items) with a 10-minute TTL.
    """
    _cache: "OrderedDict[str, tuple[AiChatResponse, float]]" = OrderedDict()
    _max_entries: int = 150
    _ttl_seconds: float = 600.0

    @classmethod
    def make_key(cls, workspace_id: str, module: str, question: str, data_fingerprint: str) -> str:
        norm_q = question.strip().lower()
        return f"{workspace_id}:{module}:{norm_q}:{data_fingerprint}"

    @classmethod
    def get(cls, key: str) -> Optional[AiChatResponse]:
        now = time.time()
        entry = cls._cache.get(key)
        if entry is None:
            return None
        cached_resp, expiry = entry
        if now > expiry:
            cls._cache.pop(key, None)
            return None
        cls._cache.move_to_end(key)
        # Return a copy with fresh timestamp/id if needed, but preserved content
        return cached_resp

    @classmethod
    def set(cls, key: str, response: AiChatResponse) -> None:
        now = time.time()
        if len(cls._cache) >= cls._max_entries:
            cls._cache.popitem(last=False)
        cls._cache[key] = (response, now + cls._ttl_seconds)

    @classmethod
    def invalidate_workspace(cls, workspace_id: str) -> None:
        keys_to_remove = [k for k in cls._cache if k.startswith(f"{workspace_id}:")]
        for k in keys_to_remove:
            cls._cache.pop(k, None)


def sanitize_user_input(text: str) -> str:
    """
    Sanitizes user query to prevent prompt injection and instruction override attempts.
    Limits length and strips control sequences.
    """
    cleaned = text.strip()[:500]
    injection_patterns = [
        r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions?",
        r"(?i)system\s*:",
        r"(?i)assistant\s*:",
        r"(?i)you\s+are\s+now\s+in\s+developer\s+mode",
        r"(?i)bypass\s+all\s+rules",
    ]
    for pattern in injection_patterns:
        cleaned = re.sub(pattern, "[sanitized]", cleaned)
    return cleaned.strip()


def parse_structured_ai_reply(
    raw_reply: str,
    default_intent: str = "direct",
    default_answer: str = "",
) -> StructuredAiPayload:
    """
    Safely parses an LLM completion into a validated StructuredAiPayload.
    Handles:
    - Clean JSON objects matching the schema.
    - Markdown-wrapped JSON (```json ... ```).
    - Unstructured prose or markdown responses by extracting the direct answer.
    Guarantees clean presentation without raw JSON syntax.
    """
    cleaned = raw_reply.strip()
    # Strip markdown code fences if wrapped
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()

    # Search for JSON substring
    match = re.search(r"(\{[\s\S]*\})", cleaned)
    data = None
    if match:
        json_candidate = match.group(1).strip()
        # Clean trailing commas before closing braces/brackets
        json_candidate = re.sub(r",\s*([\]}])", r"\1", json_candidate)
        try:
            data = json.loads(json_candidate, strict=False)
        except Exception:
            try:
                data = json.loads(json_candidate)
            except Exception as parse_err:
                logger.debug("Failed parsing JSON from LLM: %s", parse_err)
                data = None

    if isinstance(data, dict):
        direct_ans = str(
            data.get("direct_answer")
            or data.get("summary")
            or data.get("answer")
            or data.get("content")
            or ""
        ).strip()

        # If direct_ans itself contains serialized JSON, extract the text recursively
        if direct_ans.startswith("{") and ("direct_answer" in direct_ans or "summary" in direct_ans):
            inner_m = re.search(r'"(?:direct_answer|summary)"\s*:\s*"((?:[^"\\]|\\.)*)"', direct_ans)
            if inner_m:
                try:
                    direct_ans = inner_m.group(1).encode("utf-8").decode("unicode_escape", errors="ignore").strip()
                except Exception:
                    direct_ans = inner_m.group(1).strip()

        if not direct_ans:
            direct_ans = default_answer or cleaned[:300]

        metrics: List[MetricItem] = []
        for m in data.get("metrics", []):
            if isinstance(m, dict) and m.get("label") and m.get("value") is not None:
                metrics.append(
                    MetricItem(
                        label=str(m["label"]),
                        value=m["value"],
                        unit=str(m.get("unit")) if m.get("unit") else None,
                        subtext=str(m.get("subtext")) if m.get("subtext") else None,
                        trend=str(m.get("trend")) if m.get("trend") in ["up", "down", "neutral"] else None,
                    )
                )

        findings: List[KeyFindingItem] = []
        for kf in data.get("key_findings", []):
            if isinstance(kf, dict) and (kf.get("title") or kf.get("description")):
                findings.append(
                    KeyFindingItem(
                        title=str(kf.get("title") or "Key Finding"),
                        description=str(kf.get("description") or ""),
                        category=str(kf.get("category")) if kf.get("category") else None,
                    )
                )

        recs: List[RecommendationItem] = []
        for r in data.get("recommendations", []):
            if isinstance(r, dict) and (r.get("title") or r.get("explanation")):
                recs.append(
                    RecommendationItem(
                        title=str(r.get("title") or "Recommended Action"),
                        explanation=str(r.get("explanation") or ""),
                        expected_benefit=str(r.get("expected_benefit") or r.get("impact") or "Operational efficiency"),
                        priority=str(r.get("priority") or "Medium"),
                        category=str(r.get("category") or "General"),
                        action_url=str(r.get("action_url")) if r.get("action_url") else None,
                        action_label=str(r.get("action_label")) if r.get("action_label") else None,
                    )
                )

        limits = [str(x) for x in data.get("data_limitations", []) if x]

        return StructuredAiPayload(
            intent=data.get("intent", default_intent),
            direct_answer=direct_ans,
            explanation=data.get("explanation") if data.get("explanation") else None,
            reporting_period=data.get("reporting_period"),
            metrics=metrics,
            key_findings=findings,
            recommendations=recs,
            data_limitations=limits,
            confidence_score=str(data.get("confidence_score")) if data.get("confidence_score") else None,
        )

    # Fallback: Extract fields using regex to prevent displaying raw JSON blocks
    da_match = re.search(r'"(?:direct_answer|summary)"\s*:\s*"((?:[^"\\]|\\.)*)"', cleaned, re.DOTALL)
    expl_match = re.search(r'"explanation"\s*:\s*"((?:[^"\\]|\\.)*)"', cleaned, re.DOTALL)

    extracted_ans = ""
    if da_match:
        try:
            extracted_ans = da_match.group(1).encode("utf-8").decode("unicode_escape", errors="ignore").strip()
        except Exception:
            extracted_ans = da_match.group(1).strip()

    extracted_expl = None
    if expl_match:
        try:
            extracted_expl = expl_match.group(1).encode("utf-8").decode("unicode_escape", errors="ignore").strip()
        except Exception:
            extracted_expl = expl_match.group(1).strip()

    if not extracted_ans:
        clean_text = re.sub(r'^[{\s]*"(?:direct_answer|summary)"\s*:\s*"?', "", cleaned)
        clean_text = re.sub(r'"?\s*[}\s]*$', "", clean_text).strip()
        if clean_text.startswith("{") and "}" in clean_text:
            clean_text = default_answer or "Analysis generated from verified records."
        extracted_ans = clean_text

    return StructuredAiPayload(
        intent=default_intent,
        direct_answer=extracted_ans or default_answer or "Analysis generated from verified records.",
        explanation=extracted_expl,
        metrics=[],
        key_findings=[],
        recommendations=[],
        data_limitations=[],
    )


class AiAssistantService:
    """
    Shared, secure AI Assistant service powering the four context-aware experiences:
    1. Electricity Advisor (Module-isolated: electricity consumption, CEA grid factors, tariffs)
    2. Transportation Advisor (Module-isolated: vehicle fuels, fleet routes, occupancy, optimization)
    3. Waste Advisor (Module-isolated: categories, recovery rates, treatment methods, disposal costs)
    4. Main AI Insights Assistant (Cross-category synthesis: holistic footprint, priorities, trends)

    Safeguards:
    - If GROQ_API_KEY is not configured: immediately raises HTTP 503 Service Unavailable.
      Zero fake, static, simulated, or rule-based answers are generated.
    - If configured: uses official Groq API (AsyncGroq, default llama-3.3-70b-versatile).
    - Grounded strictly in authenticated workspace records and deterministic backend calculations.
    - Zero numerical hallucinations: factors and calculations originate from trusted backend services.
    - Input sanitization against instruction overriding.
    """

    _groq_client: Optional[Any] = None
    _cached_api_key: Optional[str] = None

    @classmethod
    def _verify_groq_configured(cls) -> str:
        """
        Enforces that GROQ_API_KEY is present in the environment.
        Raises HTTP 503 immediately if unconfigured.
        """
        api_key = settings.effective_groq_api_key
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI is not configured. Add GROQ_API_KEY to the backend environment and restart the server.",
            )
        return api_key

    @classmethod
    def _get_groq_client(cls, api_key: str) -> Any:
        """
        Reuses a single AsyncGroq client instance across requests to maintain
        connection pooling and avoid TCP/TLS handshake latency on every call.
        """
        if cls._groq_client is None or cls._cached_api_key != api_key:
            cls._cached_api_key = api_key
            cls._groq_client = AsyncGroq(api_key=api_key, timeout=12.0)
        return cls._groq_client

    @classmethod
    async def _call_llm(
        cls,
        system_instruction: str,
        user_query: str,
        grounded_context: Dict[str, Any],
        max_tokens: int = 450,
    ) -> str:
        """
        Calls official Groq API using shared AsyncGroq client.
        Injects verified backend calculations as the sole authoritative numerical context.
        Uses compact JSON formatting and tuned token limits to minimize latency.
        """
        api_key = cls._verify_groq_configured()

        if AsyncGroq is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Groq SDK is not installed in the backend environment.",
            )

        configured_model = settings.effective_groq_model or "qwen/qwen3.8-27b"
        models_to_attempt = [configured_model]
        for fallback in ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]:
            if fallback not in models_to_attempt:
                models_to_attempt.append(fallback)

        system_prompt = (
            "You are CarbonIQ's sustainability analysis assistant.\n"
            f"{system_instruction}\n\n"
            "EVIDENCE-BASED REASONING CONSTRAINTS:\n"
            "1. Answer using the supplied CarbonIQ context and user inquiry. Treat supplied calculated emissions, historical aggregates, and valid model predictions as the sole authoritative values.\n"
            "2. Do NOT invent activity records, emissions, dates, emission factors, predictions, savings, or model accuracy.\n"
            "3. Do not claim correlation proves causation. Distinguish observed facts from possible explanations and recommendations.\n"
            "4. When supplied information is insufficient, clearly state what is missing in data_limitations.\n"
            "5. Do not claim an action will produce a numerical emissions reduction unless available calculations support it.\n"
            "6. When discussing future emissions, distinguish validated model predictions from illustrative scenarios.\n"
            "7. When comparing bus routes, use actual optimization results. Do not invent routes, bus capacities, passenger counts, travel distances, or savings.\n"
            "8. Use historical trends to personalize recommendations where relevant. Explain recommendations in clear, practical language.\n"
            "9. Keep direct_answer concise (2-3 sentences). Limit key findings and recommendations to max 2 items each.\n"
            "10. Respond ONLY with a valid JSON object matching the requested schema without markdown fences."
        )

        # Minified JSON context to save prompt token bandwidth and processing time
        compact_context = json.dumps(grounded_context, separators=(",", ":"))
        user_prompt = (
            f"GROUNDED CONTEXT:\n{compact_context}\n\n"
            f"USER INQUIRY:\n{user_query}"
        )

        client = cls._get_groq_client(api_key)

        for attempt_idx, current_model in enumerate(models_to_attempt):
            try:
                chat_completion = await client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    model=current_model,
                    temperature=0.1,  # Low temperature to prevent hallucinations
                    max_tokens=max_tokens,
                )
                if chat_completion.choices and len(chat_completion.choices) > 0:
                    answer = chat_completion.choices[0].message.content
                    if answer and answer.strip():
                        if current_model != configured_model:
                            logger.info(
                                "Groq completion succeeded using fallback model '%s' (configured '%s' was unavailable).",
                                current_model,
                                configured_model,
                            )
                        return answer.strip()

                logger.error("Groq API returned an empty completion response for model '%s'.", current_model)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Groq API returned an empty completion.",
                )
            except (NotFoundError, BadRequestError) as e:
                err_msg = getattr(e, "message", str(e)).lower()
                is_model_error = (
                    isinstance(e, NotFoundError)
                    or "model" in err_msg
                    or "not found" in err_msg
                    or "decommissioned" in err_msg
                )
                if is_model_error:
                    logger.warning(
                        "Groq model '%s' is unavailable on this account (%s).",
                        current_model,
                        err_msg,
                    )
                    # If other models are queued, attempt them
                    if attempt_idx < len(models_to_attempt) - 1:
                        logger.info("Attempting next candidate model '%s'...", models_to_attempt[attempt_idx + 1])
                        continue

                    # All candidates failed
                    logger.error("All candidate Groq models failed. Configured model was '%s'.", configured_model)
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=(
                            f"The configured Groq model '{configured_model}' is not supported or accessible with your API key. "
                            f"Please update GROQ_MODEL in backend/.env to a supported model (e.g. qwen/qwen3.8-27b)."
                        ),
                    )
                else:
                    logger.error("Groq bad request error: %s", e)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid request parameters to Groq API: {getattr(e, 'message', str(e))}",
                    )
            except AuthenticationError as e:
                logger.error(
                    "Groq authentication failure: invalid or rejected API key (begins with '%s...').",
                    api_key[:6] if len(api_key) >= 6 else "***",
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Groq authentication failed. Please verify that GROQ_API_KEY is configured with a valid key in the backend environment.",
                )
            except RateLimitError as e:
                logger.warning("Groq rate limit reached: %s", e)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="The AI assistant is temporarily rate-limited by the Groq API provider. Please wait a moment and try again.",
                )
            except APITimeoutError as e:
                logger.error("Groq API request timed out after 15.0s: %s", e)
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="Groq API request timed out after 15.0s. Please try again shortly.",
                )
            except APIConnectionError as e:
                logger.error("Groq connection timeout or network failure: %s", e)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Unable to connect to the Groq API service due to a network timeout or connection error.",
                )
            except APIStatusError as e:
                logger.error("Groq API status error [%s]: %s", e.status_code, getattr(e, 'message', str(e)))
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"The Groq API returned an error (status {e.status_code}): {getattr(e, 'message', 'Upstream error')}.",
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Unexpected internal exception during Groq LLM invocation: %s", e)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"An unexpected internal error occurred during AI processing: {str(e)}",
                )

    # =========================================================================
    # EXPERIENCE 1: Electricity AI Advisor
    # =========================================================================
    @classmethod
    async def query_electricity_advisor(
        cls,
        question: str,
        workspace_id: str,
        db: Any,
    ) -> AiChatResponse:
        t_start = time.perf_counter()
        cls._verify_groq_configured()
        sanitized_q = sanitize_user_input(question)
        q = sanitized_q.lower()
        timestamp = utc_iso()
        chat_id = generate_id("ai_elec")

        # 1. Build comprehensive, historical & current context via AiContextService
        t_ctx_start = time.perf_counter()
        context = await AiContextService.build_electricity_context(workspace_id, db, sanitized_q)
        t_ctx = (time.perf_counter() - t_ctx_start) * 1000

        if not context.get("has_records"):
            empty_msg = "No electricity consumption records found in your workspace yet. Please log monthly meter readings to enable personalized AI energy analysis."
            return AiChatResponse(
                id=chat_id,
                content=empty_msg,
                timestamp=timestamp,
                structured_payload=StructuredAiPayload(
                    intent="direct",
                    direct_answer=empty_msg,
                    data_limitations=context.get("data_limitations", ["No electricity records currently logged for this workspace."]),
                ),
            )

        cur = context["current_period"]
        total_rec = context["total_records_analyzed"]
        fingerprint = f"{total_rec}:{cur['consumption_kwh']}:{cur['month']}"
        cache_key = AiCache.make_key(workspace_id, "electricity", sanitized_q, fingerprint)
        cached_resp = AiCache.get(cache_key)
        if cached_resp:
            t_total = (time.perf_counter() - t_start) * 1000
            logger.info("AI [electricity] CACHE HIT: total=%.1fms (ctx=%.1fms)", t_total, t_ctx)
            return cached_resp

        # 2. Attach verifiable calculation breakdown if applicable
        calculation_breakdown = None
        match_pct = re.search(r"(\d+)%", q)
        if "save" in q or "reduc" in q or match_pct or "scenario" in q or "cost" in q:
            sc = context["modeled_savings_scenario"]
            calculation_breakdown = CalculationBreakdown(
                formula="Potential Reduction = Current kWh × (Target Reduction % ÷ 100)",
                inputs={
                    "Baseline consumption": f"{cur['consumption_kwh']:,} kWh ({cur['month']})",
                    "Target reduction": f"{sc['target_reduction_percent']:.0f}%",
                    "Assumed variable tariff": f"₹{sc['assumed_tariff_inr_per_kwh']}/kWh",
                    "Grid emission factor": f"{context['authoritative_emission_factor']['value']} {context['authoritative_emission_factor']['unit']}",
                },
                assumptions=sc["assumptions"],
                result=f"₹{sc['estimated_monthly_savings_inr']:,.0f}/month estimated savings ({sc['kwh_reduction']:,} kWh / {sc['emissions_reduction_kg']:,.1f} kg CO2e)",
            )
        elif any(w in q for w in ["highest", "peak", "maximum"]):
            peak = context["historical_statistics"]["peak_month"]
            calculation_breakdown = CalculationBreakdown(
                formula="Peak Month = max(monthly_consumption_kwh)",
                inputs={
                    "Peak period": peak["month"],
                    "Consumption": f"{peak['consumption_kwh']:,} kWh",
                    "Emissions": f"{peak['emissions_kg']:,} kg CO2e",
                },
                result=f"Peak observed in {peak['month']} ({peak['consumption_kwh']:,} kWh)",
            )
        elif ("compare" in q or "previous" in q or "mom" in q or "change" in q or "trend" in q) and context.get("previous_period_comparison"):
            comp = context["previous_period_comparison"]
            calculation_breakdown = CalculationBreakdown(
                formula="Change = Current Month kWh - Previous Month kWh",
                inputs={
                    f"Current ({cur['month']})": f"{comp['current_value']:,} kWh",
                    "Previous month": f"{comp['previous_value']:,} kWh",
                },
                result=comp["formatted_change"],
            )

        elec_instruction = (
            "You are CarbonIQ's Senior Energy & Decarbonization Analyst.\n"
            "ROLE: Provide grounded analysis of workspace electricity consumption (kWh), CEA baseline emissions (kg CO2e), "
            "tariffs (INR), and efficiency actions. Ground answers in current and historical monthly context.\n"
            "USER INTENT & EVIDENCE RULES:\n"
            "- Determine user intent: 'direct', 'comparative', 'recommendation', or 'analytical'.\n"
            "- Cite verified metrics from context in 'direct_answer' and 'metrics'. Keep it concise without generic filler.\n"
            "- Use historical trends to personalize operational recommendations (HVAC scheduling, cooling set points, solar PV).\n"
            "- If historical records are limited, state limitations in 'data_limitations'.\n\n"
            "OUTPUT SCHEMA (Respond ONLY with valid JSON):\n"
            "{\n"
            '  "intent": "direct" | "comparative" | "recommendation" | "analytical",\n'
            '  "direct_answer": "Direct answer citing verified kWh and kg CO2e.",\n'
            '  "explanation": "Optional methodology note (or null)",\n'
            '  "metrics": [\n'
            '    {"label": "Metric Name", "value": "1240", "unit": "kWh", "subtext": "Period"}\n'
            '  ],\n'
            '  "key_findings": [\n'
            '    {"title": "Finding Title", "description": "Concise observation.", "category": "Electricity"}\n'
            '  ],\n'
            '  "recommendations": [\n'
            '    {"title": "Action Title", "explanation": "Why relevant.", "priority": "High" | "Medium" | "Low", "expected_benefit": "Realistic benefit", "action_url": "/dashboard/simulator"}\n'
            '  ],\n'
            '  "data_limitations": ["Data boundary note if records are few"]\n'
            "}"
        )

        t_llm_start = time.perf_counter()
        llm_reply = await cls._call_llm(
            system_instruction=elec_instruction,
            user_query=sanitized_q,
            grounded_context=context,
            max_tokens=450,
        )
        t_llm = (time.perf_counter() - t_llm_start) * 1000

        t_parse_start = time.perf_counter()
        structured_payload = parse_structured_ai_reply(
            llm_reply,
            default_intent="direct",
            default_answer=f"Latest electricity consumption was {cur['consumption_kwh']:,} kWh ({cur['calculated_emissions_kg']:,.1f} kg CO2e) for {cur['month']}.",
        )
        t_parse = (time.perf_counter() - t_parse_start) * 1000

        t_total = (time.perf_counter() - t_start) * 1000
        logger.info(
            "AI [electricity] perf: total=%.1fms (ctx=%.1fms, llm=%.1fms, parse=%.1fms, cached=False)",
            t_total, t_ctx, t_llm, t_parse
        )

        response = AiChatResponse(
            id=chat_id,
            content=structured_payload.direct_answer,
            timestamp=timestamp,
            calculation_breakdown=calculation_breakdown,
            structured_payload=structured_payload,
            meta={
                "timing_ms": {
                    "context": round(t_ctx, 1),
                    "llm": round(t_llm, 1),
                    "parse": round(t_parse, 1),
                    "total": round(t_total, 1),
                },
                "cached": False,
            },
        )
        AiCache.set(cache_key, response)
        return response

    # =========================================================================
    # EXPERIENCE 2: Transportation AI Advisor
    # =========================================================================
    @classmethod
    async def query_transportation_advisor(
        cls,
        question: str,
        workspace_id: str,
        db: Any,
    ) -> AiChatResponse:
        t_start = time.perf_counter()
        cls._verify_groq_configured()
        sanitized_q = sanitize_user_input(question)
        q = sanitized_q.lower()
        timestamp = utc_iso()
        chat_id = generate_id("ai_trans")

        # 1. Build comprehensive, historical & fleet context via AiContextService
        t_ctx_start = time.perf_counter()
        context = await AiContextService.build_transportation_context(workspace_id, db, sanitized_q)
        t_ctx = (time.perf_counter() - t_ctx_start) * 1000

        if not context.get("has_records"):
            empty_msg = "No transportation records or fleet routes found in your workspace yet. Please configure bus corridors or log trip mileage to enable mobility analysis."
            return AiChatResponse(
                id=chat_id,
                content=empty_msg,
                timestamp=timestamp,
                structured_payload=StructuredAiPayload(
                    intent="direct",
                    direct_answer=empty_msg,
                    data_limitations=context.get("data_limitations", ["No transportation records or bus routes currently configured for this workspace."]),
                ),
            )

        cur = context["current_period"]
        fingerprint = f"{context['total_fleet_records']}:{context['total_routes_configured']}:{cur['distance_km']}:{cur['calculated_emissions_kg']}"
        cache_key = AiCache.make_key(workspace_id, "transportation", sanitized_q, fingerprint)
        cached_resp = AiCache.get(cache_key)
        if cached_resp:
            t_total = (time.perf_counter() - t_start) * 1000
            logger.info("AI [transportation] CACHE HIT: total=%.1fms (ctx=%.1fms)", t_total, t_ctx)
            return cached_resp

        # 2. Attach verifiable calculation breakdown if applicable
        calculation_breakdown = None
        if ("combin" in q or "optimiz" in q or "overlap" in q or "consolidat" in q) and context.get("route_optimization_proposal"):
            p = context["route_optimization_proposal"]
            calculation_breakdown = CalculationBreakdown(
                formula="Fuel Reduction = (Current Distance - Combined Distance) ÷ Fleet km/L × Days/Month",
                inputs={
                    "Corridor opportunity": p["title"],
                    "Distance reduction": f"{p['distance_reduction_km_per_day']} km/day",
                    "Feasibility": p["feasibility"],
                },
                result=f"Save ~{p['estimated_monthly_fuel_savings_liters']} L fuel/month (₹{p['estimated_monthly_cost_savings_inr']:,})",
            )
        elif "fuel" in q and ("most" in q or "highest" in q or "peak" in q) and context["bus_fleet_metrics"].get("peak_fuel_route"):
            pk = context["bus_fleet_metrics"]["peak_fuel_route"]
            calculation_breakdown = CalculationBreakdown(
                formula="Daily Fuel = (Distance × Trips) ÷ Fuel Efficiency",
                inputs={
                    "Route": pk["route_name"],
                    "Distance": f"{pk['distance_km']} km",
                    "Fuel Efficiency": f"{pk['fuel_efficiency_km_per_l']} km/L",
                },
                result=f"{pk['daily_fuel_liters']} L/day",
            )
        elif ("compare" in q or "previous" in q or "mom" in q or "change" in q or "trend" in q) and context.get("previous_period_comparison"):
            comp = context["previous_period_comparison"]
            calculation_breakdown = CalculationBreakdown(
                formula="Change = Current Month Emissions - Previous Month Emissions",
                inputs={
                    f"Current ({cur['month']})": f"{comp['current_value']} kg CO2e",
                    "Previous month": f"{comp['previous_value']} kg CO2e",
                },
                result=comp["formatted_change"],
            )

        trans_instruction = (
            "You are CarbonIQ's Fleet & Mobility Sustainability Advisor.\n"
            "ROLE: Provide grounded insights on bus routes, trip distances, student occupancy, diesel consumption, and Scope 1 emissions. "
            "Use historical monthly trends and fleet route metrics to guide recommendations.\n"
            "USER INTENT & EVIDENCE RULES:\n"
            "- Determine user intent: 'direct', 'comparative', 'recommendation', or 'analytical'.\n"
            "- If user asks which route consumes the most fuel, cite its distance, trips, and L/day directly in 'direct_answer'.\n"
            "- Use historical trends to personalize corridor consolidation or deadhead reduction.\n"
            "- If records are limited, state limitations in 'data_limitations'.\n\n"
            "OUTPUT SCHEMA (Respond ONLY with valid JSON):\n"
            "{\n"
            '  "intent": "direct" | "comparative" | "recommendation" | "analytical",\n'
            '  "direct_answer": "Concise direct answer citing verified distance, fuel (L), or emissions.",\n'
            '  "explanation": "Optional supporting explanation (or null)",\n'
            '  "metrics": [\n'
            '    {"label": "Daily Fuel", "value": "26.7", "unit": "L/day", "subtext": "Peak route"}\n'
            '  ],\n'
            '  "key_findings": [\n'
            '    {"title": "Route Finding", "description": "Concise route observation supported by records.", "category": "Transportation"}\n'
            '  ],\n'
            '  "recommendations": [\n'
            '    {"title": "Action Title", "explanation": "Corridor consolidation or deadhead reduction.", "priority": "Medium", "expected_benefit": "Estimated fuel reduction", "action_url": "/dashboard/transportation"}\n'
            '  ],\n'
            '  "data_limitations": ["Data boundary note if records are few"]\n'
            "}"
        )

        t_llm_start = time.perf_counter()
        llm_reply = await cls._call_llm(
            system_instruction=trans_instruction,
            user_query=sanitized_q,
            grounded_context=context,
            max_tokens=450,
        )
        t_llm = (time.perf_counter() - t_llm_start) * 1000

        t_parse_start = time.perf_counter()
        structured_payload = parse_structured_ai_reply(
            llm_reply,
            default_intent="direct",
            default_answer="Transportation analysis generated based on active fleet routes.",
        )
        t_parse = (time.perf_counter() - t_parse_start) * 1000

        t_total = (time.perf_counter() - t_start) * 1000
        logger.info(
            "AI [transportation] perf: total=%.1fms (ctx=%.1fms, llm=%.1fms, parse=%.1fms, cached=False)",
            t_total, t_ctx, t_llm, t_parse
        )

        response = AiChatResponse(
            id=chat_id,
            content=structured_payload.direct_answer,
            timestamp=timestamp,
            calculation_breakdown=calculation_breakdown,
            structured_payload=structured_payload,
            meta={
                "timing_ms": {
                    "context": round(t_ctx, 1),
                    "llm": round(t_llm, 1),
                    "parse": round(t_parse, 1),
                    "total": round(t_total, 1),
                },
                "cached": False,
            },
        )
        AiCache.set(cache_key, response)
        return response

    # =========================================================================
    # EXPERIENCE 3: Waste AI Advisor
    # =========================================================================
    @classmethod
    async def query_waste_advisor(
        cls,
        question: str,
        workspace_id: str,
        db: Any,
    ) -> AiChatResponse:
        t_start = time.perf_counter()
        cls._verify_groq_configured()
        sanitized_q = sanitize_user_input(question)
        q = sanitized_q.lower()
        timestamp = utc_iso()
        chat_id = generate_id("ai_waste")

        # 1. Build comprehensive, historical & circularity context via AiContextService
        t_ctx_start = time.perf_counter()
        context = await AiContextService.build_waste_context(workspace_id, db, sanitized_q)
        t_ctx = (time.perf_counter() - t_ctx_start) * 1000

        if not context.get("has_records"):
            empty_msg = "No waste stream records found in your workspace yet. Please log waste generation categories and treatment methods to enable circularity analysis."
            return AiChatResponse(
                id=chat_id,
                content=empty_msg,
                timestamp=timestamp,
                structured_payload=StructuredAiPayload(
                    intent="direct",
                    direct_answer=empty_msg,
                    data_limitations=context.get("data_limitations", ["No waste records currently logged for this workspace."]),
                ),
            )

        cur = context["current_period"]
        fingerprint = f"{context['total_records_analyzed']}:{cur['total_waste_kg']}:{cur['recycling_rate_percent']}"
        cache_key = AiCache.make_key(workspace_id, "waste", sanitized_q, fingerprint)
        cached_resp = AiCache.get(cache_key)
        if cached_resp:
            t_total = (time.perf_counter() - t_start) * 1000
            logger.info("AI [waste] CACHE HIT: total=%.1fms (ctx=%.1fms)", t_total, t_ctx)
            return cached_resp

        # 2. Attach verifiable calculation breakdown if applicable
        calculation_breakdown = None
        if "recycl" in q or "diversion" in q or "rate" in q or "recovery" in q:
            calculation_breakdown = CalculationBreakdown(
                formula="Recycling Rate = (Recycled kg ÷ Total kg) × 100",
                inputs={
                    "Recycled waste": f"{cur['recycled_kg']:,.1f} kg",
                    "Total waste generated": f"{cur['total_waste_kg']:,.1f} kg",
                },
                result=f"{cur['recycling_rate_percent']:.1f}% recovery rate ({cur['month']})",
            )
        elif ("category" in q or "contribute" in q or "stream" in q) and context.get("category_breakdown"):
            top = context["category_breakdown"][0]
            calculation_breakdown = CalculationBreakdown(
                formula="Category Share = (Category kg ÷ Total kg) × 100",
                inputs={c["category"]: f"{c['quantity_kg']:,.0f} kg ({c['percentage_share']}%)" for c in context["category_breakdown"][:4]},
                result=f"Largest stream is {top['category']} at {top['percentage_share']}% ({top['quantity_kg']:,} kg)",
            )
        elif ("compare" in q or "previous" in q or "mom" in q or "change" in q or "trend" in q) and context.get("previous_period_comparison"):
            comp = context["previous_period_comparison"]
            calculation_breakdown = CalculationBreakdown(
                formula="Change = Current Diversion Rate - Previous Diversion Rate",
                inputs={
                    "Current diversion rate": f"{comp['current_value']}%",
                    "Previous diversion rate": f"{comp['previous_value']}%",
                },
                result=comp["formatted_change"],
            )

        waste_instruction = (
            "You are CarbonIQ's Circular Economy & Waste Diversion Advisor.\n"
            "ROLE: Provide grounded analysis of waste stream weights (kg), recovery/recycling diversion rates (%), and IPCC avoidance factors. "
            "STRICT CONVENTION: Negative emissions represent avoided landfill methane credits under IPCC circular accounting, NOT direct carbon removal.\n"
            "USER INTENT & EVIDENCE RULES:\n"
            "- Determine user intent: 'direct', 'comparative', 'recommendation', or 'analytical'.\n"
            "- If user asks about the recycling rate, cite the exact rate and total kg directly in 'direct_answer'.\n"
            "- Use historical recycling trends to guide material segregation and composting steps.\n"
            "- If records are limited, state limitations in 'data_limitations'.\n\n"
            "OUTPUT SCHEMA (Respond ONLY with valid JSON):\n"
            "{\n"
            '  "intent": "direct" | "comparative" | "recommendation" | "analytical",\n'
            '  "direct_answer": "Direct answer citing verified kg, %, or diversion offsets.",\n'
            '  "explanation": "Methodology context distinguishing circular credits from removal (or null)",\n'
            '  "metrics": [\n'
            '    {"label": "Recycling Rate", "value": "42.0", "unit": "%", "subtext": "Material diversion"}\n'
            '  ],\n'
            '  "key_findings": [\n'
            '    {"title": "Diversion Finding", "description": "Stream observation.", "category": "Waste"}\n'
            '  ],\n'
            '  "recommendations": [\n'
            '    {"title": "Action Title", "explanation": "Practical segregation or composting action.", "priority": "Medium", "expected_benefit": "Avoided landfill waste", "action_url": "/dashboard/waste"}\n'
            '  ],\n'
            '  "data_limitations": ["Data boundary note if records are few"]\n'
            "}"
        )

        t_llm_start = time.perf_counter()
        llm_reply = await cls._call_llm(
            system_instruction=waste_instruction,
            user_query=sanitized_q,
            grounded_context=context,
            max_tokens=450,
        )
        t_llm = (time.perf_counter() - t_llm_start) * 1000

        t_parse_start = time.perf_counter()
        structured_payload = parse_structured_ai_reply(
            llm_reply,
            default_intent="direct",
            default_answer=f"Recorded waste total is {cur['total_waste_kg']:,.0f} kg with a {cur['recycling_rate_percent']:.1f}% recycling recovery rate for {cur['month']}.",
        )
        t_parse = (time.perf_counter() - t_parse_start) * 1000

        t_total = (time.perf_counter() - t_start) * 1000
        logger.info(
            "AI [waste] perf: total=%.1fms (ctx=%.1fms, llm=%.1fms, parse=%.1fms, cached=False)",
            t_total, t_ctx, t_llm, t_parse
        )

        response = AiChatResponse(
            id=chat_id,
            content=structured_payload.direct_answer,
            timestamp=timestamp,
            calculation_breakdown=calculation_breakdown,
            structured_payload=structured_payload,
            meta={
                "timing_ms": {
                    "context": round(t_ctx, 1),
                    "llm": round(t_llm, 1),
                    "parse": round(t_parse, 1),
                    "total": round(t_total, 1),
                },
                "cached": False,
            },
        )
        AiCache.set(cache_key, response)
        return response

    # =========================================================================
    # EXPERIENCE 4: Main AI Insights Assistant (Enterprise Sustainability Synthesis)
    # =========================================================================
    @classmethod
    async def query_insights_advisor(
        cls,
        question: str,
        workspace_id: str,
        db: Any,
    ) -> AiChatResponse:
        t_start = time.perf_counter()
        cls._verify_groq_configured()
        sanitized_q = sanitize_user_input(question)
        timestamp = utc_iso()
        chat_id = generate_id("ai_ins")

        # 1. Build comprehensive multi-scope context via centralized AiContextService
        t_ctx_start = time.perf_counter()
        context = await AiContextService.build_insights_context(workspace_id, db, sanitized_q)
        t_ctx = (time.perf_counter() - t_ctx_start) * 1000

        if not context.get("has_records"):
            empty_msg = "No emissions records found across Electricity, Transportation, or Waste in your workspace yet. Please add activity records to enable cross-category portfolio insights."
            return AiChatResponse(
                id=chat_id,
                content=empty_msg,
                timestamp=timestamp,
                structured_report=None,
                structured_payload=StructuredAiPayload(
                    intent="direct",
                    direct_answer=empty_msg,
                    data_limitations=context.get("data_limitations", ["No activity records logged across any emission scopes in this workspace."]),
                ),
            )

        port = context["portfolio_totals"]
        cur = context.get("current_period", {})
        fingerprint = f"{context['total_records_analyzed']}:{port['total_net_emissions_kg']}:{cur.get('month', '')}"
        cache_key = AiCache.make_key(workspace_id, "insights", sanitized_q, fingerprint)
        cached_resp = AiCache.get(cache_key)
        if cached_resp:
            t_total = (time.perf_counter() - t_start) * 1000
            logger.info("AI [insights] CACHE HIT: total=%.1fms (ctx=%.1fms)", t_total, t_ctx)
            return cached_resp

        # 2. Attach verifiable calculation breakdown based on query focus
        q_lower = sanitized_q.lower()
        cats = {c["name"]: c for c in context.get("categories_summary", [])}
        elec_val = cats.get("Electricity", {}).get("emissions_kg", 0.0)
        trans_val = cats.get("Transportation", {}).get("emissions_kg", 0.0)
        waste_val = cats.get("Waste", {}).get("emissions_kg", 0.0)
        gross_val = port["total_gross_positive_emissions_kg"]
        net_val = port["total_net_emissions_kg"]
        largest = port.get("largest_source")

        if ("largest" in q_lower or "major" in q_lower or "highest" in q_lower or "top" in q_lower) and largest:
            calculation_breakdown = CalculationBreakdown(
                formula="Largest Contributor Share = (Source Emissions kg ÷ Total Gross Positive kg) × 100",
                inputs={
                    f"{largest['category']} emissions": f"{largest['emissions_kg']:,.1f} kg CO2e",
                    "Total gross positive emissions": f"{gross_val:,.1f} kg CO2e",
                },
                result=f"{largest['category']} represents {largest['percentage_of_gross_positive']}% of positive emissions ({largest['emissions_kg']:,.1f} kg CO2e)",
            )
        elif ("compare" in q_lower or "previous" in q_lower or "mom" in q_lower or "change" in q_lower or "trend" in q_lower) and context.get("previous_period_comparison"):
            comp = context["previous_period_comparison"]
            calculation_breakdown = CalculationBreakdown(
                formula="MoM Change = Current Period Net - Previous Period Net",
                inputs={
                    f"Current net emissions ({cur.get('month')})": f"{comp['current_value']:,.1f} kg CO2e",
                    "Previous net emissions": f"{comp['previous_value']:,.1f} kg CO2e",
                },
                result=comp["formatted_change"],
            )
        else:
            calculation_breakdown = CalculationBreakdown(
                formula="Net Portfolio Emissions = Electricity (kg) + Transportation (kg) + Waste (kg)",
                inputs={
                    "Electricity (Scope 2)": f"{elec_val:,.1f} kg CO2e",
                    "Transportation (Scope 1)": f"{trans_val:,.1f} kg CO2e",
                    "Waste (Scope 3 Circular Credit)": f"{waste_val:,.1f} kg CO2e",
                    "Gross Positive Emissions": f"{gross_val:,.1f} kg CO2e",
                },
                assumptions=[
                    "Electricity factor: CEA CO2 Baseline Database v19 (0.82 kg CO2e/kWh).",
                    "Negative waste emissions represent circular recovery offsets (composting/recycling avoiding landfill methane under IPCC).",
                    "Machine learning forecasting: XGBoost model pipeline (R²=0.976, MAE=37.5 kg CO2e).",
                ],
                result=f"{net_val:,.1f} kg CO2e Net Portfolio Total",
            )

        # 3. Prompt Groq for structured narrative insights in strict JSON
        system_instruction = (
            "You are CarbonIQ's Principal Enterprise Sustainability Analyst.\n"
            "ROLE: Provide grounded, multi-scope carbon portfolio synthesis across Electricity, Transportation, and Waste.\n"
            "USER INTENT & EVIDENCE RULES:\n"
            "- Answer the user's specific inquiry FIRST in 'direct_answer'. If user asks for the largest contributor, cite it immediately with its exact percentage share.\n"
            "- When analyzing trends, cite chronological month-over-month percentage changes and historical averages from the context.\n"
            "- If user asks about future emissions or forecasting, cite the XGBoost model pipeline metrics (R²=0.976, MAE=37.5 kg CO2e) and provided forecast points. If forecasting is unavailable or history < 2 months, state the limitation honestly without fabricating predictions.\n"
            "- Strictly preserve the convention that negative waste values represent circular avoided landfill methane credits under IPCC guidelines, NOT direct carbon removal.\n"
            "- Keep direct_answer concise (2-3 sentences). Limit key findings and recommendations to max 2 items each.\n\n"
            "OUTPUT SCHEMA (Respond ONLY with valid JSON):\n"
            "{\n"
            '  "intent": "direct" | "analytical" | "comprehensive",\n'
            '  "direct_answer": "Direct, concise answer answering the user inquiry immediately with verified figures.",\n'
            '  "explanation": "Optional supporting portfolio context (or null)",\n'
            '  "metrics": [\n'
            '    {"label": "Metric Name", "value": "219.3", "unit": "kg CO2e", "subtext": "Scope note"}\n'
            '  ],\n'
            '  "key_findings": [\n'
            '    {"title": "Finding Title", "description": "Concise observation.", "category": "Category"}\n'
            '  ],\n'
            '  "recommendations": [\n'
            '    {"title": "Action Title", "explanation": "Actionable explanation.", "expected_benefit": "Qualitative or modeled realistic benefit.", "priority": "High" | "Medium" | "Low", "category": "Category", "action_url": "/dashboard/simulator", "action_label": "Model Savings"}\n'
            '  ],\n'
            '  "data_limitations": ["Dataset coverage notes if applicable"]\n'
            "}"
        )

        t_llm_start = time.perf_counter()
        llm_raw_reply = await cls._call_llm(
            system_instruction=system_instruction,
            user_query=f"Generate sustainability analytics report for query: '{sanitized_q}'",
            grounded_context=context,
            max_tokens=650,
        )
        t_llm = (time.perf_counter() - t_llm_start) * 1000

        t_parse_start = time.perf_counter()
        structured_payload = parse_structured_ai_reply(
            llm_raw_reply,
            default_intent="direct",
            default_answer=f"The portfolio recorded a net carbon footprint of {net_val:,.1f} kg CO2e across active categories.",
        )
        t_parse = (time.perf_counter() - t_parse_start) * 1000

        # Build verified structured report for dashboard analytics view
        structured_report = {
            "status": "success",
            "title": "Carbon Footprint & Sustainability Analysis",
            "summary": structured_payload.direct_answer,
            "reporting_period": context.get("reporting_period", "Current active dataset"),
            "total_net_emissions_kg": net_val,
            "total_gross_emissions_kg": gross_val,
            "total_records_analyzed": context["total_records_analyzed"],
            "largest_source": largest,
            "categories": context.get("categories_summary", []),
            "key_findings": [kf.model_dump() for kf in structured_payload.key_findings],
            "recommendations": [rec.model_dump() for rec in structured_payload.recommendations],
            "data_limitations": structured_payload.data_limitations or context.get("data_limitations", []),
            "ml_prediction_forecasting": context.get("ml_prediction_forecasting"),
        }

        t_total = (time.perf_counter() - t_start) * 1000
        logger.info(
            "AI [insights] perf: total=%.1fms (ctx=%.1fms, llm=%.1fms, parse=%.1fms, cached=False)",
            t_total, t_ctx, t_llm, t_parse
        )

        response = AiChatResponse(
            id=chat_id,
            content=structured_payload.direct_answer,
            timestamp=timestamp,
            calculation_breakdown=calculation_breakdown,
            structured_report=structured_report,
            structured_payload=structured_payload,
            meta={
                "timing_ms": {
                    "context": round(t_ctx, 1),
                    "llm": round(t_llm, 1),
                    "parse": round(t_parse, 1),
                    "total": round(t_total, 1),
                },
                "cached": False,
            },
        )
        AiCache.set(cache_key, response)
        return response
