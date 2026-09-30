from apscheduler.schedulers.background import BackgroundScheduler

from app.agent.engine import VoiceAgent


scheduler = BackgroundScheduler(
    timezone="UTC"
)


def fake_ai_call(lead_id, name, phone):

    print("")
    print("====================================")
    print("STARTING AI CALL")
    print(f"Lead ID: {lead_id}")
    print(f"Name: {name}")
    print(f"Phone: {phone}")
    print("====================================")

    agent = VoiceAgent(name)

    print("")
    print("AI:", agent.start())
    print("")

    while True:

        customer = input("You: ")

        response = agent.process(customer)

        print("AI:", response)

        if agent.state == "closed":
            break

    print("")
    print("====================================")
    print("CALL ENDED")
    print("====================================")
    print("")