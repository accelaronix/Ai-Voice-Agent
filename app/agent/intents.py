import re


# =========================================================
# NORMALIZE TEXT
# =========================================================

def normalize_text(
    text: str
) -> str:

    text = text.lower().strip()

    # Keep:
    # English letters/numbers
    # Hindi/Devanagari
    # spaces
    # apostrophes
    text = re.sub(
        r"[^\w\s\u0900-\u097F']",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# DETECT DEVANAGARI
# =========================================================

def contains_devanagari(
    text: str
) -> bool:

    return bool(
        re.search(
            r"[\u0900-\u097F]",
            text
        )
    )


# =========================================================
# PHRASE MATCHING
# =========================================================

def contains_phrase(
    text: str,
    phrases: list[str]
) -> bool:

    text = normalize_text(
        text
    )

    for phrase in phrases:

        phrase = normalize_text(
            phrase
        )

        if not phrase:
            continue

        # -----------------------------------------
        # HINDI / DEVANAGARI
        #
        # Do NOT use \b because Hindi combining
        # characters can break word boundaries.
        # -----------------------------------------

        if contains_devanagari(
            phrase
        ):

            if phrase in text:
                return True

        # -----------------------------------------
        # ENGLISH / HINGLISH
        #
        # Use proper token boundaries so:
        #
        # "ha" does not match random words.
        # -----------------------------------------

        else:

            pattern = (
                r"(?<!\w)"
                + re.escape(
                    phrase
                )
                + r"(?!\w)"
            )

            if re.search(
                pattern,
                text
            ):

                return True

    return False


# =========================================================
# INTENT DETECTION
# =========================================================

def detect_intent(
    text: str
):

    text = normalize_text(
        text
    )

    print(
        "Normalized customer text:",
        repr(text)
    )

    # =====================================================
    # NOT INTERESTED
    # =====================================================

    negative_words = [

        # English
        "no",
        "no thanks",
        "not interested",
        "don't call",
        "do not call",
        "stop calling",

        # Hinglish
        "nahi",
        "nahin",
        "nahi chahiye",
        "interested nahi",
        "mujhe interest nahi hai",
        "call mat karo",
        "phone mat karo",

        # Hindi
        "नहीं",
        "नहीं चाहिए",
        "मुझे दिलचस्पी नहीं है",
        "मुझे रुचि नहीं है",
        "फोन मत करना",
        "कॉल मत करना",
        "मत करो"
    ]

    if contains_phrase(
        text,
        negative_words
    ):

        print(
            "Detected intent: NOT_INTERESTED"
        )

        return "NOT_INTERESTED"

    # =====================================================
    # CALLBACK
    # =====================================================

    callback_words = [

        # English
        "call later",
        "call me later",
        "busy",
        "call tomorrow",
        "later",
        "not now",

        # Hinglish
        "baad mein call karo",
        "bad me call karo",
        "baad me phone karo",
        "kal call karo",
        "abhi busy hu",
        "abhi busy hoon",
        "abhi nahi",
        "thodi der baad",

        # Hindi
        "बाद में कॉल करना",
        "बाद में फोन करना",
        "बाद में",
        "कल कॉल करना",
        "कल फोन करना",
        "अभी व्यस्त हूँ",
        "अभी बिजी हूँ",
        "अभी नहीं",
        "थोड़ी देर बाद"
    ]

    if contains_phrase(
        text,
        callback_words
    ):

        print(
            "Detected intent: CALLBACK"
        )

        return "CALLBACK"

    # =====================================================
    # POSITIVE / YES
    # =====================================================

    positive_words = [

        # English
        "yes",
        "yeah",
        "yep",
        "okay",
        "ok",
        "sure",
        "yes please",
        "that's fine",
        "that is fine",

        # Hinglish
        "haan",
        "han",
        "ha",
        "haanji",
        "hanji",
        "haan ji",
        "han ji",
        "ji",
        "ji haan",
        "ji han",
        "theek hai",
        "thik hai",
        "bilkul",
        "kar sakte hain",

        # Hindi
        "हाँ",
        "हां",
        "हाँ जी",
        "हां जी",
        "जी",
        "जी हाँ",
        "जी हां",
        "ठीक है",
        "ठीक",
        "बिल्कुल",
        "कर सकते हैं",
        "कर सकते है"
    ]

    if contains_phrase(
        text,
        positive_words
    ):

        print(
            "Detected intent: YES"
        )

        return "YES"

    # =====================================================
    # COURTESY
    # =====================================================

    courtesy_words = [

        # English
        "thank you",
        "thanks",
        "thankyou",
        "bye",
        "goodbye",

        # Hinglish
        "dhanyavaad",
        "dhanyawad",
        "shukriya",

        # Hindi
        "धन्यवाद",
        "शुक्रिया",
        "अलविदा"
    ]

    if contains_phrase(
        text,
        courtesy_words
    ):

        print(
            "Detected intent: COURTESY"
        )

        return "COURTESY"

    print(
        "Detected intent: UNKNOWN"
    )

    return "UNKNOWN"