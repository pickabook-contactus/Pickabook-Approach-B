import replicate
from dotenv import load_dotenv
import os

load_dotenv(override=True)

def check_failed_predictions():
    print("Fetching recent predictions...")
    predictions = replicate.predictions.list()
    
    count = 0
    for pred in predictions:
        if count > 10: break
        
        # Check if it matches our target model
        # The model name might be full ID, so check substring
        # Inspect structure safely
        # model usually matches "owner/name"
        try:
             # Depending on Replicate SDK version, exact path varies
             # Just check string representation for simplicity
             if "advanced-face-swap" in str(pred):
                print(f"ID: {pred.id} | Status: {pred.status}")
                if pred.status == "failed":
                    print(f"ERROR LOG: {pred.error}")
                    print(f"LOGS:\n{pred.logs}")
                    print("-" * 40)
        except Exception as e:
            print(f"Error checking pred: {e}")
        count += 1

if __name__ == "__main__":
    check_failed_predictions()
