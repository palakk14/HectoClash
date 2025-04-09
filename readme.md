# HectoClash - The Ultimate Mental Math Duel

**Live Demo:** [https://hectoclash-1-4248.onrender.com](https://hectoclash-1-4248.onrender.com)

**HectoClash** is a real-time multiplayer game where players compete in fast-paced mental math duels based on the Hectoc puzzle format. Solve math challenges quickly, compete with friends or strangers, and climb the leaderboard in a competitive and educational environment.

---

## What is Hectoc?

Hectoc is a mental calculation puzzle developed by Yusnier Viera. Players are given a six-digit sequence (each digit between 1 and 9) and must insert math operations—addition, subtraction, multiplication, division, exponentiation, and parentheses—to form an expression equal to 100.

**Rules:**
- Digits must be used in the given order.
- You can use any standard math operations and parentheses.

**Example:**  
Given the sequence `123456`, a valid solution is:  
`1 + (2 + 3 + 4) × (5 + 6) = 100`

---

## Features

- **Real-Time Duels**  
  Engage in live, time-bound mental math battles with other players.

- **Private Rooms**  
  Create or join private rooms to duel with friends directly.

- **Quick Play**  
  Players can challenge any person on the server to duel and chat with them. 

- **Spectate Any Game**  
  Watch your friends or any ongoing game live through spectator mode.

- **Dynamic Puzzle Generation**  
  Random six-digit challenges every match to ensure unique and varied gameplay.

- **Leaderboards and Rankings**  
  Players earn points based on accuracy and speed. Track your progress and see how you stack up against others.

- **User Profiles**  
  Register and log in to maintain your records, rank, and game history.

---

## How We Built It

HectoClash was built to combine speed, logic, and education in a multiplayer web experience. The goal was to offer a fun and competitive way to improve mental math skills.

### Tech Stack

| Layer            | Technology           |
|------------------|----------------------|
| Backend          | Python (Flask)       |
| Real-Time Events | Flask-SocketIO       |
| Frontend         | HTML, CSS, Jinja2    |
| Deployment       | Render.com           |
| Database         | PostgreSQL           |


