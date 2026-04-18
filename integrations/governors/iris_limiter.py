import functools
import os
import yaml
import time
import json
from utils.logger import log

class IrisClient:
    """
    Local implementation of the LinkedIn Iris Governor pattern.
    Enforces per-account quotas as defined in iris_config.yaml.
    Stores state in .iris_state.json to persist across runs.
    """
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.state_path = os.path.join(os.path.dirname(config_path), ".iris_state.json")
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.state = self._load_state()
        log.info(f"--- IRIS: Local Governor Initialized with {config_path} ---")

    def _load_state(self):
        if os.path.exists(self.state_path):
            with open(self.state_path, 'r') as f:
                return json.load(f)
        return {"plans": {}}

    def _save_state(self):
        with open(self.state_path, 'w') as f:
            json.dump(self.state, f)

    def throttle(self, plan: str):
        """
        Decorator that enforces the specified quota plan.
        """
        plan_config = self.config['plans'].get(plan)
        if not plan_config:
            raise ValueError(f"Iris Plan '{plan}' not found in config.")

        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Official Pattern: Check quota before execution
                self._check_and_update_quota(plan, plan_config)
                
                try:
                    result = func(*args, **kwargs)
                    # For successful posts, we could track them here if _check_and_update_quota 
                    # didn't already increment. In this hardened implementation, 
                    # we increment on ATTEMPT to be most conservative.
                    return result
                except Exception as e:
                    raise e
            return wrapper
        return decorator

    def _check_and_update_quota(self, plan_name: str, config: dict):
        now = time.time()
        plan_state = self.state["plans"].get(plan_name, {"attempts": []})
        
        # window is in format like '24h'
        window_seconds = 24 * 3600 # default
        if config['window'] == '24h':
            window_seconds = 24 * 3600
            
        # Clean old attempts
        cutoff = now - window_seconds
        plan_state["attempts"] = [t for t in plan_state["attempts"] if t > cutoff]
        
        if len(plan_state["attempts"]) >= config['quota']:
            log.warning(f"--- IRIS: Quota Exceeded for '{plan_name}' ({config['quota']} posts/{config['window']}) ---")
            raise Exception("QuotaExceeded: LinkedIn Iris daily limit reached.")
        
        # Record new attempt
        plan_state["attempts"].append(now)
        self.state["plans"][plan_name] = plan_state
        self._save_state()
        log.info(f"--- IRIS: Quota Check Passed for '{plan_name}' ({len(plan_state['attempts'])}/{config['quota']}) ---")

# Initialize Iris client with the config file
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "configs/iris_config.yaml")

try:
    iris_client = IrisClient(config_path=CONFIG_PATH)
except Exception as e:
    log.error(f"Failed to initialize Iris client: {e}")
    iris_client = None

def iris_guarded_post(func):
    """
    Decorator that enforces LinkedIn Iris rate limiting.
    Specifically uses the 'linkedin_post_daily' plan defined in iris_config.yaml.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not iris_client:
            log.warning("Iris client not initialized - bypassing rate limit safety!")
            return func(*args, **kwargs)
            
        try:
            # Plan name matches iris_config.yaml
            @iris_client.throttle(plan="linkedin_post_daily")
            def _execute():
                return func(*args, **kwargs)
                
            return _execute()
            
        except Exception as e:
            if "QuotaExceeded" in str(e):
                return {
                    "success": False, 
                    "error": "quota_exceeded",
                    "details": "Daily Iris quota for LinkedIn posts reached."
                }
            raise e
            
    return wrapper
