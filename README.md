# Personalized Social Robot

## Overview

This project delivers a final version of an adaptive social robot designed to enhance user engagement through personalized interactions. with the incorporation of individual personality types, the robot  adjusts its conversational style using **Large Language Models (LLMs)** (via OpenAI GPT) and **DialogFlow** for intent recognition.

The robot:
- Collects user information: name, personality type, and topic of interest.
- Switches to a GPT-centered conversation, adjusting its responses based on the user's personality.
- Engages users with personality-adapted conversation about the specified topic.
---

## Functionality

### Interaction Flow:
1. **Greeting and Information Gathering**:
   - The robot greets the user, introduces itself and collects:
     - **Name**
     - **Personality Type**: Analyst, Explorer, Diplomat, or Sentinel.
     - **Topic of Interest**.
   - This is done via **DialogFlow** for intent recognition.
   - unzip **nao1.zip** to accesss Dialogflow agent definition

2. **Personalized Conversations**:
   - Once the user data is gathered, the robot switches to **GPT-powered interactions**.
   - Tailored prompts guide the conversation based on personality type:
     - **Analyst**: Logical and in-depth explanations.
     - **Explorer**: Imaginative and curiosity-driven responses.
     - **Diplomat**: Empathetic and collaborative discussions.
     - **Sentinel**: Practical and structured guidance.
   - The conversation is limited to **10 turns**.

3. **Verbal and Non-Verbal Behaviors**:
   - **Speech-to-Text**: Transcribes user speech into text using auditory input for intent recognition and conversational processing.
   - **Text-to-Speech**: Converts the robot's text responses into verbal speech, providing clear and engaging audio output.
   - **Postures**: Includes actions like standing and sitting to add physical interaction dynamics.
   - **Gestures**: Executes specific explanatory movements during interactions, enhancing engagement when the robot is speaking.
   - **Blinking**: Performs blinking during the interaction for a more lifelike experience.
   - **Threading**: Enables the robot to perform multiple tasks simultaneously, such as speaking, gesturing, and blinking in parallel. 


---

## Directory and File Structure

- **`Final_version/Conversation.py`**:
  - The **main script** handling:
    - DialogFlow interactions.
    - GPT-powered conversations.
    - Gestures, blinking and motion control.

- **`Final_version/move.py`**:
  - Contains helper functions for robot postures:
    - `stand(nao)`: Makes the robot stand up.
    - `sit(nao)`: Makes the robot sit down.

- **`Final_version/make_prompt.py`**:
  - Defines GPT prompts:
    - Initial prompts tailored for different personality types.
    - Rules for GPT responses during ongoing conversations. Also tailered for different personality types.

---

## How to Run

### Prerequisites
1. **Setup DialogFlow and GPT Services**:
   - Configure DialogFlow for intent recognition.
   - Ensure OpenAI GPT API credentials are set up in an `.env` file.

2. **Install Dependencies**:
   Run the following command to install the required libraries:
   ```bash
   pip install -r requirements.txt

3. **Redis**:
   - Ensure Redis is installed and running.

### Running the Robot
Follow these steps in separate terminals to run the robot:

1. **Start Redis (on Mac)**:
   ```bash
   redis-server conf/redis/redis.conf
   ```
   
2. **Run DialogFlow**:
    ```bash
    run-dialogflow
    ```

3. **Run GPT**:
    ```bash
    run-gpt
    ```

4. **Set correct Nao ip in Conversation.py**:
    ```bash
    nao_ip = "10.0.0.###" # line 182
    ```

5. **Run Conversation.py**:
    ```bash
    python Conversation.py
    ```


## Key Features

1. **Personalized Interaction**:
   - Tailored responses based on personality type, enhancing conversational engagement.

2. **Dynamic Transitions**:
   - Smoothly switches between scripted DialogFlow interactions and GPT-powered conversations.

3. **Verbal and Non-Verbal Communication**:
   - Integrates speech-to-text, text-to-speech, gestures, postures and blinking for a lifelike interaction experience.

4. **Customizable Prompts**:
   - Prompts and response logic can be easily adjusted for different use cases or personality profiles.

5. **Threaded Execution**:
    - Simultaneous tasks like speaking, gesturing, and blinking make for more realistic interactions.
