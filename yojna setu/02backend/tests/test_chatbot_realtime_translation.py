import pytest
import re
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.schemas.ai import AIChatRequest, AIChatResponse, AICopilotAction, RichCard
from app.ai.copilot_router import AICopilotQueryRouter
from app.ai.agent import GPTCopilotAgent
from app.services.translation_service import ChatbotTranslationService


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 1. LANGUAGE DETECTION FOR ALL 12 LANGUAGES & HINGLISH
# ---------------------------------------------------------------------------
def test_all_12_languages_detection_and_script_routing():
    """Verifies that all 12 supported Indian languages and Hinglish/Roman Hindi are correctly detected."""
    sample_queries = {
        "en": "I want to apply for a small business loan",
        "hi": "मुझे नया व्यापार शुरू करने के लिए लोन चाहिए",
        "bn": "আমি একটি নতুন ব্যবসার জন্য ঋণ নিতে চাই",
        "mr": "मला नवीन व्यवसायासाठी कर्ज हवे आहे",
        "ta": "நான் ஒரு புதிய தொழில் தொடங்க கடன் பெற விரும்புகிறேன்",
        "te": "నేను కొత్త వ్యాపారం ప్రారంభించడానికి రుణం పొందాలనుకుంటున్నాను",
        "gu": "મારે નવો વ્યવસાય શરૂ કરવા માટે લોન જોઈએ છે",
        "kn": "ನಾನು ಹೊಸ ವ್ಯವಹಾರವನ್ನು ಪ್ರಾರಂಭಿಸಲು ಸಾಲವನ್ನು ಪಡೆಯಲು ಬಯಸುತ್ತೇನೆ",
        "ml": "എനിക്ക് ഒരു പുതിയ ബിസിനസ്സ് ആരംഭിക്കുന്നതിന് വായ്പ വേണം",
        "pa": "ਮੈਂ ਇੱਕ ਨਵਾਂ ਕਾਰੋਬਾਰ ਸ਼ੁਰੂ ਕਰਨ ਲਈ ਕਰਜ਼ਾ ਲੈਣਾ ਚਾਹੁੰਦਾ ਹਾਂ",
        "or": "ମୁଁ ଏକ ନୂତନ ବ୍ୟବସାୟ ଆରମ୍ଭ କରିବା ପାଇଁ ଋଣ ଚାହୁଁଛି",
        "as": "মই এটা নতুন ব্যৱসায় আৰম্ভ কৰিব বিচাৰো",
    }

    for expected_lang, text in sample_queries.items():
        detected = AICopilotQueryRouter.detect_language(text)
        assert detected == expected_lang, f"Failed detection for {expected_lang}: got {detected}"

    # Hinglish detection tests
    hinglish_queries = [
        "bhai mujhe naya dairy business shuru karna hai loan chahiye",
        "mera cibil score 720 hai pmegp loan milega kya",
        "gareeb hu dukan kholni hai paise chahiye"
    ]
    for hq in hinglish_queries:
        detected = AICopilotQueryRouter.detect_language(hq)
        assert detected == "hi", f"Hinglish should route to 'hi', got {detected} for: {hq}"


# ---------------------------------------------------------------------------
# 2. INVARIANT MASKING AND RESTORATION
# ---------------------------------------------------------------------------
def test_invariant_masking_and_restoration():
    """Verifies that currency amounts, percentages, tenures, URLs, and scheme names are preserved byte-for-byte."""
    raw_text = (
        "Under PMEGP, you can get a loan of up to ₹50,00,000 for manufacturing. "
        "The subsidy is 25% in urban areas and 35% in rural areas. "
        "The interest rate is 5.0% p.a. with a repayment tenure of 84 months. "
        "Check guidelines at https://pmegp.gov.in or /schemes/SIH26092-001."
    )

    masked_text, token_map = ChatbotTranslationService.mask_invariants(raw_text)

    # Invariants should be replaced by placeholders
    assert "₹50,00,000" not in masked_text
    assert "35%" not in masked_text
    assert "https://pmegp.gov.in" not in masked_text
    assert "/schemes/SIH26092-001" not in masked_text
    assert "84 months" not in masked_text

    # Restoring invariants should return the exact original text
    restored = ChatbotTranslationService.restore_invariants(masked_text, token_map)
    assert restored == raw_text


# ---------------------------------------------------------------------------
# 3. SIMPLE SCHEME QUESTIONS IN ALL 12 LANGUAGES
# ---------------------------------------------------------------------------
def test_all_12_languages_simple_scheme_question(db_session: Session):
    """Verifies chatbot handles a scheme query in each of the 12 languages and responds in that language."""
    queries_by_lang = {
        "en": "Tell me about PMEGP scheme",
        "hi": "PMEGP योजना के बारे में बताएं",
        "bn": "PMEGP প্রকল্প সম্পর্কে বলুন",
        "mr": "PMEGP योजनेबद्दल माहिती सांगा",
        "ta": "PMEGP திட்டம் பற்றி கூறுங்கள்",
        "te": "PMEGP పథకం గురించి చెప్పండి",
        "gu": "PMEGP યોજના વિશે જણાવો",
        "kn": "PMEGP ಯೋಜನೆ ಬಗ್ಗೆ ತಿಳಿಸಿ",
        "ml": "PMEGP പദ്ധതിയെക്കുറിച്ച് പറയുക",
        "pa": "PMEGP ਸਕੀਮ ਬਾਰੇ ਦੱਸੋ",
        "or": "PMEGP ଯୋଜନା ବିଷୟରେ କୁହନ୍ତୁ",
        "as": "PMEGP আঁচনিৰ বিষয়ে কওক",
    }

    for lang, q_text in queries_by_lang.items():
        req = AIChatRequest(
            message=q_text,
            session_id=f"test_simple_{lang}"
        )
        res = GPTCopilotAgent.process_query(db_session, req)

        assert res is not None
        assert res.language == lang, f"Expected response language {lang}, got {res.language}"
        assert len(res.answer) > 20, f"Answer too short for {lang}"
        # Official scheme name must be preserved
        assert "PMEGP" in res.answer or "Prime Minister" in res.answer


# ---------------------------------------------------------------------------
# 4. ELIGIBILITY QUESTIONS IN ALL 12 LANGUAGES
# ---------------------------------------------------------------------------
def test_all_12_languages_eligibility_question(db_session: Session):
    """Verifies eligibility questions run deterministic rules and output translated statutory criteria."""
    elig_queries = {
        "hi": "क्या मैं PMEGP लोन के लिए पात्र हूँ?",
        "bn": "আমি কি PMEGP ঋণের জন্য যোগ্য?",
        "ta": "நான் PMEGP கடனுக்கு தகுதியானவரா?",
        "te": "నేను PMEGP రુణానికి అర్హుడనా?",
        "mr": "मी PMEGP कर्जासाठी पात्र आहे का?",
        "gu": "શું હું PMEGP લોન માટે પાત્ર છું?",
        "kn": "ನಾನು PMEGP ಸಾಲಕ್ಕೆ ಅರ್ಹನೇ?",
        "ml": "ഞാൻ PMEGP വായ്പയ്ക്ക് അർഹനാണോ?",
        "pa": "ਕੀ ਮੈਂ PMEGP ਲੋਨ ਲਈ ਯੋਗ ਹਾਂ?",
        "or": "ମୁଁ କଣ PMEGP ଋଣ ପାଇଁ ଯୋଗ୍ୟ?",
        "as": "মই PMEGP ঋণৰ বাবে যোগ্য নে?",
        "en": "Am I eligible for PMEGP loan?",
    }

    for lang, q_text in elig_queries.items():
        req = AIChatRequest(
            message=q_text,
            session_id=f"test_elig_{lang}"
        )
        res = GPTCopilotAgent.process_query(db_session, req)

        assert res.language == lang
        assert res.deterministic_used is True
        assert len(res.answer) > 30


# ---------------------------------------------------------------------------
# 5. FINANCIAL QUESTIONS AND NUMBER PRESERVATION
# ---------------------------------------------------------------------------
def test_all_12_languages_financial_question_number_preservation(db_session: Session):
    """Verifies financial EMI calculations strictly preserve numeric values, ₹ currency symbols, and interest rates."""
    fin_queries = {
        "hi": "₹5,00,000 लोन का 5 वर्ष के लिए EMI कितना होगा?",
        "bn": "₹5,00,000 ঋণের 5 বছরের জন্য EMI কত হবে?",
        "ta": "₹5,00,000 கடனுக்கு 5 ஆண்டுகளுக்கு EMI எவ்வளவு?",
        "te": "₹5,00,000 రుణానికి 5 సంవత్సరాలకు EMI ఎంత అవుతుంది?",
        "mr": "₹5,00,000 कर्जासाठी 5 वर्षांसाठी EMI किती असेल?",
        "gu": "₹5,00,000 લોન માટે 5 વર્ષ માટે EMI કેટલી થશે?",
        "kn": "₹5,00,000 ಸಾಲಕ್ಕೆ 5 ವರ್ಷಗಳ ಕಾಲ EMI ಎಷ್ಟು?",
        "ml": "₹5,00,000 വായ്പയ്ക്ക് 5 വർഷത്തേക്ക് EMI എത്രയായിരിക്കും?",
        "pa": "₹5,00,000 ਕਰਜ਼ੇ ਲਈ 5 ਸਾਲਾਂ ਲਈ EMI ਕਿੰਨੀ ਹੋਵੇਗੀ?",
        "or": "₹5,00,000 ଋଣ ପାଇଁ 5 ବର୍ଷର EMI କେତେ ହେବ?",
        "as": "₹5,00,000 ঋণৰ বাবে 5 বছৰৰ EMI কিমান হ'ব?",
        "en": "What is the EMI for ₹5,00,000 loan for 5 years?",
    }

    for lang, q_text in fin_queries.items():
        req = AIChatRequest(
            message=q_text,
            session_id=f"test_fin_{lang}"
        )
        res = GPTCopilotAgent.process_query(db_session, req)

        assert res.language == lang
        # Currency symbol or loan amount must be strictly preserved
        assert "₹" in res.answer or "5,00,000" in res.answer or "500000" in res.answer
        if res.financial_calculation:
            assert (
                res.financial_calculation.get("eligible_loan_amount") is not None
                or res.financial_calculation.get("periodic_installment") is not None
            )


# ---------------------------------------------------------------------------
# 6. DOCUMENT QUESTIONS AND URL PRESERVATION
# ---------------------------------------------------------------------------
def test_all_12_languages_document_question_url_preservation(db_session: Session):
    """Verifies document questions return checklists and preserve official URLs and route links."""
    doc_queries = {
        "hi": "PMEGP के लिए कौन से दस्तावेज़ चाहिए?",
        "bn": "PMEGP এর জন্য কি কি নথি লাগবে?",
        "ta": "PMEGP திட்டத்திற்கு என்ன ஆவணங்கள் தேவை?",
        "te": "PMEGP కోసం ఏ పత్రాలు అవసరం?",
        "mr": "PMEGP साठी कोणती कागदपत्रे लागतात?",
        "gu": "PMEGP માટે કયા દસ્તાવેજોની જરૂર છે?",
        "kn": "PMEGP ಗಾಗಿ ಯಾವ ದಾಖಲೆಗಳು ಬೇಕು?",
        "ml": "PMEGP-ക്ക് ഏതൊക്കെ രേഖകൾ ആവശ്യമാണ്?",
        "pa": "PMEGP ਲਈ ਕਿਹੜੇ ਦਸਤਾਵੇਜ਼ ਚਾਹੀਦੇ ਹਨ?",
        "or": "PMEGP ପାଇଁ କେଉଁ ଦସ୍ତାବିଜ ଆବଶ୍ୟକ?",
        "as": "PMEGP ৰ বাবে কি কি নথি-পত্ৰ প্ৰয়োজন?",
        "en": "What documents are required for PMEGP?",
    }

    for lang, q_text in doc_queries.items():
        req = AIChatRequest(
            message=q_text,
            session_id=f"test_doc_{lang}"
        )
        res = GPTCopilotAgent.process_query(db_session, req)

        assert res.language == lang
        assert len(res.answer) > 30
        # If actions are present, check their route links and translations
        for act in res.actions:
            assert act.target_url.startswith("/") or act.target_url.startswith("http")


# ---------------------------------------------------------------------------
# 7. MULTI-TURN FOLLOW-UP LANGUAGE PRESERVATION
# ---------------------------------------------------------------------------
def test_follow_up_question_language_preservation(db_session: Session):
    """Verifies that follow-up questions without explicit script retain the active language in session memory."""
    session_id = "test_multi_turn_followup_bn"

    # Turn 1: User asks in Bengali
    req1 = AIChatRequest(
        message="PMEGP প্রকল্প কি?",
        session_id=session_id
    )
    res1 = GPTCopilotAgent.process_query(db_session, req1)
    assert res1.language == "bn"

    # Turn 2: Follow-up question (user asks subsidy in short form)
    req2 = AIChatRequest(
        message="এতে কত সাবসিডি পাওয়া যায়?",
        session_id=session_id
    )
    res2 = GPTCopilotAgent.process_query(db_session, req2)
    assert res2.language == "bn"
    assert "PMEGP" in res2.answer or "সাবসিডি" in res2.answer or "subsidy" in res2.answer.lower() or "%" in res2.answer


# ---------------------------------------------------------------------------
# 8. HINGLISH QUERIES AND NATURAL HINDI RESPONSES
# ---------------------------------------------------------------------------
def test_hinglish_queries_and_natural_hindi_responses(db_session: Session):
    """Verifies that colloquial Hinglish queries are routed to Hindi and produce natural Hindi responses."""
    hinglish_queries = [
        "bhai mujhe dairy business start karna hai koi scheme batao",
        "meri dukan ke liye loan chahiye kaise milega"
    ]

    for hq in hinglish_queries:
        req = AIChatRequest(
            message=hq,
            session_id=f"test_hinglish_{hash(hq)}"
        )
        res = GPTCopilotAgent.process_query(db_session, req)
        assert res.language == "hi"
        assert len(res.answer) > 20
        # Check Devanagari presence in answer
        assert re.search(r"[\u0900-\u097F]", res.answer) is not None


# ---------------------------------------------------------------------------
# 9. DYNAMIC LANGUAGE SWITCHING MID-SESSION
# ---------------------------------------------------------------------------
def test_dynamic_language_switching(db_session: Session):
    """Verifies mid-session language switching between English, Hindi, and regional languages."""
    session_id = "test_lang_switch_session"

    # 1. Start in English
    res1 = GPTCopilotAgent.process_query(db_session, AIChatRequest(
        message="Tell me about PMEGP loan",
        session_id=session_id
    ))
    assert res1.language == "en"

    # 2. Switch to Hindi using 'हिंदी में समझाओ'
    res2 = GPTCopilotAgent.process_query(db_session, AIChatRequest(
        message="हिंदी में समझाओ",
        session_id=session_id
    ))
    assert res2.intent == "LANGUAGE_CHANGE"
    assert res2.language == "hi"
    assert "हिंदी" in res2.answer

    # 3. Next query in Hindi
    res3 = GPTCopilotAgent.process_query(db_session, AIChatRequest(
        message="इसके लिए क्या पात्रता है?",
        session_id=session_id
    ))
    assert res3.language == "hi"

    # 4. Switch to English using 'English me batao'
    res4 = GPTCopilotAgent.process_query(db_session, AIChatRequest(
        message="English me batao",
        session_id=session_id
    ))
    assert res4.intent == "LANGUAGE_CHANGE"
    assert res4.language == "en"

    # 5. Switch to Bengali using 'বাংলায় বলুন'
    res5 = GPTCopilotAgent.process_query(db_session, AIChatRequest(
        message="বাংলায় বলুন",
        session_id=session_id
    ))
    assert res5.intent == "LANGUAGE_CHANGE"
    assert res5.language == "bn"


# ---------------------------------------------------------------------------
# 10. TRANSLATION FALLBACK SAFETY
# ---------------------------------------------------------------------------
def test_translation_fallback_safety(monkeypatch):
    """Verifies that if translation encounters an error, the system safely falls back to canonical English."""
    def broken_call_ai_translation(*args, **kwargs):
        raise RuntimeError("Simulated AI Provider Outage")

    monkeypatch.setattr(ChatbotTranslationService, "_call_ai_translation", broken_call_ai_translation)

    canonical_english = "Under PMEGP, you can get a loan of ₹50,00,000 at 5% interest."
    # Rule fallback or canonical fallback should retain numbers safely
    result = ChatbotTranslationService.translate_text(canonical_english, target_lang="hi")
    assert "₹50,00,000" in result
    assert "5%" in result
    assert "PMEGP" in result


# ---------------------------------------------------------------------------
# 11. CACHING AND STALENESS PREVENTION
# ---------------------------------------------------------------------------
def test_caching_and_staleness_prevention():
    """Verifies that translations are cached by content hash and that changing facts yields new translations."""
    ChatbotTranslationService.clear_cache()

    text_v1 = "Maximum subsidy under PMEGP is 35%."
    trans_v1 = ChatbotTranslationService.translate_text(text_v1, target_lang="hi")

    # Second call should hit cache
    trans_v1_cached = ChatbotTranslationService.translate_text(text_v1, target_lang="hi")
    assert trans_v1 == trans_v1_cached

    # Changing the statutory fact changes the content hash, preventing stale data
    text_v2 = "Maximum subsidy under PMEGP is 50%."
    trans_v2 = ChatbotTranslationService.translate_text(text_v2, target_lang="hi")
    assert "50%" in trans_v2
    assert trans_v1 != trans_v2


# ---------------------------------------------------------------------------
# 12. NO SEMANTIC FACT DISTORTION AFTER TRANSLATION
# ---------------------------------------------------------------------------
def test_no_semantic_fact_distortion_after_translation():
    """Verifies that post-translation invariant checks guarantee no financial facts are lost or altered."""
    english_text = (
        "Loan amount: ₹10,00,000\n"
        "Interest rate: 8.5% p.a.\n"
        "Tenure: 60 months\n"
        "Scheme: MUDRA Loan\n"
        "Portal: https://www.mudra.org.in"
    )

    for lang in ["hi", "bn", "mr", "ta", "te", "gu", "kn", "ml", "pa", "or", "as"]:
        translated = ChatbotTranslationService.translate_text(english_text, target_lang=lang)
        # Verify invariant tokens are restored without corruption
        assert "₹10,00,000" in translated, f"Currency lost in {lang}"
        assert "8.5%" in translated, f"Interest rate lost in {lang}"
        assert "60 months" in translated, f"Tenure lost in {lang}"
        assert "MUDRA Loan" in translated, f"Scheme name altered in {lang}"
        assert "https://www.mudra.org.in" in translated, f"URL altered in {lang}"
