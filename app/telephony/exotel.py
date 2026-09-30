import os
import requests
import xml.etree.ElementTree as ET

from dotenv import load_dotenv


load_dotenv()


# =========================================================
# EXOTEL CONFIGURATION
# =========================================================

ACCOUNT_SID = os.getenv(
    "EXOTEL_ACCOUNT_SID"
)

API_KEY = os.getenv(
    "EXOTEL_API_KEY"
)

API_TOKEN = os.getenv(
    "EXOTEL_API_TOKEN"
)

CALLER_ID = os.getenv(
    "EXOTEL_CALLER_ID"
)


# Your account is working on the Singapore cluster.
EXOTEL_BASE_URL = (
    "https://api.exotel.com"
)


# =========================================================
# VALIDATE CONFIG
# =========================================================

def validate_config():

    missing = []

    if not ACCOUNT_SID:
        missing.append(
            "EXOTEL_ACCOUNT_SID"
        )

    if not API_KEY:
        missing.append(
            "EXOTEL_API_KEY"
        )

    if not API_TOKEN:
        missing.append(
            "EXOTEL_API_TOKEN"
        )

    if not CALLER_ID:
        missing.append(
            "EXOTEL_CALLER_ID"
        )

    if missing:

        raise RuntimeError(
            "Missing Exotel environment variables: "
            + ", ".join(missing)
        )


# =========================================================
# AUTH
# =========================================================

def exotel_auth():

    return (
        API_KEY,
        API_TOKEN
    )


# =========================================================
# START OUTBOUND CALL
# =========================================================

def start_outbound_call(
    phone: str,
    stream_url: str
):

    validate_config()

    url = (
        f"{EXOTEL_BASE_URL}/"
        f"v1/Accounts/"
        f"{ACCOUNT_SID}/Calls/connect"
    )

    data = {
        "From":
            phone,

        "CallerId":
            CALLER_ID,

        "StreamUrl":
            stream_url,

        "StreamType":
            "bidirectional",

        "Record":
            "true",

        "TimeLimit":
            "300"
    }

    try:

        response = requests.post(
            url,
            auth=exotel_auth(),
            data=data,
            timeout=30
        )

    except requests.exceptions.Timeout:

        return {
            "success": False,
            "status_code": 408,
            "message":
                "Exotel request timed out."
        }

    except requests.exceptions.ConnectionError as e:

        return {
            "success": False,
            "status_code": 503,
            "message":
                "Could not connect to Exotel.",
            "error":
                str(e)
        }

    except requests.exceptions.RequestException as e:

        return {
            "success": False,
            "status_code": 500,
            "message":
                "Exotel request failed.",
            "error":
                str(e)
        }

    print("")
    print(
        "========================================"
    )

    print(
        "EXOTEL OUTBOUND CALL RESPONSE"
    )

    print(
        "========================================"
    )

    print(
        "Status:",
        response.status_code
    )

    print(
        "Response:"
    )

    print(
        response.text
    )

    print(
        "========================================"
    )

    print("")

    if (
        200
        <= response.status_code
        < 300
    ):

        call_sid = None

        try:

            root = ET.fromstring(
                response.text
            )

            call = root.find(
                ".//Call"
            )

            if call is not None:

                call_sid = (
                    call.findtext(
                        "Sid"
                    )
                )

        except ET.ParseError:

            pass

        print(
            "Outbound API Call SID:",
            call_sid
        )

        return {
            "success": True,

            "status_code":
                response.status_code,

            "call_sid":
                call_sid,

            "response":
                response.text
        }

    if response.status_code == 401:

        return {
            "success": False,

            "status_code": 401,

            "message":
                "Exotel authentication failed.",

            "exotel_response":
                response.text
        }

    if response.status_code == 403:

        return {
            "success": False,

            "status_code": 403,

            "message":
                "Exotel rejected the call.",

            "exotel_response":
                response.text
        }

    return {
        "success": False,

        "status_code":
            response.status_code,

        "message":
            "Exotel returned an error.",

        "exotel_response":
            response.text
    }


# =========================================================
# GET CALL DETAILS
# =========================================================

def get_call_details(
    call_sid: str
):

    validate_config()

    url = (
        f"{EXOTEL_BASE_URL}/"
        f"v1/Accounts/"
        f"{ACCOUNT_SID}/Calls/"
        f"{call_sid}"
    )

    print(
        "Call details URL:",
        url
    )

    try:

        response = requests.get(
            url,
            auth=exotel_auth(),
            timeout=15
        )

    except requests.exceptions.RequestException as e:

        print(
            "Call details request error:",
            type(e).__name__,
            repr(e)
        )

        return {
            "success": False,
            "error":
                str(e)
        }

    print(
        "Call details status:",
        response.status_code
    )

    print(
        "Call details response:",
        response.text
    )

    if not (
        200
        <= response.status_code
        < 300
    ):

        return {
            "success": False,

            "status_code":
                response.status_code,

            "response":
                response.text
        }

    return {
        "success": True,
        "status_code":
            response.status_code,
        "response":
            response.text
    }


# =========================================================
# GET ACTIVE CALL LEGS
# =========================================================

def get_active_legs(
    call_sid: str
):

    validate_config()

    url = (
        f"{EXOTEL_BASE_URL}/"
        f"v1/Accounts/"
        f"{ACCOUNT_SID}/Calls/"
        f"{call_sid}/activelegs.json"
    )

    print(
        "Active legs URL:",
        url
    )

    print(
        "Getting active Exotel legs..."
    )

    try:

        response = requests.get(
            url,
            auth=exotel_auth(),
            timeout=15
        )

    except requests.exceptions.RequestException as e:

        print(
            "Active legs request error:",
            type(e).__name__,
            repr(e)
        )

        return []

    print(
        "Active legs status:",
        response.status_code
    )

    print(
        "Active legs response:",
        response.text
    )

    if not (
        200
        <= response.status_code
        < 300
    ):

        return []

    try:

        payload = (
            response.json()
        )

    except ValueError:

        print(
            "Could not decode active "
            "legs JSON response."
        )

        return []

    # =====================================================
    # NORMAL EXPECTED RESPONSE
    #
    # {
    #   "legs": [
    #       {
    #           "sid": "...",
    #           "status": "in progress",
    #           "origin": "outbound"
    #       }
    #   ]
    # }
    # =====================================================

    legs = (
        payload.get(
            "legs"
        )
    )

    if isinstance(
        legs,
        dict
    ):

        return [
            legs
        ]

    if isinstance(
        legs,
        list
    ):

        return legs

    # =====================================================
    # YOUR ACCOUNT CURRENTLY RETURNS:
    #
    # {
    #   "Call": {
    #       "Sid": "...",
    #       "Status": "in-progress"
    #   }
    # }
    #
    # This Call SID is NOT automatically a Leg SID.
    # =====================================================

    call_data = (
        payload.get(
            "Call"
        )
    )

    if isinstance(
        call_data,
        dict
    ):

        print(
            "WARNING: Exotel returned Call details "
            "instead of a legs list."
        )

        print(
            "Returned Call SID:",
            call_data.get(
                "Sid"
            )
        )

        print(
            "Returned Call status:",
            call_data.get(
                "Status"
            )
        )

        return []

    print(
        "No usable active legs were returned."
    )

    return []


# =========================================================
# HANG UP ONE CALL LEG
# =========================================================

def hangup_leg(
    call_sid: str,
    leg_sid: str
):

    validate_config()

    url = (
        f"{EXOTEL_BASE_URL}/"
        f"v1/Accounts/"
        f"{ACCOUNT_SID}/Calls/"
        f"{call_sid}/legs/"
        f"{leg_sid}"
    )

    data = {
        "action":
            "hangup"
    }

    print(
        "Hangup URL:",
        url
    )

    print(
        "Hanging up Exotel leg:",
        leg_sid
    )

    try:

        response = requests.put(
            url,
            auth=exotel_auth(),
            data=data,
            timeout=15
        )

    except requests.exceptions.RequestException as e:

        print(
            "Hangup request error:",
            type(e).__name__,
            repr(e)
        )

        return {
            "success": False,

            "error":
                str(e)
        }

    print(
        "Hangup status:",
        response.status_code
    )

    print(
        "Hangup response:",
        response.text
    )

    return {
        "success":
            200
            <= response.status_code
            < 300,

        "status_code":
            response.status_code,

        "response":
            response.text
    }


# =========================================================
# HANG UP CURRENT CALL
# =========================================================

def hangup_call(
    call_sid: str
):

    print("")
    print(
        "========================================"
    )

    print(
        "AUTO HANGUP"
    )

    print(
        "Call SID:",
        call_sid
    )

    print(
        "========================================"
    )

    legs = get_active_legs(
        call_sid
    )

    if not legs:

        print(
            "No active Exotel leg SID available."
        )

        print(
            "Cannot perform leg hangup "
            "without a real leg SID."
        )

        return {
            "success": False,

            "message":
                "Exotel did not return an active leg SID."
        }

    print(
        "Number of active legs:",
        len(legs)
    )

    for leg in legs:

        print(
            "Leg:",
            leg
        )

    selected_leg = None

    # =====================================================
    # FIRST CHOICE:
    # outbound customer leg
    # =====================================================

    for leg in legs:

        status = str(
            leg.get(
                "status",
                leg.get(
                    "Status",
                    ""
                )
            )
        ).lower()

        origin = str(
            leg.get(
                "origin",
                leg.get(
                    "Origin",
                    ""
                )
            )
        ).lower()

        if (
            status
            in [
                "in-progress",
                "in progress"
            ]
            and
            origin
            in [
                "outbound",
                "outbound-dial",
                "outbound dial"
            ]
        ):

            selected_leg = leg

            break

    # =====================================================
    # SECOND CHOICE:
    # any in-progress leg
    # =====================================================

    if not selected_leg:

        for leg in legs:

            status = str(
                leg.get(
                    "status",
                    leg.get(
                        "Status",
                        ""
                    )
                )
            ).lower()

            if status in [
                "in-progress",
                "in progress"
            ]:

                selected_leg = leg

                break

    if not selected_leg:

        print(
            "No in-progress call leg found."
        )

        return {
            "success": False,

            "message":
                "No in-progress call leg found."
        }

    leg_sid = (
        selected_leg.get(
            "sid"
        )
        or
        selected_leg.get(
            "Sid"
        )
    )

    if not leg_sid:

        print(
            "Selected call leg has no SID."
        )

        return {
            "success": False,

            "message":
                "Selected call leg has no SID."
        }

    print(
        "Selected customer leg SID:",
        leg_sid
    )

    result = hangup_leg(
        call_sid,
        leg_sid
    )

    print(
        "Auto hangup result:",
        result
    )

    return result


# =========================================================
# GET RECORDING URL
# =========================================================

def get_call_recording(
    call_sid: str
):

    validate_config()

    url = (
        f"{EXOTEL_BASE_URL}/"
        f"v1/Accounts/"
        f"{ACCOUNT_SID}/Calls/"
        f"{call_sid}"
    )

    print(
        "Fetching Exotel call details..."
    )

    try:

        response = requests.get(
            url,
            auth=exotel_auth(),
            timeout=15
        )

    except requests.exceptions.RequestException as e:

        print(
            "Call details request error:",
            type(e).__name__,
            repr(e)
        )

        return {
            "success": False,

            "error":
                str(e)
        }

    print(
        "Call details status:",
        response.status_code
    )

    print(
        "Call details response:",
        response.text
    )

    if not (
        200
        <= response.status_code
        < 300
    ):

        return {
            "success": False,

            "status_code":
                response.status_code,

            "response":
                response.text
        }

    try:

        root = ET.fromstring(
            response.text
        )

        call = root.find(
            ".//Call"
        )

        if call is None:

            return {
                "success": False,

                "message":
                    "Call details were not found."
            }

        recording_url = (
            call.findtext(
                "RecordingUrl"
            )
        )

        status = (
            call.findtext(
                "Status"
            )
        )

        duration = (
            call.findtext(
                "Duration"
            )
        )

        return {
            "success": True,

            "call_sid":
                call_sid,

            "status":
                status,

            "duration":
                duration,

            "recording_url":
                recording_url
        }

    except ET.ParseError as e:

        return {
            "success": False,

            "message":
                "Could not parse Exotel response.",

            "error":
                str(e)
        }


# =========================================================
# DOWNLOAD RECORDING
# =========================================================

def download_recording(
    recording_url: str,
    output_file: str = "last_call.mp3"
):

    validate_config()

    try:

        response = requests.get(
            recording_url,
            auth=exotel_auth(),
            timeout=60
        )

        response.raise_for_status()

    except requests.exceptions.RequestException as e:

        print(
            "Recording download error:",
            type(e).__name__,
            repr(e)
        )

        return {
            "success": False,

            "error":
                str(e)
        }

    with open(
        output_file,
        "wb"
    ) as file:

        file.write(
            response.content
        )

    print(
        "Recording saved:",
        output_file
    )

    return {
        "success": True,

        "file":
            output_file
    }