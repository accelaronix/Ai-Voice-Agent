from app.agent.intents import (
    detect_intent
)


class VoiceAgent:

    def __init__(
        self,
        name
    ):

        self.name = name

        self.state = (
            "permission"
        )

    # =====================================================
    # START CONVERSATION
    # =====================================================

    def start(
        self
    ):

        return (
            f"नमस्ते {self.name}, "
            "मैं अजय बोल रहा हूँ Knowlathon से। "
            "क्या अभी आपसे बात करने का सही समय है?"
        )

    # =====================================================
    # PROCESS CUSTOMER RESPONSE
    # =====================================================

    def process(
        self,
        customer_text
    ):

        intent = detect_intent(
            customer_text
        )

        # =================================================
        # CONVERSATION ALREADY CLOSED
        # =================================================

        if (
            self.state
            == "closed"
        ):

            return (
                "धन्यवाद। "
                "आपका दिन शुभ हो।"
            )

        # =================================================
        # PERMISSION
        # =================================================

        if (
            self.state
            == "permission"
        ):

            if (
                intent
                == "YES"
            ):

                self.state = (
                    "course"
                )

                return (
                    "जी, हमें आपकी तरफ़ से "
                    "एक कोर्स के लिए enquiry मिली थी। "
                    "क्या आप बता सकते हैं कि "
                    "आप किस कोर्स में इंटरेस्टेड हैं?"
                )

            if (
                intent
                == "CALLBACK"
            ):

                self.state = (
                    "callback"
                )

                return (
                    "कोई समस्या नहीं। "
                    "आप किस समय वापस कॉल करवाना पसंद करेंगे?"
                )

            if (
                intent
                == "NOT_INTERESTED"
            ):

                self.state = (
                    "closed"
                )

                return (
                    "ठीक है। "
                    "आपका समय देने के लिए धन्यवाद। "
                    "आपका दिन शुभ हो।"
                )

            if (
                intent
                == "COURTESY"
            ):

                return (
                    "आपका स्वागत है। "
                    "क्या अभी आपसे बात करने का सही समय है?"
                )

            return (
                "माफ़ कीजिए, "
                "मैं आपकी बात ठीक से समझ नहीं पाया। "
                "क्या अभी आपसे बात करने का सही समय है?"
            )

        # =================================================
        # COURSE INTEREST
        # =================================================

        elif (
            self.state
            == "course"
        ):

            self.state = (
                "closed"
            )

            return (
                "बहुत बढ़िया। "
                "हमारे काउंसलर आपसे जल्द ही संपर्क करेंगे। "
                "धन्यवाद।"
            )

        # =================================================
        # CALLBACK
        # =================================================

        elif (
            self.state
            == "callback"
        ):

            self.state = (
                "closed"
            )

            return (
                "ठीक है। "
                "हम उस समय आपसे दोबारा संपर्क करेंगे। "
                "धन्यवाद।"
            )

        return (
            "कृपया अपनी बात "
            "एक बार फिर बताइए।"
        )