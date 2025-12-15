# APO Files Explained

**Both files work together!** Here's how:

| File | Role | When Run |
|------|------|----------|
| **`room_selector_apo.py`** | Training script | ✅ This is what gets executed when you click "Start APO" |
| **`room_selector.py`** | The agent | ✅ Imported and called by the training script |

## The Flow

```
You click "Start APO" (Room Selector)
         ↓
Backend runs: room_selector_apo.py
         ↓
Which imports: room_selector.py (the @rollout agent)
         ↓
APO algorithm calls room_selector() many times with different prompts
```

## In Code

**`room_selector_apo.py`** (the training script):
```python
from room_selector import room_selector, load_room_tasks, prompt_template_baseline

def main():
    algo = APO[RoomSelectionTask](...)
    trainer = Trainer(algorithm=algo, ...)
    trainer.fit(agent=room_selector, ...)  # <-- Calls the agent
```

**`room_selector.py`** (the agent):
```python
@rollout
def room_selector(task, prompt_template) -> float:
    # This function gets called many times during optimization
    ...
```

## Use Case Mapping

| Dashboard Selection | Script Executed |
|---------------------|-----------------|
| "Room Selector" | `room_selector_apo.py` |
| "Wealth Onboarding" | `wealth_onboarding_apo.py` |
