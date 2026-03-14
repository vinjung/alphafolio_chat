# services/chat/alpha_ai_model/tools/feedback_tools.py
"""
Feedback Tools for Alpha AI

Handles user feedback collection, storage, and few-shot example generation.
Supports:
- Feedback saving (rating, corrections)
- Auto-adding good Q&A pairs to few-shot examples
- Feedback statistics and analysis
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from config import logger


# Feedback storage path
FEEDBACK_DIR = Path(__file__).parent.parent / "data" / "feedback"
FEEDBACK_FILE = FEEDBACK_DIR / "feedback_log.json"
APPROVED_EXAMPLES_FILE = FEEDBACK_DIR / "approved_examples.json"


class FeedbackTools:
    """
    Tools for managing user feedback on SQL generation

    Features:
    - Save user feedback (positive/negative/correction)
    - Track feedback statistics
    - Auto-add approved Q&A pairs to few-shot examples
    - Review pending feedback for manual approval
    """

    # Feedback rating types
    RATING_POSITIVE = "positive"
    RATING_NEGATIVE = "negative"
    RATING_CORRECTION = "correction"

    # Review status
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"

    def __init__(self):
        """Initialize FeedbackTools and ensure storage directory exists"""
        self._ensure_storage_exists()
        logger.info("[FeedbackTools] Initialized")

    def _ensure_storage_exists(self) -> None:
        """Create storage directory and files if they don't exist"""
        FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)

        if not FEEDBACK_FILE.exists():
            self._write_json(FEEDBACK_FILE, {"feedbacks": []})

        if not APPROVED_EXAMPLES_FILE.exists():
            self._write_json(APPROVED_EXAMPLES_FILE, {"examples": []})

    def _read_json(self, filepath: Path) -> Dict[str, Any]:
        """Read JSON file safely"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _write_json(self, filepath: Path, data: Dict[str, Any]) -> bool:
        """Write JSON file safely"""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"[FeedbackTools] Failed to write JSON: {e}")
            return False

    def save_feedback(
        self,
        question: str,
        generated_sql: str,
        rating: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        corrected_sql: Optional[str] = None,
        comment: Optional[str] = None,
        market: str = "KR",
        intent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save user feedback for a SQL generation result

        Args:
            question: Original user question
            generated_sql: SQL that was generated
            rating: Feedback rating (positive/negative/correction)
            user_id: User identifier (optional)
            session_id: Session identifier (optional)
            corrected_sql: User-provided corrected SQL (for correction rating)
            comment: Additional user comment (optional)
            market: Market type (KR/US)
            intent: Query intent category

        Returns:
            Saved feedback record with ID
        """
        # Validate rating
        valid_ratings = [self.RATING_POSITIVE, self.RATING_NEGATIVE, self.RATING_CORRECTION]
        if rating not in valid_ratings:
            logger.warning(f"[FeedbackTools] Invalid rating: {rating}")
            rating = self.RATING_NEGATIVE

        # Create feedback record
        feedback_id = f"fb_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        feedback = {
            "id": feedback_id,
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "generated_sql": generated_sql,
            "rating": rating,
            "user_id": user_id,
            "session_id": session_id,
            "corrected_sql": corrected_sql,
            "comment": comment,
            "market": market,
            "intent": intent,
            "review_status": self.STATUS_PENDING if rating == self.RATING_POSITIVE else None,
            "reviewed_at": None,
            "reviewed_by": None
        }

        # Load existing feedbacks and append
        data = self._read_json(FEEDBACK_FILE)
        feedbacks = data.get("feedbacks", [])
        feedbacks.append(feedback)

        # Save updated feedbacks
        data["feedbacks"] = feedbacks
        data["last_updated"] = datetime.now().isoformat()

        if self._write_json(FEEDBACK_FILE, data):
            logger.info(f"[FeedbackTools] Saved feedback: {feedback_id} ({rating})")

            # Auto-approve positive feedback for few-shot if SQL is valid
            if rating == self.RATING_POSITIVE:
                self._queue_for_review(feedback)

            return feedback
        else:
            logger.error("[FeedbackTools] Failed to save feedback")
            return {}

    def _queue_for_review(self, feedback: Dict[str, Any]) -> None:
        """
        Queue positive feedback for review before adding to few-shot

        Args:
            feedback: Feedback record to queue
        """
        logger.info(f"[FeedbackTools] Queued for review: {feedback['id']}")
        # Positive feedbacks are automatically queued with STATUS_PENDING
        # They will be reviewed and approved/rejected later

    def get_feedback_stats(self) -> Dict[str, Any]:
        """
        Get feedback statistics

        Returns:
            Dictionary with feedback statistics
        """
        data = self._read_json(FEEDBACK_FILE)
        feedbacks = data.get("feedbacks", [])

        if not feedbacks:
            return {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "correction": 0,
                "pending_review": 0,
                "approved": 0,
                "by_market": {"KR": 0, "US": 0}
            }

        stats = {
            "total": len(feedbacks),
            "positive": sum(1 for f in feedbacks if f.get("rating") == self.RATING_POSITIVE),
            "negative": sum(1 for f in feedbacks if f.get("rating") == self.RATING_NEGATIVE),
            "correction": sum(1 for f in feedbacks if f.get("rating") == self.RATING_CORRECTION),
            "pending_review": sum(1 for f in feedbacks if f.get("review_status") == self.STATUS_PENDING),
            "approved": sum(1 for f in feedbacks if f.get("review_status") == self.STATUS_APPROVED),
            "by_market": {
                "KR": sum(1 for f in feedbacks if f.get("market") == "KR"),
                "US": sum(1 for f in feedbacks if f.get("market") == "US")
            },
            "by_intent": {}
        }

        # Count by intent
        for f in feedbacks:
            intent = f.get("intent") or "unknown"
            stats["by_intent"][intent] = stats["by_intent"].get(intent, 0) + 1

        return stats

    def get_pending_reviews(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get feedbacks pending review for few-shot addition

        Args:
            limit: Maximum number of records to return

        Returns:
            List of pending feedback records
        """
        data = self._read_json(FEEDBACK_FILE)
        feedbacks = data.get("feedbacks", [])

        pending = [
            f for f in feedbacks
            if f.get("review_status") == self.STATUS_PENDING
        ]

        # Sort by timestamp descending (newest first)
        pending.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return pending[:limit]

    def approve_for_few_shot(
        self,
        feedback_id: str,
        reviewer: str = "system",
        category: Optional[str] = None
    ) -> bool:
        """
        Approve a feedback record for addition to few-shot examples

        Args:
            feedback_id: ID of the feedback to approve
            reviewer: Identifier of the reviewer
            category: Category for the few-shot example

        Returns:
            True if approved successfully
        """
        data = self._read_json(FEEDBACK_FILE)
        feedbacks = data.get("feedbacks", [])

        # Find the feedback
        feedback = None
        feedback_idx = None
        for idx, f in enumerate(feedbacks):
            if f.get("id") == feedback_id:
                feedback = f
                feedback_idx = idx
                break

        if not feedback:
            logger.warning(f"[FeedbackTools] Feedback not found: {feedback_id}")
            return False

        # Update status
        feedback["review_status"] = self.STATUS_APPROVED
        feedback["reviewed_at"] = datetime.now().isoformat()
        feedback["reviewed_by"] = reviewer

        feedbacks[feedback_idx] = feedback
        data["feedbacks"] = feedbacks

        if not self._write_json(FEEDBACK_FILE, data):
            return False

        # Add to approved examples
        example = {
            "id": f"ex_{feedback_id}",
            "question": feedback["question"],
            "sql": feedback.get("corrected_sql") or feedback["generated_sql"],
            "category": category or feedback.get("intent") or "query",
            "market": feedback.get("market", "KR"),
            "source_feedback_id": feedback_id,
            "approved_at": datetime.now().isoformat(),
            "approved_by": reviewer
        }

        approved_data = self._read_json(APPROVED_EXAMPLES_FILE)
        examples = approved_data.get("examples", [])
        examples.append(example)
        approved_data["examples"] = examples
        approved_data["last_updated"] = datetime.now().isoformat()

        if self._write_json(APPROVED_EXAMPLES_FILE, approved_data):
            logger.info(f"[FeedbackTools] Approved: {feedback_id} -> few-shot example")
            return True

        return False

    def reject_for_few_shot(
        self,
        feedback_id: str,
        reviewer: str = "system",
        reason: Optional[str] = None
    ) -> bool:
        """
        Reject a feedback record from few-shot addition

        Args:
            feedback_id: ID of the feedback to reject
            reviewer: Identifier of the reviewer
            reason: Reason for rejection

        Returns:
            True if rejected successfully
        """
        data = self._read_json(FEEDBACK_FILE)
        feedbacks = data.get("feedbacks", [])

        for idx, f in enumerate(feedbacks):
            if f.get("id") == feedback_id:
                f["review_status"] = self.STATUS_REJECTED
                f["reviewed_at"] = datetime.now().isoformat()
                f["reviewed_by"] = reviewer
                f["rejection_reason"] = reason
                feedbacks[idx] = f
                break
        else:
            logger.warning(f"[FeedbackTools] Feedback not found: {feedback_id}")
            return False

        data["feedbacks"] = feedbacks

        if self._write_json(FEEDBACK_FILE, data):
            logger.info(f"[FeedbackTools] Rejected: {feedback_id}")
            return True

        return False

    def get_approved_examples(self) -> List[Dict[str, Any]]:
        """
        Get all approved few-shot examples from feedback

        Returns:
            List of approved examples
        """
        data = self._read_json(APPROVED_EXAMPLES_FILE)
        return data.get("examples", [])

    async def sync_to_few_shot_rag(self, few_shot_rag) -> int:
        """
        Sync approved examples to FewShotRAG vector store

        Args:
            few_shot_rag: FewShotRAG instance

        Returns:
            Number of examples synced
        """
        examples = self.get_approved_examples()

        if not examples:
            logger.info("[FeedbackTools] No approved examples to sync")
            return 0

        synced = 0
        for example in examples:
            # Check if already synced (by checking metadata)
            if example.get("synced_to_rag"):
                continue

            success = await few_shot_rag.add_example(
                question=example["question"],
                sql=example["sql"],
                category=example.get("category", "query"),
                market=example.get("market", "KR")
            )

            if success:
                # Mark as synced
                example["synced_to_rag"] = True
                example["synced_at"] = datetime.now().isoformat()
                synced += 1

        # Save updated examples
        if synced > 0:
            approved_data = self._read_json(APPROVED_EXAMPLES_FILE)
            approved_data["examples"] = examples
            self._write_json(APPROVED_EXAMPLES_FILE, approved_data)

        logger.info(f"[FeedbackTools] Synced {synced} examples to FewShotRAG")
        return synced

    def get_recent_feedbacks(
        self,
        limit: int = 50,
        rating: Optional[str] = None,
        market: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent feedback records with optional filters

        Args:
            limit: Maximum number of records
            rating: Filter by rating type
            market: Filter by market

        Returns:
            List of feedback records
        """
        data = self._read_json(FEEDBACK_FILE)
        feedbacks = data.get("feedbacks", [])

        # Apply filters
        if rating:
            feedbacks = [f for f in feedbacks if f.get("rating") == rating]
        if market:
            feedbacks = [f for f in feedbacks if f.get("market") == market]

        # Sort by timestamp descending
        feedbacks.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return feedbacks[:limit]

    def get_correction_examples(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get feedbacks with corrections (for learning from mistakes)

        Args:
            limit: Maximum number of records

        Returns:
            List of correction feedbacks with before/after SQL
        """
        data = self._read_json(FEEDBACK_FILE)
        feedbacks = data.get("feedbacks", [])

        corrections = [
            {
                "question": f["question"],
                "original_sql": f["generated_sql"],
                "corrected_sql": f["corrected_sql"],
                "market": f.get("market", "KR"),
                "timestamp": f.get("timestamp")
            }
            for f in feedbacks
            if f.get("rating") == self.RATING_CORRECTION and f.get("corrected_sql")
        ]

        # Sort by timestamp descending
        corrections.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return corrections[:limit]

    def clear_all_feedbacks(self) -> bool:
        """
        Clear all feedback data (use with caution)

        Returns:
            True if cleared successfully
        """
        try:
            self._write_json(FEEDBACK_FILE, {"feedbacks": []})
            self._write_json(APPROVED_EXAMPLES_FILE, {"examples": []})
            logger.info("[FeedbackTools] All feedback data cleared")
            return True
        except Exception as e:
            logger.error(f"[FeedbackTools] Failed to clear data: {e}")
            return False
