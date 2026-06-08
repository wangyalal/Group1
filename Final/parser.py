import os
import json
from datetime import date, timedelta
from huggingface_hub import hf_hub_download
#import bootstrap  # Keeps Python 3.14 DLL paths stabilized on Windows(may or may not be necessary)
#bootstrap.initialize_environment()

try:
    from llama_cpp import Llama
except ImportError as e:
    print("Error loading llama_cpp. If you are on Windows, ensure your GPU drivers/CUDA paths are set up globally.")
    raise e

from aischema import TransactionData
from HWconfig import get_optimal_gpu_layers

# Standardized path to model
#MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "Qwen2.5-7B-Instruct-Q4_K_M.gguf")

repo_id = "Qwen/Qwen2.5-7B-Instruct-GGUF"
model_filename = "Qwen2.5-7B-Instruct-Q4_K_M.gguf"

def find_or_dl_model() -> str:
    """
    Check if the model exists in local 'models' directory, downloads and places it there using hugging face.
    """
    local_dir = os.path.join(os.path.dirname(__file__),"models")
    local_path = os.path.join(local_dir, model_filename)
    if os.path.exists(local_path):
        print(f"[Model Check] Found model locally at: {local_path}")
        return local_path
    
    print(f"[Model Check] Model not found locally. Downloading {model_filename} from hugging face")
    print("NB: Depending on internet speed may take a while")
    #hugging face function to download model and store in target folder
    dl_path = hf_hub_download(repo_id=repo_id, filename=model_filename, local_dir=local_dir, local_dir_use_symlinks=False)
    print(f"Model download complete and saved to:{dl_path}")
    return dl_path

#function call to resolve model path
MODEL_PATH = find_or_dl_model()

# Calculate layers dynamically based hardware
GPU_LAYERS = get_optimal_gpu_layers()

print(f"Loading Qwen 2.5 Engine (Targeting {GPU_LAYERS if GPU_LAYERS != -1 else 'ALL'} layers)...")
llm = Llama(
    model_path=MODEL_PATH,
    n_gpu_layers=GPU_LAYERS,
    n_ctx=1024,
    temperature=0.1,
    verbose=False
)

def calc_date(weekday_name: str, weeks_ago: int) -> str:
    today = date.today()
    
    # Handle absolute quick targets
    if weekday_name.lower() == "today":
        return today.strftime("%Y-%m-%d")
    if weekday_name.lower() == "yesterday":
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")
        
    # Map weekdays to integers (Monday=0, Tuesday=1, ..., Sunday=6)
    days_map = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
    
    target_weekday_num = days_map.get(weekday_name.lower(), today.weekday())
    current_weekday_num = today.weekday()
    
    # Find this week's target day by computing the difference
    days_difference = current_weekday_num - target_weekday_num
    this_weeks_target_date = today - timedelta(days=days_difference)
    
    # Subtract the number of weeks requested
    final_date = this_weeks_target_date - timedelta(weeks=weeks_ago)
    return final_date.strftime("%Y-%m-%d")

def parse_natural_language_expense(user_text: str) -> dict:
    today_str = date.today().strftime("%Y-%m-%d")
    
    messages = [
        {
            "role": "system",
            "content": (
                "You are a precise backend data-parsing engine. Extract transactions into strict JSON.\n\n"
                "TRANSACTION TYPE RULES:\n"
                "1. Look closely at the action verb in the user text to determine 'transaction_type'.\n"
                "2. If the text uses words like 'earned', 'made', 'received', 'paid for work', 'salary', 'bonus', or 'got paid', you MUST classify it as 'Income'.\n"
                "3. If the text uses words like 'bought', 'spent', 'paid for', 'purchased', 'cost', or 'ordered', classify it as 'Expense'.\n\n"
                "RULES FOR TIME EXTRACTION:\n"
                "- 'bought a sofa last week tuesday': weekday_mentioned='Tuesday', weeks_ago_modifier=1\n"
                "- 'mop on friday two weeks ago': weekday_mentioned='Friday', weeks_ago_modifier=2\n"
                "- 'yesterday': weekday_mentioned='Yesterday', weeks_ago_modifier=0\n"
                "- 'today': weekday_mentioned='Today', weeks_ago_modifier=0\n\n"
                "CRITICAL CATEGORY RULES:\n"
                "If the item does not fit the specific categories, classify it as 'Other'."
            )
        },
        {
            "role": "user",
            "content": f"Parse this statement: '{user_text}'"
        }
    ]
    
    response = llm.create_chat_completion(
        messages=messages,
        response_format={
            "type": "json_object",
            "schema": TransactionData.model_json_schema(),
        }
    )
    
    raw_data = json.loads(response["choices"][0]["message"]["content"])
    
    # --- Python takes over the calculation entirely ---
    day_name = raw_data.get("weekday_mentioned", "Today")
    weeks_back = raw_data.get("weeks_ago_modifier", 0)
    
    raw_data["transaction_date"] = calc_date(day_name, weeks_back)

    #force positive amount
    if "amount" in raw_data and raw_data["amount"] is not None:
        raw_data["amount"] = abs(float(raw_data["amount"]))
    
    # Clean up fields so the GUI doesn't see the helper keys
    if "weekday_mentioned" in raw_data: del raw_data["weekday_mentioned"]
    if "weeks_ago_modifier" in raw_data: del raw_data["weeks_ago_modifier"]
    
    return raw_data