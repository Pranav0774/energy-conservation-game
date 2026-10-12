# Play-test kit

Use this to run the real-player tests the plan asks for (3–5 people). The automated checks in [playtest.md](playtest.md) cannot tell you whether the game is understandable or fun. Only players can.

## Setup
- Run the game on a laptop, or share one screen.
- Choose people who have not seen it. Do not explain the rules first.
- Tell them: "Try to get a good score. Say what you are thinking out loud. I can't help until the end."
- Let them play one full day at their own speed. Then offer a second go.
- Do not intervene. Write down where they hesitate.

## Observe (tick while they play)
| Moment | Did they... | Y/N | Notes |
|---|---|---|---|
| Start | Pick a level without help? | | |
| First minute | Work out that clicking appliances switches them? | | |
| First minute | Notice the budget ring? | | |
| Midday | Understand what "comfort" is? | | |
| 17:00 | React to the peak-pricing message? | | |
| Evening | Move any use to night? | | |
| Any time | Check the "must run today" chips? | | |
| End | Read the tips? | | |
| End | Ask to play again? | | |

## Ask afterwards (1 to 5, where 5 is best)
| Question | Score | Comment |
|---|---|---|
| It was clear what I had to do | | |
| The controls were easy | | |
| The speed of the day was right (1 = far too fast, 3 = right, 5 = far too slow) | | |
| The score felt fair | | |
| I learned something about saving energy | | |
| I would play again | | |

Open questions:
1. What was the most confusing moment?
2. Which number on the screen did you look at most?
3. What would you change first?
4. Did the tips make sense? Would you act on any of them?

## Record the results
| Player | Device | Level | Score and rating | Longest hesitation | Biggest comment |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

## Decide what to change
- If 2 or more players hit the same problem, fix it.
- If only one player did, note it and fix it only if it is cheap.
- Typical fixes: change `SEC_PER_HOUR` in `frontend/game.js` if the pace is wrong, reword text in `frontend/index.html` or `frontend/tips.js`, adjust `docs` wording.
- After changes, run `python -m pytest` and play one full day on each level.

Copy the summary table into `docs/report.md`, section 7, when you are done.
