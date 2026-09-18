"""Finite Catch warm-up for APS1053, inspired by Packt's 7.1 notebook.

This uses an explicit state and a Q table, unlike the source's pixel input
and neural network. It is not a reproduction of the financial A2C case.
See upstream/LICENSE for the original Catch example's MIT attribution.
"""
import csv
import json
import random
from collections import defaultdict
from pathlib import Path


def step(state, action, grid=8):
    row, col, basket = state
    if action not in (0, 1, 2):
        raise ValueError('Action must be left=0, stay=1, right=2')
    if not (0 <= row < grid - 1 and 0 <= col < grid and 1 <= basket < grid):
        raise ValueError('Invalid or terminal state')
    nxt = (row + 1, col, min(grid - 1, max(1, basket + action - 1)))
    done = nxt[0] == grid - 1
    reward = (1 if abs(nxt[1] - nxt[2]) <= 1 else -1) if done else 0
    return nxt, reward, done


def initial_states(grid=8):
    # Match the source's reset support: exclude the last fruit column and
    # the last two basket positions. Sampling uses Python's seeded RNG.
    return [(0, col, basket) for col in range(grid - 1) for basket in range(1, grid - 2)]


def greedy(values, rng=None):
    best = max(values)
    choices = [a for a, v in enumerate(values) if v == best]
    return rng.choice(choices) if rng else choices[0]


def target(reward, done, next_values, gamma):
    return reward if done else reward + gamma * max(next_values)


def train(seed, epsilon, episodes=2500, grid=8, alpha=0.25, gamma=0.95):
    rng = random.Random(seed)
    q = defaultdict(lambda: [0.0, 0.0, 0.0])
    starts = initial_states(grid)
    curve = []
    for episode in range(episodes):
        state = rng.choice(starts)
        done = False
        while not done:
            action = rng.randrange(3) if rng.random() < epsilon else greedy(q[state], rng)
            nxt, reward, done = step(state, action, grid)
            value = target(reward, done, q[nxt], gamma)
            q[state][action] += alpha * (value - q[state][action])
            state = nxt
        curve.append({'seed': seed, 'epsilon': epsilon, 'episode': episode + 1, 'reward': reward})
    return dict(q), curve


def evaluate(q=None, baseline='stay', seed=1000, grid=8):
    rng = random.Random(seed)
    traces = []
    for start in initial_states(grid):
        state = start
        done = False
        while not done:
            action = greedy(q.get(state, [0.0] * 3)) if q is not None else (rng.randrange(3) if baseline == 'random' else 1)
            nxt, reward, done = step(state, action, grid)
            traces.append({'start_col': start[1], 'start_basket': start[2],
                           'row': state[0], 'basket': state[2], 'action': action,
                           'next_basket': nxt[2], 'reward': reward, 'done': done})
            state = nxt
    rewards = [t['reward'] for t in traces if t['done']]
    return {'success_rate': sum(r == 1 for r in rewards) / len(rewards),
            'mean_return': sum(rewards) / len(rewards), 'episodes': len(rewards)}, traces


def check_transition_contract(grid=8):
    """Exhaustive check for this finite grid, not a Lean or general proof."""
    count = 0
    for row in range(grid - 1):
        for col in range(grid):
            for basket in range(1, grid):
                for action in range(3):
                    nxt, reward, done = step((row, col, basket), action, grid)
                    assert nxt[0] == row + 1 and nxt[1] == col
                    assert 1 <= nxt[2] < grid
                    assert done == (row == grid - 2)
                    assert reward == ((1 if abs(col - nxt[2]) <= 1 else -1) if done else 0)
                    count += 1
    # A terminal target must not bootstrap from a fictitious next state.
    assert target(-1, True, [100, 100, 100], 0.95) == -1
    assert target(1, False, [0, 2, 1], 0.5) == 2
    return count


def write_csv(path, rows):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    checked = check_transition_contract()
    metrics, all_curves = [], []
    for seed in range(5):
        for epsilon in (0.0, 0.2):
            q, curve = train(seed, epsilon)
            score, trace = evaluate(q, seed=1000 + seed)
            metrics.append({'policy': 'tabular_q', 'seed': seed, 'epsilon': epsilon, **score})
            all_curves.extend(curve)
            write_csv(output / f'evaluation_seed{seed}_epsilon{epsilon}.csv', trace)
        for baseline in ('stay', 'random'):
            score, _ = evaluate(baseline=baseline, seed=1000 + seed)
            metrics.append({'policy': baseline, 'seed': seed, 'epsilon': '', **score})
    write_csv(output / 'metrics.csv', metrics)
    write_csv(output / 'training.csv', all_curves)
    (output / 'run.json').write_text(json.dumps({
        'grid': 8, 'train_episodes_per_run': 2500, 'seeds': list(range(5)),
        'alpha': 0.25, 'gamma': 0.95, 'epsilons': [0.0, 0.2],
        'finite_transition_checks': checked,
        'evaluation': 'Frozen greedy policy over every original-support initial state; no learning during evaluation. Same MDP, not held-out market data.',
        'limitations': 'Explicit-state toy game; not neural Q-learning, financial case reproduction, or evidence of market performance. Epsilon=0 still randomly breaks training ties.'
    }, indent=2) + '\n')
    print(f'Finite transition checks passed: {checked}')
    for policy, epsilon in [('tabular_q', 0.0), ('tabular_q', 0.2), ('stay', ''), ('random', '')]:
        scores = [r['success_rate'] for r in metrics if r['policy'] == policy and r['epsilon'] == epsilon]
        print(f'{policy}, epsilon={epsilon}: mean success={sum(scores)/len(scores):.3f}, min={min(scores):.3f}, max={max(scores):.3f}')


if __name__ == '__main__':
    run(Path(__file__).resolve().parent / 'results')
