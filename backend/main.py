from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import re
import json
import subprocess
import threading
import time
import os
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Try both: repo/examples/apo/apo.log and repo/examples/apo/backend/apo.log
APO_LOG_PATHS = [
    Path(__file__).parent.parent / "apo.log",
    Path(__file__).parent / "apo.log",
]

# Also look for run logs
RUN_LOGS_DIR = Path(__file__).parent / "run_logs"

def locate_apo_log():
    """Find the most recent APO log - prefer run_logs if available"""
    # First check run_logs directory for any logs
    if RUN_LOGS_DIR.exists():
        logs = sorted(RUN_LOGS_DIR.glob("run_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        if logs:
            return logs[0]
    # Fall back to standard locations
    for p in APO_LOG_PATHS:
        if p.exists():
            return p
    return APO_LOG_PATHS[0]

APO_LOG_PATH = locate_apo_log()

# Track running APO processes in-memory: pid -> {process, log}
RUN_PROCS: dict[int, dict] = {}

# ============================================================
# MOCK DATA: Realistic 10-version APO optimization journey
# ============================================================
def generate_mock_optimization_data():
    """Generate realistic mock data showing 10 prompt versions with clear optimization story"""
    
    # The prompts showing evolution from verbose to optimized
    prompts_data = [
        {
            "version": "0",
            "prompt": """You are a helpful assistant for a hotel booking system. Your task is to help users select the best room for their needs.

When a user describes their preferences, analyze their requirements and recommend the most suitable room from the available options.

Consider factors like:
- Budget constraints
- Number of guests
- Desired amenities
- Special requests

Please provide a clear recommendation with reasoning.""",
            "parent": None,
            "is_seed": True,
            "round": 0,
            "changes": "Original seed prompt",
            "strategy": "baseline"
        },
        {
            "version": "1",
            "prompt": """You are a hotel room selection assistant. Help users find the perfect room.

TASK: Analyze user preferences and recommend the best room option.

CONSIDER:
1. Budget (strict constraint)
2. Guest count (must fit)
3. Amenities (nice to have)
4. Special needs (accessibility, etc.)

OUTPUT: Room recommendation with brief justification.""",
            "parent": "0",
            "is_seed": False,
            "round": 1,
            "changes": "Structured format, clearer instructions",
            "strategy": "Add structure"
        },
        {
            "version": "2", 
            "prompt": """Hotel Room Selector

INPUT: User preferences (budget, guests, amenities)
OUTPUT: Best room match with reason

Rules:
- Never exceed budget
- Room must fit all guests  
- Match amenities when possible
- Flag any constraints that can't be met

Be concise. One room recommendation only.""",
            "parent": "1",
            "is_seed": False,
            "round": 1,
            "changes": "More concise, added explicit rules",
            "strategy": "Reduce tokens"
        },
        {
            "version": "3",
            "prompt": """You are an expert hotel concierge AI. Your role is to match guests with their ideal room.

PROCESS:
1. Parse guest requirements carefully
2. Filter rooms by hard constraints (budget, capacity)
3. Rank remaining rooms by amenity match
4. Select top choice

RESPONSE FORMAT:
- Recommended Room: [room name]
- Price: [price]
- Why: [1-2 sentence justification]
- Alternative: [backup option if available]

Be helpful and professional.""",
            "parent": "1",
            "is_seed": False,
            "round": 2,
            "changes": "Added step-by-step process, response format",
            "strategy": "Chain of thought"
        },
        {
            "version": "4",
            "prompt": """ROLE: Hotel room matcher
GOAL: Best room for guest needs

HARD CONSTRAINTS (must meet):
- Budget: never exceed
- Capacity: must fit all guests

SOFT CONSTRAINTS (prefer):
- Amenities match
- Guest preferences

OUTPUT: JSON format
{
  "room": "name",
  "price": number,
  "reason": "brief explanation"
}""",
            "parent": "2",
            "is_seed": False,
            "round": 2,
            "changes": "JSON output format, hard vs soft constraints",
            "strategy": "Structured output"
        },
        {
            "version": "5",
            "prompt": """Select the best hotel room for the guest.

CRITICAL: Stay within budget. Room must fit all guests.

Steps:
1. Check budget limit
2. Check guest count
3. Match amenities
4. Pick best fit

Reply with: [Room Name] - $[Price] - [One sentence why]""",
            "parent": "4",
            "is_seed": False,
            "round": 3,
            "changes": "Simplified, emphasized critical constraints",
            "strategy": "Emphasis on constraints"
        },
        {
            "version": "6",
            "prompt": """You're a hotel booking AI. Match guests to rooms.

RULES:
1. BUDGET IS ABSOLUTE - never recommend over budget
2. CAPACITY IS ABSOLUTE - room must fit everyone
3. Amenities are preferences, not requirements

THINK: What does this guest really need?
THEN: Pick the room that best balances their needs.

Answer: "[Room]" because [reason]. Price: $[X]""",
            "parent": "3",
            "is_seed": False,
            "round": 3,
            "changes": "Added reasoning prompt, clearer priority",
            "strategy": "Think-then-answer"
        },
        {
            "version": "7",
            "prompt": """Hotel Room Selector v7

Given guest preferences, select optimal room.

Priority order:
1. Within budget (REQUIRED)
2. Fits all guests (REQUIRED)  
3. Has requested amenities (PREFERRED)
4. Best value (TIEBREAKER)

<output>
Room: [name]
Price: [amount]
Match: [why this room fits]
</output>""",
            "parent": "5",
            "is_seed": False,
            "round": 4,
            "changes": "Explicit priority ordering, XML-style output",
            "strategy": "Priority hierarchy"
        },
        {
            "version": "8",
            "prompt": """Match hotel guest to best room.

MUST: budget ok, capacity ok
WANT: amenities, value

Think step by step:
1. List rooms in budget
2. Filter by capacity
3. Score by amenity match
4. Return best

Format: ROOM | PRICE | REASON""",
            "parent": "7",
            "is_seed": False,
            "round": 4,
            "changes": "Minimal tokens, step-by-step scoring",
            "strategy": "Minimal + CoT"
        },
        {
            "version": "9",
            "prompt": """You are a precise hotel room selector.

INPUT: Guest needs (budget, guests, preferences)
OUTPUT: Single best room choice

ALGORITHM:
1. Eliminate rooms over budget
2. Eliminate rooms too small
3. From remaining, pick highest amenity match
4. Ties: pick cheaper option

RESPOND: [Room Name] at $[Price]. Chosen because: [reason]

Be direct. No alternatives needed.""",
            "parent": "8",
            "is_seed": False,
            "round": 5,
            "changes": "Algorithm-style instructions, tiebreaker rule",
            "strategy": "Algorithmic"
        },
    ]
    
    # Generate realistic metrics - showing improvement over time with some variation
    # Best performer should be v7 or v8 to show optimization worked
    base_scores = {
        "0": 0.62,  # Seed - decent but verbose
        "1": 0.68,  # Better structure
        "2": 0.64,  # Too terse, lost context
        "3": 0.75,  # Good process
        "4": 0.71,  # JSON format helped
        "5": 0.73,  # Simple but effective
        "6": 0.78,  # Think-then-answer works well
        "7": 0.85,  # Best! Priority ordering is key
        "8": 0.82,  # Good but maybe too minimal
        "9": 0.80,  # Algorithmic works but slightly worse
    }
    
    metrics = []
    for p in prompts_data:
        ver = p["version"]
        base_score = base_scores[ver]
        
        # Add some realistic variation
        tasks = 20
        # Calculate successes based on score
        successes = int(tasks * (base_score + random.uniform(-0.05, 0.05)))
        successes = max(0, min(tasks, successes))
        
        # Token cost based on prompt length
        token_cost = len(p["prompt"].split())
        
        # Generate individual rewards
        rewards = []
        for _ in range(tasks):
            if random.random() < base_score:
                rewards.append(round(random.uniform(0.7, 1.0), 3))
            else:
                rewards.append(round(random.uniform(0.0, 0.4), 3))
        
        avg_reward = sum(rewards) / len(rewards)
        
        metrics.append({
            "version": ver,
            "tasks": tasks,
            "successes": successes,
            "failures": tasks - successes,
            "rewards": rewards,
            "average": round(avg_reward, 4),
            "prompt": p["prompt"],
            "parent": p["parent"],
            "is_seed": p["is_seed"],
            "avg_cost": token_cost,
            "round": p.get("round", 0),
            "changes": p.get("changes", ""),
            "strategy": p.get("strategy", ""),
            "success_rate": round(successes / tasks * 100, 1),
            "cost_per_success": round(token_cost / max(successes, 1), 2)
        })
    
    # Sort by version
    metrics.sort(key=lambda x: int(x["version"]))
    
    # Find best and worst
    best = max(metrics, key=lambda x: x["average"])
    worst = min(metrics, key=lambda x: x["average"])
    seed = metrics[0]
    most_efficient = min(metrics, key=lambda x: x["cost_per_success"])
    
    # Create optimization story
    optimization_story = {
        "seed_version": seed["version"],
        "seed_score": seed["average"],
        "seed_cost": seed["avg_cost"],
        "best_version": best["version"],
        "best_score": best["average"],
        "best_cost": best["avg_cost"],
        "best_strategy": best["strategy"],
        "improvement": round(best["average"] - seed["average"], 4),
        "improvement_pct": round((best["average"] - seed["average"]) / seed["average"] * 100, 1),
        "cost_change": best["avg_cost"] - seed["avg_cost"],
        "cost_change_pct": round((best["avg_cost"] - seed["avg_cost"]) / seed["avg_cost"] * 100, 1),
        "total_versions_tested": len(metrics),
        "most_efficient_version": most_efficient["version"],
        "most_efficient_cost_per_success": most_efficient["cost_per_success"],
        "worst_version": worst["version"],
        "worst_score": worst["average"],
        "key_insight": f"Adding explicit priority ordering (v{best['version']}) improved accuracy by {round((best['average'] - seed['average']) / seed['average'] * 100, 1)}% while reducing token cost by {abs(round((best['avg_cost'] - seed['avg_cost']) / seed['avg_cost'] * 100, 1))}%",
        "recommendations": [
            {
                "action": "Use Priority Hierarchy",
                "description": f"Version {best['version']} performs best by clearly separating REQUIRED vs PREFERRED constraints",
                "impact": "high"
            },
            {
                "action": "Add Structure",
                "description": "Structured output formats (XML tags, specific format) improve consistency",
                "impact": "medium"
            },
            {
                "action": "Reduce Verbosity", 
                "description": f"Your seed prompt uses {seed['avg_cost']} tokens. Best version uses only {best['avg_cost']} tokens (-{abs(round((best['avg_cost'] - seed['avg_cost']) / seed['avg_cost'] * 100, 1))}%)",
                "impact": "medium"
            },
            {
                "action": "Avoid Over-Simplification",
                "description": f"Version 2 shows that being too terse ({metrics[2]['average']:.2%} accuracy) hurts performance",
                "impact": "low"
            }
        ]
    }
    
    return {
        "prompts": prompts_data,
        "metrics": metrics,
        "rounds": [
            {"round": 0, "description": "Seed evaluation", "versions": ["0"]},
            {"round": 1, "description": "Structure variations", "versions": ["1", "2"]},
            {"round": 2, "description": "Process & format experiments", "versions": ["3", "4"]},
            {"round": 3, "description": "Constraint emphasis", "versions": ["5", "6"]},
            {"round": 4, "description": "Priority & minimalism", "versions": ["7", "8"]},
            {"round": 5, "description": "Algorithmic refinement", "versions": ["9"]},
        ],
        "optimization_story": optimization_story
    }


PROMPT_PATTERN = re.compile(r"\[Prompt v(\w+)]|New prompt template created from parent v\w+: v(\w+)|^\s*`{3}(.*?)`{3}", re.DOTALL | re.MULTILINE)

# Utility to parse apo.log for prompt history and metrics
def parse_apo_log(log_path: Path = None):
    log_file = log_path or locate_apo_log()
    if not log_file.exists():
        return {"prompts": [], "metrics": [], "rounds": [], "optimization_story": None}
    with open(log_file, "r") as f:
        full_log = f.read()
    
    # Find the start of the latest APO run by looking for "Seed prompt baseline score"
    # This marks the beginning of each APO optimization session
    seed_markers = list(re.finditer(r'Seed prompt baseline score', full_log))
    if seed_markers:
        # Get content from the last seed prompt marker onwards
        last_marker_pos = seed_markers[-1].start()
        # Go back to find the start of that line/section (find the previous [Round 00 marker)
        round_start = full_log.rfind('[Round 00', 0, last_marker_pos)
        if round_start == -1:
            round_start = max(0, last_marker_pos - 2000)  # fallback to 2000 chars before
        log = full_log[round_start:]
    else:
        log = full_log
    
    prompts = []
    metrics = []
    rounds_info = []
    gradients = []

    # Extract initial prompt (v0) - seed prompt
    # Try with code block first - look for first code block in log as seed
    first_block = re.search(r"```(.*?)```", log, re.DOTALL)
    if first_block:
        seed_text = first_block.group(1).strip()
        # Clean up whitespace from rich console format
        seed_text = re.sub(r'\s+', ' ', seed_text)
        prompts.append({"version": "0", "prompt": seed_text, "parent": None, "is_seed": True})

    # Extract prompt templates more robustly: find fenced code blocks and
    # associate them with a nearby version marker in the surrounding context.
    seen_versions = {"0"} if prompts else set()
    
    # Find all "New prompt template created" entries with their full content
    # Handle both standard format and rich console format (multi-line with whitespace)
    for m in re.finditer(r"\[Round (\d+) \| Prompt v(\w+)\] New prompt template created from parent v(\w+):\s*```(.*?)```", log, re.DOTALL):
        round_num = m.group(1)
        ver = m.group(2)
        parent = m.group(3)
        block = m.group(4).strip()
        if ver not in seen_versions:
            prompts.append({"version": ver, "prompt": block, "parent": parent, "round": int(round_num), "is_seed": False})
            seen_versions.add(ver)

    # For rich console format, find all code blocks first, then match to versions
    code_blocks = list(re.finditer(r'```(.*?)```', log, re.DOTALL))
    
    # Find version creation entries and match to nearest subsequent code block
    for m in re.finditer(r"Prompt v(\w+)\] New prompt template created from parent v(\w+):", log):
        ver = m.group(1)
        parent = m.group(2)
        if ver not in seen_versions and ver != "0":  # Skip v0, it's the seed
            # Find the next code block after this position
            for cb in code_blocks:
                if cb.start() > m.end() and cb.start() < m.end() + 3000:
                    block = cb.group(1).strip()
                    # Clean up whitespace from rich console format
                    block = re.sub(r'\s+', ' ', block)
                    if len(block) > 50:  # Only add if it's a real prompt
                        prompts.append({"version": ver, "prompt": block, "parent": parent, "round": 1, "is_seed": False})
                        seen_versions.add(ver)
                        break

    # Also try simpler pattern as fallback
    for m in re.finditer(r"```(.*?)```", log, re.DOTALL):
        block = m.group(1).strip()
        start = m.start()
        context_start = max(0, start - 400)
        context = log[context_start:start]
        ver = None
        parent = None
        # prefer explicit markers
        for pat in [r"Prompt v(?P<ver>\w+)", r"New prompt template created from parent v(?P<parent>\w+):\s*v(?P<ver>\w+)"]:
            mm = re.search(pat, context, re.IGNORECASE | re.DOTALL)
            if mm:
                ver = mm.group('ver')
                parent = mm.groupdict().get('parent')
                break
        if ver and ver not in seen_versions:
            # Clean up whitespace from rich console format
            block = re.sub(r'\s+', ' ', block)
            prompts.append({"version": ver, "prompt": block, "parent": parent, "is_seed": ver == "0"})
            seen_versions.add(ver)

    # Extract gradient/critique information
    for m in re.finditer(r"\[Round (\d+).*?Prompt v(\w+)\] Gradient computed.*?has result: (.*?)(?=\s*INFO|\s*\[|\Z)", log, re.DOTALL):
        round_num = m.group(1)
        ver = m.group(2)
        gradient_text = m.group(3).strip()[:500]  # Truncate long gradients
        gradients.append({"round": int(round_num), "version": ver, "gradient": gradient_text})

    # Extract evaluation metrics lines - handle both apo.log format and rich console format
    # The rich console format splits "average is X" across multiple lines
    # Pattern: look for "average" followed eventually by "is" and then a number
    for match in re.finditer(r"\[Round (?P<round>\d+).*?Prompt v(?P<ver>\w+)\].*?Evaluated (?P<tasks>\d+) rollouts\..*?Statuses: Counter\((?P<statuses>.*?)\)\..*?average.*?is\s+(?P<avg>[-0-9.]+)", log, re.DOTALL):
        round_num = match.group('round')
        ver = match.group('ver')
        tasks = int(match.group('tasks'))
        statuses_raw = match.group('statuses')
        # find succeeded count if present
        succ_match = re.search(r"'succeeded':\s*(\d+)", statuses_raw)
        failed_match = re.search(r"'failed':\s*(\d+)", statuses_raw)
        succeeded = int(succ_match.group(1)) if succ_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0
        # Try to extract rewards, but they may not be captured in multi-line format
        try:
            rewards_raw = match.group('rewards')
            rewards = []
            for part in rewards_raw.split(','):
                p = part.strip()
                if not p or p == 'None':
                    continue
                try:
                    rewards.append(float(p))
                except ValueError:
                    continue
        except IndexError:
            rewards = []
        avg = float(match.group('avg'))
        metrics.append({
            "version": ver,
            "round": int(round_num),
            "tasks": tasks,
            "successes": succeeded,
            "failures": failed,
            "rewards": rewards,
            "average": avg,
        })

    # Extract round-level information
    for m in re.finditer(r"\[Round (\d+)\] Round (\d+)/(\d+)", log):
        round_num = int(m.group(1))
        current = int(m.group(2))
        total = int(m.group(3))
        rounds_info.append({"round": round_num, "current": current, "total": total})
    
    # Extract parent prompt info for each round
    for m in re.finditer(r"\[Round (\d+)\] Parent prompts: (.*?)(?:\n|$)", log):
        round_num = int(m.group(1))
        parents = m.group(2).strip()
        for r in rounds_info:
            if r["round"] == round_num:
                r["parents"] = parents
    
    # Extract top candidates info
    for m in re.finditer(r"\[Round (\d+)\] Top (\d+) candidates.*?: \[(.*?)\]", log):
        round_num = int(m.group(1))
        top_n = int(m.group(2))
        candidates = m.group(3)
        for r in rounds_info:
            if r["round"] == round_num:
                r["top_candidates"] = candidates

    # Extract best prompt updates
    best_updates = []
    for m in re.finditer(r"\[Round (\d+).*?Prompt v(\w+)\] Best prompt updated\. New best score: ([\d.]+) \(prev: ([\d.]+)\)", log):
        best_updates.append({
            "round": int(m.group(1)),
            "version": m.group(2),
            "new_score": float(m.group(3)),
            "prev_score": float(m.group(4)),
            "improvement": float(m.group(3)) - float(m.group(4))
        })

    # Aggregate metrics by version to avoid many duplicate rows
    agg: dict[str, dict] = {}
    for m in metrics:
        v = m["version"]
        if v not in agg:
            agg[v] = {
                "version": v,
                "tasks": 0,
                "successes": 0,
                "failures": 0,
                "rewards": [],
                "total_weighted_reward": 0.0,
                "evaluations": []
            }
        agg[v]["tasks"] += m["tasks"]
        agg[v]["successes"] += m.get("successes", 0)
        agg[v]["failures"] += m.get("failures", 0)
        agg[v]["rewards"].extend(m.get("rewards", []))
        agg[v]["total_weighted_reward"] += m.get("average", 0.0) * m.get("tasks", 0)
        agg[v]["evaluations"].append({"round": m["round"], "tasks": m["tasks"], "average": m["average"]})

    aggregated_metrics = []
    for v, info in agg.items():
        total_tasks = info["tasks"] or 1
        average = info["total_weighted_reward"] / total_tasks
        # Attach prompt text if available
        prompt_entry = next((p for p in prompts if p["version"] == v), None)
        prompt_text = prompt_entry["prompt"] if prompt_entry else None
        parent = prompt_entry.get("parent") if prompt_entry else None
        is_seed = prompt_entry.get("is_seed", False) if prompt_entry else False
        prompt_round = prompt_entry.get("round", 0) if prompt_entry else 0
        # Token cost by word count of prompt
        avg_cost = len(prompt_text.split()) if prompt_text else 0
        
        # Find gradient for this version  
        version_gradient = next((g["gradient"] for g in gradients if g["version"] == v), None)
        
        # Calculate success rate and efficiency
        success_rate = round(info["successes"] / total_tasks * 100, 1) if total_tasks > 0 else 0
        cost_per_success = round(avg_cost / max(info["successes"], 1), 2) if info["successes"] > 0 else avg_cost
        
        # Determine strategy based on gradient analysis or prompt structure
        strategy = ""
        if version_gradient:
            grad_lower = version_gradient.lower()
            if "tie-break" in grad_lower or "tiebreak" in grad_lower:
                strategy = "Added tiebreakers"
            elif "priority" in grad_lower or "order" in grad_lower:
                strategy = "Priority ordering"
            elif "threshold" in grad_lower or "numeric" in grad_lower:
                strategy = "Numeric thresholds"
            elif "rule" in grad_lower or "explicit" in grad_lower:
                strategy = "Explicit rules"
            elif "format" in grad_lower or "output" in grad_lower:
                strategy = "Output format"
            elif "constraint" in grad_lower:
                strategy = "Constraint clarity"
            elif "example" in grad_lower:
                strategy = "Added examples"
            elif "flag" in grad_lower or "red" in grad_lower:
                strategy = "Red flag handling"
        
        if not strategy and prompt_text:
            prompt_lower = prompt_text.lower()
            # Check for specific patterns (order matters - more specific first)
            if "decision rules" in prompt_lower or "follow these" in prompt_lower:
                strategy = "Decision rules"
            elif any(x in prompt_lower for x in [">$", "> $", "≥", "threshold", ">1,000,000", ">5,000,000"]):
                strategy = "Numeric thresholds"
            elif "priority" in prompt_lower and ("1)" in prompt_text or "1." in prompt_text):
                strategy = "Priority ordering"
            elif "CRITICAL" in prompt_text or "MUST" in prompt_text:
                strategy = "Constraint emphasis"
            elif "Step " in prompt_text or ("1)" in prompt_text and "2)" in prompt_text):
                strategy = "Step-by-step"
            elif "example:" in prompt_lower or "e.g." in prompt_lower:
                strategy = "Includes examples"
            elif "regex" in prompt_lower or "validation" in prompt_lower:
                strategy = "Validation rules"
            elif "JSON" in prompt_text:
                strategy = "JSON output"
            elif is_seed:
                strategy = "Baseline prompt"
            else:
                strategy = "Iterative refinement"
        
        # Determine changes description
        changes = ""
        if is_seed:
            changes = "Original seed prompt"
        elif parent and version_gradient:
            # Extract key change from gradient
            changes = f"Improved from v{parent}"
        
        aggregated_metrics.append({
            "version": v,
            "tasks": info["tasks"],
            "successes": info["successes"],
            "failures": info["failures"],
            "rewards": info["rewards"],
            "average": round(average, 6),
            "prompt": prompt_text,
            "parent": parent,
            "is_seed": is_seed,
            "avg_cost": avg_cost,
            "round": prompt_round,
            "changes": changes,
            "strategy": strategy,
            "success_rate": success_rate,
            "cost_per_success": cost_per_success,
            "evaluations": info["evaluations"],
            "gradient": version_gradient
        })

    # sort by version (attempt numeric where possible)
    def _ver_key(x):
        try:
            return int(x["version"])
        except Exception:
            return x["version"]

    aggregated_metrics.sort(key=_ver_key)
    
    # Find the seed and best prompts
    seed_prompt = next((m for m in aggregated_metrics if m.get("is_seed")), None)
    best_prompt = max(aggregated_metrics, key=lambda x: x["average"]) if aggregated_metrics else None
    worst_prompt = min(aggregated_metrics, key=lambda x: x["average"]) if aggregated_metrics else None
    most_efficient = min([m for m in aggregated_metrics if m["successes"] > 0], key=lambda x: x["cost_per_success"]) if aggregated_metrics else None
    
    # Create optimization story/summary
    optimization_story = None
    if seed_prompt and best_prompt:
        improvement = best_prompt["average"] - seed_prompt["average"]
        improvement_pct = (improvement / seed_prompt["average"] * 100) if seed_prompt["average"] else 0
        cost_change = best_prompt["avg_cost"] - seed_prompt["avg_cost"]
        # Only calculate cost_change_pct if both prompts have valid token counts
        if seed_prompt["avg_cost"] > 0 and best_prompt["avg_cost"] > 0:
            cost_change_pct = (cost_change / seed_prompt["avg_cost"] * 100)
        else:
            cost_change_pct = 0  # Can't calculate if prompts weren't extracted
        
        # Generate recommendations based on analysis
        recommendations = []
        
        # Best version recommendation
        if best_prompt["strategy"]:
            recommendations.append({
                "action": f"Use {best_prompt['strategy']}",
                "description": f"Version {best_prompt['version']} achieved {best_prompt['average']*100:.1f}% accuracy using this approach",
                "impact": "high"
            })
        else:
            recommendations.append({
                "action": f"Adopt Version {best_prompt['version']}",
                "description": f"This version achieved the highest score of {best_prompt['average']*100:.1f}%",
                "impact": "high"
            })
        
        # Cost efficiency recommendation
        if most_efficient and most_efficient["version"] != best_prompt["version"]:
            recommendations.append({
                "action": "Consider efficiency trade-off",
                "description": f"Version {most_efficient['version']} has best efficiency ({most_efficient['cost_per_success']:.1f} tokens/success) vs best accuracy v{best_prompt['version']}",
                "impact": "medium"
            })
        
        # Cost reduction if applicable
        if cost_change < 0:
            recommendations.append({
                "action": "Token costs reduced",
                "description": f"Best prompt uses {abs(cost_change_pct):.0f}% fewer tokens ({best_prompt['avg_cost']} vs {seed_prompt['avg_cost']})",
                "impact": "medium"
            })
        elif cost_change > 0:
            recommendations.append({
                "action": "Review token usage",
                "description": f"Best prompt uses {cost_change_pct:.0f}% more tokens - consider if accuracy gain justifies cost",
                "impact": "low"
            })
        
        # Worst performer warning
        if worst_prompt and worst_prompt["version"] != seed_prompt["version"]:
            recommendations.append({
                "action": f"Avoid v{worst_prompt['version']} approach",
                "description": f"This version scored only {worst_prompt['average']*100:.1f}% - " + (worst_prompt['strategy'] or "approach didn't work well"),
                "impact": "low"
            })
        
        # Key insight
        if improvement > 0:
            key_insight = f"APO improved accuracy from {seed_prompt['average']*100:.1f}% to {best_prompt['average']*100:.1f}% (+{improvement_pct:.1f}%) by testing {len(aggregated_metrics)} prompt variations. "
            if best_prompt['strategy']:
                key_insight += f"The winning strategy was: {best_prompt['strategy']}."
        else:
            key_insight = f"The original seed prompt (v0) performed best at {seed_prompt['average']*100:.1f}%. Consider running more optimization rounds."
        
        optimization_story = {
            "seed_version": seed_prompt["version"],
            "seed_score": seed_prompt["average"],
            "seed_cost": seed_prompt["avg_cost"],
            "best_version": best_prompt["version"],
            "best_score": best_prompt["average"],
            "best_cost": best_prompt["avg_cost"],
            "best_strategy": best_prompt.get("strategy", ""),
            "improvement": round(improvement, 4),
            "improvement_pct": round(improvement_pct, 2),
            "cost_change": cost_change,
            "cost_change_pct": round(cost_change_pct, 1),
            "total_versions_tested": len(aggregated_metrics),
            "total_rounds": max([r.get("round", 0) for r in rounds_info]) if rounds_info else 0,
            "most_efficient_version": most_efficient["version"] if most_efficient else best_prompt["version"],
            "most_efficient_cost_per_success": most_efficient["cost_per_success"] if most_efficient else 0,
            "worst_version": worst_prompt["version"] if worst_prompt else "",
            "worst_score": worst_prompt["average"] if worst_prompt else 0,
            "key_insight": key_insight,
            "recommendations": recommendations,
            "best_updates": best_updates
        }

    # Build rounds info with versions
    rounds_with_versions = []
    for r in rounds_info:
        round_num = r.get("round", 0)
        versions_in_round = [m["version"] for m in aggregated_metrics if m.get("round") == round_num or (round_num == 0 and m.get("is_seed"))]
        rounds_with_versions.append({
            "round": round_num,
            "description": f"Round {round_num}" + (f" - {r.get('parents', '')}" if r.get('parents') else ""),
            "versions": versions_in_round
        })

    return {
        "prompts": prompts,
        "metrics": aggregated_metrics,
        "rounds": rounds_with_versions if rounds_with_versions else rounds_info,
        "gradients": gradients,
        "optimization_story": optimization_story
    }

@app.get("/api/prompts")
def get_prompts():
    # Try real data first, fall back to mock if no real data
    real_data = parse_apo_log()
    if real_data["metrics"]:
        return real_data["prompts"]
    return generate_mock_optimization_data()["prompts"]

@app.get("/api/metrics")
def get_metrics():
    # Try real data first, fall back to mock if no real data
    real_data = parse_apo_log()
    if real_data["metrics"]:
        return real_data["metrics"]
    return generate_mock_optimization_data()["metrics"]

@app.get("/api/optimization")
def get_optimization():
    """Get full optimization data including story, rounds, and comparisons"""
    # Try real data first, fall back to mock if no real data
    real_data = parse_apo_log()
    if real_data["metrics"]:
        return real_data
    return generate_mock_optimization_data()

@app.get("/api/log")
def get_log():
    log_file = locate_apo_log()
    if not log_file.exists():
        raise HTTPException(404, "apo.log not found")
    return {"log": log_file.read_text()}


# Available APO examples
APO_EXAMPLES = {
    "room_selector": {
        "name": "Room Selector",
        "description": "Optimize prompts for a conference room booking assistant",
        "script": "room_selector_apo.py"
    },
    "wealth_onboarding": {
        "name": "Wealth Client Onboarding",
        "description": "Optimize prompts for bank KYC/AML compliance - inheritance and business profit claims",
        "script": "wealth_onboarding_apo.py"
    }
}

@app.get("/api/examples")
def get_examples():
    """Get list of available APO examples."""
    return APO_EXAMPLES


@app.post("/api/run_apo")
def run_apo(example: str = "room_selector"):
    """Start the APO runner (non-blocking). Returns pid and log path.
    
    Args:
        example: Which example to run - 'room_selector' or 'wealth_onboarding'
    """
    if example not in APO_EXAMPLES:
        raise HTTPException(400, f"Unknown example: {example}. Available: {list(APO_EXAMPLES.keys())}")
    
    script_name = APO_EXAMPLES[example]["script"]
    script_path = Path(__file__).parent / script_name
    if not script_path.exists():
        raise HTTPException(404, f"APO runner not found: {script_path}")

    run_dir = Path(__file__).parent / "run_logs"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Use the same Python interpreter that's running this server (from the venv)
    import sys
    python_path = sys.executable
    
    # Start the process with stdout piped, then write to a logfile in a background thread
    proc = subprocess.Popen([python_path, str(script_path)], cwd=str(script_path.parent), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    logfile = run_dir / f"run_{proc.pid}.log"

    def _drain_stdout(p: subprocess.Popen, path: Path):
        try:
            with open(path, "w") as f:
                if p.stdout:
                    for line in p.stdout:
                        f.write(line)
        except Exception:
            pass
        finally:
            try:
                p.wait()
            except Exception:
                pass

    t = threading.Thread(target=_drain_stdout, args=(proc, logfile), daemon=True)
    t.start()

    RUN_PROCS[proc.pid] = {"process": proc, "log": str(logfile)}
    return {"pid": proc.pid, "log_path": str(logfile), "started": True}


@app.get("/api/run_status/{pid}")
def run_status(pid: int):
    entry = RUN_PROCS.get(pid)
    alive = False
    exit_code = None
    if entry:
        proc: subprocess.Popen = entry.get("process")
        exit_code = proc.poll()
        alive = exit_code is None
    else:
        # process not tracked live; check if pid exists
        try:
            os.kill(pid, 0)
            alive = True
        except Exception:
            alive = False
    return {"pid": pid, "alive": alive, "exit_code": exit_code, "log_path": entry.get("log") if entry else None}


@app.get("/api/run_logs/{pid}")
def run_logs(pid: int, tail: int = 5000):
    entry = RUN_PROCS.get(pid)
    logpath = None
    if entry:
        logpath = Path(entry.get("log"))
    else:
        # try find file by convention
        candidate = Path(__file__).parent / "run_logs" / f"run_{pid}.log"
        if candidate.exists():
            logpath = candidate
    if not logpath or not logpath.exists():
        raise HTTPException(404, "log not found")
    data = logpath.read_text(errors='ignore')
    if len(data) <= tail:
        return {"log": data}
    return {"log": data[-tail:]}
