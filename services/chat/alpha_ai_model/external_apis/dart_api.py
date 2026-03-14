# services/chat/alpha_ai_model/external_apis/dart_api.py
"""
DART API Integration

Provides access to Korea's Electronic Disclosure System (DART).
Retrieves corporate disclosures, financial statements, and major shareholder info.

API Documentation: https://opendart.fss.or.kr/guide/main.do
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from config import settings, logger

from .base import BaseExternalAPI, APIResponse, APIErrorCode


class DartAPI(BaseExternalAPI):
    """
    DART (Data Analysis, Retrieval and Transfer System) API client

    Supports:
    - Disclosure search (공시 검색)
    - Company info (기업 정보)
    - Financial statements (재무제표)
    - Major shareholder info (대주주 현황)

    Rate Limits:
    - 10,000 requests/day (basic)
    """

    # DART API endpoints
    BASE_URL = "https://opendart.fss.or.kr/api"

    # Disclosure endpoints
    DISCLOSURE_LIST = f"{BASE_URL}/list.json"          # 공시 목록
    DISCLOSURE_SEARCH = f"{BASE_URL}/list.json"        # 공시 검색
    COMPANY_INFO = f"{BASE_URL}/company.json"          # 기업 개황

    # Financial statement endpoints
    SINGLE_FINANCIAL = f"{BASE_URL}/fnlttSinglAcnt.json"      # 단일회사 재무제표
    MULTI_FINANCIAL = f"{BASE_URL}/fnlttMultiAcnt.json"       # 다중회사 재무제표

    # Shareholder endpoints
    MAJOR_SHAREHOLDER = f"{BASE_URL}/hyslrSttus.json"         # 최대주주 현황

    # Disclosure types
    DISCLOSURE_TYPES = {
        "A": "정기공시",
        "B": "주요사항보고",
        "C": "발행공시",
        "D": "지분공시",
        "E": "기타공시",
        "F": "외부감사관련",
        "G": "펀드공시",
        "H": "자산유동화",
        "I": "거래소공시",
        "J": "공정위공시"
    }

    def __init__(self):
        """Initialize DART API client"""
        super().__init__("DartAPI")
        self.api_key = settings.DART_API_KEY or ""

    @property
    def is_available(self) -> bool:
        """Check if DART API is configured"""
        return bool(self.api_key)

    async def search(
        self,
        query: str,
        **kwargs
    ) -> APIResponse:
        """
        Search disclosures by company name or keyword

        Args:
            query: Search query (company name)
            **kwargs: Additional parameters

        Returns:
            APIResponse with disclosure results
        """
        # For general search, search disclosures
        return await self.search_disclosures(corp_name=query, **kwargs)

    async def search_disclosures(
        self,
        corp_name: str = None,
        corp_code: str = None,
        bgn_de: str = None,
        end_de: str = None,
        pblntf_ty: str = None,
        page_no: int = 1,
        page_count: int = 20
    ) -> APIResponse:
        """
        Search disclosure list

        Args:
            corp_name: Company name (partial match)
            corp_code: Company code (8 digits)
            bgn_de: Start date (YYYYMMDD)
            end_de: End date (YYYYMMDD)
            pblntf_ty: Disclosure type (A-J)
            page_no: Page number
            page_count: Results per page (max 100)

        Returns:
            APIResponse with disclosure list
        """
        query = corp_name or corp_code or ""
        error_response = self._check_availability(query)
        if error_response:
            return error_response

        try:
            # Set default date range (last 30 days)
            if not bgn_de:
                bgn_de = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
            if not end_de:
                end_de = datetime.now().strftime("%Y%m%d")

            params = {
                "crtfc_key": self.api_key,
                "bgn_de": bgn_de,
                "end_de": end_de,
                "page_no": str(page_no),
                "page_count": str(min(page_count, 100))
            }

            if corp_name:
                params["corp_name"] = corp_name
            if corp_code:
                params["corp_code"] = corp_code
            if pblntf_ty:
                params["pblntf_ty"] = pblntf_ty

            logger.info(f"[DartAPI] Searching disclosures: {query}")

            response = await self._make_request(
                method="GET",
                url=self.DISCLOSURE_LIST,
                params=params
            )

            # Check DART API status
            status = response.get("status", "")
            if status != "000":
                error_msg = response.get("message", "Unknown DART API error")
                if status == "013":
                    # No data found
                    return APIResponse.success_response(
                        source=self.api_name,
                        data=[],
                        query=query,
                        metadata={"message": "No disclosures found"}
                    )
                return APIResponse.error_response(
                    self.api_name,
                    f"DART API error: {error_msg}",
                    APIErrorCode.INVALID_RESPONSE,
                    query
                )

            # Parse results
            items = response.get("list", [])
            results = self._format_disclosure_results(items)

            return APIResponse.success_response(
                source=self.api_name,
                data=results,
                query=query,
                metadata={
                    "page_no": response.get("page_no", page_no),
                    "page_count": response.get("page_count", page_count),
                    "total_count": response.get("total_count", len(results)),
                    "total_page": response.get("total_page", 1)
                }
            )

        except Exception as e:
            logger.error(f"[DartAPI] Search failed: {e}")
            return self._handle_error(e, query)

    async def get_company_info(self, corp_code: str) -> APIResponse:
        """
        Get company overview information

        Args:
            corp_code: Company code (8 digits)

        Returns:
            APIResponse with company info
        """
        error_response = self._check_availability(corp_code)
        if error_response:
            return error_response

        try:
            params = {
                "crtfc_key": self.api_key,
                "corp_code": corp_code
            }

            logger.info(f"[DartAPI] Getting company info: {corp_code}")

            response = await self._make_request(
                method="GET",
                url=self.COMPANY_INFO,
                params=params
            )

            status = response.get("status", "")
            if status != "000":
                return APIResponse.error_response(
                    self.api_name,
                    response.get("message", "Company not found"),
                    APIErrorCode.NOT_FOUND,
                    corp_code
                )

            # Format company info
            company = {
                "corp_code": response.get("corp_code", ""),
                "corp_name": response.get("corp_name", ""),
                "corp_name_eng": response.get("corp_name_eng", ""),
                "stock_code": response.get("stock_code", ""),
                "ceo_name": response.get("ceo_nm", ""),
                "corp_cls": response.get("corp_cls", ""),  # Y:유가, K:코스닥, N:코넥스, E:기타
                "industry": response.get("induty_code", ""),
                "establishment_date": response.get("est_dt", ""),
                "address": response.get("adres", ""),
                "homepage": response.get("hm_url", ""),
                "phone": response.get("phn_no", ""),
                "fax": response.get("fax_no", ""),
                "employees": response.get("emp_cnt", ""),
                "fiscal_month": response.get("acc_mt", "")
            }

            return APIResponse.success_response(
                source=self.api_name,
                data=[company],
                query=corp_code,
                metadata={"type": "company_info"}
            )

        except Exception as e:
            logger.error(f"[DartAPI] Get company info failed: {e}")
            return self._handle_error(e, corp_code)

    async def get_financial_statement(
        self,
        corp_code: str,
        bsns_year: str,
        reprt_code: str = "11011",
        fs_div: str = "CFS"
    ) -> APIResponse:
        """
        Get financial statement

        Args:
            corp_code: Company code (8 digits)
            bsns_year: Business year (YYYY)
            reprt_code: Report code (11011:1Q, 11012:2Q, 11014:3Q, 11013:Annual)
            fs_div: Statement type (CFS:연결, OFS:개별)

        Returns:
            APIResponse with financial statement
        """
        error_response = self._check_availability(corp_code)
        if error_response:
            return error_response

        try:
            params = {
                "crtfc_key": self.api_key,
                "corp_code": corp_code,
                "bsns_year": bsns_year,
                "reprt_code": reprt_code,
                "fs_div": fs_div
            }

            logger.info(f"[DartAPI] Getting financial statement: {corp_code} ({bsns_year})")

            response = await self._make_request(
                method="GET",
                url=self.SINGLE_FINANCIAL,
                params=params
            )

            status = response.get("status", "")
            if status != "000":
                if status == "013":
                    return APIResponse.success_response(
                        source=self.api_name,
                        data=[],
                        query=corp_code,
                        metadata={"message": "No financial data found"}
                    )
                return APIResponse.error_response(
                    self.api_name,
                    response.get("message", "Financial data not found"),
                    APIErrorCode.NOT_FOUND,
                    corp_code
                )

            items = response.get("list", [])
            results = self._format_financial_results(items)

            return APIResponse.success_response(
                source=self.api_name,
                data=results,
                query=corp_code,
                metadata={
                    "bsns_year": bsns_year,
                    "reprt_code": reprt_code,
                    "fs_div": fs_div,
                    "type": "financial_statement"
                }
            )

        except Exception as e:
            logger.error(f"[DartAPI] Get financial statement failed: {e}")
            return self._handle_error(e, corp_code)

    async def get_recent_disclosures(
        self,
        corp_code: str = None,
        corp_name: str = None,
        days: int = 7,
        limit: int = 20
    ) -> APIResponse:
        """
        Get recent disclosures for a company

        Args:
            corp_code: Company code
            corp_name: Company name
            days: Number of days to look back
            limit: Maximum results

        Returns:
            APIResponse with recent disclosures
        """
        bgn_de = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        end_de = datetime.now().strftime("%Y%m%d")

        return await self.search_disclosures(
            corp_code=corp_code,
            corp_name=corp_name,
            bgn_de=bgn_de,
            end_de=end_de,
            page_count=limit
        )

    def _format_disclosure_results(
        self,
        items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Format disclosure list results

        Args:
            items: Raw API response items

        Returns:
            Formatted disclosure list
        """
        results = []

        for item in items:
            disclosure_type = item.get("pblntf_ty", "")
            results.append({
                "corp_code": item.get("corp_code", ""),
                "corp_name": item.get("corp_name", ""),
                "stock_code": item.get("stock_code", ""),
                "corp_cls": item.get("corp_cls", ""),
                "report_name": item.get("report_nm", ""),
                "rcept_no": item.get("rcept_no", ""),  # 접수번호
                "flr_name": item.get("flr_nm", ""),    # 공시 제출인
                "rcept_dt": item.get("rcept_dt", ""),  # 접수일자
                "rm": item.get("rm", ""),              # 비고
                "disclosure_type": disclosure_type,
                "disclosure_type_name": self.DISCLOSURE_TYPES.get(disclosure_type, ""),
                "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={item.get('rcept_no', '')}"
            })

        return results

    def _format_financial_results(
        self,
        items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Format financial statement results

        Args:
            items: Raw API response items

        Returns:
            Formatted financial data list
        """
        results = []

        for item in items:
            results.append({
                "account_name": item.get("account_nm", ""),
                "sj_div": item.get("sj_div", ""),      # 재무제표구분
                "sj_name": item.get("sj_nm", ""),      # 재무제표명
                "thstrm_amount": item.get("thstrm_amount", ""),      # 당기금액
                "thstrm_add_amount": item.get("thstrm_add_amount", ""),  # 당기누적금액
                "frmtrm_amount": item.get("frmtrm_amount", ""),      # 전기금액
                "frmtrm_add_amount": item.get("frmtrm_add_amount", ""),  # 전기누적금액
                "bfefrmtrm_amount": item.get("bfefrmtrm_amount", ""),    # 전전기금액
                "ord": item.get("ord", "")             # 계정과목 정렬순서
            })

        return results
