import time
from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_motion import NaoPostureRequest
from sic_framework.devices.common_naoqi.naoqi_autonomous import (
    NaoBlinkingRequest,
    NaoListeningMovementRequest,
    NaoSpeakingMovementRequest,
)


def stand(nao):
    """
    Enable blinking, listening, and speaking movements.
    """
    # Make the robot stand up
    print("Making the robot stand up...")
    nao.motion.request(NaoPostureRequest("Stand", speed=0.8))
    time.sleep(2)  # Allow time for the robot to complete the posture


def sit(nao):

    
     # Make the robot sit down
    print("Making the robot sit down...")
    nao.motion.request(NaoPostureRequest("Sit", speed=0.8))
    time.sleep(2)  # Allow time for the robot to adjust to the posture


def main():
    # Initialize the NAO robot
    nao = Nao(ip="10.0.0.248")  # Replace with your robot's IP address

    try:
        

        # Enable blink, listen, and talk movements
        stand(nao)

        # Keep the program running to observe the movements
        print("Blink, listen, and talk movements are active. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected. Shutting down gracefully...")

    finally:
        # Disable blink, listen, and talk movements
        sit(nao)

        # Stop the robot
        print("Stopping the robot...")
        nao.stop()
        print("Robot session ended gracefully.")


if __name__ == "__main__":
    main()
