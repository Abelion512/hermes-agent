# Architectural Test: Multi-Agent Hierarchy

## Objective
Verify the 3-level delegation hierarchy: CEO -> Division -> Worker.

## Instructions for Agent
1. You are the CEO Agent.
2. USE 'abelion_delegate' to delegate to an 'Engineering' Division.
3. The Engineering Division MUST then use 'abelion_delegate' to delegate to a 'FileIO' Worker.
4. The FileIO Worker MUST write "ABELION HIERARCHY SUCCESS" to 'abelion_hierarchy.txt'.
5. DO NOT bypass any level.
6. Verify the file content at the end.

## Success Criteria
- [ ] 'abelion_hierarchy.txt' exists.
- [ ] Content is "ABELION HIERARCHY SUCCESS".
- [ ] Trajectory shows 3 levels of agents.
