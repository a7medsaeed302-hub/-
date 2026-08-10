"""
Islamic Channel Guardian - Content Verifier
============================================
نظام التحقق الصارم من المحتوى الديني

المبدأ الأساسي: "لا نؤلف المحتوى الديني، بل نتحقق منه وننشر الموثوق منه"

سلسلة التحقق:
1. Database Verification → التحقق من وجود المحتوى في القاعدة
2. Source Check → التحقق من المصدر
3. Content Integrity Check → التحقق من سلامة المحتوى
4. Duplicate Check → التحقق من التكرار
5. Safety Check → التحقق الأمني
6. Publish → النشر (فقط إذا نجحت جميع الخطوات)
"""

import hashlib
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from config import VERIFIED_CONTENT, content_verification, security_config


# إعداد السجلات
logger = logging.getLogger(__name__)


class VerificationStatus(Enum):
    """حالات نتيجة التحقق"""
    VERIFIED = "verified"
    FAILED = "failed"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"


@dataclass
class VerificationResult:
    """نتيجة عملية التحقق"""
    status: VerificationStatus
    message: str
    content: Optional[Dict] = None
    checks_passed: List[str] = None
    checks_failed: List[str] = None
    
    def __post_init__(self):
        if self.checks_passed is None:
            self.checks_passed = []
        if self.checks_failed is None:
            self.checks_failed = []
    
    def to_dict(self) -> Dict:
        return {
            'status': self.status.value,
            'message': self.message,
            'content': self.content,
            'checks_passed': self.checks_passed,
            'checks_failed': self.checks_failed
        }


class ContentVerifier:
    """
    نظام التحقق من المحتوى الديني
    
    يمنع نشر أي محتوى:
    - غير موثق
    - بلا مصدر
    - مشكوك فيه
    - مولد بواسطة AI
    """
    
    def __init__(self, database_manager=None):
        """
        تهيئة نظام التحقق
        
        Args:
            database_manager: مدير قاعدة البيانات للتحقق من سجل النشر
        """
        self.db = database_manager
        self.accepted_sources = content_verification.ACCEPTED_SOURCES
        self.rejected_keywords = content_verification.REJECTED_KEYWORDS
        
        logger.info("تم تهيئة نظام التحقق من المحتوى")
    
    # =========================================================================
    # الواجهة الرئيسية للتحقق
    # =========================================================================
    
    def verify_content(self, content_type: str, content_data: Dict,
                       channel_id: int = None) -> VerificationResult:
        """
        التحقق الشامل من المحتوى قبل النشر
        
        Args:
            content_type: نوع المحتوى (verse, hadith, adkar, dua, tasbih, istighfar)
            content_data: بيانات المحتوى
            channel_id: معرف القناة (للتحقق من التكرار)
            
        Returns:
            VerificationResult: نتيجة التحقق
        """
        
        logger.info(f"بدء التحقق من المحتوى: {content_type}")
        
        result = VerificationResult(
            status=VerificationStatus.FAILED,
            message="فشل التحقق",
            content=content_data
        )
        
        # 1. التحقق من قاعدة البيانات
        db_check = self._check_database(content_type, content_data)
        if not db_check[0]:
            result.checks_failed.append("Database Verification")
            result.message = "المحتوى غير موجود في قاعدة المحتوى الموثوق"
            result.status = VerificationStatus.REJECTED
            logger.warning(f"فشل التحقق من قاعدة البيانات: {content_type}")
            return result
        result.checks_passed.append("Database Verification")
        
        # 2. التحقق من المصدر
        source_check = self._check_source(content_data)
        if not source_check[0]:
            result.checks_failed.append("Source Check")
            result.message = f"المصدر غير موثوق: {source_check[1]}"
            result.status = VerificationStatus.REJECTED
            logger.warning(f"فشل التحقق من المصدر: {content_data.get('source', 'unknown')}")
            return result
        result.checks_passed.append("Source Check")
        
        # 3. التحقق من سلامة المحتوى
        integrity_check = self._check_content_integrity(content_data)
        if not integrity_check[0]:
            result.checks_failed.append("Content Integrity Check")
            result.message = integrity_check[1]
            result.status = VerificationStatus.REJECTED
            logger.warning(f"فشل التحقق من سلامة المحتوى: {integrity_check[1]}")
            return result
        result.checks_passed.append("Content Integrity Check")
        
        # 4. التحقق من التكرار (إذا تم تقديم channel_id)
        if channel_id and self.db:
            duplicate_check = self._check_duplicate(channel_id, content_data)
            if duplicate_check[0]:
                result.checks_failed.append("Duplicate Check")
                result.message = "المحتوى تم نشره مؤخراً"
                result.status = VerificationStatus.REJECTED
                logger.info("تم رفض المحتوى بسبب التكرار")
                return result
        result.checks_passed.append("Duplicate Check")
        
        # 5. التحقق الأمني
        safety_check = self._check_safety(content_data)
        if not safety_check[0]:
            result.checks_failed.append("Safety Check")
            result.message = safety_check[1]
            result.status = VerificationStatus.REJECTED
            logger.warning(f"فشل التحقق الأمني: {safety_check[1]}")
            return result
        result.checks_passed.append("Safety Check")
        
        # جميع التحققات نجحت
        result.status = VerificationStatus.VERIFIED
        result.message = "تم التحقق بنجاح - جاهز للنشر"
        logger.info(f"تم التحقق بنجاح من المحتوى: {content_type}")
        
        return result
    
    # =========================================================================
    # خطوات التحقق الفردية
    # =========================================================================
    
    def _check_database(self, content_type: str, content_data: Dict) -> Tuple[bool, str]:
        """
        الخطوة 1: التحقق من وجود المحتوى في قاعدة المحتوى الموثوق
        
        Returns:
            Tuple[bool, str]: (نجح, رسالة)
        """
        
        text = content_data.get('text', '')
        
        if not text:
            return False, "النص فارغ"
        
        # البحث عن المحتوى في القاعدة
        verified_items = VERIFIED_CONTENT.get(content_type, [])
        
        for item in verified_items:
            item_text = item.get('text', '')
            
            # مقارنة مرنة (تجاهل الفواصل والمسافات الزائدة)
            if self._normalize_text(text) == self._normalize_text(item_text):
                return True, "تم العثور على المحتوى في قاعدة البيانات"
        
        # محاولة بحث جزئي (70% تطابق على الأقل)
        for item in verified_items:
            item_text = item.get('text', '')
            if self._partial_match(text, item_text, threshold=0.7):
                return True, "تم العثور على تطابق جزئي في قاعدة البيانات"
        
        return False, "المحتوى غير موجود في قاعدة المحتوى الموثوق"
    
    def _check_source(self, content_data: Dict) -> Tuple[bool, Optional[str]]:
        """
        الخطوة 2: التحقق من المصدر
        
        Returns:
            Tuple[bool, Optional[str]]: (نجح, سبب الرفض إن وجد)
        """
        
        source = content_data.get('source', '')
        
        if not source:
            return False, "المصدر غير محدد"
        
        # التحقق من أن المصدر مقبول
        source_normalized = self._normalize_text(source)
        
        for accepted in self.accepted_sources:
            if accepted in source or self._normalize_text(accepted) in source_normalized:
                return True, None
        
        return False, f"المصدر '{source}' غير مدرج في المصادر المقبولة"
    
    def _check_content_integrity(self, content_data: Dict) -> Tuple[bool, str]:
        """
        الخطوة 3: التحقق من سلامة المحتوى
        
        Returns:
            Tuple[bool, str]: (نجح, رسالة)
        """
        
        text = content_data.get('text', '')
        
        # التحقق من أن النص ليس فارغاً
        if not text or not text.strip():
            return False, "النص فارغ"
        
        # التحقق من أن النص باللغة العربية (للمحتوى العربي)
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        if arabic_chars < len(text) * 0.5:
            # قد يكون هناك آيات بالإنجليزية أو أرقام
            pass  # نسمح بذلك
        
        # التحقق من عدم وجود مؤشرات على محتوى مولد بالذكاء الاصطناعي
        ai_indicators = [
            "بصفتي ذكاءً اصطناعياً",
            "أنا نموذج لغوي",
            "تم إنشاؤه بواسطة",
            "generated by",
            "AI generated",
            "chatgpt",
            "claude",
            "gemini"
        ]
        
        text_lower = text.lower()
        for indicator in ai_indicators:
            if indicator in text_lower:
                return False, "تم اكتشاف مؤشرات على محتوى مولد بالذكاء الاصطناعي"
        
        # التحقق من الطول المعقول
        if len(text) < 5:
            return False, "النص قصير جداً"
        
        if len(text) > 5000:
            return False, "النص طويل جداً"
        
        return True, "المحتوى سليم"
    
    def _check_duplicate(self, channel_id: int, content_data: Dict) -> Tuple[bool, str]:
        """
        الخطوة 4: التحقق من التكرار
        
        Returns:
            Tuple[bool, str]: (True إذا كان مكرراً, رسالة)
        """
        
        text = content_data.get('text', '')
        
        if not self.db:
            return False, "قاعدة البيانات غير متاحة"
        
        is_duplicate = self.db.check_content_published_recently(
            channel_id=channel_id,
            content_text=text
        )
        
        if is_duplicate:
            hours = content_verification.DUPLICATE_PREVENTION_HOURS
            return True, f"المحتوى تم نشره خلال آخر {hours} ساعة"
        
        return False, "المحتوى غير مكرر"
    
    def _check_safety(self, content_data: Dict) -> Tuple[bool, str]:
        """
        الخطوة 5: التحقق الأمني
        
        Returns:
            Tuple[bool, str]: (نجح, رسالة)
        """
        
        text = content_data.get('text', '')
        source = content_data.get('source', '')
        reference = content_data.get('reference', '')
        
        # دمج كل النصوص للتحقق
        full_text = f"{text} {source} {reference}".lower()
        
        # التحقق من الكلمات المرفوضة
        for keyword in self.rejected_keywords:
            if keyword in full_text:
                return False, f"تم اكتشاف كلمة مرفوضة: '{keyword}'"
        
        # التحقق من روابط خارجية مشبوهة
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, full_text)
        
        allowed_domains = ['quran.com', 'sunnah.com', 'hadithcollection.com']
        
        for url in urls:
            is_allowed = any(domain in url for domain in allowed_domains)
            if not is_allowed:
                return False, f"رابط غير مسموح: {url}"
        
        return True, "التحقق الأمني ناجح"
    
    # =========================================================================
    # دوال مساعدة
    # =========================================================================
    
    def _normalize_text(self, text: str) -> str:
        """
        تطبيع النص للمقارنة
        
        - إزالة التشكيل
        - توحيد الألف
        - إزالة المسافات الزائدة
        """
        
        if not text:
            return ""
        
        # إزالة التشكيل
        diacritics = '\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652'
        for d in diacritics:
            text = text.replace(d, '')
        
        # توحيد الألف
        text = text.replace('آ', 'ا').replace('أ', 'ا').replace('إ', 'ا')
        
        # إزالة المسافات الزائدة
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _partial_match(self, text1: str, text2: str, threshold: float = 0.7) -> bool:
        """
        التحقق من التطابق الجزئي بين نصين
        
        Args:
            text1: النص الأول
            text2: النص الثاني
            threshold: نسبة التطابق المطلوبة (0-1)
            
        Returns:
            bool: True إذا كان هناك تطابق جزئي
        """
        
        norm1 = self._normalize_text(text1)
        norm2 = self._normalize_text(text2)
        
        if not norm1 or not norm2:
            return False
        
        # حساب نسبة التطابق البسيطة
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if not words1 or not words2:
            return False
        
        common_words = words1.intersection(words2)
        total_words = words1.union(words2)
        
        similarity = len(common_words) / len(total_words)
        
        return similarity >= threshold
    
    # =========================================================================
    # الحصول على محتوى موثق
    # =========================================================================
    
    def get_verified_content(self, content_type: str, 
                             exclude_recent: List[str] = None) -> Optional[Dict]:
        """
        الحصول على محتوى موثق عشوائي
        
        Args:
            content_type: نوع المحتوى
            exclude_recent: قائمة النصوص المستبعدة (تم نشرها مؤخراً)
            
        Returns:
            Optional[Dict]: المحتوى الموثق أو None
        """
        
        items = VERIFIED_CONTENT.get(content_type, [])
        
        if not items:
            logger.error(f"لا يوجد محتوى من نوع: {content_type}")
            return None
        
        # تصفية العناصر المستبعدة
        if exclude_recent:
            exclude_normalized = [self._normalize_text(t) for t in exclude_recent]
            items = [
                item for item in items
                if self._normalize_text(item.get('text', '')) not in exclude_normalized
            ]
        
        if not items:
            return None
        
        # اختيار عشوائي
        import random
        selected = random.choice(items)
        
        logger.info(f"تم اختيار محتوى موثق من نوع {content_type}")
        return selected
    
    def get_all_content_types(self) -> List[str]:
        """الحصول على جميع أنواع المحتوى المتاحة"""
        return list(VERIFIED_CONTENT.keys())
    
    def get_content_count(self, content_type: str) -> int:
        """الحصول على عدد العناصر في نوع محتوى معين"""
        return len(VERIFIED_CONTENT.get(content_type, []))
    
    def get_statistics(self) -> Dict:
        """الحصول على إحصائيات المحتوى الموثوق"""
        
        stats = {
            'total_types': len(VERIFIED_CONTENT),
            'types': {}
        }
        
        for content_type, items in VERIFIED_CONTENT.items():
            stats['types'][content_type] = {
                'count': len(items),
                'sources': list(set(
                    item.get('source', 'unknown') for item in items
                ))
            }
        
        return stats
