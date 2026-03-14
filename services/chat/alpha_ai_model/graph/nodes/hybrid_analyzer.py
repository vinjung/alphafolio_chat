# services/chat/alpha_ai_model/graph/nodes/hybrid_analyzer.py
"""
Hybrid Analyzer Node

Combines database results with external data for comprehensive analysis.
Uses LLM to generate integrated insights from multiple data sources.
Integrates with analysis_prompts.py for templates and formatting.
"""
import asyncio
from typing import Dict, Any, List, Optional
from config import logger

from core.llm.factory import get_llm, LLMProvider

# Import utilities from analysis_prompts
from ...prompts.analysis_prompts import (
    format_db_results_for_prompt,
    format_news_for_prompt,
    format_disclosure_for_prompt,
    build_hybrid_response,
    get_analysis_prompt,
    CAUSE_ANALYSIS_PROMPT,
    CROSS_MARKET_ANALYSIS_PROMPT,
)


# Analysis prompt template (enhanced with template integration)
HYBRID_ANALYSIS_PROMPT = """You are Alpha AI, a professional financial analysis expert.
Analyze the following data and provide a comprehensive response to the user's question.

## User Question
{question}

## Database Results (Quantitative Data)
{db_results}

## News Data (Recent News)
{news_summary}

## Disclosure Data (Corporate Announcements)
{disclosure_summary}

## Analysis Guidelines
1. Start with a direct answer to the user's question
2. Support your answer with quantitative data from the database
3. Add context from recent news and disclosures
4. Identify key factors affecting the stock/market
5. Provide balanced perspective (positive and negative factors)
6. Use clear, professional language
7. Do not use emojis
8. When database results contain scenario data (scenario_bullish_prob, scenario_sideways_prob, scenario_bearish_prob), structure the response as:
   - Quant grade and overall signal first
   - Three scenarios (bullish/sideways/bearish) with probabilities, expected returns
   - Entry/exit strategy (stop_loss, take_profit, entry_timing_score)
   - Buy/sell/hold triggers (from JSONB arrays)
   - Risk profile summary
   Present as "data + interpretation" style - show the numbers first, then explain what they mean.

## Prohibited Expressions (ABSOLUTE BAN)
NEVER use these words/phrases in your response:
- 추천, 권유, 확정, 확실, 무조건, 반드시, 틀림없이, 보장
- "~을 추천합니다", "매수/매도를 권유", "확실히 오릅니다"
- Any expression that implies certainty about future stock performance
Instead use: "~할 가능성이 있습니다", "~를 고려해 볼 수 있습니다", "~로 판단됩니다"

## Data Availability Rules
- If Database Results have data, ANALYZE it. Do NOT say "데이터가 제한적입니다"
- If News Data is available, SUMMARIZE it. Do NOT ignore it
- Only state "데이터 없음" when the data section is genuinely empty
- NEVER claim data limitations when data is actually provided above

{disclaimer_section}

## Response Format
- Use Korean language for the response
- Maximum 3 top-level sections. Be concise (under 1500 characters excluding disclaimer)
- For top-level sections: use "1." "2." "3." numbering
- For sub-items within a section: use "1)" "2)" "3)" format
- NEVER use "1." format for both parent sections and child items
- NEVER use dash (-) for sub-items. Always use "1)" "2)" "3)" numbering
- Include specific numbers and dates
- Do NOT use markdown headers (##), bold (**), or markdown tables

Example format:
1. 선별 종목 현황
1) 삼성전자: 외국인 순매수 지속, 시가총액 1위
2) 셀트리온: 기관 순매수 전환, 변동성 15.1%
2. 리스크 지표 비교
1) VaR 95%: 삼성전자 -3.2%, 셀트리온 -4.1%
2) 샤프비율: 삼성전자 1.2, 셀트리온 0.8
3. 종합 판단
1) 긍정 요인: ...
2) 부정 요인: ...

Please provide your analysis:
"""


# Legal disclaimer (unified across all response paths)
LEGAL_DISCLAIMER = """

---
※ 본 서비스 및 LLM이 제공하는 모든 정보, 분석, 예측, 의견 등은 일반적인 참고용 정보이며, 「자본시장과 금융투자업에 관한 법률」상 투자자문 또는 투자권유에 해당하지 않습니다.
※ 본 서비스는 이용자의 투자 목적, 재산 상황, 투자 경험 등을 고려하지 않으며, 제공되는 정보의 정확성, 완전성, 최신성을 보장하지 않습니다.
※ 과거 데이터나 모형에 기반한 설명 및 예시는 미래 수익률이나 성과를 보장하지 않습니다.
※ 투자에 대한 최종 판단과 그에 따른 손실 및 법적 책임은 전적으로 이용자 본인에게 있으며, 본 서비스 제공자 및 개발자는 이에 대해 어떠한 책임도 지지 않습니다.
"""


def get_disclaimer_for_intent(requires_disclaimer: bool, intent: str) -> str:
    """
    Get legal disclaimer for hybrid analysis responses.

    Always returns the full legal disclaimer regardless of intent or flag.

    Args:
        requires_disclaimer: Unused (kept for backward compatibility)
        intent: Query intent (unused)

    Returns:
        Legal disclaimer text
    """
    return LEGAL_DISCLAIMER


async def hybrid_analyzer(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze combined database and external data

    Uses analysis_prompts.py utilities for formatting and templates.

    Args:
        state: Current graph state with DB results and external data

    Returns:
        Updated state with hybrid analysis
    """
    logger.info("[AlphaAI:HybridAnalyzer] Processing...")

    message = state.get("message", "")
    data_source = state.get("data_source", "db_only")
    intent = state.get("intent", "")

    # Skip if not hybrid mode
    if data_source != "hybrid":
        logger.info("[AlphaAI:HybridAnalyzer] Skipping - not hybrid mode")
        return {
            **state,
            "processing_steps": state.get("processing_steps", []) + ["hybrid_analyzer_skipped"]
        }

    # Get data from state
    query_result = state.get("query_result", [])
    news_data = state.get("news_data", [])
    disclosure_data = state.get("disclosure_data", [])
    requires_disclaimer = state.get("requires_disclaimer", False)

    # Format data using analysis_prompts utilities
    db_results_formatted = format_db_results_for_prompt(query_result, max_rows=10)
    news_summary = format_news_for_prompt(news_data, max_items=5)
    disclosure_summary = format_disclosure_for_prompt(disclosure_data, max_items=5)
    disclaimer = get_disclaimer_for_intent(requires_disclaimer, intent)

    # Build skipped conditions notice if any
    skipped_conditions = state.get("skipped_conditions", [])
    skipped_notice = ""
    if skipped_conditions:
        skipped_items = [sc["question"] for sc in skipped_conditions if sc.get("question")]
        if skipped_items:
            skipped_notice = (
                "\n\n## Note: Incomplete Filter Conditions\n"
                "The following filter conditions could not be applied due to SQL errors. "
                "Mention this limitation in your analysis:\n"
                + "\n".join(f"- {item}" for item in skipped_items)
            )

    # Build prompt
    prompt = HYBRID_ANALYSIS_PROMPT.format(
        question=message,
        db_results=db_results_formatted,
        news_summary=news_summary,
        disclosure_summary=disclosure_summary,
        disclaimer_section=disclaimer
    ) + skipped_notice

    try:
        # Get LLM
        provider = state.get("provider")
        model = state.get("model_name")

        llm_provider = LLMProvider(provider) if provider else LLMProvider.ANTHROPIC
        llm = get_llm(llm_provider, model_name=model)

        # Log prompt details for debugging
        logger.debug(f"[HybridAnalyzer] Prompt length: {len(prompt)} chars")
        logger.debug(f"[HybridAnalyzer] DB results count: {len(query_result)}, News count: {len(news_data)}, Disclosure count: {len(disclosure_data)}")

        # Generate analysis with retry for API errors
        max_api_retries = 2
        response = None
        for attempt in range(max_api_retries + 1):
            try:
                response = await llm.ainvoke(prompt)
                break
            except Exception as e:
                error_str = str(e)
                is_retryable = any(keyword in error_str.lower() for keyword in [
                    "overloaded", "internal server error", "api_error", "rate_limit",
                    "529", "500", "503"
                ])
                if is_retryable and attempt < max_api_retries:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"[HybridAnalyzer] API error (attempt {attempt+1}), retrying in {wait_time}s: {error_str[:100]}")
                    await asyncio.sleep(wait_time)
                    continue
                raise
        analysis = response.content if hasattr(response, 'content') else str(response)

        # Log response details for debugging
        logger.debug(f"[HybridAnalyzer] Response length: {len(analysis)} chars")
        logger.info("[AlphaAI:HybridAnalyzer] Analysis generated successfully")

        return {
            **state,
            "hybrid_analysis": analysis,
            "response": analysis,  # Also set as main response for hybrid mode
            "response_type": "hybrid",
            "processing_steps": state.get("processing_steps", []) + ["hybrid_analyzer"]
        }

    except Exception as e:
        logger.error(f"[AlphaAI:HybridAnalyzer] Error: {e}")

        # Fallback: use build_hybrid_response from analysis_prompts
        try:
            fallback_analysis = build_hybrid_response(
                db_data={"query_results": query_result},
                external_data={"news": news_data},
                template_category="complex",
                template_key="multi_condition"
            )
        except Exception:
            # Ultimate fallback
            fallback_analysis = _generate_fallback_analysis(
                message, query_result, news_data, disclosure_data
            )

        return {
            **state,
            "hybrid_analysis": fallback_analysis,
            "response": fallback_analysis,
            "response_type": "hybrid",
            "processing_steps": state.get("processing_steps", []) + ["hybrid_analyzer_fallback"]
        }


def _generate_fallback_analysis(
    question: str,
    db_results: List[Dict],
    news_data: List[Dict],
    disclosure_data: List[Dict]
) -> str:
    """
    Generate fallback analysis without LLM

    Args:
        question: User question
        db_results: Database results
        news_data: News data
        disclosure_data: Disclosure data

    Returns:
        Basic analysis text
    """
    lines = []

    lines.append("## Analysis Summary\n")

    # DB results summary
    if db_results:
        lines.append(f"### Database Results")
        lines.append(f"Found {len(db_results)} records matching your query.\n")

    # News summary
    if news_data:
        lines.append(f"### Recent News")
        lines.append(f"Found {len(news_data)} related news articles.")
        if news_data:
            lines.append(f"Latest: {news_data[0].get('title', 'N/A')}\n")

    # Disclosure summary
    if disclosure_data:
        lines.append(f"### Recent Disclosures")
        lines.append(f"Found {len(disclosure_data)} recent disclosures.")
        if disclosure_data:
            lines.append(f"Latest: {disclosure_data[0].get('report_name', 'N/A')}\n")

    if not any([db_results, news_data, disclosure_data]):
        lines.append("No data available for analysis.")

    lines.append("\n---")
    lines.append("*Note: This is a basic summary. Full analysis temporarily unavailable.*")

    return "\n".join(lines)
