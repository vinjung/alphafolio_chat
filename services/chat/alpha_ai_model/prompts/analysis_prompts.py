# services/chat/alpha_ai_model/prompts/analysis_prompts.py
"""
Analysis Prompts for Alpha AI Phase 5

Contains all prompts for:
- News analysis and summarization
- Investment analysis
- Cause analysis
- Disclaimer templates
- Response formatting utilities
"""
from typing import Dict, Any, List, Optional
from datetime import datetime


# =============================================================================
# SECTION 1: NEWS ANALYSIS PROMPTS
# =============================================================================

NEWS_SUMMARY_PROMPT = """You are a financial news analyst. Summarize the following news articles concisely.

## News Articles
{news_items}

## Instructions
1. Identify the main themes across all articles
2. Highlight key facts and figures
3. Note any conflicting information
4. Summarize in 3-5 bullet points
5. Use Korean language

## Summary Format
- Main theme: [핵심 주제]
- Key points:
  * [요점 1]
  * [요점 2]
  * [요점 3]
- Market implications: [시장 영향]
"""

NEWS_SENTIMENT_PROMPT = """Analyze the sentiment of the following news articles about {stock_name}.

## News Articles
{news_items}

## Instructions
1. Classify overall sentiment: POSITIVE / NEUTRAL / NEGATIVE
2. Identify sentiment drivers (what caused the sentiment)
3. Assess reliability of sources
4. Rate confidence level (HIGH / MEDIUM / LOW)

## Response Format (Korean)
- Overall Sentiment: [감성]
- Confidence: [신뢰도]
- Key Drivers:
  * [요인 1]: [긍정/부정] - [설명]
  * [요인 2]: [긍정/부정] - [설명]
- Summary: [종합 의견]
"""

NEWS_EVENT_EXTRACTION_PROMPT = """Extract key events from the following news that may impact {stock_name}.

## News Articles
{news_items}

## Instructions
1. Identify specific events (earnings, product launches, regulations, etc.)
2. Classify event type and potential impact
3. Note event dates if mentioned
4. Assess impact magnitude (HIGH / MEDIUM / LOW)

## Response Format (Korean)
| Event | Type | Date | Impact | Description |
|-------|------|------|--------|-------------|
| [이벤트] | [유형] | [날짜] | [영향] | [설명] |
"""


# -----------------------------------------------------------------------------
# 1.4 QUICK SENTIMENT ANALYSIS (Fast tagging for news items)
# -----------------------------------------------------------------------------

QUICK_SENTIMENT_PROMPT = """Analyze sentiment of the following news headlines for investment decisions.
Respond ONLY with valid JSON array, no explanation.

## Headlines
{headlines}

## Rules
1. POSITIVE: Good for stock price (earnings beat, new contracts, upgrades)
2. NEGATIVE: Bad for stock price (lawsuits, downgrades, losses, recalls)
3. NEUTRAL: No clear impact (routine announcements, general news)
4. Confidence: 0.0 (guess) to 1.0 (certain)

## Output Format (JSON array only)
[
  {{"index": 0, "sentiment": "POSITIVE", "confidence": 0.85, "keywords": ["earnings", "beat"]}},
  {{"index": 1, "sentiment": "NEGATIVE", "confidence": 0.70, "keywords": ["lawsuit"]}}
]
"""

AGGREGATE_SENTIMENT_PROMPT = """Summarize overall market sentiment for {stock_name} based on analyzed news.

## Individual News Sentiments
{sentiment_data}

## Instructions
1. Determine overall sentiment direction
2. Weight by confidence and recency
3. Identify dominant themes

## Output Format (Korean, exactly this structure)
### 종합 감성 분석

**전체 감성**: [POSITIVE/NEGATIVE/NEUTRAL]
**신뢰도**: [HIGH/MEDIUM/LOW]
**분석 근거**:
- 긍정 요인: [요인들]
- 부정 요인: [요인들]

**투자 시사점**: [1-2문장 요약]
"""


# =============================================================================
# SECTION 2: INVESTMENT ANALYSIS PROMPTS
# =============================================================================

CAUSE_ANALYSIS_PROMPT = """You are a financial analyst. Analyze the causes of {stock_name}'s price movement.

## Question
{question}

## Quantitative Data (Database)
{db_results}

## Recent News
{news_summary}

## Recent Disclosures
{disclosure_summary}

## Instructions
1. Identify primary causes of price movement
2. Separate internal factors (company-specific) from external factors (market/macro)
3. Assess the weight of each factor
4. Provide evidence for each cause
5. Use Korean language
6. Compare quantitative metrics to relevant benchmarks (market index, sector average)
7. Provide specific comparative numbers, not just "high/low" labels
   - GOOD: "변동성 24.5%로 코스피 평균(18%) 대비 약 6.5%p 높은 수준"
   - BAD: "변동성 24.5%로 리스크가 높습니다"
8. Consider sector characteristics when interpreting volatility and returns

## Response Format
### 주가 변동 원인 분석

#### 1. 내부 요인 (기업 관련)
- [요인 1]: [설명] (영향도: 높음/중간/낮음)
- [요인 2]: [설명] (영향도: 높음/중간/낮음)

#### 2. 외부 요인 (시장/매크로)
- [요인 1]: [설명] (영향도: 높음/중간/낮음)
- [요인 2]: [설명] (영향도: 높음/중간/낮음)

#### 3. 종합 분석
[종합적인 원인 분석 및 향후 전망]

{disclaimer}
"""

PORTFOLIO_RECOMMENDATION_PROMPT = """You are a portfolio advisor. Create a portfolio recommendation based on user preferences.

## User Profile
- Investment Style: {investment_style}  (conservative/moderate/aggressive)
- Investment Horizon: {investment_horizon}  (short/medium/long term)
- Risk Tolerance: {risk_tolerance}

## Available Data
{stock_data}

## Instructions
1. Select appropriate stocks based on user profile
2. Suggest allocation percentages
3. Explain selection rationale for each stock
4. Include risk factors
5. Use Korean language

## Response Format
### 맞춤형 포트폴리오 추천

#### 투자 성향 요약
- 투자 스타일: {investment_style}
- 투자 기간: {investment_horizon}
- 위험 허용도: {risk_tolerance}

#### 추천 포트폴리오

| 종목 | 비중 | 선정 이유 | 리스크 |
|------|------|-----------|--------|
| [종목1] | [%] | [이유] | [리스크] |
| [종목2] | [%] | [이유] | [리스크] |

#### 포트폴리오 특성
- 예상 수익률: [범위]
- 예상 변동성: [수준]
- 주요 리스크: [설명]

{disclaimer}
"""

TIMING_ANALYSIS_PROMPT = """Analyze potential entry/exit points based on technical and fundamental data.

## Stock: {stock_name} ({stock_code})

## Technical Data
{technical_data}

## Fundamental Data
{fundamental_data}

## Recent News Context
{news_context}

## Instructions
1. Analyze current technical position (support/resistance, indicators)
2. Assess fundamental valuation
3. Consider news/event catalysts
4. Provide scenario-based analysis (not direct recommendations)
5. Use Korean language

## Response Format
### 기술적/펀더멘털 분석

#### 1. 기술적 분석
- 현재 위치: [지지/저항 대비 위치]
- 주요 지표:
  * RSI: [수치] - [해석]
  * MACD: [상태] - [해석]
  * 이동평균: [배열] - [해석]

#### 2. 펀더멘털 분석
- 밸류에이션: [PER/PBR 등 평가]
- 재무 상태: [요약]

#### 3. 시나리오 분석
- 상승 시나리오: [조건] -> [예상 움직임]
- 하락 시나리오: [조건] -> [예상 움직임]
- 횡보 시나리오: [조건] -> [예상 움직임]

#### 4. 주요 모니터링 포인트
- [포인트 1]
- [포인트 2]
- [포인트 3]

{disclaimer}
"""

ANALYST_OPINION_SUMMARY_PROMPT = """Summarize analyst opinions and research reports for {stock_name}.

## Research Report Data
{report_data}

## Instructions
1. Aggregate target prices (average, high, low)
2. Summarize investment opinions distribution
3. Identify consensus view and outliers
4. Note recent opinion changes
5. Use Korean language

## Response Format
### 애널리스트 의견 종합

#### 1. 목표가 분포
- 평균 목표가: [금액]원
- 최고 목표가: [금액]원 ([증권사])
- 최저 목표가: [금액]원 ([증권사])
- 현재가 대비: [상승여력]%

#### 2. 투자의견 분포
- 매수: [N]건
- 중립: [N]건
- 매도: [N]건

#### 3. 최근 의견 변화
| 날짜 | 증권사 | 변경 전 | 변경 후 | 목표가 |
|------|--------|---------|---------|--------|

#### 4. 컨센서스 요약
[주요 논점 및 투자 포인트 요약]
"""

CROSS_MARKET_ANALYSIS_PROMPT = """Analyze {stock_name} from both domestic and global perspectives.

## Domestic (Korean) News/Analysis
{domestic_data}

## Global (English) News/Analysis
{global_data}

## Instructions
1. Compare domestic vs global sentiment
2. Identify perspective differences
3. Note information gaps between markets
4. Synthesize a balanced view
5. Use Korean language

## Response Format
### 국내외 시각 비교 분석

#### 1. 국내 시각
- 주요 관점: [요약]
- 감성: [긍정/중립/부정]
- 핵심 논점: [포인트들]

#### 2. 글로벌 시각
- 주요 관점: [요약]
- 감성: [긍정/중립/부정]
- 핵심 논점: [포인트들]

#### 3. 시각 차이 분석
| 항목 | 국내 | 글로벌 | 차이점 |
|------|------|--------|--------|

#### 4. 종합 분석
[균형 잡힌 종합 의견]
"""


# =============================================================================
# SECTION 3: DISCLAIMER TEMPLATES
# =============================================================================

DISCLAIMER_INVESTMENT = """
---
**투자 유의사항**
- 본 정보는 투자 참고용이며, 투자 권유가 아닙니다.
- 투자 결정은 본인의 판단과 책임 하에 이루어져야 합니다.
- 과거 수익률이 미래 수익을 보장하지 않습니다.
- 투자 전 전문가 상담을 권장합니다.
"""

DISCLAIMER_FORECAST = """
---
**예측 관련 유의사항**
- 본 분석은 현재 데이터 기반 예측이며, 실제 결과와 다를 수 있습니다.
- 시장 상황 변화에 따라 전망이 변경될 수 있습니다.
- 예측 정보를 투자의 유일한 근거로 사용하지 마십시오.
"""

DISCLAIMER_NEWS_ANALYSIS = """
---
**뉴스 분석 유의사항**
- 뉴스 요약은 AI가 생성한 것으로, 원문 확인을 권장합니다.
- 감성 분석은 참고용이며, 실제 시장 반응과 다를 수 있습니다.
"""

DISCLAIMER_RECOMMENDATION = """
---
**추천 관련 유의사항**
- 본 추천은 일반적인 정보 제공 목적이며, 개인 맞춤 투자 조언이 아닙니다.
- 개인의 재정 상황, 투자 목표에 따라 적합성이 다를 수 있습니다.
- 투자 손실의 책임은 투자자 본인에게 있습니다.
- 금융투자상품은 원금 손실이 발생할 수 있습니다.
"""

DISCLAIMER_TIMING = """
---
**매매 시점 관련 유의사항**
- 본 분석은 기술적/펀더멘털 분석에 기반한 참고 정보입니다.
- 특정 시점의 매수/매도를 권유하는 것이 아닙니다.
- 시장 상황은 급변할 수 있으며, 분석 시점과 실제 거래 시점의 괴리가 있을 수 있습니다.
"""


def get_disclaimer(disclaimer_type: str) -> str:
    """
    Get appropriate disclaimer based on type

    Args:
        disclaimer_type: Type of disclaimer needed

    Returns:
        Disclaimer text
    """
    disclaimers = {
        "investment": DISCLAIMER_INVESTMENT,
        "forecast": DISCLAIMER_FORECAST,
        "news": DISCLAIMER_NEWS_ANALYSIS,
        "recommendation": DISCLAIMER_RECOMMENDATION,
        "timing": DISCLAIMER_TIMING,
        "default": DISCLAIMER_INVESTMENT
    }
    return disclaimers.get(disclaimer_type, DISCLAIMER_INVESTMENT)


# =============================================================================
# SECTION 4: RESPONSE FORMATTING UTILITIES
# =============================================================================

def format_news_for_prompt(news_items: List[Dict[str, Any]], max_items: int = 5) -> str:
    """
    Format news items for inclusion in prompts

    Args:
        news_items: List of news dictionaries
        max_items: Maximum items to include

    Returns:
        Formatted string
    """
    if not news_items:
        return "No news data available."

    lines = []
    for i, item in enumerate(news_items[:max_items], 1):
        title = item.get("title", "No title")
        date = item.get("pub_date", item.get("date", ""))
        snippet = item.get("description", item.get("snippet", ""))[:300]
        source = item.get("source", item.get("_source", ""))

        lines.append(f"### Article {i}")
        lines.append(f"- Title: {title}")
        if date:
            lines.append(f"- Date: {date}")
        if source:
            lines.append(f"- Source: {source}")
        if snippet:
            lines.append(f"- Content: {snippet}")
        lines.append("")

    return "\n".join(lines)


def format_disclosure_for_prompt(disclosures: List[Dict[str, Any]], max_items: int = 5) -> str:
    """
    Format disclosure items for inclusion in prompts

    Args:
        disclosures: List of disclosure dictionaries
        max_items: Maximum items to include

    Returns:
        Formatted string
    """
    if not disclosures:
        return "No disclosure data available."

    lines = []
    for i, item in enumerate(disclosures[:max_items], 1):
        report_name = item.get("report_name", "No title")
        date = item.get("rcept_dt", "")
        corp_name = item.get("corp_name", "")
        disc_type = item.get("disclosure_type_name", "")

        lines.append(f"{i}. [{disc_type}] {report_name}")
        lines.append(f"   - Company: {corp_name}, Date: {date}")

    return "\n".join(lines)


def format_db_results_for_prompt(
    results: List[Dict[str, Any]],
    max_rows: int = 10,
    max_cols: int = 8
) -> str:
    """
    Format database results as markdown table for prompts.

    Prioritizes most recent rows (tail) so LLM analyzes current data.
    Includes a summary header with total row count and date range when available.

    Args:
        results: Query results
        max_rows: Maximum rows to include
        max_cols: Maximum columns to include

    Returns:
        Formatted markdown table with summary header
    """
    if not results:
        return "No database results."

    total_rows = len(results)

    # Get columns (limit to max_cols)
    all_cols = list(results[0].keys())
    cols = all_cols[:max_cols]

    # Summary header: total rows + date range if date column exists
    summary_parts = [f"Total rows: {total_rows}"]
    date_col = None
    for col_name in ["date", "trade_date", "trading_date", "base_date"]:
        if col_name in all_cols:
            date_col = col_name
            break
    if date_col:
        first_date = str(results[0].get(date_col, ""))
        last_date = str(results[-1].get(date_col, ""))
        summary_parts.append(f"Date range: {first_date} ~ {last_date}")

    lines = [f"[{', '.join(summary_parts)}]"]

    # Build header
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("|" + "|".join(["---"] * len(cols)) + "|")

    # Use most recent rows (tail) so LLM focuses on current data
    display_rows = results[-max_rows:] if total_rows > max_rows else results

    if total_rows > max_rows:
        lines.append(f"| *... {total_rows - max_rows} older rows omitted ...* |")

    # Build rows
    for row in display_rows:
        values = []
        for col in cols:
            val = str(row.get(col, ""))
            # Truncate long values
            if len(val) > 30:
                val = val[:27] + "..."
            values.append(val)
        lines.append("| " + " | ".join(values) + " |")

    return "\n".join(lines)


def format_technical_data(indicators: Dict[str, Any]) -> str:
    """
    Format technical indicator data for prompts

    Args:
        indicators: Technical indicators dictionary

    Returns:
        Formatted string
    """
    if not indicators:
        return "No technical data available."

    lines = ["### Technical Indicators"]

    indicator_names = {
        "rsi": "RSI (14)",
        "macd": "MACD",
        "macd_signal": "MACD Signal",
        "macd_hist": "MACD Histogram",
        "bb_upper": "Bollinger Upper",
        "bb_middle": "Bollinger Middle",
        "bb_lower": "Bollinger Lower",
        "ma5": "MA 5",
        "ma20": "MA 20",
        "ma60": "MA 60",
        "ma120": "MA 120"
    }

    for key, name in indicator_names.items():
        if key in indicators:
            value = indicators[key]
            if isinstance(value, float):
                value = f"{value:.2f}"
            lines.append(f"- {name}: {value}")

    return "\n".join(lines)


def build_analysis_prompt(
    prompt_template: str,
    question: str,
    db_results: List[Dict] = None,
    news_data: List[Dict] = None,
    disclosure_data: List[Dict] = None,
    stock_name: str = None,
    stock_code: str = None,
    disclaimer_type: str = "investment",
    **kwargs
) -> str:
    """
    Build a complete analysis prompt with all components

    Args:
        prompt_template: Base prompt template
        question: User's question
        db_results: Database query results
        news_data: News data
        disclosure_data: Disclosure data
        stock_name: Stock name
        stock_code: Stock code
        disclaimer_type: Type of disclaimer to include
        **kwargs: Additional template variables

    Returns:
        Complete prompt string
    """
    # Format data components
    db_formatted = format_db_results_for_prompt(db_results) if db_results else "No data"
    news_formatted = format_news_for_prompt(news_data) if news_data else "No news"
    disclosure_formatted = format_disclosure_for_prompt(disclosure_data) if disclosure_data else "No disclosures"
    disclaimer = get_disclaimer(disclaimer_type)

    # Build substitution dict
    subs = {
        "question": question,
        "db_results": db_formatted,
        "news_summary": news_formatted,
        "news_items": news_formatted,
        "disclosure_summary": disclosure_formatted,
        "stock_name": stock_name or "Unknown",
        "stock_code": stock_code or "",
        "disclaimer": disclaimer,
        **kwargs
    }

    # Substitute template
    try:
        return prompt_template.format(**subs)
    except KeyError as e:
        # Return template with available substitutions
        for key, value in subs.items():
            prompt_template = prompt_template.replace("{" + key + "}", str(value))
        return prompt_template


# =============================================================================
# SECTION 5: PROMPT SELECTOR
# =============================================================================

def get_analysis_prompt(
    analysis_type: str,
    **kwargs
) -> str:
    """
    Get the appropriate analysis prompt based on type

    Args:
        analysis_type: Type of analysis needed
        **kwargs: Variables for prompt template

    Returns:
        Complete prompt string
    """
    prompt_map = {
        "news_summary": NEWS_SUMMARY_PROMPT,
        "news_sentiment": NEWS_SENTIMENT_PROMPT,
        "news_events": NEWS_EVENT_EXTRACTION_PROMPT,
        "cause_analysis": CAUSE_ANALYSIS_PROMPT,
        "portfolio": PORTFOLIO_RECOMMENDATION_PROMPT,
        "timing": TIMING_ANALYSIS_PROMPT,
        "analyst_opinion": ANALYST_OPINION_SUMMARY_PROMPT,
        "cross_market": CROSS_MARKET_ANALYSIS_PROMPT,
        "strategy": INVESTMENT_STRATEGY_TEMPLATE["template"],
    }

    template = prompt_map.get(analysis_type, CAUSE_ANALYSIS_PROMPT)

    # Determine disclaimer type
    disclaimer_type_map = {
        "news_summary": "news",
        "news_sentiment": "news",
        "cause_analysis": "forecast",
        "portfolio": "recommendation",
        "timing": "timing",
        "analyst_opinion": "investment"
    }
    disclaimer_type = disclaimer_type_map.get(analysis_type, "investment")

    return build_analysis_prompt(
        prompt_template=template,
        disclaimer_type=disclaimer_type,
        **kwargs
    )


# =============================================================================
# SECTION 6: RESPONSE TEMPLATES (모범 답안 템플릿)
# =============================================================================
"""
Response Templates for Alpha AI

각 질문 유형별 모범 답안 템플릿.
LLM이 SQL 실행 결과 + 외부 데이터를 기반으로
금융 전문가 수준의 응답을 생성하도록 가이드.

템플릿 변수:
- {result_table}: SQL 실행 결과 테이블
- {summary}: 데이터 요약
- {interpretation}: 해석/분석
- {news_context}: 뉴스/외부 데이터 컨텍스트
- {disclaimer}: 면책 조항
"""

# -----------------------------------------------------------------------------
# 6.1 SIMPLE QUERY TEMPLATES (단순 조회)
# -----------------------------------------------------------------------------

SIMPLE_QUERY_TEMPLATES: Dict[str, Dict[str, str]] = {
    "stock_price": {
        "name": "종목 현재가 조회",
        "template": """## {stock_name} 현재 시세

**기준 시점**: {timestamp}

| 항목 | 값 |
|------|-----|
| 현재가 | {close:,}원 |
| 전일대비 | {change:+,}원 ({change_rate:+.2f}%) |
| 거래량 | {volume:,}주 |
| 거래대금 | {trading_value_billion:.0f}억원 |

{interpretation}

{disclaimer}"""
    },
    "stock_price_detail": {
        "name": "종목 상세 시세",
        "template": """## {stock_name} ({symbol}) 상세 시세

**기준 시점**: {timestamp}

### 가격 정보
| 항목 | 값 |
|------|-----|
| 현재가 | {close:,}원 |
| 시가 | {open:,}원 |
| 고가 | {high:,}원 |
| 저가 | {low:,}원 |
| 전일대비 | {change:+,}원 ({change_rate:+.2f}%) |

### 거래 정보
| 항목 | 값 |
|------|-----|
| 거래량 | {volume:,}주 |
| 거래대금 | {trading_value_billion:.0f}억원 |
| 시가총액 | {market_cap_trillion:.1f}조원 |

{interpretation}

{disclaimer}"""
    },
    "market_cap": {
        "name": "시가총액 조회",
        "template": """## {stock_name} 시가총액

**기준 시점**: {timestamp}

| 항목 | 값 |
|------|-----|
| 시가총액 | {market_cap_trillion:.2f}조원 |
| 현재가 | {close:,}원 |
| 발행주식수 | {shares:,}주 |

**시총 순위**: 코스피/코스닥 {rank}위

{disclaimer}"""
    },
}

# -----------------------------------------------------------------------------
# 6.2 RANKING TEMPLATES (랭킹/정렬)
# -----------------------------------------------------------------------------

RANKING_TEMPLATES: Dict[str, Dict[str, str]] = {
    "trading_value_top": {
        "name": "거래대금 상위 종목",
        "template": """## 거래대금 상위 {limit}개 종목

**기준**: {timestamp} | 시장: {market}

{result_table}

### 해석
- 상위 종목은 대형주 중심으로 기관/외국인 참여도가 높은 종목
- 거래대금 집중 = 시장 관심도 및 유동성 지표
- 단기 트레이딩 관점에서 슬리피지 리스크 낮음

{news_context}

{disclaimer}"""
    },
    "trading_value_avg": {
        "name": "N일 평균 거래대금 상위",
        "template": """## {days}일 평균 거래대금 상위 {limit}개 종목

**기준**: {timestamp} | 시장: {market}
**지표**: 최근 {days}거래일 일별 거래대금 평균

{result_table}

### 해석
- 평균 거래대금은 일시적 급등락을 제외한 지속적 관심 종목 파악에 유용
- 상위권 = 기관/외국인의 꾸준한 매매 참여
- 유동성 안정 구간으로 중장기 투자에도 적합

{disclaimer}"""
    },
    "market_cap_top": {
        "name": "시가총액 상위 종목",
        "template": """## 시가총액 상위 {limit}개 종목

**기준**: {timestamp} | 시장: {market}

{result_table}

### 해석
- 대형주 중심 포트폴리오 구성 시 참고
- 시총 상위 = 시장 대표 지수 영향력 큼
- 기관 벤치마크 종목군

{disclaimer}"""
    },
    "volume_top": {
        "name": "거래량 상위 종목",
        "template": """## 거래량 상위 {limit}개 종목

**기준**: {timestamp} | 시장: {market}

{result_table}

### 해석
- 거래량 급증 = 시장 이슈 또는 수급 변화 신호
- 저가주 포함 가능성 있으므로 거래대금과 함께 확인 권장
- 단기 모멘텀 트레이딩 후보군

{news_context}

{disclaimer}"""
    },
    "change_rate_top": {
        "name": "상승률 상위 종목",
        "template": """## 상승률 상위 {limit}개 종목

**기준**: {timestamp} | 시장: {market}

{result_table}

### 해석
- 당일 강세 종목으로 단기 모멘텀 확인
- 상한가 근접 종목은 다음날 갭 리스크 존재
- 테마/이슈 관련 뉴스 확인 필요

{news_context}

{disclaimer}"""
    },
    "change_rate_bottom": {
        "name": "하락률 상위 종목",
        "template": """## 하락률 상위 {limit}개 종목

**기준**: {timestamp} | 시장: {market}

{result_table}

### 해석
- 급락 종목은 악재 확인 필수
- 기술적 반등 가능성과 펀더멘털 훼손 구분 필요
- 저가 매수 전 원인 분석 권장

{news_context}

{disclaimer}"""
    },
}

# -----------------------------------------------------------------------------
# 6.3 FILTER TEMPLATES (필터링)
# -----------------------------------------------------------------------------

FILTER_TEMPLATES: Dict[str, Dict[str, str]] = {
    "market_cap_filter": {
        "name": "시가총액 필터",
        "template": """## 시가총액 {condition} 종목

**필터 조건**: 시가총액 {operator} {threshold_display}
**기준**: {timestamp} | 시장: {market}
**결과**: 총 {count}개 종목

{result_table}

### 해석
- {cap_category} 기준 필터링 결과
- 대형주: 안정성 높음, 변동성 낮음
- 중소형주: 성장 잠재력, 변동성 높음

{disclaimer}"""
    },
    "trading_value_filter": {
        "name": "거래대금 필터",
        "template": """## 거래대금 {condition} 종목

**필터 조건**: 거래대금 {operator} {threshold_display}
**기준**: {timestamp} | 시장: {market}
**결과**: 총 {count}개 종목

{result_table}

### 해석
- 유동성 기준 필터링으로 실제 매매 가능 종목 선별
- 거래대금 충분 = 슬리피지 최소화
- 기관/외국인 매매 가능 종목군

{disclaimer}"""
    },
    "change_rate_filter": {
        "name": "등락률 필터",
        "template": """## 등락률 {condition} 종목

**필터 조건**: 등락률 {operator} {threshold}%
**기준**: {timestamp} | 시장: {market}
**결과**: 총 {count}개 종목

{result_table}

### 해석
- 당일 강세/약세 종목 필터링
- 급등주: 추격 매수 주의, 차익 실현 매물 대기 가능
- 급락주: 원인 분석 후 접근 권장

{news_context}

{disclaimer}"""
    },
}

# -----------------------------------------------------------------------------
# 6.4 TECHNICAL INDICATOR TEMPLATES (기술적 지표)
# -----------------------------------------------------------------------------

TECHNICAL_TEMPLATES: Dict[str, Dict[str, str]] = {
    "rsi_oversold": {
        "name": "RSI 과매도 종목",
        "template": """## RSI 과매도 구간 종목 (RSI < 30)

**기준**: {timestamp} | 시장: {market}
**지표**: RSI(14) 30 미만

{result_table}

### 기술적 해석
- RSI 30 이하 = 과매도 구간, 기술적 반등 가능성
- 단, 추세적 하락 중인 종목은 추가 하락 가능
- 거래량 반등 동반 시 신뢰도 상승

### 활용 전략
- 분할 매수 접근 권장
- 손절 기준: 직전 저점 이탈 시
- 목표: 20일선 또는 RSI 50 회복

{disclaimer}"""
    },
    "rsi_overbought": {
        "name": "RSI 과매수 종목",
        "template": """## RSI 과매수 구간 종목 (RSI > 70)

**기준**: {timestamp} | 시장: {market}
**지표**: RSI(14) 70 초과

{result_table}

### 기술적 해석
- RSI 70 이상 = 과매수 구간, 조정 가능성
- 강한 상승 추세에서는 80 이상도 지속 가능
- 다이버전스 발생 시 주의 필요

### 활용 전략
- 신규 매수 자제, 보유자는 일부 차익 실현 고려
- 추세 강도 확인: 거래량, MACD 동반 확인

{disclaimer}"""
    },
    "macd_golden_cross": {
        "name": "MACD 골든크로스",
        "template": """## MACD 골든크로스 발생 종목

**기준**: {timestamp} | 시장: {market}
**조건**: MACD > Signal Line, Histogram > 0

{result_table}

### 기술적 해석
- MACD 골든크로스 = 단기 추세 상승 전환 신호
- 0선 위에서 발생 시 신뢰도 상승
- 거래량 증가 동반 시 강한 신호

### 활용 전략
- 추세 전환 초기 진입 후보
- 손절 기준: Signal Line 재이탈
- 목표: 직전 고점 또는 저항선

{disclaimer}"""
    },
    "bollinger_upper_break": {
        "name": "볼린저밴드 상단 돌파",
        "template": """## 볼린저밴드 상단 돌파 종목

**기준**: {timestamp} | 시장: {market}
**조건**: 종가 > 볼린저밴드 상단 (20일, 2표준편차)

{result_table}

### 기술적 해석
- 상단 돌파 = 강한 상승 모멘텀 또는 과열 신호
- 추세 지속 시 밴드워크(Band Walk) 가능
- 거래량 급증 동반 시 추세 강화

### 활용 전략
- 추세 추종 매매 후보
- 단, 밴드 내 복귀 시 단기 조정 가능
- 중심선(20MA) 지지 여부 모니터링

{disclaimer}"""
    },
    "bollinger_lower_break": {
        "name": "볼린저밴드 하단 이탈",
        "template": """## 볼린저밴드 하단 이탈 종목

**기준**: {timestamp} | 시장: {market}
**조건**: 종가 < 볼린저밴드 하단 (20일, 2표준편차)

{result_table}

### 기술적 해석
- 하단 이탈 = 과매도 또는 강한 하락 추세
- 반등 시 중심선(20MA)이 1차 저항
- 밴드 수축 후 확장 시 방향성 주목

### 활용 전략
- 역추세 매매 시 분할 접근
- 추세 하락 중이면 추가 하락 가능
- 거래량 반등 확인 후 진입

{disclaimer}"""
    },
    "ma_alignment_bullish": {
        "name": "이동평균선 정배열",
        "template": """## 이동평균선 정배열 종목

**기준**: {timestamp} | 시장: {market}
**조건**: 5MA > 20MA > 60MA (> 120MA)

{result_table}

### 기술적 해석
- 정배열 = 단기/중기/장기 모두 상승 추세
- 가장 강한 상승 추세 신호 중 하나
- 눌림목 발생 시 매수 기회

### 활용 전략
- 추세 추종 매매에 적합
- 5일선 지지 확인 후 진입
- 20일선 이탈 시 추세 약화 경계

{disclaimer}"""
    },
    "ma_alignment_bearish": {
        "name": "이동평균선 역배열",
        "template": """## 이동평균선 역배열 종목

**기준**: {timestamp} | 시장: {market}
**조건**: 종가 < 5MA < 20MA < 60MA < 120MA

{result_table}

### 기술적 해석
- 역배열 = 전형적인 하락 추세 구간
- 반등 시도해도 이평선이 저항으로 작용
- 추세 전환까지 상당 시간 소요 가능

### 활용 전략
- 매수 자제, 관망 권장
- 단기 이격 과대 시 기술적 반등 가능
- 정배열 전환 시까지 본격 매수 보류

{disclaimer}"""
    },
    "multi_indicator_bullish": {
        "name": "복합 기술적 지표 강세",
        "template": """## 복합 기술적 지표 강세 종목

**기준**: {timestamp} | 시장: {market}
**조건**: MACD 골든크로스 + RSI 30~70 + 볼린저 중단 돌파

{result_table}

### 기술적 해석
- 다중 지표 동시 강세 = 높은 신뢰도
- 과열 전 단계에서 추세 전환 포착
- 거래량 증가 시 모멘텀 강화

### 활용 전략
- 단기 진입 후보로 적합
- 손절: 20일선 이탈
- 목표: 최근 고점 재시험

{disclaimer}"""
    },
}

# -----------------------------------------------------------------------------
# 6.5 COMPLEX FILTER TEMPLATES (복합 조건)
# -----------------------------------------------------------------------------

COMPLEX_TEMPLATES: Dict[str, Dict[str, str]] = {
    "cap_and_rsi": {
        "name": "시총 + RSI 복합",
        "template": """## 시총 {cap_condition} + RSI 과매도 종목

**필터 조건**:
- 시가총액: {cap_threshold_display} 이상
- RSI(14): 30 미만

**기준**: {timestamp} | 시장: {market}
**결과**: {count}개 종목

{result_table}

### 해석
- 대형주 중 기술적 과매도 구간 종목
- 펀더멘털 안정성 + 기술적 반등 기대
- 단기 저점 매수 후보

### 활용 전략
- 분할 매수로 리스크 관리
- 거래량 반등 동반 시 신뢰도 상승
- 목표: RSI 50 회복 또는 20일선

{disclaimer}"""
    },
    "trading_and_rsi": {
        "name": "거래대금 + RSI 복합",
        "template": """## 거래대금 {value_threshold_display} 이상 + RSI 과매도

**필터 조건**:
- 거래대금: {value_threshold_display} 이상
- RSI(14): 30 미만

**기준**: {timestamp} | 시장: {market}
**결과**: {count}개 종목

{result_table}

### 해석
- 유동성 확보 + 과매도 = 기술적 반등 기대
- 기관/외국인 매매 가능한 종목군
- 실제 매매 시 슬리피지 최소화

{disclaimer}"""
    },
    "cap_macd_golden": {
        "name": "대형주 MACD 골든크로스",
        "template": """## 대형주 MACD 골든크로스

**필터 조건**:
- 시가총액: {cap_threshold_display} 이상
- MACD > Signal Line

**기준**: {timestamp} | 시장: {market}
**결과**: {count}개 종목

{result_table}

### 해석
- 대형주의 추세 전환 신호
- 시장 전체 방향성 가늠에 참고
- 기관 매수세 유입 가능성

{disclaimer}"""
    },
    "multi_condition": {
        "name": "다중 조건 필터",
        "template": """## 다중 조건 필터 결과

**필터 조건**:
{conditions_list}

**기준**: {timestamp} | 시장: {market}
**결과**: {count}개 종목

{result_table}

### 해석
{interpretation}

### 활용 전략
{strategy}

{disclaimer}"""
    },
}

# -----------------------------------------------------------------------------
# 6.6 INVESTOR FLOW TEMPLATES (투자자 동향)
# -----------------------------------------------------------------------------

INVESTOR_TEMPLATES: Dict[str, Dict[str, str]] = {
    "foreign_net_buy": {
        "name": "외국인 순매수 상위",
        "template": """## 외국인 순매수 상위 {limit}개 종목

**기준**: {timestamp} | 시장: {market}

{result_table}

### 수급 해석
- 외국인 순매수 = 글로벌 자금 유입 신호
- 대형주 중심 매수 시 지수 상승 기대
- 환율 변동과 연계하여 해석 필요

### 투자 시사점
- 외국인 매수 지속 시 추세 강화
- 단, 차익 실현 매물 출회 가능성 상존
- 보유 비중 상한 근접 종목 주의

{disclaimer}"""
    },
    "institution_net_buy": {
        "name": "기관 순매수 상위",
        "template": """## 기관 순매수 상위 {limit}개 종목

**기준**: {timestamp} | 시장: {market}

{result_table}

### 수급 해석
- 기관 순매수 = 펀드/연기금 등 국내 기관 수요
- 실적 시즌 전후 포지션 조정 가능성
- 장기 투자 관점의 매수세

### 투자 시사점
- 기관 매수 = 펀더멘털 기반 접근
- 프로그램 매매와 구분 필요
- 지속적 순매수 시 주가 상승 지지력

{disclaimer}"""
    },
    "foreign_institution_both": {
        "name": "외국인+기관 동반 순매수",
        "template": """## 외국인+기관 동반 순매수 종목

**기준**: {timestamp} | 시장: {market}
**조건**: 외국인 순매수 > 0 AND 기관 순매수 > 0

{result_table}

### 수급 해석
- 쌍끌이 매수 = 가장 강한 수급 신호
- 기관과 외국인 동시 관심 = 컨센서스 형성
- 주가 상승 확률 높은 패턴

### 투자 시사점
- 추세 추종 매매에 적합
- 수급 반전 시점 모니터링 필요
- 단기 급등 후 차익 매물 주의

{disclaimer}"""
    },
    "foreign_net_sell": {
        "name": "외국인 순매도 상위",
        "template": """## 외국인 순매도 상위 {limit}개 종목

**기준**: {timestamp} | 시장: {market}

{result_table}

### 수급 해석
- 외국인 순매도 = 글로벌 자금 이탈 신호
- 환율 상승기에 매도세 강화 경향
- 업종 전반 리스크 오프 가능성

### 투자 시사점
- 신규 매수 신중, 기존 보유자 리스크 관리
- 순매도 지속 기간과 규모 확인 필요
- 펀더멘털 변화 없으면 역발상 매수 기회일 수도

{disclaimer}"""
    },
}

# -----------------------------------------------------------------------------
# 6.7 QUANT GRADE TEMPLATES (퀀트 분석)
# -----------------------------------------------------------------------------

INVESTMENT_STRATEGY_TEMPLATE = {
    "name": "투자 전략 시나리오 분석",
    "template": """**핵심 결론: {final_grade}** (종합점수 {final_score}/100, {signal_overall})

---

## {stock_name} 투자 전략 분석

**퀀트 등급**: {final_grade} (점수: {final_score}/100)
**종합 신호**: {signal_overall}
**시장 상태**: {market_state}

### 시나리오별 분석

**1. 상승 시나리오 (확률: {scenario_bullish_prob}%)**
- 예상 수익률: {scenario_bullish_return}
- 목표가: 현재가 기준 +{take_profit_pct}%
- 매수 트리거:
{buy_triggers_formatted}

**2. 횡보 시나리오 (확률: {scenario_sideways_prob}%)**
- 예상 수익률: {scenario_sideways_return}
- 관망 트리거:
{hold_triggers_formatted}

**3. 하락 시나리오 (확률: {scenario_bearish_prob}%)**
- 예상 수익률: {scenario_bearish_return}
- 손절가: 현재가 기준 {stop_loss_pct}%
- 매도 트리거:
{sell_triggers_formatted}

### 운영 전략
- 진입 타이밍 점수: {entry_timing_score}/100
- 리스크/리워드 비율: {risk_reward_ratio}
- 권장 포지션 비중: {position_size_pct}%
- 리스크 프로파일: {risk_profile_text}

{disclaimer}"""
}

QUANT_TEMPLATES: Dict[str, Dict[str, str]] = {
    "total_grade_top": {
        "name": "퀀트 종합등급 상위",
        "template": """## 퀀트 종합등급 상위 종목

**기준**: {timestamp}
**조건**: 종합등급 {grade_condition}

{result_table}

### 퀀트 분석 해석
- 종합등급 = 가치/성장/모멘텀/퀄리티 종합 평가
- A등급 이상 = 다수 팩터에서 우수
- 계량적 관점의 투자 후보

### 팩터별 특성
- 가치(Value): 저평가 매력
- 성장(Growth): 실적 성장성
- 모멘텀(Momentum): 주가 추세
- 퀄리티(Quality): 재무 안정성

{disclaimer}"""
    },
    "value_grade_top": {
        "name": "가치주 등급 상위",
        "template": """## 가치주 등급 상위 종목

**기준**: {timestamp}
**조건**: 가치등급 {grade_condition}

{result_table}

### 가치 팩터 해석
- PER, PBR, PCR 등 밸류에이션 지표 종합
- 저평가 = 안전마진 확보
- 가치 함정(Value Trap) 구분 필요

### 투자 시사점
- 중장기 투자에 적합
- 실적 개선 동반 시 리레이팅 기대
- 저평가 지속 이유 확인 필요

{disclaimer}"""
    },
    "momentum_grade_top": {
        "name": "모멘텀 등급 상위",
        "template": """## 모멘텀 등급 상위 종목

**기준**: {timestamp}
**조건**: 모멘텀등급 {grade_condition}

{result_table}

### 모멘텀 팩터 해석
- 최근 수익률, 추세 강도, 상대강도 종합
- 강한 모멘텀 = 추세 지속 기대
- 단, 과열 구간 진입 가능성 체크

### 투자 시사점
- 추세 추종 전략에 적합
- 모멘텀 약화 시 신속한 대응 필요
- 기술적 지표와 함께 활용

{disclaimer}"""
    },
    "quality_value_both": {
        "name": "퀄리티+가치 복합",
        "template": """## 퀄리티+가치 동시 우수 종목

**기준**: {timestamp}
**조건**: 퀄리티등급 A 이상 AND 가치등급 A 이상

{result_table}

### 복합 팩터 해석
- 재무 안정성 + 저평가 = 보수적 투자 최적
- 워런 버핏 스타일 가치투자 후보
- 장기 보유 시 안정적 성과 기대

### 투자 시사점
- 시장 하락기 방어력 우수
- 배당 투자와 병행 가능
- 성장성은 상대적으로 제한적일 수 있음

{disclaimer}"""
    },
    "investment_strategy": INVESTMENT_STRATEGY_TEMPLATE,
}

# -----------------------------------------------------------------------------
# 6.8 MARKET INDEX TEMPLATES (시장 지수)
# -----------------------------------------------------------------------------

MARKET_TEMPLATES: Dict[str, Dict[str, str]] = {
    "kospi_index": {
        "name": "코스피 지수",
        "template": """## 코스피 지수 현황

**기준**: {timestamp}

| 항목 | 값 |
|------|-----|
| 현재 지수 | {close:,.2f} |
| 전일대비 | {change:+,.2f} ({change_rate:+.2f}%) |
| 거래량 | {volume:,}주 |
| 거래대금 | {trading_value_trillion:.1f}조원 |

### 시장 동향
{market_comment}

{disclaimer}"""
    },
    "kosdaq_index": {
        "name": "코스닥 지수",
        "template": """## 코스닥 지수 현황

**기준**: {timestamp}

| 항목 | 값 |
|------|-----|
| 현재 지수 | {close:,.2f} |
| 전일대비 | {change:+,.2f} ({change_rate:+.2f}%) |
| 거래량 | {volume:,}주 |
| 거래대금 | {trading_value_trillion:.1f}조원 |

### 시장 동향
{market_comment}

{disclaimer}"""
    },
    "us_index": {
        "name": "미국 지수",
        "template": """## 미국 주요 지수 현황

**기준**: {timestamp} (현지시간)

| 지수 | 현재가 | 등락률 |
|------|--------|--------|
| 나스닥 | {nasdaq:,.2f} | {nasdaq_change:+.2f}% |
| S&P 500 | {sp500:,.2f} | {sp500_change:+.2f}% |
| 다우존스 | {dow:,.2f} | {dow_change:+.2f}% |

### 시장 동향
{market_comment}

{disclaimer}"""
    },
    "index_history": {
        "name": "지수 추이",
        "template": """## {index_name} 최근 {days}일 추이

**기준**: {timestamp}

{result_table}

### 추세 분석
- 기간 등락률: {period_change:+.2f}%
- 최고점: {high_point:,.2f} ({high_date})
- 최저점: {low_point:,.2f} ({low_date})

{interpretation}

{disclaimer}"""
    },
}

# -----------------------------------------------------------------------------
# 6.9 US STOCK TEMPLATES (미국 주식)
# -----------------------------------------------------------------------------

US_STOCK_TEMPLATES: Dict[str, Dict[str, str]] = {
    "us_stock_price": {
        "name": "미국 종목 시세",
        "template": """## {stock_name} ({symbol}) 현재 시세

**기준**: {timestamp} (현지시간)

| 항목 | 값 |
|------|-----|
| 현재가 | ${close:,.2f} |
| 전일대비 | ${change:+,.2f} ({change_percent:+.2f}%) |
| 거래량 | {volume:,}주 |
| 52주 최고 | ${high_52w:,.2f} |
| 52주 최저 | ${low_52w:,.2f} |

{interpretation}

{disclaimer}"""
    },
    "us_volume_top": {
        "name": "미국 거래량 상위",
        "template": """## 미국 거래량 상위 {limit}개 종목

**기준**: {timestamp} (현지시간)

{result_table}

### 해석
- 거래량 상위 = 시장 관심 집중 종목
- 실적 발표, 뉴스 이벤트 확인 필요
- 옵션 만기 등 수급 이벤트 체크

{disclaimer}"""
    },
    "us_technical": {
        "name": "미국 기술적 지표",
        "template": """## 미국 {condition} 종목

**기준**: {timestamp} (현지시간)
**조건**: {indicator_condition}

{result_table}

### 기술적 해석
{technical_interpretation}

{disclaimer}"""
    },
}

# -----------------------------------------------------------------------------
# 6.10 MACRO ECONOMIC TEMPLATES (거시경제)
# -----------------------------------------------------------------------------

MACRO_TEMPLATES: Dict[str, Dict[str, str]] = {
    "fed_rate": {
        "name": "미국 기준금리",
        "template": """## 미국 연방기금 금리 (Fed Funds Rate)

**기준**: {timestamp}

| 항목 | 값 |
|------|-----|
| 현재 금리 | {rate:.2f}% |
| 목표 범위 | {target_low:.2f}% ~ {target_high:.2f}% |
| 직전 변경 | {last_change_date} ({last_change:+.2f}%p) |

### 시장 영향
{interpretation}

### 향후 전망
- 다음 FOMC: {next_fomc_date}
- 시장 예상: {market_expectation}

{disclaimer}"""
    },
    "treasury_yield": {
        "name": "미국 국채 금리",
        "template": """## 미국 국채 금리 현황

**기준**: {timestamp}

| 만기 | 금리 | 전일대비 |
|------|------|----------|
| 2년물 | {yield_2y:.3f}% | {change_2y:+.3f}%p |
| 10년물 | {yield_10y:.3f}% | {change_10y:+.3f}%p |
| 30년물 | {yield_30y:.3f}% | {change_30y:+.3f}%p |

### 장단기 금리차
- 10Y-2Y 스프레드: {spread_10y2y:.3f}%p

### 시장 함의
{interpretation}

{disclaimer}"""
    },
    "us_cpi": {
        "name": "미국 소비자물가",
        "template": """## 미국 소비자물가지수 (CPI)

**기준**: {timestamp} 발표

| 항목 | 값 | 전월대비 |
|------|-----|----------|
| CPI (YoY) | {cpi_yoy:.1f}% | {cpi_change:+.1f}%p |
| Core CPI (YoY) | {core_cpi_yoy:.1f}% | {core_change:+.1f}%p |

### 인플레이션 해석
{interpretation}

### 연준 정책 영향
{fed_implication}

{disclaimer}"""
    },
    "unemployment": {
        "name": "미국 실업률",
        "template": """## 미국 실업률

**기준**: {timestamp} 발표

| 항목 | 값 |
|------|-----|
| 실업률 | {unemployment_rate:.1f}% |
| 비농업 고용 증감 | {nonfarm_payroll:+,}명 |
| 경제활동참가율 | {participation_rate:.1f}% |

### 고용시장 해석
{interpretation}

### 시장 영향
{market_implication}

{disclaimer}"""
    },
    "vix_index": {
        "name": "VIX 지수",
        "template": """## VIX 지수 (공포지수)

**기준**: {timestamp}

| 항목 | 값 |
|------|-----|
| 현재 VIX | {vix:.2f} |
| 전일대비 | {change:+.2f} ({change_percent:+.2f}%) |
| 20일 평균 | {avg_20d:.2f} |

### VIX 해석 기준
- 12 미만: 극도의 낙관 (주의)
- 12~20: 정상 범위
- 20~30: 불안 확대
- 30 이상: 공포 구간

### 현재 상태
{interpretation}

{disclaimer}"""
    },
}


# =============================================================================
# SECTION 6.5: SENTIMENT ANALYSIS UTILITIES
# =============================================================================

import json
import re


async def analyze_news_sentiment(
    news_items: List[Dict[str, Any]],
    stock_name: str = None,
    provider: str = None,
    model: str = None
) -> Dict[str, Any]:
    """
    Analyze sentiment of news items using LLM.

    Args:
        news_items: List of news dictionaries with 'title' field
        stock_name: Stock name for context
        provider: LLM provider
        model: Model name

    Returns:
        Dict with overall sentiment and tagged items:
        {
            "overall": "POSITIVE",
            "confidence": "HIGH",
            "positive_count": 3,
            "negative_count": 1,
            "neutral_count": 2,
            "items": [news items with sentiment field added]
        }
    """
    if not news_items:
        return {
            "overall": "NEUTRAL",
            "confidence": "LOW",
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "items": []
        }

    try:
        # Import LLM here to avoid circular imports
        from core.llm.factory import get_llm, LLMProvider

        # Get LLM
        llm_provider = LLMProvider(provider) if provider else LLMProvider.ANTHROPIC
        llm = get_llm(llm_provider, model_name=model)

        # Extract headlines for analysis
        headlines = []
        for i, item in enumerate(news_items[:15]):  # Limit to 15 items
            title = item.get("title", item.get("headline", ""))
            if title:
                headlines.append(f"{i}. {title}")

        if not headlines:
            return {
                "overall": "NEUTRAL",
                "confidence": "LOW",
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "items": news_items
            }

        # Create prompt
        prompt = QUICK_SENTIMENT_PROMPT.format(headlines="\n".join(headlines))

        # Get LLM response
        response = await llm.ainvoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)

        # Parse JSON response
        sentiment_results = _parse_sentiment_response(response_text)

        # Apply sentiment to news items
        tagged_items = []
        positive_count = 0
        negative_count = 0
        neutral_count = 0

        for i, item in enumerate(news_items):
            tagged_item = item.copy()

            # Find matching sentiment result
            sentiment_data = next(
                (s for s in sentiment_results if s.get("index") == i),
                {"sentiment": "NEUTRAL", "confidence": 0.5, "keywords": []}
            )

            tagged_item["sentiment"] = sentiment_data.get("sentiment", "NEUTRAL")
            tagged_item["sentiment_confidence"] = sentiment_data.get("confidence", 0.5)
            tagged_item["sentiment_keywords"] = sentiment_data.get("keywords", [])

            # Count sentiments
            if tagged_item["sentiment"] == "POSITIVE":
                positive_count += 1
            elif tagged_item["sentiment"] == "NEGATIVE":
                negative_count += 1
            else:
                neutral_count += 1

            tagged_items.append(tagged_item)

        # Determine overall sentiment
        overall, confidence = _calculate_overall_sentiment(
            positive_count, negative_count, neutral_count
        )

        return {
            "overall": overall,
            "confidence": confidence,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "items": tagged_items
        }

    except Exception as e:
        # Log error and return neutral sentiment
        import logging
        logging.warning(f"[SentimentAnalysis] Error: {e}")

        # Return original items without sentiment
        return {
            "overall": "NEUTRAL",
            "confidence": "LOW",
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "items": news_items,
            "error": str(e)
        }


def _parse_sentiment_response(response_text: str) -> List[Dict[str, Any]]:
    """
    Parse LLM sentiment response to extract JSON array.

    Args:
        response_text: Raw LLM response

    Returns:
        List of sentiment dictionaries
    """
    try:
        # Try to extract JSON array from response
        text = response_text.strip()

        # Find JSON array pattern
        json_match = re.search(r'\[[\s\S]*\]', text)
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)

        # Try parsing entire response as JSON
        return json.loads(text)

    except (json.JSONDecodeError, AttributeError):
        return []


def _calculate_overall_sentiment(
    positive: int,
    negative: int,
    neutral: int
) -> tuple:
    """
    Calculate overall sentiment from counts.

    Args:
        positive: Count of positive items
        negative: Count of negative items
        neutral: Count of neutral items

    Returns:
        Tuple of (overall_sentiment, confidence)
    """
    total = positive + negative + neutral
    if total == 0:
        return "NEUTRAL", "LOW"

    # Calculate ratios
    pos_ratio = positive / total
    neg_ratio = negative / total

    # Determine overall sentiment
    if pos_ratio > 0.5:
        overall = "POSITIVE"
        confidence = "HIGH" if pos_ratio > 0.7 else "MEDIUM"
    elif neg_ratio > 0.5:
        overall = "NEGATIVE"
        confidence = "HIGH" if neg_ratio > 0.7 else "MEDIUM"
    elif pos_ratio > neg_ratio:
        overall = "POSITIVE"
        confidence = "LOW"
    elif neg_ratio > pos_ratio:
        overall = "NEGATIVE"
        confidence = "LOW"
    else:
        overall = "NEUTRAL"
        confidence = "MEDIUM" if neutral / total > 0.5 else "LOW"

    return overall, confidence


def format_sentiment_for_response(sentiment_result: Dict[str, Any]) -> str:
    """
    Format sentiment analysis result for inclusion in response.

    Args:
        sentiment_result: Result from analyze_news_sentiment

    Returns:
        Formatted Korean string
    """
    if not sentiment_result:
        return ""

    overall = sentiment_result.get("overall", "NEUTRAL")
    confidence = sentiment_result.get("confidence", "LOW")
    pos = sentiment_result.get("positive_count", 0)
    neg = sentiment_result.get("negative_count", 0)
    neu = sentiment_result.get("neutral_count", 0)

    sentiment_kr = {
        "POSITIVE": "긍정적",
        "NEGATIVE": "부정적",
        "NEUTRAL": "중립"
    }

    confidence_kr = {
        "HIGH": "높음",
        "MEDIUM": "보통",
        "LOW": "낮음"
    }

    lines = [
        "### 뉴스 감성 분석",
        f"- **전체 감성**: {sentiment_kr.get(overall, overall)}",
        f"- **신뢰도**: {confidence_kr.get(confidence, confidence)}",
        f"- **분포**: 긍정 {pos}건 / 부정 {neg}건 / 중립 {neu}건"
    ]

    return "\n".join(lines)


# =============================================================================
# SECTION 7: RESPONSE TEMPLATE UTILITIES
# =============================================================================

# All templates combined for easy access
ALL_RESPONSE_TEMPLATES: Dict[str, Dict[str, Dict[str, str]]] = {
    "simple_query": SIMPLE_QUERY_TEMPLATES,
    "ranking": RANKING_TEMPLATES,
    "filter": FILTER_TEMPLATES,
    "technical": TECHNICAL_TEMPLATES,
    "complex": COMPLEX_TEMPLATES,
    "investor": INVESTOR_TEMPLATES,
    "quant": QUANT_TEMPLATES,
    "market": MARKET_TEMPLATES,
    "us_stock": US_STOCK_TEMPLATES,
    "macro": MACRO_TEMPLATES,
}

# Intent to template category mapping
INTENT_TO_TEMPLATE_CATEGORY: Dict[str, str] = {
    # Simple queries
    "query": "simple_query",
    "price": "simple_query",
    "stock_info": "simple_query",

    # Ranking
    "ranking": "ranking",
    "top": "ranking",
    "bottom": "ranking",

    # Filtering
    "filter": "filter",
    "condition": "filter",
    "screening": "filter",

    # Technical analysis
    "technical": "technical",
    "indicator": "technical",
    "rsi": "technical",
    "macd": "technical",
    "bollinger": "technical",
    "ma": "technical",

    # Complex queries
    "complex": "complex",
    "multi_condition": "complex",
    "analysis": "complex",

    # Investor flow
    "investor": "investor",
    "foreign": "investor",
    "institution": "investor",
    "supply_demand": "investor",

    # Quant
    "quant": "quant",
    "grade": "quant",
    "factor": "quant",
    "strategy": "quant",

    # Market
    "market": "market",
    "index": "market",
    "kospi": "market",
    "kosdaq": "market",

    # US stocks
    "us_stock": "us_stock",
    "nasdaq": "us_stock",
    "nyse": "us_stock",

    # Macro
    "macro": "macro",
    "fed": "macro",
    "treasury": "macro",
    "cpi": "macro",
    "unemployment": "macro",
    "vix": "macro",
}


def get_response_template(
    category: str,
    template_key: str
) -> Optional[Dict[str, str]]:
    """
    Get a specific response template

    Args:
        category: Template category (ranking, technical, etc.)
        template_key: Specific template key within the category

    Returns:
        Template dict with 'name' and 'template' keys, or None if not found
    """
    category_templates = ALL_RESPONSE_TEMPLATES.get(category)
    if not category_templates:
        return None

    return category_templates.get(template_key)


def get_template_by_intent(
    intent: str,
    sub_type: Optional[str] = None
) -> Optional[Dict[str, str]]:
    """
    Get response template based on detected intent

    Args:
        intent: User intent (ranking, technical, etc.)
        sub_type: Specific sub-type within the intent (e.g., 'rsi_oversold')

    Returns:
        Template dict or None
    """
    # investment_strategy is intent-agnostic: always resolve from QUANT_TEMPLATES
    if sub_type == "investment_strategy":
        return QUANT_TEMPLATES.get("investment_strategy")

    category = INTENT_TO_TEMPLATE_CATEGORY.get(intent.lower(), "simple_query")
    category_templates = ALL_RESPONSE_TEMPLATES.get(category, {})

    if sub_type and sub_type in category_templates:
        return category_templates[sub_type]

    # Return first template in category as default
    if category_templates:
        first_key = list(category_templates.keys())[0]
        return category_templates[first_key]

    return None


def list_available_templates(category: Optional[str] = None) -> Dict[str, List[str]]:
    """
    List all available response templates

    Args:
        category: Optional category filter

    Returns:
        Dict mapping categories to list of template keys
    """
    if category:
        templates = ALL_RESPONSE_TEMPLATES.get(category, {})
        return {category: list(templates.keys())}

    return {
        cat: list(templates.keys())
        for cat, templates in ALL_RESPONSE_TEMPLATES.items()
    }


def format_response_with_template(
    template_key: str,
    category: str,
    data: Dict[str, Any],
    include_disclaimer: bool = True,
    disclaimer_type: str = "investment"
) -> str:
    """
    Format a response using a template and provided data

    Args:
        template_key: Specific template to use
        category: Template category
        data: Data to fill into template
        include_disclaimer: Whether to include disclaimer
        disclaimer_type: Type of disclaimer to include

    Returns:
        Formatted response string
    """
    template_info = get_response_template(category, template_key)
    if not template_info:
        return f"Template not found: {category}/{template_key}"

    template = template_info.get("template", "")

    # Add disclaimer if needed
    if include_disclaimer:
        data["disclaimer"] = get_disclaimer(disclaimer_type)
    else:
        data["disclaimer"] = ""

    # Add timestamp if not present (KST for Korean market hours)
    if "timestamp" not in data:
        from datetime import timezone, timedelta
        KST = timezone(timedelta(hours=9))
        data["timestamp"] = datetime.now(KST).strftime("%Y-%m-%d %H:%M")

    # Try to format with provided data
    try:
        return template.format(**data)
    except KeyError as e:
        # Return template with available substitutions
        result = template
        for key, value in data.items():
            placeholder = "{" + key + "}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        return result


def build_hybrid_response(
    db_data: Dict[str, Any],
    external_data: Dict[str, Any],
    template_category: str,
    template_key: str,
    analysis_type: str = "cause_analysis"
) -> str:
    """
    Build a hybrid response combining DB data and external API data

    Args:
        db_data: Data from PostgreSQL (quantitative)
        external_data: Data from external APIs (qualitative)
        template_category: Response template category
        template_key: Specific template to use
        analysis_type: Type of analysis for prompt selection

    Returns:
        Complete formatted response
    """
    # Merge data sources
    combined_data = {**db_data}

    # Format DB results as table
    if "query_results" in db_data:
        combined_data["result_table"] = format_db_results_for_prompt(
            db_data["query_results"]
        )

    # Add news context if available
    if "news" in external_data:
        combined_data["news_context"] = format_news_for_prompt(
            external_data["news"]
        )
    else:
        combined_data["news_context"] = ""

    # Add interpretation placeholder for LLM to fill
    if "interpretation" not in combined_data:
        combined_data["interpretation"] = ""

    # Format using template
    return format_response_with_template(
        template_key=template_key,
        category=template_category,
        data=combined_data,
        include_disclaimer=True,
        disclaimer_type="investment"
    )


# Template statistics
TEMPLATE_STATS = {
    "total_templates": sum(
        len(templates) for templates in ALL_RESPONSE_TEMPLATES.values()
    ),
    "categories": list(ALL_RESPONSE_TEMPLATES.keys()),
    "templates_per_category": {
        cat: len(templates)
        for cat, templates in ALL_RESPONSE_TEMPLATES.items()
    }
}
