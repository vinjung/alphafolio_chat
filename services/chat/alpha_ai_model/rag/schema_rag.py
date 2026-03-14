# services/chat/alpha_ai_model/rag/schema_rag.py
"""
Schema RAG for Alpha AI

Retrieves relevant schema information based on user query.
Uses vector similarity search to find relevant tables and columns.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import time
from config import logger

from .vector_store import VectorStore
from ..prompts.sql_prompt import (
    KR_SCHEMAS,
    US_SCHEMAS,
    COMMON_SCHEMAS,
    ALL_SCHEMAS
)


# Korea Standard Time (UTC+9)
KST = timezone(timedelta(hours=9))

# Cache TTL constants (seconds)
CACHE_TTL_MARKET_OPEN = 1800     # 30 minutes during market hours
CACHE_TTL_MARKET_CLOSED = 86400  # 24 hours when market is closed
CACHE_TTL_DEFAULT = 300          # 5 minutes default

# Module-level cache for trading calendar (reset daily at 00:00 KST)
_holiday_cache: Dict[str, Any] = {
    "date": None,        # Cached date (YYYY-MM-DD)
    "is_holiday": None,  # True/False
    "cached_at": None    # Cache timestamp
}


def _get_kst_now() -> datetime:
    """Get current time in KST"""
    return datetime.now(KST)


class SchemaRAG:
    """
    Schema Retrieval-Augmented Generation

    Retrieves relevant database schema information for SQL generation.
    Indexes table schemas and retrieves based on semantic similarity.
    """

    # Korean keywords for each table (prepended to schema content for bilingual embedding)
    TABLE_KOREAN_KEYWORDS: Dict[str, str] = {
        # KR tables
        "kr_intraday": "현재가 종가 시가 고가 저가 거래량 거래대금 시가총액 주가 실시간",
        "kr_intraday_detail": "PER PBR EPS BPS 배당수익률 배당금 주당순이익 주가수익비율",
        "kr_intraday_total": "현재가 종가 시가 고가 저가 거래량 시가총액 PER PBR ROE 배당수익률",
        "kr_indicators": "RSI MACD 볼린저밴드 이동평균 기술적지표 스토캐스틱 MFI ADX OBV ATR VWAP",
        "kr_stock_grade": "퀀트등급 투자등급 종합점수 가치점수 품질점수 모멘텀점수 성장점수 강력매수 매수 매도 샤프비율 변동성 베타 리스크",
        "kr_individual_investor_daily_trading": "외국인 기관 개인 순매수 순매도 투자자별 매매동향",
        "kr_investor_daily_trading": "투자자별 매매 기관 외국인 개인 순매수 순매도",
        "kr_program_daily_trading": "프로그램매매 차익거래 비차익거래",
        "kr_stock_basic": "종목코드 종목명 상장일 시장구분 증권구분 상장주식수",
        "kr_stock_detail": "업종 산업 테마 관련주 반도체 바이오 배터리 AI 소프트웨어 결산월 대표이사 회사정보 theme industry semiconductor",
        "kr_blocktrades": "대량매매 블록딜 대량거래",
        "kr_foreign_ownership": "외국인지분율 외국인보유 외국인한도 외국인투자",
        "kr_financial_position": "재무제표 재무상태표 당기금액 전기금액 재무정보 자산 부채 자본 손익계산서 현금흐름",
        "kr_dividends": "배당 배당금 주당배당 결산기준",
        "kr_largest_shareholder": "최대주주 대주주 지분율 주주현황",
        "kr_stockacquisitiondisposal": "자기주식 자사주 취득 처분 소각",
        "kr_executive": "임원 대표이사 경영진 임원현황 직위",
        "kr_research_reports": "리포트 증권사 목표가 투자의견 애널리스트 리서치",
        "kr_benchmark_index": "벤치마크 지수 코스피 코스닥 선물 금",
        "mv_sector_daily_performance": "섹터성과 업종수익률 섹터모멘텀 섹터순위",
        # US tables
        "us_intraday": "미국주가 실시간 시가 고가 저가 종가",
        "us_daily": "미국주가 일별 종가 등락률 거래량 PER PBR",
        "us_daily_etf": "ETF 상장지수펀드 미국ETF",
        "us_weekly": "미국주가 주간 주봉",
        "us_monthly": "미국주가 월간 월봉",
        "us_indicators": "미국기술적지표 RSI MACD 볼린저밴드 이동평균 ATR VWAP",
        "us_stock_basic": "미국종목정보 회사명 섹터 산업 업종 반도체 바이오 소프트웨어 시가총액 배당 애널리스트 목표가 sector industry semiconductor biotechnology",
        "us_stock_grade": "미국퀀트등급 투자등급 종합점수 가치점수 품질점수 모멘텀점수 성장점수 샤프비율 변동성",
        "us_option": "옵션 콜옵션 풋옵션 델타 감마 세타 베가 내재변동성 행사가",
        "us_option_daily_summary": "옵션요약 풋콜비율 콜거래량 풋거래량 내재변동성 감마익스포저 GEX",
        "us_ipo_calendar": "IPO 상장예정 기업공개 신규상장",
        "us_income_statement": "손익계산서 매출 영업이익 순이익 EBITDA 매출총이익 연구개발비",
        "us_balance_sheet": "재무상태표 자산 부채 자본 현금 재고 유동자산 비유동자산",
        "us_cash_flow": "현금흐름표 영업현금흐름 투자현금흐름 재무현금흐름 자본지출 배당지급",
        "us_earnings_estimates": "실적전망 EPS전망 EPS추정치 EPS추정 매출전망 애널리스트 실적추정 컨센서스 어닝스",
        "us_earnings_calendar": "실적발표 어닝스캘린더 실적일정",
        "us_dividends": "미국배당 배당금 배당락일 배당지급일",
        "us_splits": "주식분할 액면분할 분할비율",
        "us_news": "뉴스 기사 센티먼트 감성분석 sentiment 여론",
        "us_insider_transactions": "내부자거래 인사이더 내부자매수 내부자매도",
        "us_fed_funds_rate": "금리 연방금리 기준금리 Fed금리 이자율 interest rate",
        "us_treasury_yield": "국채금리 국채수익률 미국국채 10년물",
        "us_cpi": "소비자물가 CPI 물가지수 인플레이션",
        "us_unemployment_rate": "실업률 고용 노동시장",
        "us_gdp": "GDP 국내총생산 경제성장률",
        "us_pmi": "PMI 구매관리자지수 제조업지수",
        "us_market_regime": "시장레짐 시장상태 강세장 약세장 중립장",
        "us_vix": "VIX 공포지수 변동성지수 빅스 fear index",
        "us_move_index": "MOVE지수 무브지수 채권변동성",
        "us_dollar_index": "달러인덱스 달러지수 달러가치",
        "us_credit_spread": "신용스프레드 회사채스프레드 크레딧스프레드",
        "us_fed_rrp": "역레포 연준역레포 유동성",
        "us_sector_benchmarks": "섹터벤치마크 섹터밸류에이션 섹터PER 섹터성장률 업종벤치마크 업종비교",
        "mv_us_sector_daily_performance": "미국섹터성과 섹터수익률 섹터모멘텀 섹터순위",
        # Common tables
        "market_index": "코스피 코스닥 나스닥 NYSE 시장지수 주가지수",
        "bok_economic_indicators": "한국경제지표 한국은행 기준금리 GDP 물가 경제심리",
        "exchange_rate": "환율 원달러 원엔 통화",
        "daily_recommendation": "매수추천 추천종목 뭐사 살만한 좋은종목 매수후보 오늘추천 daily pick recommendation",
    }

    def __init__(self, vector_store: Optional[VectorStore] = None):
        """
        Initialize SchemaRAG

        Args:
            vector_store: Vector store instance for similarity search
        """
        self.vector_store = vector_store or VectorStore(
            collection_name="alpha_ai_schema"
        )
        self.initialized = False
        self.schema_cache = {}
        logger.info("[SchemaRAG] Initialized")

    async def _is_kr_market_open(self) -> bool:
        """
        Check if Korean stock market is open

        Uses 24-hour cache for holiday check (reset at 00:00 KST)
        Time check: Mon-Fri 09:30-16:00 KST

        Returns:
            True if market is open, False otherwise
        """
        global _holiday_cache

        now = _get_kst_now()
        today_str = now.strftime("%Y-%m-%d")

        # Check if cache needs refresh (new day or no cache)
        if _holiday_cache["date"] != today_str:
            # Query trading_calendar for today's holiday status
            try:
                from database import db
                if db.pool:
                    async with db.pool.acquire() as conn:
                        row = await conn.fetchrow(
                            "SELECT is_kr_holiday FROM trading_calendar WHERE date = $1",
                            now.date()
                        )
                        is_holiday = row["is_kr_holiday"] if row else False
                else:
                    is_holiday = False
            except Exception as e:
                logger.warning(f"[SchemaRAG] trading_calendar query failed: {e}")
                is_holiday = False

            # Update cache
            _holiday_cache["date"] = today_str
            _holiday_cache["is_holiday"] = is_holiday
            _holiday_cache["cached_at"] = now
            logger.info(f"[SchemaRAG] Holiday cache updated: {today_str}, is_holiday={is_holiday}")

        # If holiday, market is closed
        if _holiday_cache["is_holiday"]:
            return False

        # Check day of week (Mon=0, Sun=6)
        if now.weekday() >= 5:  # Saturday or Sunday
            return False

        # Check time (09:30 ~ 16:00)
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)

        return market_open <= now <= market_close

    def _get_from_cache(self, key: str, market: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get data from schema_cache if TTL has not expired.

        Args:
            key: Cache key
            market: Market for TTL determination

        Returns:
            Cached data if valid, None otherwise
        """
        entry = self.schema_cache.get(key)
        if entry is None:
            return None

        elapsed = time.time() - entry.get("cached_at", 0)
        ttl = entry.get("ttl", CACHE_TTL_DEFAULT)

        if elapsed > ttl:
            del self.schema_cache[key]
            return None

        logger.debug(f"[SchemaRAG] Cache hit: {key} (age={elapsed:.0f}s, ttl={ttl}s)")
        return entry.get("data")

    async def _set_cache(self, key: str, data: List[Dict[str, Any]], market: str) -> None:
        """
        Store data in schema_cache with market-aware TTL.

        Args:
            key: Cache key
            data: Data to cache
            market: Market for TTL determination
        """
        if market == "KR":
            try:
                is_open = await self._is_kr_market_open()
                ttl = CACHE_TTL_MARKET_OPEN if is_open else CACHE_TTL_MARKET_CLOSED
            except Exception:
                ttl = CACHE_TTL_DEFAULT
        else:
            ttl = CACHE_TTL_DEFAULT

        self.schema_cache[key] = {
            "data": data,
            "cached_at": time.time(),
            "ttl": ttl
        }

    async def initialize(self) -> bool:
        """
        Initialize vector store with schema documents

        Returns:
            True if successful
        """
        if self.initialized:
            return True

        try:
            # Initialize vector store
            success = await self.vector_store.initialize()
            if not success:
                logger.error("[SchemaRAG] Vector store initialization failed")
                return False

            # Check if schemas are already indexed
            stats = await self.vector_store.get_stats()
            if stats.get("document_count", 0) > 0:
                logger.info("[SchemaRAG] Schemas already indexed")
                self.initialized = True
                return True

            # Index schema documents
            await self._index_schemas()

            self.initialized = True
            logger.info("[SchemaRAG] Initialization complete")
            return True

        except Exception as e:
            logger.error(f"[SchemaRAG] Initialization failed: {e}")
            return False

    async def _index_schemas(self) -> None:
        """
        Index all schema documents into vector store
        """
        logger.info("[SchemaRAG] Indexing schema documents...")

        documents = []

        # Index Korean stock schemas
        for table_name, schema_text in KR_SCHEMAS.items():
            keywords = self.TABLE_KOREAN_KEYWORDS.get(table_name, "")
            content = f"Korean: {keywords}\n{schema_text}" if keywords else schema_text
            documents.append({
                "content": content,
                "metadata": {
                    "table_name": table_name,
                    "market": "KR",
                    "category": self._get_table_category(table_name)
                }
            })

        # Index US stock schemas
        for table_name, schema_text in US_SCHEMAS.items():
            keywords = self.TABLE_KOREAN_KEYWORDS.get(table_name, "")
            content = f"Korean: {keywords}\n{schema_text}" if keywords else schema_text
            documents.append({
                "content": content,
                "metadata": {
                    "table_name": table_name,
                    "market": "US",
                    "category": self._get_table_category(table_name)
                }
            })

        # Index common schemas
        for table_name, schema_text in COMMON_SCHEMAS.items():
            keywords = self.TABLE_KOREAN_KEYWORDS.get(table_name, "")
            content = f"Korean: {keywords}\n{schema_text}" if keywords else schema_text
            documents.append({
                "content": content,
                "metadata": {
                    "table_name": table_name,
                    "market": "COMMON",
                    "category": self._get_table_category(table_name)
                }
            })

        # Add to vector store
        count = await self.vector_store.add_documents(documents, doc_type="schema")
        logger.info(f"[SchemaRAG] Indexed {count} schema documents")

    def _get_table_category(self, table_name: str) -> str:
        """
        Determine table category from name

        Args:
            table_name: Table name

        Returns:
            Category string
        """
        if "intraday" in table_name or "daily" in table_name:
            return "quote"
        elif "indicator" in table_name:
            return "technical"
        elif "grade" in table_name or "score" in table_name:
            return "quant"
        elif "investor" in table_name or "trading" in table_name:
            return "investor"
        elif "basic" in table_name or "detail" in table_name:
            return "info"
        elif "index" in table_name or "market" in table_name:
            return "market"
        else:
            return "other"

    def _enhance_query(self, query: str) -> str:
        """
        Enhance query with table name hints from TermMapper

        Uses TermMapper to extract financial terms and append
        associated table names to improve vector similarity search.

        Args:
            query: Original user query

        Returns:
            Enhanced query string with table name hints
        """
        try:
            from .term_mapper import TermMapper
            tm = TermMapper()
            terms = tm.extract_terms(query)
            enhancements = []
            for term, term_type, mapping in terms:
                tables = mapping.get("tables", [])
                enhancements.extend(tables)
            if enhancements:
                unique_tables = " ".join(set(enhancements))
                enhanced = f"{query} {unique_tables}"
                logger.debug(f"[SchemaRAG] Query enhanced: '{query}' -> '{enhanced}'")
                return enhanced
        except Exception as e:
            logger.warning(f"[SchemaRAG] Query enhancement failed: {e}")
        return query

    async def retrieve_tables(
        self,
        query: str,
        market: str = "KR",
        top_k: int = 5,
        stock_codes: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant tables for query

        Args:
            query: User query
            market: 'KR' or 'US'
            top_k: Number of tables to retrieve

        Returns:
            List of relevant table information
        """
        if not self.initialized:
            await self.initialize()

        # Check cache
        cache_key = f"tables:{market}:{query[:100]}"
        cached = self._get_from_cache(cache_key, market)
        if cached is not None:
            logger.info(f"[SchemaRAG] Cache hit for tables ({len(cached)} tables)")
            return cached

        logger.info(f"[SchemaRAG] Retrieving tables for: {query[:50]}...")

        # Build metadata filter
        filter_metadata = None
        if market in ["KR", "US"]:
            # Include market-specific and common tables
            filter_metadata = {
                "$or": [
                    {"market": market},
                    {"market": "COMMON"}
                ]
            }
        elif market == "BOTH":
            # Include both KR and US tables plus common tables
            filter_metadata = {
                "$or": [
                    {"market": "KR"},
                    {"market": "US"},
                    {"market": "COMMON"}
                ]
            }

        # Enhance query with table name hints from TermMapper
        enhanced_query = self._enhance_query(query)

        # Search for relevant schemas
        results = await self.vector_store.similarity_search(
            query=enhanced_query,
            top_k=top_k,
            filter_metadata=filter_metadata
        )

        # Extract table information
        tables = []
        for result in results:
            metadata = result.get("metadata", {})
            tables.append({
                "table": metadata.get("table_name", "unknown"),
                "market": metadata.get("market", ""),
                "category": metadata.get("category", ""),
                "relevance": result.get("score", 0),
                "schema": result.get("content", "")
            })

        # Add essential tables if not present
        tables = await self._ensure_essential_tables(tables, market, query, stock_codes=stock_codes)

        # Store in cache
        await self._set_cache(cache_key, tables, market)

        logger.info(f"[SchemaRAG] Found {len(tables)} relevant tables")
        return tables

    async def _ensure_essential_tables(
        self,
        tables: List[Dict[str, Any]],
        market: str,
        query: str,
        stock_codes: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Ensure essential tables are included based on query patterns

        Args:
            tables: Current table list
            market: Market (KR/US)
            query: User query
            stock_codes: Resolved stock codes (empty = no specific stock)

        Returns:
            Updated table list with essential tables
        """
        table_names = [t["table"] for t in tables]
        query_lower = query.lower()
        # Space-normalized query for Korean compound word matching
        # (e.g., "시장 레짐" → "시장레짐", "신용 스프레드" → "신용스프레드")
        query_normalized = query_lower.replace(" ", "")

        # Determine default table for KR market based on market open status
        if market == "KR":
            is_market_open = await self._is_kr_market_open()
            kr_default_table = "kr_intraday" if is_market_open else "kr_intraday_total"
            logger.debug(f"[SchemaRAG] KR market open: {is_market_open}, using: {kr_default_table}")
        else:
            kr_default_table = "kr_intraday_total"  # Fallback

        # Essential table mapping
        essential_tables = {
            "KR": {
                "default": kr_default_table,
                "technical": "kr_indicators",
                "investor": "kr_individual_investor_daily_trading",
                "quant": "kr_stock_grade"
            },
            "US": {
                "default": "us_daily",
                "technical": "us_indicators",
                "quant": "us_stock_grade"
            }
        }

        # Handle BOTH market - add tables from both KR and US
        if market == "BOTH":
            # Add KR default table
            kr_default = essential_tables["KR"]["default"]
            if kr_default not in table_names and kr_default in ALL_SCHEMAS:
                tables.append({
                    "table": kr_default,
                    "market": "KR",
                    "category": "quote",
                    "relevance": 0.5,
                    "schema": ALL_SCHEMAS[kr_default]
                })
            # Add US default table
            us_default = essential_tables["US"]["default"]
            if us_default not in table_names and us_default in ALL_SCHEMAS:
                tables.append({
                    "table": us_default,
                    "market": "US",
                    "category": "quote",
                    "relevance": 0.5,
                    "schema": ALL_SCHEMAS[us_default]
                })
        else:
            market_tables = essential_tables.get(market, essential_tables["KR"])

            # Add default table if no quote table present
            if not any("intraday" in t or "daily" in t for t in table_names):
                default_table = market_tables["default"]
                if default_table in ALL_SCHEMAS:
                    tables.append({
                        "table": default_table,
                        "market": market,
                        "category": "quote",
                        "relevance": 0.5,
                        "schema": ALL_SCHEMAS[default_table]
                    })

        # Add technical indicator table if query mentions indicators
        indicator_keywords = ["rsi", "macd", "볼린저", "이평", "기술적", "지표", "골든크로스"]
        if any(kw.replace(" ", "") in query_normalized for kw in indicator_keywords):
            if market == "BOTH":
                # Add both KR and US indicator tables
                for m, tech_table in [("KR", "kr_indicators"), ("US", "us_indicators")]:
                    if tech_table not in table_names and tech_table in ALL_SCHEMAS:
                        tables.append({
                            "table": tech_table,
                            "market": m,
                            "category": "technical",
                            "relevance": 0.7,
                            "schema": ALL_SCHEMAS[tech_table]
                        })
            else:
                tech_table = market_tables["technical"]
                if tech_table not in table_names and tech_table in ALL_SCHEMAS:
                    tables.append({
                        "table": tech_table,
                        "market": market,
                        "category": "technical",
                        "relevance": 0.7,
                        "schema": ALL_SCHEMAS[tech_table]
                    })

        # Add investor table if query mentions investor types (KR only - US has no investor data)
        investor_keywords = ["외국인", "외인", "기관", "개인", "순매수", "순매도"]
        if any(kw.replace(" ", "") in query_normalized for kw in investor_keywords):
            if market == "KR":
                inv_table = market_tables["investor"]
                if inv_table not in table_names and inv_table in ALL_SCHEMAS:
                    tables.append({
                        "table": inv_table,
                        "market": market,
                        "category": "investor",
                        "relevance": 0.7,
                        "schema": ALL_SCHEMAS[inv_table]
                    })

        # Add quant table if query mentions grades/scores
        quant_keywords = ["등급", "grade", "점수", "score", "퀀트", "가치주", "성장주"]
        if any(kw.replace(" ", "") in query_normalized for kw in quant_keywords):
            if market == "BOTH":
                # Add both KR and US quant tables
                for m, quant_table in [("KR", "kr_stock_grade"), ("US", "us_stock_grade")]:
                    if quant_table not in table_names and quant_table in ALL_SCHEMAS:
                        tables.append({
                            "table": quant_table,
                            "market": m,
                            "category": "quant",
                            "relevance": 0.7,
                            "schema": ALL_SCHEMAS[quant_table]
                        })
            else:
                quant_table = market_tables["quant"]
                if quant_table not in table_names and quant_table in ALL_SCHEMAS:
                    tables.append({
                        "table": quant_table,
                        "market": market,
                        "category": "quant",
                        "relevance": 0.7,
                        "schema": ALL_SCHEMAS[quant_table]
                    })

        # Add sector/industry/theme table if query mentions sector-related terms
        sector_keywords = ["업종", "섹터", "테마", "관련주", "산업", "sector", "industry", "theme",
                           "반도체", "바이오", "자동차", "금융", "에너지", "헬스케어", "IT",
                           "semiconductor", "biotech", "software", "bank", "technology",
                           "healthcare", "소프트웨어", "은행", "배터리", "battery", "ai"]
        if any(kw.replace(" ", "") in query_normalized for kw in sector_keywords):
            if market == "BOTH":
                for m, detail_table in [("KR", "kr_stock_detail"), ("US", "us_stock_basic")]:
                    if detail_table not in table_names and detail_table in ALL_SCHEMAS:
                        tables.append({
                            "table": detail_table,
                            "market": m,
                            "category": "company",
                            "relevance": 0.7,
                            "schema": ALL_SCHEMAS[detail_table]
                        })
            elif market == "KR":
                if "kr_stock_detail" not in table_names and "kr_stock_detail" in ALL_SCHEMAS:
                    tables.append({
                        "table": "kr_stock_detail",
                        "market": "KR",
                        "category": "company",
                        "relevance": 0.7,
                        "schema": ALL_SCHEMAS["kr_stock_detail"]
                    })
            elif market == "US":
                if "us_stock_basic" not in table_names and "us_stock_basic" in ALL_SCHEMAS:
                    tables.append({
                        "table": "us_stock_basic",
                        "market": "US",
                        "category": "company",
                        "relevance": 0.7,
                        "schema": ALL_SCHEMAS["us_stock_basic"]
                    })

        # Add financial statement tables if query mentions financial terms
        financial_keywords = ["재무", "재무제표", "손익", "매출", "영업이익", "순이익", "자산", "부채",
                              "자본", "현금흐름", "수익", "이익률", "마진", "earnings", "revenue",
                              "income", "balance sheet", "cash flow", "profit"]
        if any(kw.replace(" ", "") in query_normalized for kw in financial_keywords):
            if market == "BOTH":
                for m, fin_tables in [
                    ("KR", ["kr_financial_position"]),
                    ("US", ["us_income_statement", "us_balance_sheet", "us_cash_flow"])
                ]:
                    for ft in fin_tables:
                        if ft not in table_names and ft in ALL_SCHEMAS:
                            tables.append({
                                "table": ft, "market": m,
                                "category": "other", "relevance": 0.7,
                                "schema": ALL_SCHEMAS[ft]
                            })
            elif market == "KR":
                if "kr_financial_position" not in table_names and "kr_financial_position" in ALL_SCHEMAS:
                    tables.append({
                        "table": "kr_financial_position", "market": "KR",
                        "category": "other", "relevance": 0.7,
                        "schema": ALL_SCHEMAS["kr_financial_position"]
                    })
            elif market == "US":
                for ft in ["us_income_statement", "us_balance_sheet", "us_cash_flow"]:
                    if ft not in table_names and ft in ALL_SCHEMAS:
                        tables.append({
                            "table": ft, "market": "US",
                            "category": "other", "relevance": 0.7,
                            "schema": ALL_SCHEMAS[ft]
                        })

        # Add earnings estimates table if query mentions consensus/EPS estimate terms (US only)
        earnings_keywords = ["실적추정", "컨센서스", "eps추정", "eps전망", "매출전망",
                             "실적전망", "어닝스", "earnings estimate"]
        if any(kw.replace(" ", "") in query_normalized for kw in earnings_keywords):
            if market in ("US", "BOTH"):
                if "us_earnings_estimates" not in table_names and "us_earnings_estimates" in ALL_SCHEMAS:
                    tables.append({
                        "table": "us_earnings_estimates", "market": "US",
                        "category": "other", "relevance": 0.7,
                        "schema": ALL_SCHEMAS["us_earnings_estimates"]
                    })

        # Add sector benchmarks table if query mentions sector valuation comparison (US only)
        sector_bench_keywords = ["섹터벤치마크", "섹터밸류에이션", "섹터per", "섹터성장률",
                                 "업종벤치마크", "업종비교", "sector benchmark"]
        if any(kw.replace(" ", "") in query_normalized for kw in sector_bench_keywords):
            if market in ("US", "BOTH"):
                if "us_sector_benchmarks" not in table_names and "us_sector_benchmarks" in ALL_SCHEMAS:
                    tables.append({
                        "table": "us_sector_benchmarks", "market": "US",
                        "category": "other", "relevance": 0.7,
                        "schema": ALL_SCHEMAS["us_sector_benchmarks"]
                    })

        # Add options tables if query mentions options-related terms (US only)
        options_keywords = ["옵션", "풋", "콜", "내재변동성", "implied volatility",
                            "델타", "감마", "theta", "vega", "GEX", "감마익스포저",
                            "풋콜비율", "미결제약정", "행사가", "open interest", "strike"]
        if any(kw.replace(" ", "") in query_normalized for kw in options_keywords):
            if market in ("US", "BOTH"):
                for ot in ["us_option", "us_option_daily_summary"]:
                    if ot not in table_names and ot in ALL_SCHEMAS:
                        tables.append({
                            "table": ot, "market": "US",
                            "category": "other", "relevance": 0.7,
                            "schema": ALL_SCHEMAS[ot]
                        })

        # Add macro economic tables if query mentions economic terms
        macro_keywords = ["금리", "경제지표", "cpi", "물가", "gdp", "실업률", "pmi",
                          "연방", "국채", "기준금리", "인플레이션", "제조업",
                          "treasury", "federal", "inflation"]
        if any(kw.replace(" ", "") in query_normalized for kw in macro_keywords):
            if market in ("US", "BOTH"):
                for mt in ["us_fed_funds_rate", "us_treasury_yield", "us_cpi"]:
                    if mt not in table_names and mt in ALL_SCHEMAS:
                        tables.append({
                            "table": mt, "market": "US",
                            "category": "market", "relevance": 0.7,
                            "schema": ALL_SCHEMAS[mt]
                        })
                # Add specific macro tables based on sub-keywords
                macro_specific = {
                    "gdp": "us_gdp", "실업": "us_unemployment_rate",
                    "pmi": "us_pmi", "제조업": "us_pmi"
                }
                for kw, tbl in macro_specific.items():
                    if kw.replace(" ", "") in query_normalized and tbl not in table_names and tbl in ALL_SCHEMAS:
                        tables.append({
                            "table": tbl, "market": "US",
                            "category": "market", "relevance": 0.7,
                            "schema": ALL_SCHEMAS[tbl]
                        })
            if market in ("KR", "BOTH"):
                if "bok_economic_indicators" not in table_names and "bok_economic_indicators" in ALL_SCHEMAS:
                    tables.append({
                        "table": "bok_economic_indicators", "market": "COMMON",
                        "category": "market", "relevance": 0.7,
                        "schema": ALL_SCHEMAS["bok_economic_indicators"]
                    })

        # Add research reports table if query mentions analyst/target price terms (KR only)
        research_keywords = ["목표가", "투자의견", "애널리스트", "리포트", "보고서",
                             "증권사", "리서치", "analyst", "target price", "report"]
        if any(kw.replace(" ", "") in query_normalized for kw in research_keywords):
            if market in ("KR", "BOTH"):
                if "kr_research_reports" not in table_names and "kr_research_reports" in ALL_SCHEMAS:
                    tables.append({
                        "table": "kr_research_reports", "market": "KR",
                        "category": "other", "relevance": 0.7,
                        "schema": ALL_SCHEMAS["kr_research_reports"]
                    })

        # Add dividend and corporate action tables
        dividend_keywords = ["배당", "dividend", "배당금", "배당수익", "배당락"]
        if any(kw.replace(" ", "") in query_normalized for kw in dividend_keywords):
            if market in ("KR", "BOTH"):
                if "kr_dividends" not in table_names and "kr_dividends" in ALL_SCHEMAS:
                    tables.append({
                        "table": "kr_dividends", "market": "KR",
                        "category": "other", "relevance": 0.7,
                        "schema": ALL_SCHEMAS["kr_dividends"]
                    })
            if market in ("US", "BOTH"):
                if "us_dividends" not in table_names and "us_dividends" in ALL_SCHEMAS:
                    tables.append({
                        "table": "us_dividends", "market": "US",
                        "category": "other", "relevance": 0.7,
                        "schema": ALL_SCHEMAS["us_dividends"]
                    })

        corporate_keywords = ["자사주", "자기주식", "주식분할", "분할", "splits", "buyback"]
        if any(kw.replace(" ", "") in query_normalized for kw in corporate_keywords):
            if market in ("KR", "BOTH"):
                if "kr_stockacquisitiondisposal" not in table_names and "kr_stockacquisitiondisposal" in ALL_SCHEMAS:
                    tables.append({
                        "table": "kr_stockacquisitiondisposal", "market": "KR",
                        "category": "other", "relevance": 0.7,
                        "schema": ALL_SCHEMAS["kr_stockacquisitiondisposal"]
                    })
            if market in ("US", "BOTH"):
                if "us_splits" not in table_names and "us_splits" in ALL_SCHEMAS:
                    tables.append({
                        "table": "us_splits", "market": "US",
                        "category": "other", "relevance": 0.7,
                        "schema": ALL_SCHEMAS["us_splits"]
                    })

        # Add insider transaction and institutional activity tables
        insider_keywords = ["내부자", "인사이더", "insider"]
        if any(kw.replace(" ", "") in query_normalized for kw in insider_keywords):
            if market in ("US", "BOTH"):
                if "us_insider_transactions" not in table_names and "us_insider_transactions" in ALL_SCHEMAS:
                    tables.append({
                        "table": "us_insider_transactions", "market": "US",
                        "category": "other", "relevance": 0.7,
                        "schema": ALL_SCHEMAS["us_insider_transactions"]
                    })

        blocktrade_keywords = ["대량매매", "블록딜", "대량거래"]
        if any(kw.replace(" ", "") in query_normalized for kw in blocktrade_keywords):
            if market in ("KR", "BOTH"):
                if "kr_blocktrades" not in table_names and "kr_blocktrades" in ALL_SCHEMAS:
                    tables.append({
                        "table": "kr_blocktrades", "market": "KR",
                        "category": "other", "relevance": 0.7,
                        "schema": ALL_SCHEMAS["kr_blocktrades"]
                    })

        foreign_ownership_keywords = ["외국인지분", "외국인보유", "외국인한도", "지분율"]
        if any(kw.replace(" ", "") in query_normalized for kw in foreign_ownership_keywords):
            if market in ("KR", "BOTH"):
                if "kr_foreign_ownership" not in table_names and "kr_foreign_ownership" in ALL_SCHEMAS:
                    tables.append({
                        "table": "kr_foreign_ownership", "market": "KR",
                        "category": "investor", "relevance": 0.7,
                        "schema": ALL_SCHEMAS["kr_foreign_ownership"]
                    })

        # Add market regime and volatility index tables (US only)
        regime_keywords = ["vix", "공포지수", "변동성지수", "시장레짐", "강세장", "약세장",
                           "무브지수", "move", "달러인덱스", "dxy", "달러지수",
                           "크레딧스프레드", "신용스프레드", "역레포"]
        if any(kw.replace(" ", "") in query_normalized for kw in regime_keywords):
            if market in ("US", "BOTH"):
                # Always add VIX and market regime as core context
                for rt in ["us_vix", "us_market_regime"]:
                    if rt not in table_names and rt in ALL_SCHEMAS:
                        tables.append({
                            "table": rt, "market": "US",
                            "category": "market", "relevance": 0.7,
                            "schema": ALL_SCHEMAS[rt]
                        })
                # Add specific tables based on sub-keywords
                regime_specific = {
                    "무브": "us_move_index", "move": "us_move_index",
                    "달러": "us_dollar_index", "dxy": "us_dollar_index",
                    "스프레드": "us_credit_spread",
                    "역레포": "us_fed_rrp"
                }
                for kw, tbl in regime_specific.items():
                    if kw.replace(" ", "") in query_normalized and tbl not in table_names and tbl in ALL_SCHEMAS:
                        tables.append({
                            "table": tbl, "market": "US",
                            "category": "market", "relevance": 0.7,
                            "schema": ALL_SCHEMAS[tbl]
                        })

        # Add exchange rate table if query mentions currency/FX terms
        fx_keywords = ["환율", "원달러", "원엔", "달러환율", "exchange rate"]
        if any(kw.replace(" ", "") in query_normalized for kw in fx_keywords):
            if "exchange_rate" not in table_names and "exchange_rate" in ALL_SCHEMAS:
                tables.append({
                    "table": "exchange_rate", "market": "COMMON",
                    "category": "market", "relevance": 0.7,
                    "schema": ALL_SCHEMAS["exchange_rate"]
                })

        # Add daily_recommendation table for buy recommendation queries (only when no specific stock)
        recommend_keywords = ["추천", "뭐사", "뭘사", "뭐살", "살만", "좋은종목", "매수할만", "살까", "사야"]
        if not stock_codes and any(kw.replace(" ", "") in query_normalized for kw in recommend_keywords):
            if "daily_recommendation" not in table_names and "daily_recommendation" in ALL_SCHEMAS:
                tables.append({
                    "table": "daily_recommendation", "market": "COMMON",
                    "category": "recommendation", "relevance": 0.9,
                    "schema": ALL_SCHEMAS["daily_recommendation"]
                })

        # Add program trading table if query mentions program trading (KR only)
        program_keywords = ["프로그램매매", "프로그램 매매", "차익거래", "비차익거래", "프로그램순매수"]
        if any(kw.replace(" ", "") in query_normalized for kw in program_keywords):
            if market in ("KR", "BOTH"):
                if "kr_program_daily_trading" not in table_names and "kr_program_daily_trading" in ALL_SCHEMAS:
                    tables.append({
                        "table": "kr_program_daily_trading", "market": "KR",
                        "category": "investor", "relevance": 0.7,
                        "schema": ALL_SCHEMAS["kr_program_daily_trading"]
                    })

        return tables

    async def retrieve_columns(
        self,
        query: str,
        tables: List[str],
        top_k: int = 10
    ) -> List[Dict[str, str]]:
        """
        Retrieve relevant columns from specified tables

        Args:
            query: User query
            tables: List of table names to search
            top_k: Number of columns to retrieve

        Returns:
            List of relevant column information
        """
        logger.info(f"[SchemaRAG] Retrieving columns from: {tables}")

        columns = []
        query_lower = query.lower()

        # Column keywords mapping
        column_keywords = {
            "가격": ["close", "open", "high", "low"],
            "현재가": ["close"],
            "종가": ["close"],
            "거래량": ["volume"],
            "거래대금": ["trading_value"],
            "시총": ["market_cap"],
            "시가총액": ["market_cap"],
            "등락": ["change_rate", "change_amount"],
            "rsi": ["rsi"],
            "macd": ["macd", "macd_signal", "macd_hist"],
            "볼린저": ["bb_upper", "bb_middle", "bb_lower"],
            "이평": ["ma5", "ma20", "ma60", "ma120", "sma_20", "sma_50", "sma_200"],
            "외국인": ["foreign_net_volume", "foreign_net_value"],
            "기관": ["institution_net_volume", "institution_net_value"],
            "등급": ["total_grade", "value_grade", "quality_grade", "momentum_grade"],
            "점수": ["total_score", "value_score", "quality_score", "momentum_score"]
        }

        # Find matching columns
        matched_columns = set()
        for keyword, col_list in column_keywords.items():
            if keyword in query_lower:
                matched_columns.update(col_list)

        # Default columns if no specific match
        if not matched_columns:
            matched_columns = {"symbol", "stock_name", "close", "volume", "trading_value"}

        # Always include identifier columns
        matched_columns.add("symbol")
        if any("kr_" in t for t in tables):
            matched_columns.add("stock_name")

        # Build column list with table context
        for table in tables:
            schema_text = ALL_SCHEMAS.get(table, "")
            for col in matched_columns:
                if col in schema_text.lower():
                    columns.append({
                        "table": table,
                        "column": col,
                        "type": self._infer_column_type(col),
                        "description": self._get_column_description(col)
                    })

        # Limit results
        return columns[:top_k]

    def _infer_column_type(self, column: str) -> str:
        """Infer column type from name"""
        if column in ["symbol", "stock_name", "name"]:
            return "VARCHAR"
        elif column in ["volume", "trading_value", "market_cap"]:
            return "BIGINT"
        elif "date" in column:
            return "DATE"
        else:
            return "NUMERIC"

    def _get_column_description(self, column: str) -> str:
        """Get column description"""
        descriptions = {
            "symbol": "Stock code/ticker",
            "stock_name": "Stock name",
            "close": "Closing price",
            "open": "Opening price",
            "high": "Day high price",
            "low": "Day low price",
            "volume": "Trading volume",
            "trading_value": "Trading value (KRW)",
            "market_cap": "Market capitalization",
            "change_rate": "Price change rate (%)",
            "rsi": "Relative Strength Index (0-100)",
            "macd": "MACD value",
            "macd_signal": "MACD signal line",
            "bb_upper": "Bollinger Band upper",
            "bb_middle": "Bollinger Band middle (SMA20)",
            "bb_lower": "Bollinger Band lower",
            "ma5": "5-day moving average",
            "ma20": "20-day moving average",
            "ma60": "60-day moving average",
            "foreign_net_volume": "Foreign net trading volume",
            "institution_net_volume": "Institution net trading volume",
            "total_grade": "Overall quant grade",
            "total_score": "Overall quant score"
        }
        return descriptions.get(column, column)

    async def get_schema_context(
        self,
        query: str,
        market: str = "KR",
        max_tables: int = 5
    ) -> str:
        """
        Get formatted schema context for SQL generation prompt

        Args:
            query: User query
            market: 'KR' or 'US'
            max_tables: Maximum tables to include

        Returns:
            Formatted schema string for prompt
        """
        # Retrieve relevant tables
        tables = await self.retrieve_tables(query, market, max_tables)

        if not tables:
            return "No relevant schema found."

        # Add table inventory header - only list tables with schemas provided
        # (prevents LLM from using tables whose columns it doesn't know)
        retrieved_table_names = sorted([t["table"] for t in tables])
        inventory_header = (
            f"## Available Tables ({market} market)\n"
            f"Tables with schema details below: {', '.join(retrieved_table_names)}\n"
            f"ONLY use these tables. Do NOT use any table not listed here."
        )

        # Format schema context
        context_parts = [inventory_header]

        for table_info in tables:
            table_name = table_info["table"]
            schema = table_info.get("schema", "")

            if schema:
                context_parts.append(schema)

        return "\n\n".join(context_parts)

    async def get_table_names(self, market: str = "KR") -> List[str]:
        """
        Get all table names for a market

        Args:
            market: 'KR', 'US', or 'BOTH'

        Returns:
            List of table names
        """
        if market == "KR":
            return list(KR_SCHEMAS.keys()) + list(COMMON_SCHEMAS.keys())
        elif market == "US":
            return list(US_SCHEMAS.keys()) + list(COMMON_SCHEMAS.keys())
        elif market == "BOTH":
            return list(KR_SCHEMAS.keys()) + list(US_SCHEMAS.keys()) + list(COMMON_SCHEMAS.keys())
        else:
            return list(KR_SCHEMAS.keys()) + list(COMMON_SCHEMAS.keys())

    async def reindex(self) -> bool:
        """
        Reindex all schema documents

        Returns:
            True if successful
        """
        try:
            # Clear schema cache
            self.schema_cache.clear()

            # Delete existing schema documents
            await self.vector_store.delete_by_type("schema")

            # Reindex
            await self._index_schemas()

            logger.info("[SchemaRAG] Reindex complete")
            return True

        except Exception as e:
            logger.error(f"[SchemaRAG] Reindex failed: {e}")
            return False
