import logging
from collections import deque

logger = logging.getLogger(__name__)

class LoopDetector:
    def __init__(self, max_similar_actions=3, window_size=5):
        self.max_similar_actions = max_similar_actions
        self.window_size = window_size
        self.action_history = deque(maxlen=window_size)

    def add_action(self, tool_name, args):
        self.action_history.append({"tool": tool_name, "args": args})

    def is_infinity_loop(self):
        if len(self.action_history) < self.max_similar_actions:
            return False
        
        # Simple detection: check if the same tool with same args is called repeatedly
        recent = list(self.action_history)
        last_action = recent[-1]
        count = 0
        for action in reversed(recent):
            if action["tool"] == last_action["tool"] and action["args"] == last_action["args"]:
                count += 1
            else:
                break
        
        return count >= self.max_similar_actions

_detector = LoopDetector()

def check_loop(tool_name, args, **kwargs):
    """
    Hook: pre_tool_call
    """
    _detector.add_action(tool_name, args)
    if _detector.is_infinity_loop():
        logger.warning(f"[abelion_autonomous] Infinity loop detected for tool: {tool_name}")
        # In Phase 1, we just log. In later phases, we might raise an exception or alert the user.
        # To break the loop in Hermes, we might need to return a specific value or raise an error.
        # For now, let's keep it passive as requested for "light task".
    return None
