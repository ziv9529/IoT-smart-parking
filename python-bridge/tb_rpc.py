import os

import requests
from dotenv import load_dotenv


load_dotenv()

TB_HOST = os.getenv("TB_HOST", "https://eu.thingsboard.cloud").rstrip("/")
TB_TOKEN = os.getenv("TB_TOKEN")
RPC_URL = f"{TB_HOST}/api/v1/{TB_TOKEN}/rpc"

COMMANDS = {
    "openGate": "OPEN_GATE",
    "closeGate": "CLOSE_GATE"
}


def send_reply(request_id, data):
    response = requests.post(
        f"{RPC_URL}/{request_id}",
        json=data,
        timeout=5
    )
    response.raise_for_status()


def handle_rpc(request):
    request_id = request.get("id")
    method = request.get("method")

    if request_id is None or not method:
        print("invalid RPC request:", request)
        return

    arduino_command = COMMANDS.get(method)

    if not arduino_command:
        print(f"unsupported RPC method: {method}")
        send_reply(request_id, {
            "success": False,
            "error": "unsupported method"
        })
        return

    print("\nRPC received from ThingsBoard")
    print("method:", method)
    print("params:", request.get("params", {}))

    print("\ncopy this command to the Tinkercad serial monitor:")
    print(arduino_command)

    input("\nafter the command runs in Tinkercad, press Enter here...")

    send_reply(request_id, {
        "success": True,
        "command": arduino_command
    })

    print("reply sent to ThingsBoard")


def main():
    if not TB_TOKEN:
        raise RuntimeError("TB_TOKEN is missing from the .env file")

    print("waiting for ThingsBoard RPC commands")
    print("press Ctrl+C to stop")

    while True:
        try:
            response = requests.get(
                RPC_URL,
                params={"timeout": 20000},
                timeout=25
            )

            if response.status_code in [204, 408]:
                continue

            response.raise_for_status()

            if not response.text.strip():
                continue

            handle_rpc(response.json())

        except requests.ReadTimeout:
            continue
        except requests.RequestException as error:
            print("network error:", error)
        except ValueError as error:
            print("invalid response:", error)
        except KeyboardInterrupt:
            break

    print("\nstopped")


if __name__ == "__main__":
    main()