import os
import groq
from groq import Groq
import json
from requests.exceptions import HTTPError
import time
import socket
import sys

# Replace 'your_groq_api_key' with your actual Groq API key
GROQ_API_KEY = "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"
MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"
MODEL2 = "llama-3.3-70b-versatile"
MODEL3 = "meta-llama/llama-4-scout-17b-16e-instruct"
MODEL4 = "deepseek-r1-distill-llama-70b"

# Much smaller content to reduce input size
CONTENT = '''# CIVilizaTu game project
A web-based strategy game inspired by Civilization where players take turns against an AI opponent.
The game includes cities, resources, and technology development.'''

# Create a list of models to try in sequence
MODELS_TO_TRY = [MODEL4, MODEL3, MODEL2, MODEL]

# Rate limit testing settings
RATE_LIMIT_TEST = True
REQUEST_DELAY = 0.5  # Half second between requests to trigger limits faster
MAX_RETRIES = 3      # Maximum number of connection retries
RETRY_DELAY = 2      # Initial delay between retries (will increase with backoff)

# Start with the first model and only change on errors
current_model_index = 0
current_model = MODELS_TO_TRY[current_model_index]

try:
    for i in range(0, 10000):
        client = Groq(api_key=GROQ_API_KEY)
        
        print(f"\n--- Request #{i} using model: {current_model} ---")
        
        # Add retry logic for connection issues
        retry_count = 0
        success = False
        
        while retry_count <= MAX_RETRIES and not success:
            try:
                # Use a system message to request a brief response
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "Provide very brief responses of just 1-2 sentences."},
                        {"role": "user", "content": "Summarize this briefly: " + CONTENT},
                    ],
                    model=current_model,
                    max_tokens=100,  # Limit output size
                    temperature=0.7,
                    timeout=30.0,    # Set an explicit timeout
                )
                
                print("Response:")
                print(chat_completion.choices[0].message.content)
                success = True
                
            except (socket.error, ConnectionError, TimeoutError) as e:
                retry_count += 1
                wait_time = RETRY_DELAY * (2 ** (retry_count - 1))  # Exponential backoff
                
                print(f"\n⚠️  Connection error: {e}")
                print(f"Retry {retry_count}/{MAX_RETRIES} in {wait_time} seconds...")
                
                with open("connection_errors.log", "a") as log:
                    log.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Connection error with {current_model}: {e}\n")
                
                time.sleep(wait_time)
                
                if retry_count > MAX_RETRIES:
                    print("Max retries exceeded, switching models...")
                    # Only switch models after exhausting retries
                    current_model_index = (current_model_index + 1) % len(MODELS_TO_TRY)
                    current_model = MODELS_TO_TRY[current_model_index]
                    break
                
            except groq.RateLimitError as e:
                print("\n")
                print("*" * 80)
                print("*" + " "*78 + "*")
                print("*" + "🚫 RATE LIMIT ERROR DETECTED (429) 🚫".center(78) + "*")
                print("*" + "-"*78 + "*")
                print("*" + f"Model: {current_model}".center(78) + "*")
                print("*" + f"Request: #{i}".center(78) + "*")
                print("*" + "-"*78 + "*")
                print("*" + "Error details:".center(78) + "*")
                print("*" + str(e).center(78) + "*")
                print("*" + " "*78 + "*")
                print("*" * 80)
                print("\n")
                
                # Log the error with timestamp
                with open("rate_limit_errors.log", "a") as log:
                    log.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Rate limit hit with {current_model}\n")
                
                # Switch models on rate limit error
                current_model_index = (current_model_index + 1) % len(MODELS_TO_TRY)
                current_model = MODELS_TO_TRY[current_model_index]
                
                print(f"Switching to model: {current_model}")
                print("Waiting 5 seconds before next request...")
                time.sleep(5)
                break
                
            except Exception as e:
                print(f"\n⚠️  Error encountered: {e}")
                
                # Check if it's a 429 error but caught as a different exception type
                error_str = str(e).lower()
                if "429" in error_str or "too many requests" in error_str or "rate limit" in error_str:
                    print("\n")
                    print("#" * 80)
                    print("#" + "429 RATE LIMITING ERROR DETECTED AS GENERAL EXCEPTION!".center(78) + "#")
                    print("#" * 80)
                    print("\n")
                    
                    # Log the error with timestamp
                    with open("rate_limit_errors.log", "a") as log:
                        log.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 429 error via general exception with {current_model}\n")
                    
                    # Switch models on rate limit error
                    current_model_index = (current_model_index + 1) % len(MODELS_TO_TRY)
                    current_model = MODELS_TO_TRY[current_model_index]
                    print(f"Switching to model: {current_model}")
                
                else:
                    # For other errors, log but don't switch models unless max retries reached
                    retry_count += 1
                    wait_time = RETRY_DELAY * (2 ** (retry_count - 1))
                    
                    with open("general_errors.log", "a") as log:
                        log.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error with {current_model}: {e}\n")
                    
                    print(f"Retry {retry_count}/{MAX_RETRIES} in {wait_time} seconds...")
                    time.sleep(wait_time)
                    
                    if retry_count > MAX_RETRIES:
                        print("Max retries exceeded, switching models...")
                        current_model_index = (current_model_index + 1) % len(MODELS_TO_TRY)
                        current_model = MODELS_TO_TRY[current_model_index]
                
                break
        
        # Add short delay between requests if testing rate limits
        if RATE_LIMIT_TEST and success:
            time.sleep(REQUEST_DELAY)
            
except KeyboardInterrupt:
    print("\nExiting script due to keyboard interrupt...")
    sys.exit(0)
