import json
import numpy as np
import time
import os
import random
import threading
from os import environ
from os.path import abspath, join
from time import sleep
from dotenv import load_dotenv
from proto.marshal.collections.maps import MapComposite

from sic_framework.devices import Nao
from sic_framework.devices.nao import NaoqiTextToSpeechRequest
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiAnimationRequest
from sic_framework.devices.common_naoqi.naoqi_autonomous import (
    NaoBlinkingRequest,
    NaoListeningMovementRequest,
    NaoSpeakingMovementRequest,
)
from sic_framework.services.dialogflow.dialogflow import (
    Dialogflow,
    DialogflowConf,
    GetIntentRequest,
    RecognitionResult,
)
from sic_framework.services.openai_gpt.gpt import GPT, GPTConf, GPTRequest

from make_prompt import start_prompt, repeat_rules
from move import stand, sit

from sic_framework.devices.common_naoqi.naoqi_leds import (
    NaoLEDRequest,
    NaoFadeRGBRequest,
)

class NaoHybridConversation:
    def __init__(
        self,
        nao_ip,
        dialogflow_keyfile_path,
        openai_env_path,
        scripted_turns=5,
        conversation_turns=10,
        log_dir="logs",
    ):
        load_dotenv(openai_env_path)
        openai_key = environ.get("OPENAI_API_KEY")

        gpt_conf = GPTConf(openai_key=openai_key)
        self.gpt = GPT(conf=gpt_conf)

        self.nao = Nao(ip=nao_ip)

        dialogflow_conf = DialogflowConf(
            keyfile_json=json.load(open(dialogflow_keyfile_path)),
            sample_rate_hertz=16000,
        )
        self.dialogflow = Dialogflow(ip="localhost", conf=dialogflow_conf)
        self.dialogflow.connect(self.nao.mic)

        self.scripted_turns = scripted_turns
        self.conversation_turns = conversation_turns
        self.context = []

        self.name = None
        self.personality_type = None
        self.topic = None

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        self.log_dir = log_dir
        self.log_file = self.get_unique_log_file()
        self.conversation_log = []

        self.gestures = [
            "Explain_1",
            "Explain_10",
            "Explain_11",
            "Explain_2",
            "Explain_3",
            "Explain_4",
            "Explain_5",
            "Explain_6",
            "Explain_7",
            "Explain_8",
            "YouKnowWhat_1",
            "YouKnowWhat_5",
        ]

        # Blinking control
        self.blink_thread = None
        self.blinking = False

    def get_unique_log_file(self):
        i = 1
        while os.path.exists(os.path.join(self.log_dir, f"user{i}.json")):
            i += 1
        return os.path.join(self.log_dir, f"user{i}.json")

    def log_interaction(self, role, message, intent=None):
        log_entry = {"role": role, "message": message}
        if intent:
            log_entry["intent"] = intent
        self.conversation_log.append(log_entry)
        with open(self.log_file, "w") as f:
            json.dump(self.conversation_log, f, indent=4)

    def parse_map_composite(self, map_composite):
        result = {}
        for key, value in map_composite.items():
            if isinstance(value, MapComposite):
                result[key] = self.parse_map_composite(value)
            else:
                result[key] = value
        return result

    def perform_random_gesture(self):
        gesture = random.choice(self.gestures)
        print(f"[DEBUG] Performing gesture: {gesture}")
        try:
            self.nao.motion.request(NaoqiAnimationRequest(f"animations/Stand/Gestures/{gesture}"))
            #self.log_interaction("NAO", f"Performed gesture: {gesture}")
        except Exception as e:
            print(f"[DEBUG] Failed to perform gesture {gesture}: {e}")
            #self.log_interaction("Error", f"Failed to perform gesture {gesture}: {e}")

    def dialogflow_interaction(self):
        """Handles the scripted Dialogflow conversation."""
        
        session_id = np.random.randint(10000)
        attempts = 0
        max_attempts = 10
        init = True
        name, personality_type, topic = None, None, None

        while attempts < max_attempts:
            try:
                if init:
                    self.nao.tts.request(NaoqiTextToSpeechRequest("Hi there!"))
                    message1 = "Hi there!"
                    self.log_interaction("NAO", message1)
                    print("[DEBUG] Initial greeting sent.")
                    init = False

                reply = self.dialogflow.request(GetIntentRequest(session_id))
                print("[DEBUG] Detected intent:", reply.intent)
                
                if reply.intent:

                    # Added to save all user responses
                    if reply.response.query_result.query_text:
                        user_message = reply.response.query_result.query_text
                        self.log_interaction("user", user_message)
                    
                    # User greets
                    if reply.intent == "1welcome":
                        self.nao.tts.request(NaoqiTextToSpeechRequest("Hi, my name is Nao. What is your name?", animated=True))
                        message2 = "Hi, my name is Nao. What is your name?"
                        print("[DEBUG] Asked for user's name.")
                        self.log_interaction("NAO", message2)
                        continue

                    # User provides their name
                    elif reply.intent == "1welcome_name":
                        parameters = self.parse_map_composite(reply.response.query_result.parameters)
                        name = parameters.get("person", {}).get("name", "Unknown")
                        self.name = name
                        print(f"[DEBUG] Extracted name: {name}")
                        if name:
                            self.nao.tts.request(NaoqiTextToSpeechRequest(f"Hello {name}! Nice to meet you. Could you please tell me your personality type?", animated=True))
                            message3 = f"Hello {name}! Nice to meet you. Could you please tell me your personality type?"
                            self.log_interaction("NAO", message3)
                        else:
                            self.nao.tts.request(NaoqiTextToSpeechRequest("I didn’t catch your name. Could you repeat it, please?", animated=True))
                            print("[DEBUG] Name was not provided or unclear.")
                            message4 = "I didn’t catch your name. Could you repeat it, please?"
                            self.log_interaction("NAO", message4)
                        continue

                    # User has a personality type
                    elif reply.intent == "1welcome_name - yes_personality":
                        personality_type = reply.response.query_result.parameters.get("personality_type", "Unknown")
                        print(f"[DEBUG] Extracted personality type: {personality_type}")
                        self.nao.tts.request(NaoqiTextToSpeechRequest(f"Amazing. Thanks. Just to check, your type is {personality_type}, correct?", animated=True))
                        message5 = f"Amazing. Thanks. Just to check, your type is {personality_type}, correct?"
                        self.log_interaction("NAO", message5)   
                        self.personality_type = personality_type
                        continue

                    # User confirms their personality type
                    elif reply.intent == "1welcome_name - yes_personality - yes":
                        print(f"[DEBUG] Personality type confirmed: {self.personality_type}")
                        self.personality_type = personality_type
                        self.nao.tts.request(NaoqiTextToSpeechRequest("Thank you! I will adjust to your type now. What would you like to talk about today?", animated=True))
                        message6 = "Thank you! I will adjust to your type now. What would you like to talk about today?"
                        self.log_interaction("NAO", message6)
                        continue

                    # User mentions the topic of discussion
                    elif reply.intent == "1welcome_name - yes_personality - yes - custom":
                        topic = reply.response.query_result.parameters.get("topics", "Unknown topic")
                        print(f"[DEBUG] Extracted topic: {topic}")
                        self.topic = topic
                        self.nao.tts.request(NaoqiTextToSpeechRequest(f"Great, sounds interesting! Let's talk about {topic}.", animated=True))
                        message7 = f"Great, sounds interesting! Let's talk about {topic}."
                        self.log_interaction("NAO", message7)
                        break  # Exit the loop after successfully extracting the topic

                    # User says their personality type is incorrect
                    elif reply.intent == "1welcome_name - yes_personality - no":
                        personality_type = reply.response.query_result.parameters.get("personality_type", "Unknown")
                        print(f"[DEBUG] Updated personality type after correction: {personality_type}")
                        self.personality_type = personality_type
                        self.nao.tts.request(NaoqiTextToSpeechRequest(f"Ah, got it. I will adjust to your type of {personality_type}. What would you like to talk about?", animated=True))
                        message8 = f"Ah, got it. I will adjust to your type of {personality_type}. What would you like to talk about?"
                        self.log_interaction("NAO", message8)
                        continue

                    # User does not have a personality type
                    elif reply.intent == "1welcome_name - no_personality":
                        self.nao.tts.request(NaoqiTextToSpeechRequest("No worries! You can fill it out using your phone by scanning the QR code on my back. Let me know when you're ready to continue.", animated=True))
                        print("[DEBUG] User does not have a personality type.")
                        message9 = "No worries! You can fill it out using your phone by scanning the QR code on my back. Let me know when you're ready to continue."
                        self.log_interaction("NAO", message9)
                        continue

                else:
                    self.nao.tts.request(NaoqiTextToSpeechRequest("Sorry, I did not understand. Can you repeat?", animated=True))
                    message10 = "Sorry, I did not understand. Can you repeat?"
                    self.log_interaction("NAO", message10)
                    print("[DEBUG] Intent not understood.")
                    attempts += 1

                if reply and reply.fulfillment_message:
                    print("[DEBUG] Dialogflow Reply:", reply.fulfillment_message)
                    self.nao.tts.request(NaoqiTextToSpeechRequest(reply.fulfillment_message))

            except KeyboardInterrupt:
                print("[DEBUG] Stopping Dialogflow interaction.")
                self.dialogflow.stop()
                break

            except Exception as e:
                print(f"[DEBUG] An error occurred: {e}")
                break

        print(f"[DEBUG] Final data: Name = {self.name}, Personality Type = {self.personality_type}, Topic = {self.topic}")
        final_data = f"[DEBUG] Final data: Name = {self.name}, Personality Type = {self.personality_type}, Topic = {self.topic}"
        self.log_interaction("Final Data", final_data)
        if self.name and self.personality_type and self.topic:
            self.gpt_interaction()  # Start GPT interaction after collecting all necessary data


    def prompt(self, name, personality_type, topic):
        prompt = start_prompt(name, personality_type, topic)
        return prompt

    def repeat_context(self, reaction, name, personality_type, topic):
        rules = repeat_rules(reaction, name, personality_type, topic)
        return rules

    def gpt_interaction(self):
        if not self.name or not self.personality_type or not self.topic:
            message = "I need more information to start the discussion."
            self.nao.tts.request(NaoqiTextToSpeechRequest(message))
            self.log_interaction("NAO", message)
            return

        start_prompt_str = self.prompt(self.name, self.personality_type, self.topic)
        print(f"[DEBUG] Starting GPT interaction with prompt: {start_prompt_str}")

        for turn in range(self.conversation_turns):
            print(f"[DEBUG] --- GPT Turn {turn + 1} ---")

            if turn == 0:
                prompt = start_prompt_str
            else:
                prompt = self.repeat_context(user_input, self.name, self.personality_type, self.topic)

            gpt_request = GPTRequest(prompt, max_tokens=200)
            gpt_response = self.gpt.request(gpt_request)
            response_text = str(gpt_response.response)
            print(f"[DEBUG] GPT Response: {response_text}")

            speech_done = threading.Event()

            def speak():
                self.nao.tts.request(NaoqiTextToSpeechRequest(response_text))
                speech_done.set()

            def gesture():
                while not speech_done.is_set():
                    self.perform_random_gesture()
                    time.sleep(1)

            speech_thread = threading.Thread(target=speak)
            gesture_thread = threading.Thread(target=gesture)
            speech_thread.start()
            gesture_thread.start()

            speech_thread.join()
            gesture_thread.join()

            self.log_interaction("NAO", response_text)

            user_input = self.listen_to_user()
            if not user_input:
                message = "I didn't catch that. Can you repeat?"
                self.nao.tts.request(NaoqiTextToSpeechRequest(message, animated=True))
                self.log_interaction("NAO", message)
                continue

            self.log_interaction("user", user_input)
            self.context.append({"role": "user", "content": user_input})
            self.context.append({"role": "assistant", "content": response_text})

    def listen_to_user(self, retries=3):
        for _ in range(retries):
            request_id = np.random.randint(10000)
            response = self.dialogflow.request(GetIntentRequest(request_id))
            if response and response.response.query_result.query_text:
                print("User said:", response.response.query_result.query_text)
                return response.response.query_result.query_text
        print("No valid response received after retries.")
        return None


    def start_blinking(self):
        """
        Starts a thread that continuously "blinks" the robot's eye LEDs
        until stopped. A "blink" can be simulated by turning off LEDs
        briefly and then turning them back on.
        """
        self.blinking = True
        self.blink_thread = threading.Thread(target=self._blink_loop)
        self.blink_thread.start()

    def stop_blinking(self):
        """
        Stops the blinking thread.
        """
        self.blinking = False
        if self.blink_thread is not None:
            self.blink_thread.join()

    def _blink_loop(self):
        # Set initial LED color or state if desired
        self.nao.leds.request(NaoLEDRequest("FaceLeds", True))
        while self.blinking:
            # Turn LEDs off briefly
            self.nao.leds.request(NaoLEDRequest("FaceLeds", False))
            time.sleep(0.15)  # Eyes closed for 0.15 seconds
            # Turn LEDs back on
            self.nao.leds.request(NaoLEDRequest("FaceLeds", True))
            # Wait a while before next blink
            time.sleep(3)  # Blink every 5 seconds

    def start_conversation(self):
        self.dialogflow_interaction()


def main():
    nao_ip = "10.0.0.241"
    dialogflow_keyfile_path = abspath(join('..', 'conf', 'dialogflow', 'nao1_real.json'))
    openai_env_path = abspath(join("..", "conf", "openai", ".openai_env"))

    nao = Nao(ip=nao_ip)

    hybrid_conversation = NaoHybridConversation(
        nao_ip=nao_ip,
        dialogflow_keyfile_path=dialogflow_keyfile_path,
        openai_env_path=openai_env_path,
        scripted_turns=10,
        conversation_turns=10,
        log_dir="logs"
    )

    try:
        print("Initializing robot movements...")
        stand(nao)

        # Start blinking after the robot stands up
        hybrid_conversation.start_blinking()

        print("Starting hybrid conversation...")
        hybrid_conversation.start_conversation()

    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected. Shutting down gracefully.")

    finally:
        # Stop blinking before sitting down
        hybrid_conversation.stop_blinking()

        print("Disabling movements and resetting robot posture...")
        sit(nao)
        nao.stop()
        print("Robot session ended gracefully.")


if __name__ == "__main__":
    main()