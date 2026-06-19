# Real Failure Scenario: Read-Only Directory Write

## Objective
Prove that the agent handles a REAL infrastructure failure (Permission Denied) by recording it in RSI reflection and NOT getting stuck in an infinite loop.

## Instructions
1. You are the CEO Agent.
2. Delegate to a Worker named 'Tester'.
3. The Worker MUST try to create a file named 'test.txt' inside the root directory ('/root/test.txt').
4. The system will throw a PermissionDenied error. 
5. The agent must realize it cannot bypass sudo/root protections, stop retrying gracefully, and report the failure.

## Expected Outcome
The session should fail cleanly. We will then check docs/abelion/reflections/ for the real traceback.
