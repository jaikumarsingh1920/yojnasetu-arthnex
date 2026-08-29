import pytest
from app.ai.copilot_router import AICopilotQueryRouter

def test_detect_language_12_languages():
    assert AICopilotQueryRouter.detect_language("Namaste! I need a scheme") == "en"
    assert AICopilotQueryRouter.detect_language("नमस्ते! मुझे स्कीम चाहिए") == "hi"
    assert AICopilotQueryRouter.detect_language("আমি ব্যবসার জন্য ঋণ চাই") == "bn"
    assert AICopilotQueryRouter.detect_language("எனக்கு தொழில் தொடங்க கடன் வேண்டும்") == "ta"
    assert AICopilotQueryRouter.detect_language("నేను వ్యాపారం ప్రారంభించాలనుకుంటున్నాను") == "te"
    assert AICopilotQueryRouter.detect_language("मला व्यवसाय सुरू करायचा आहे") == "mr"
    assert AICopilotQueryRouter.detect_language("મારે વ્યવસાય શરૂ કરવો છે") == "gu"
    assert AICopilotQueryRouter.detect_language("ನಾನು ವ್ಯವಹಾರ ಪ್ರಾರಂಭಿಸಲು ಬಯಸುತ್ತೇನೆ") == "kn"
    assert AICopilotQueryRouter.detect_language("എനിക്ക് ഒരു ബിസിനസ് തുടങ്ങണം") == "ml"
    assert AICopilotQueryRouter.detect_language("ਮੈਨੂੰ ਕਾਰੋਬਾਰ ਸ਼ੁਰੂ ਕਰਨਾ ਹੈ") == "pa"
    assert AICopilotQueryRouter.detect_language("ମୁଁ ବ୍ୟବସାୟ ଆରମ୍ଭ କରିବାକୁ ଚାହୁଁଛି") == "or"
    assert AICopilotQueryRouter.detect_language("মই ব্যৱসায় আৰম্ভ কৰিব বিচাৰো") == "as"
    assert AICopilotQueryRouter.detect_language("bhai mujhe business start krna h") == "hi"

def test_multilingual_intent_classification_all_12_prompts():
    prompts = [
        ("Hindi", "mujhe business start karna hai"),
        ("Bengali", "আমি ব্যবসা শুরু করতে চাই"),
        ("Tamil", "எனக்கு தொழில் தொடங்க வேண்டும்"),
        ("Telugu", "నేను వ్యాపారం ప్రారంభించాలనుకుంటున్నాను"),
        ("Marathi", "मला व्यवसाय सुरू करायचा आहे"),
        ("Gujarati", "મારે વ્યવસાય શરૂ કરવો છે"),
        ("Kannada", "ನಾನು ವ್ಯವಹಾರ ಪ್ರಾರಂಭಿಸಲು ಬಯಸುತ್ತೇನೆ"),
        ("Malayalam", "എനിക്ക് ഒരു ബിസിനസ് തുടങ്ങണം"),
        ("Punjabi", "ਮੈਨੂੰ ਕਾਰੋਬਾਰ ਸ਼ੁਰੂ ਕਰਨਾ ਹੈ"),
        ("Odia", "ମୁଁ ବ୍ୟବସାୟ ଆରମ୍ଭ କରିବାକୁ ଚାହୁଁଛି"),
        ("Assamese", "মই ব্যৱসায় আৰম্ভ কৰিব বিচাৰো"),
        ("Hinglish", "bhai mujhe scheme chahiye"),
    ]

    for lang, prompt in prompts:
        intent = AICopilotQueryRouter.classify_intent(prompt)
        assert intent in ["BUSINESS_PROFILE_INIT", "RECOMMENDATION_QUERY"], f"Failed for {lang}: got {intent}"
