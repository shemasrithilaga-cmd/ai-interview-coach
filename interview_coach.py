import json
import os
import random
import time
import urllib.error
import urllib.request

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AI Interview Coach",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Syne:wght@400;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
}

h1, h2, h3 {
    font-family: 'Syne', sans-serif;
}

.main-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    padding: 2rem;
    border-radius: 16px;
    margin-bottom: 2rem;
    border: 1px solid #e94560;
    box-shadow: 0 8px 32px rgba(233,69,96,0.2);
}

.main-header h1 {
    color: #e94560;
    font-size: 2.5rem;
    margin: 0;
}

.main-header p {
    color: #a8b2d8;
    margin: 0.5rem 0 0 0;
}

.card {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border: 1px solid #0f3460;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}

.metric-card {
    background: linear-gradient(135deg, #0f3460, #16213e);
    border: 1px solid #e94560;
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    box-shadow: 0 4px 16px rgba(233,69,96,0.15);
}

.metric-card h2 {
    color: #e94560;
    font-size: 2rem;
    margin: 0;
}

.metric-card p {
    color: #a8b2d8;
    margin: 0.3rem 0 0 0;
    font-size: 0.9rem;
}

.score-green { color: #00ff88; }
.score-yellow { color: #ffd700; }
.score-red { color: #e94560; }

.company-card {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border: 1px solid #0f3460;
    border-radius: 10px;
    padding: 1.2rem;
    margin-bottom: 0.8rem;
    transition: border-color 0.3s;
}

.company-card:hover {
    border-color: #e94560;
}

.stButton > button {
    background: linear-gradient(135deg, #e94560, #c23152);
    color: white;
    border: none;
    border-radius: 8px;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    transition: all 0.3s;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #ff5577, #e94560);
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(233,69,96,0.4);
}

.sidebar-btn {
    width: 100%;
    margin-bottom: 0.4rem;
}

.timer-green { color: #00ff88; font-size: 1.5rem; font-weight: bold; }
.timer-yellow { color: #ffd700; font-size: 1.5rem; font-weight: bold; }
.timer-red { color: #e94560; font-size: 1.5rem; font-weight: bold; animation: blink 1s step-end infinite; }

@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

.leaderboard-row {
    display: flex;
    align-items: center;
    padding: 0.7rem 1rem;
    border-radius: 8px;
    margin-bottom: 0.5rem;
    background: linear-gradient(135deg, #16213e, #1a1a2e);
    border: 1px solid #0f3460;
}

.badge-gold { color: #ffd700; font-size: 1.3rem; }
.badge-silver { color: #c0c0c0; font-size: 1.3rem; }
.badge-bronze { color: #cd7f32; font-size: 1.3rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
def init_state():
    defaults = {
        "page": "🏠 Home",
        "logged_in": False,
        "user": {},
        "sessions": [],          # list of {date, type, scores[]}
        "interview_active": False,
        "q_index": 0,
        "questions": [],
        "answers": [],
        "scores": [],
        "feedback": [],
        "hints_used": [],
        "interview_type": None,
        "interview_done": False,
        "timer_start": None,
        "mentor_reply": "",
        "mentor_error": "",
        "mentor_messages": [],
        "mentor_context_key": "",
        "skill_test_done": False,
        "skill_test_result": {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

SKILL_AREAS = {
    "hard_skills": [
        "Python",
        "Data Structures",
        "DBMS",
        "Operating Systems",
        "System Design",
        "Problem Solving",
    ],
    "soft_skills": [
        "Communication",
        "Confidence",
        "Leadership",
        "Teamwork",
        "Adaptability",
        "Time Management",
    ],
}

PRACTICE_PLATFORMS = [
    {
        "name": "LeetCode",
        "focus": "Interview-style DSA, company prep, topic practice",
        "problemset_url": "https://leetcode.com/problemset/",
        "tracks": [
            ("Top Interview 150", "https://leetcode.com/studyplan/top-interview-150/"),
            ("LeetCode 75", "https://leetcode.com/studyplan/leetcode-75/"),
            ("Daily Challenge", "https://leetcode.com/problemset/all/"),
        ],
    },
    {
        "name": "HackerRank",
        "focus": "Language practice, DSA, SQL, interview prep",
        "problemset_url": "https://www.hackerrank.com/domains",
        "tracks": [
            ("Problem Solving", "https://www.hackerrank.com/domains/algorithms"),
            ("SQL", "https://www.hackerrank.com/domains/sql"),
            ("Interview Preparation Kit", "https://www.hackerrank.com/interview/interview-preparation-kit"),
        ],
    },
    {
        "name": "Codeforces",
        "focus": "Competitive programming, rating-based problem solving",
        "problemset_url": "https://codeforces.com/problemset?lang=en",
        "tracks": [
            ("Problemset", "https://codeforces.com/problemset?lang=en"),
            ("Educational Rounds", "https://codeforces.com/edu/courses"),
            ("Contests", "https://codeforces.com/contests"),
        ],
    },
    {
        "name": "CodeChef",
        "focus": "Practice paths, contests, curated coding tracks",
        "problemset_url": "https://www.codechef.com/practice",
        "tracks": [
            ("Practice", "https://www.codechef.com/practice"),
            ("Learn", "https://www.codechef.com/learn"),
            ("Contests", "https://www.codechef.com/contests"),
        ],
    },
    {
        "name": "GeeksforGeeks Practice",
        "focus": "Topic-based interview problems, company-tagged questions",
        "problemset_url": "https://www.geeksforgeeks.org/explore?page=1",
        "tracks": [
            ("All Practice", "https://www.geeksforgeeks.org/explore?page=1"),
            ("Basic", "https://www.geeksforgeeks.org/explore?difficulty=Basic&page=1"),
            ("Medium", "https://www.geeksforgeeks.org/explore?difficulty=Medium&page=1"),
        ],
    },
]

PROBLEM_ROADMAPS = {
    "Beginner": [
        "Arrays and strings basics",
        "Hash maps and sets",
        "Sorting and binary search basics",
        "Stack and queue fundamentals",
        "Easy SQL and basic Python practice",
    ],
    "Intermediate": [
        "Two pointers and sliding window",
        "Linked lists, trees, and graphs",
        "Recursion, backtracking, and heaps",
        "Dynamic programming basics",
        "Medium SQL, OOP, and system basics",
    ],
    "Advanced": [
        "Advanced DP and graph algorithms",
        "Segment trees, tries, and union-find",
        "System design and concurrency concepts",
        "Hard interview problems by pattern",
        "Company-tagged timed mock rounds",
    ],
}

HARD_SKILL_TEST_QUESTIONS = [
    {
        "skill": "Python",
        "question": "What is the output type of a list comprehension in Python?",
        "options": ["tuple", "set", "list", "generator"],
        "answer": "list",
        "explanation": "A standard list comprehension creates a list object.",
    },
    {
        "skill": "Python",
        "question": "Which keyword is used to handle exceptions in Python?",
        "options": ["catch", "except", "error", "handle"],
        "answer": "except",
        "explanation": "Python uses try/except blocks for exception handling.",
    },
    {
        "skill": "Data Structures",
        "question": "Which data structure is best suited for LIFO behavior?",
        "options": ["Queue", "Stack", "Heap", "Tree"],
        "answer": "Stack",
        "explanation": "Stack follows Last In, First Out ordering.",
    },
    {
        "skill": "Data Structures",
        "question": "What is the average time complexity of hash table lookup?",
        "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
        "answer": "O(1)",
        "explanation": "Average-case hash table lookup is constant time.",
    },
    {
        "skill": "DBMS",
        "question": "Which normal form removes transitive dependency?",
        "options": ["1NF", "2NF", "3NF", "BCNF"],
        "answer": "3NF",
        "explanation": "3NF removes transitive dependency from non-key attributes.",
    },
    {
        "skill": "DBMS",
        "question": "Which SQL clause is used to filter aggregated results?",
        "options": ["WHERE", "ORDER BY", "HAVING", "GROUP BY"],
        "answer": "HAVING",
        "explanation": "HAVING filters groups after aggregation.",
    },
    {
        "skill": "Operating Systems",
        "question": "Which condition is NOT one of the Coffman deadlock conditions?",
        "options": ["Mutual exclusion", "Circular wait", "Preemption allowed", "Hold and wait"],
        "answer": "Preemption allowed",
        "explanation": "The deadlock condition is no preemption, not preemption allowed.",
    },
    {
        "skill": "Operating Systems",
        "question": "What does virtual memory primarily help with?",
        "options": ["Networking", "Using disk as memory extension", "Compiling code", "Improving monitor refresh rate"],
        "answer": "Using disk as memory extension",
        "explanation": "Virtual memory extends usable memory through disk-backed paging.",
    },
    {
        "skill": "System Design",
        "question": "What is the main purpose of caching in system design?",
        "options": ["Increase latency", "Reduce repeated expensive reads", "Encrypt data", "Balance salaries"],
        "answer": "Reduce repeated expensive reads",
        "explanation": "Caching improves performance by avoiding repeated expensive fetches.",
    },
    {
        "skill": "System Design",
        "question": "Which component typically distributes traffic across multiple servers?",
        "options": ["Compiler", "Load balancer", "Debugger", "Container registry"],
        "answer": "Load balancer",
        "explanation": "A load balancer routes requests across multiple backend instances.",
    },
    {
        "skill": "Problem Solving",
        "question": "Which technique is commonly used for subarray problems with contiguous ranges?",
        "options": ["Sliding window", "Heap sort", "Recursion tree", "Binary heap"],
        "answer": "Sliding window",
        "explanation": "Sliding window is a common pattern for contiguous range problems.",
    },
    {
        "skill": "Problem Solving",
        "question": "What is usually the first step before coding an algorithmic solution?",
        "options": ["Deploy the app", "Memorize syntax", "Clarify the problem and constraints", "Write random test cases"],
        "answer": "Clarify the problem and constraints",
        "explanation": "Understanding the problem and constraints is the foundation of a good solution.",
    },
]

DEBUG_TEST_BANK = [
    {
        "company": "TCS",
        "title": "Loop Boundary Bug",
        "skill": "Python",
        "languages": ["Python", "Java", "C++"],
        "prompt": "Fix the bug so the function correctly returns the sum of all numbers in the list.",
        "buggy_code": """def total(nums):
    s = 0
    for i in range(len(nums) - 1):
        s += nums[i]
    return s""",
        "correct_solution": """def total(nums):
    s = 0
    for i in range(len(nums)):
        s += nums[i]
    return s""",
        "expected_keywords": ["range(len(nums))", "range(len(nums)-1)", "off by one", "last element"],
        "fix_signals": ["len(nums)", "last", "off"],
    },
    {
        "company": "Infosys",
        "title": "Dictionary Frequency Fix",
        "skill": "Python",
        "languages": ["Python", "Java", "C++"],
        "prompt": "Fix the code so it counts each character frequency correctly.",
        "buggy_code": """def count_chars(text):
    freq = {}
    for ch in text:
        freq[ch] = 1
    return freq""",
        "correct_solution": """def count_chars(text):
    freq = {}
    for ch in text:
        freq[ch] = freq.get(ch, 0) + 1
    return freq""",
        "expected_keywords": ["freq[ch] = freq.get(ch, 0) + 1", "increment", "existing count"],
        "fix_signals": ["get(", "+ 1", "increment"],
    },
    {
        "company": "Wipro",
        "title": "SQL Join Debug",
        "skill": "DBMS",
        "languages": ["SQL"],
        "prompt": "The query should return all students even if they have no marks. Explain the fix.",
        "buggy_code": """SELECT s.name, m.score
FROM students s
INNER JOIN marks m
ON s.id = m.student_id;""",
        "correct_solution": """SELECT s.name, m.score
FROM students s
LEFT JOIN marks m
ON s.id = m.student_id;""",
        "expected_keywords": ["LEFT JOIN", "all students", "inner join drops unmatched rows"],
        "fix_signals": ["left join", "all students", "unmatched"],
    },
    {
        "company": "Cognizant",
        "title": "Stack Pop Safety",
        "skill": "Data Structures",
        "languages": ["Python", "Java", "C++"],
        "prompt": "Fix the bug so popping from an empty stack does not crash the program.",
        "buggy_code": """stack = []
def pop_item():
    return stack.pop()""",
        "correct_solution": """stack = []
def pop_item():
    if stack:
        return stack.pop()
    return None""",
        "expected_keywords": ["check if stack", "if stack", "empty", "guard condition"],
        "fix_signals": ["if stack", "empty", "guard"],
    },
    {
        "company": "Zoho Corporation",
        "title": "Sorting Logic Bug",
        "skill": "Problem Solving",
        "languages": ["Python", "Java", "C++", "JavaScript"],
        "prompt": "The function should sort numbers in ascending order. Explain the bug and fix.",
        "buggy_code": """def sort_nums(nums):
    return sorted(nums, reverse=True)""",
        "correct_solution": """def sort_nums(nums):
    return sorted(nums)""",
        "expected_keywords": ["reverse=False", "remove reverse", "ascending"],
        "fix_signals": ["ascending", "reverse", "false"],
    },
    {
        "company": "Freshworks",
        "title": "Cache Lookup Fallback",
        "skill": "System Design",
        "languages": ["Python", "Java", "JavaScript"],
        "prompt": "Fix the logic so the app falls back to database fetch when cache miss happens.",
        "buggy_code": """def get_user(cache, db, user_id):
    user = cache.get(user_id)
    return user.name""",
        "correct_solution": """def get_user(cache, db, user_id):
    user = cache.get(user_id)
    if user is None:
        user = db.get(user_id)
    return user.name if user else None""",
        "expected_keywords": ["if user is None", "cache miss", "fetch from db", "fallback"],
        "fix_signals": ["none", "db", "cache miss", "fallback"],
    },
]

# ─────────────────────────────────────────────
# QUESTION BANK  (50+ questions)
# ─────────────────────────────────────────────
QUESTION_BANK = {
    "HR": [
        {"q": "Tell me about yourself.", "keywords": ["experience","skills","background","graduated","worked","passionate","team","goal"], "sample": "I'm a final-year CS student at Anna University. I've developed strong skills in Python and data structures through projects and internships. I'm passionate about problem-solving and thrive in collaborative environments. My goal is to contribute to innovative products while continuously growing.", "tips": "Keep it under 2 minutes. Follow: Present → Past → Future structure."},
        {"q": "Why do you want to join our company?", "keywords": ["culture","growth","values","product","mission","align","contribute","learn"], "sample": "Your company's commitment to innovation and its collaborative culture align with my values. I'm particularly excited about your AI product roadmap and believe I can contribute meaningfully to that vision.", "tips": "Research the company before. Mention specific products or values."},
        {"q": "What are your strengths?", "keywords": ["analytical","communication","team","problem","adapt","leader","quick","creative"], "sample": "My key strength is analytical thinking—I break complex problems into manageable parts. I'm also a strong communicator and have led team projects in college successfully.", "tips": "Give 2–3 strengths with brief examples."},
        {"q": "What is your greatest weakness?", "keywords": ["improve","working","overcome","learning","awareness","action","steps"], "sample": "I sometimes focus too much on perfecting details. I've been working on this by setting time-boxed goals and using the 80/20 rule to prioritize.", "tips": "Show self-awareness + active improvement. Never say 'I work too hard.'"},
        {"q": "Where do you see yourself in 5 years?", "keywords": ["grow","senior","lead","skill","expertise","team","contribute","long-term"], "sample": "In 5 years I see myself as a senior engineer, leading a small team and contributing to architectural decisions. I want to deepen my expertise in distributed systems.", "tips": "Show ambition, but keep it realistic and company-relevant."},
        {"q": "Why should we hire you?", "keywords": ["skills","experience","contribute","value","unique","fit","team","deliver"], "sample": "I bring a strong technical foundation, hands-on project experience, and the ability to learn fast. My internship at XYZ showed I can deliver under pressure, and I'm confident I'll add value from day one.", "tips": "Connect your skills directly to the role requirements."},
        {"q": "Tell me about a time you failed.", "keywords": ["mistake","learned","improved","handled","recover","action","result","lesson"], "sample": "During a hackathon, I underestimated the time for integration. We missed a feature. I learned to break tasks into smaller chunks and build buffer time. Since then I've delivered all projects on schedule.", "tips": "Use STAR method. Focus on the lesson, not the failure."},
        {"q": "How do you handle pressure?", "keywords": ["prioritize","calm","deadline","manage","organize","breathe","plan","focus"], "sample": "I handle pressure by breaking the problem into steps and prioritizing. During exam season, I used a Kanban board to manage 3 deadlines simultaneously and delivered all on time.", "tips": "Give a concrete example. Mention a technique you use."},
        {"q": "Are you a team player or individual contributor?", "keywords": ["team","collaborate","independent","balance","support","communicate","flexible"], "sample": "I'm adaptable—I can work independently when needed but thrive in teams. In my final-year project, I coordinated a 4-person team while also handling the backend solo during crunch time.", "tips": "Show flexibility. Don't just say 'both'—demonstrate it."},
        {"q": "What motivates you?", "keywords": ["challenge","learn","impact","build","solve","grow","passion","achieve"], "sample": "I'm driven by building things that solve real problems. Seeing a user use something I built—whether it's an app or a script—gives me immense satisfaction.", "tips": "Be genuine. Tie it to the role."},
    ],
    "Python": [
        {"q": "What are Python's key features?", "keywords": ["interpreted","dynamic","typing","readable","oop","functional","library","duck"], "sample": "Python is interpreted, dynamically typed, and supports OOP and functional paradigms. Its readability and rich standard library make it ideal for rapid development.", "tips": "Mention: GIL, duck typing, memory management."},
        {"q": "Explain list vs tuple vs set.", "keywords": ["mutable","immutable","ordered","unordered","duplicate","hashable","tuple","set"], "sample": "Lists are mutable ordered collections. Tuples are immutable ordered. Sets are mutable unordered with no duplicates. Use tuples for fixed data, sets for uniqueness checks.", "tips": "Mention time complexity: set lookup is O(1)."},
        {"q": "What is a decorator in Python?", "keywords": ["wrapper","function","modify","extend","@","higher-order","closure","behaviour"], "sample": "A decorator is a higher-order function that wraps another function to extend its behaviour without modifying it. Used with @syntax. Common examples: @staticmethod, @property, @functools.lru_cache.", "tips": "Be ready to write a simple decorator from scratch."},
        {"q": "Explain generators and yield.", "keywords": ["lazy","iterator","memory","yield","next","iterable","state","efficient"], "sample": "Generators use yield to produce values lazily, pausing execution between calls. They're memory-efficient for large datasets. `range()` in Python 3 is a generator.", "tips": "Contrast with list comprehensions. Mention StopIteration."},
        {"q": "What is the GIL?", "keywords": ["global","interpreter","lock","thread","memory","cpython","performance","multiprocessing"], "sample": "The Global Interpreter Lock prevents multiple native threads from executing Python bytecode simultaneously. It's a CPython limitation. Use multiprocessing for CPU-bound tasks, asyncio/threads for I/O-bound tasks.", "tips": "Know when GIL matters and when it doesn't."},
        {"q": "Explain list comprehension with example.", "keywords": ["comprehension","concise","filter","map","expression","iterable","condition","readable"], "sample": "`[x**2 for x in range(10) if x%2==0]` creates a list of even squares. Comprehensions are more Pythonic and often faster than equivalent for-loops.", "tips": "Don't overuse nested comprehensions—readability matters."},
        {"q": "What are *args and **kwargs?", "keywords": ["positional","keyword","variable","arguments","unpack","flexible","tuple","dict"], "sample": "*args collects extra positional arguments as a tuple. **kwargs collects extra keyword arguments as a dict. They allow flexible function signatures.", "tips": "Demonstrate with a simple example. Mention order: args before kwargs."},
        {"q": "Explain OOP concepts in Python.", "keywords": ["class","object","inheritance","polymorphism","encapsulation","abstraction","method","self"], "sample": "Python supports all OOP pillars: Encapsulation via classes, Inheritance via subclassing, Polymorphism via method overriding, Abstraction via abstract base classes (ABC module).", "tips": "Give a short code example for each pillar."},
        {"q": "What is monkey patching?", "keywords": ["runtime","modify","class","attribute","dynamic","patch","test","mock"], "sample": "Monkey patching is dynamically modifying a class or module at runtime. Often used in testing to replace methods with mocks. Should be used carefully to avoid confusion.", "tips": "Mention unittest.mock as a safer alternative."},
        {"q": "How does Python manage memory?", "keywords": ["garbage","reference","counting","cyclic","gc","heap","del","allocation"], "sample": "Python uses reference counting as its primary GC mechanism. When count hits 0, memory is freed. The `gc` module handles cyclic references. Objects live on the heap.", "tips": "Mention __del__, weak references, and memory profiling tools."},
    ],
    "DBMS": [
        {"q": "What is normalization? Explain 1NF, 2NF, 3NF.", "keywords": ["redundancy","dependency","atomic","partial","transitive","key","relation","form"], "sample": "Normalization reduces redundancy. 1NF: atomic values, no repeating groups. 2NF: 1NF + no partial dependencies on composite key. 3NF: 2NF + no transitive dependencies.", "tips": "Draw small table examples. BCNF is stricter than 3NF."},
        {"q": "Explain ACID properties.", "keywords": ["atomicity","consistency","isolation","durability","transaction","rollback","commit","database"], "sample": "ACID ensures reliable transactions. Atomicity: all-or-nothing. Consistency: DB stays valid. Isolation: transactions don't interfere. Durability: committed data persists after crash.", "tips": "Give real-world examples for each property."},
        {"q": "What is an index and when should you use it?", "keywords": ["b-tree","lookup","read","write","clustered","non-clustered","performance","query"], "sample": "An index speeds up data retrieval using a B-tree or hash structure. Use indexes on frequently queried/joined columns. Avoid over-indexing—it slows writes.", "tips": "Know clustered vs non-clustered. Mention EXPLAIN in MySQL."},
        {"q": "Difference between JOIN types.", "keywords": ["inner","left","right","full","cross","outer","null","match"], "sample": "INNER JOIN: matching rows only. LEFT JOIN: all left rows + matches. RIGHT JOIN: all right + matches. FULL OUTER: all rows from both. CROSS JOIN: cartesian product.", "tips": "Draw Venn diagrams mentally. Practice writing all 4 types."},
        {"q": "What is a transaction? Explain with SQL.", "keywords": ["begin","commit","rollback","savepoint","lock","isolation","concurrent","integrity"], "sample": "A transaction is a unit of work. BEGIN TRANSACTION → SQL statements → COMMIT or ROLLBACK. Savepoints allow partial rollback within a transaction.", "tips": "Know isolation levels: READ UNCOMMITTED, READ COMMITTED, REPEATABLE READ, SERIALIZABLE."},
        {"q": "Explain SQL vs NoSQL databases.", "keywords": ["relational","schema","scalable","document","key-value","horizontal","consistency","flexible"], "sample": "SQL: structured schema, ACID, vertical scaling (MySQL, PostgreSQL). NoSQL: flexible schema, horizontal scaling, eventual consistency (MongoDB, Cassandra, Redis).", "tips": "Use cases: SQL for transactions, NoSQL for big data/real-time apps."},
        {"q": "What are stored procedures and triggers?", "keywords": ["procedure","trigger","automate","event","reusable","server-side","before","after"], "sample": "Stored procedures: precompiled SQL logic stored in DB, called explicitly. Triggers: automatically fire on INSERT/UPDATE/DELETE events. Both reduce app-DB round trips.", "tips": "Know the difference between BEFORE and AFTER triggers."},
        {"q": "What is denormalization?", "keywords": ["performance","redundancy","read","trade-off","join","cache","reporting","analytics"], "sample": "Denormalization intentionally adds redundancy to improve read performance by reducing joins. Common in data warehouses and reporting systems. Trade-off: more storage, update anomalies.", "tips": "Contrast with normalization. Mention OLAP vs OLTP."},
    ],
    "OS": [
        {"q": "What is a process vs thread?", "keywords": ["process","thread","memory","lightweight","share","context","switch","overhead"], "sample": "A process is an independent program in execution with its own memory space. A thread is a lightweight unit within a process sharing the same memory. Context switching is cheaper for threads.", "tips": "Mention: PCB, TCB, multi-threading advantages."},
        {"q": "Explain deadlock and its conditions.", "keywords": ["mutual","exclusion","hold","wait","circular","preemption","resource","prevent"], "sample": "Deadlock occurs when processes wait for each other's resources forever. Four conditions: Mutual Exclusion, Hold & Wait, No Preemption, Circular Wait. Prevention: break any one condition.", "tips": "Know Banker's Algorithm for deadlock avoidance."},
        {"q": "What is virtual memory?", "keywords": ["paging","swap","page","fault","physical","logical","address","mmu"], "sample": "Virtual memory allows processes to use more memory than physically available by using disk as an extension. The OS maps virtual addresses to physical via page tables. Page faults trigger disk reads.", "tips": "Know TLB, page replacement algorithms (LRU, FIFO, Optimal)."},
        {"q": "Explain CPU scheduling algorithms.", "keywords": ["fcfs","sjf","round","robin","priority","preemptive","burst","starvation"], "sample": "FCFS: first come first served, simple but convoy effect. SJF: shortest job first, optimal but needs burst time prediction. Round Robin: time-slice based, fair. Priority: starvation risk.", "tips": "Calculate average waiting time for small examples."},
        {"q": "What is semaphore?", "keywords": ["synchronization","binary","counting","wait","signal","mutex","critical","section"], "sample": "A semaphore is a synchronization primitive. Binary semaphore (0/1) is like a mutex. Counting semaphore tracks available resources. wait() decrements, signal() increments.", "tips": "Know Producer-Consumer problem solution using semaphores."},
        {"q": "Explain memory management techniques.", "keywords": ["paging","segmentation","fragmentation","compaction","buddy","slab","allocation","fit"], "sample": "Techniques include: Paging (fixed-size frames), Segmentation (variable logical units), Buddy System (power-of-2 allocation). External fragmentation handled by compaction or paging.", "tips": "Know internal vs external fragmentation clearly."},
        {"q": "What is a system call?", "keywords": ["kernel","user","mode","interface","trap","api","interrupt","privilege"], "sample": "System calls are interfaces between user space and kernel space. When a program needs OS services (file I/O, process creation), it triggers a software interrupt, switching to kernel mode.", "tips": "Examples: fork(), exec(), read(), write(), open()."},
    ],
    "Data Structures": [
        {"q": "Explain time complexity of common operations in arrays vs linked lists.", "keywords": ["O(1)","O(n)","access","insert","delete","head","tail","random"], "sample": "Arrays: O(1) access, O(n) insert/delete. Linked Lists: O(n) access, O(1) insert/delete at head. Use arrays for random access, linked lists for frequent insertions.", "tips": "Always state best/average/worst cases."},
        {"q": "What is a binary search tree (BST)?", "keywords": ["left","right","smaller","larger","inorder","balanced","search","insert"], "sample": "BST: left subtree contains smaller values, right contains larger. Search/insert/delete: O(log n) average, O(n) worst (skewed). Inorder traversal gives sorted output.", "tips": "Know AVL tree for balanced BST. Mention Red-Black Tree."},
        {"q": "Explain graph traversal: BFS vs DFS.", "keywords": ["queue","stack","level","depth","visited","adjacent","shortest","path"], "sample": "BFS uses a queue, explores level by level—ideal for shortest path in unweighted graphs. DFS uses a stack/recursion, explores depth-first—used for cycle detection, topological sort.", "tips": "Know time complexity: O(V+E) for both."},
        {"q": "What is dynamic programming?", "keywords": ["overlapping","subproblem","memoization","tabulation","optimal","cache","state","recurrence"], "sample": "DP solves problems with overlapping subproblems and optimal substructure. Top-down: memoization (cache recursive results). Bottom-up: tabulation (fill table iteratively). Examples: Fibonacci, Knapsack.", "tips": "Identify: can problem be broken into subproblems? Do they overlap?"},
        {"q": "Explain hashing and collision resolution.", "keywords": ["hash","function","collision","chaining","probing","bucket","load","factor"], "sample": "Hashing maps keys to indices via a hash function. Collisions resolved by: Chaining (linked list at bucket) or Open Addressing (linear/quadratic probing). Load factor affects performance.", "tips": "Average O(1) for insert/search. Know when to resize."},
        {"q": "What is a heap and where is it used?", "keywords": ["min","max","priority","queue","heapify","complete","binary","O(log n)"], "sample": "A heap is a complete binary tree satisfying heap property (min-heap: parent ≤ children). Used in: Priority Queues, Heap Sort, Dijkstra's algorithm. Heapify is O(n), insert/delete O(log n).", "tips": "Know heapify operation. Python's heapq module implements min-heap."},
        {"q": "Explain stack applications.", "keywords": ["undo","browser","expression","balanced","parentheses","call","backtrack","reverse"], "sample": "Stacks (LIFO) are used in: function call stack, expression evaluation (infix→postfix), balanced parentheses checking, undo operations, browser back button, DFS.", "tips": "Be ready to trace through a balanced parentheses algorithm."},
        {"q": "What are tries?", "keywords": ["prefix","string","search","autocomplete","dictionary","node","character","path"], "sample": "A trie (prefix tree) stores strings character by character. Each node represents a character. Enables O(m) search where m is word length. Used in autocomplete, spell-check, IP routing.", "tips": "Space can be large—mention compressed tries (Patricia tree)."},
    ],
    "Behavioral": [
        {"q": "Describe a challenging team project you worked on.", "keywords": ["situation","task","action","result","team","conflict","resolve","delivered"], "sample": "S: Our final-year project had 4 members with conflicting ideas. T: I needed to align the team. A: I organized a structured meeting, listed pros/cons of each approach, and we voted. R: We delivered ahead of schedule and won best project award.", "tips": "Use STAR: Situation, Task, Action, Result."},
        {"q": "Tell me about a time you showed leadership.", "keywords": ["led","initiative","motivated","decision","responsibility","outcome","team","influence"], "sample": "S: Our team lead dropped out a week before submission. T: Someone had to step up. A: I redistributed tasks based on strengths, held daily standups. R: We submitted on time with the best demo in class.", "tips": "Leadership doesn't require a title. Show initiative."},
        {"q": "How did you handle a conflict with a teammate?", "keywords": ["disagreement","communicate","listen","resolve","perspective","compromise","outcome","professional"], "sample": "S: Teammate and I disagreed on tech stack. T: We needed consensus to proceed. A: I listened to their reasoning, shared mine, and we researched both options together. R: We chose a hybrid approach that worked better than either original idea.", "tips": "Show maturity. Never badmouth the other person."},
        {"q": "Describe a time you went above and beyond.", "keywords": ["extra","initiative","unexpected","value","impact","surprise","effort","recognized"], "sample": "S: Internship task was just to fix a bug. T: While fixing it, I noticed a larger performance issue. A: I fixed the bug and documented the performance issue with a proposed solution. R: Manager implemented my suggestion, improving response time by 40%.", "tips": "Quantify the impact when possible."},
        {"q": "How do you prioritize when you have multiple deadlines?", "keywords": ["prioritize","urgent","important","matrix","list","communicate","deadline","manage"], "sample": "I use the Eisenhower Matrix: urgent+important first, then schedule important-not-urgent tasks. I communicate proactively if a deadline is at risk. During finals I managed 3 project deadlines simultaneously using this method.", "tips": "Mention specific tools or frameworks you use."},
        {"q": "Tell me about a time you learned something quickly.", "keywords": ["learn","adapt","fast","new","skill","technology","applied","short","time"], "sample": "S: Internship required Flask, which I hadn't used. T: Had 2 days to build an API. A: I did the official tutorial in day 1, built the API on day 2 referencing docs. R: Delivered on time, mentor said it was production-quality.", "tips": "Shows adaptability—highly valued in startups."},
    ],
    "TCS": [
        {"q": "What is TCS and what are its core values?", "keywords": ["tata","consultancy","services","integrity","respect","excellence","learning","agility"], "sample": "TCS (Tata Consultancy Services) is India's largest IT company. Core values: Integrity, Respect for individuals, Excellence, Learning & Sharing, Customer centricity.", "tips": "Know TCS's revenue, headcount, and key business verticals."},
        {"q": "Explain the difference between agile and waterfall.", "keywords": ["iterative","sprint","flexible","sequential","phase","requirement","change","feedback"], "sample": "Waterfall: sequential phases (requirements→design→code→test→deploy), rigid. Agile: iterative sprints, adaptive to change, continuous feedback. TCS uses both—Agile for product work, Waterfall for fixed-scope contracts.", "tips": "Know Scrum roles: PO, Scrum Master, Dev Team."},
        {"q": "What is cloud computing?", "keywords": ["iaas","paas","saas","aws","azure","gcp","scalable","on-demand","service"], "sample": "Cloud computing delivers on-demand IT resources over the internet. Models: IaaS (infrastructure), PaaS (platform), SaaS (software). Providers: AWS, Azure, GCP. TCS is a major cloud migration partner.", "tips": "Know TCS's cloud partnerships and offerings."},
        {"q": "What do you know about TCS iON and TCS BaNCS?", "keywords": ["ion","bancs","platform","digital","banking","education","product","tcs"], "sample": "TCS iON is a digital learning and assessment platform. TCS BaNCS is a financial services platform used by banks globally. Both are key TCS product offerings.", "tips": "Research at least 2–3 TCS products/platforms."},
    ],
    "Google": [
        {"q": "How does Google Search work at a high level?", "keywords": ["crawl","index","rank","pagerank","algorithm","spider","serp","relevance"], "sample": "Google crawls the web via bots, indexes content in massive data stores, then ranks results using algorithms including PageRank (link authority), content relevance, user signals, and hundreds of other factors.", "tips": "Mention: crawl budget, canonicalization, Core Web Vitals."},
        {"q": "Explain MapReduce.", "keywords": ["map","reduce","distributed","parallel","hadoop","key-value","aggregate","scale"], "sample": "MapReduce is a programming model for processing large datasets in parallel. Map phase: splits data and applies a function. Reduce phase: aggregates map outputs by key. Used in Hadoop, and influenced Google's Bigtable/Spanner.", "tips": "Word count is the classic example. Know its limitations vs Spark."},
        {"q": "What is CAP theorem?", "keywords": ["consistency","availability","partition","tolerance","choose","two","distributed","trade-off"], "sample": "CAP: In a distributed system, you can guarantee only 2 of 3: Consistency (all nodes same data), Availability (always responds), Partition Tolerance (works despite network splits). Most systems sacrifice C (Cassandra) or A (HBase).", "tips": "Google Spanner achieves CA+P with TrueTime—mention this."},
        {"q": "Describe your approach to a system design problem.", "keywords": ["requirements","scale","api","database","cache","load","balancer","trade-off"], "sample": "I start by clarifying functional and non-functional requirements, estimate scale (DAU, QPS), design APIs, choose data stores, add caching layer, design for scalability with load balancers and horizontal scaling, then discuss trade-offs.", "tips": "Use a structured approach: Requirements → High-level → Deep dive → Trade-offs."},
    ],
    "Startup": [
        {"q": "Why do you want to work at a startup?", "keywords": ["ownership","impact","learn","fast","build","iterate","autonomy","growth"], "sample": "I want direct ownership over what I build and to see its real-world impact quickly. Startups offer fast feedback loops, diverse responsibilities, and the chance to learn across the stack—not just one narrow area.", "tips": "Be honest. Mention risk tolerance. Ask about equity culture."},
        {"q": "How do you handle ambiguity?", "keywords": ["clarify","assumption","prototype","iterate","feedback","decision","comfortable","undefined"], "sample": "I first try to clarify with stakeholders. If that's not possible, I make explicit assumptions, prototype quickly, and seek early feedback. I'm comfortable making decisions with incomplete information and correcting course.", "tips": "Startups value bias-to-action. Don't say 'I wait for clarity.'"},
        {"q": "Describe a product you'd build to solve a local problem.", "keywords": ["problem","user","market","solution","build","validate","iterate","impact"], "sample": "I'd build a hyperlocal gig marketplace for Tamil Nadu's unorganized labour sector—connecting skilled workers (plumbers, electricians) with households via WhatsApp-first interface, solving the trust and discovery problem.", "tips": "Show product thinking: problem → solution → market → validation."},
        {"q": "How do you stay up-to-date with technology?", "keywords": ["read","blog","paper","twitter","newsletter","build","side","project","community"], "sample": "I follow Hacker News, specific GitHub repos, and newsletters like TLDR. I build side projects to apply new tech hands-on. I also engage with local developer communities like Chennai's tech meetups.", "tips": "Name specific resources. Build projects to show—not just read."},
    ],
}

# ─────────────────────────────────────────────
# COMPANIES DATA
# ─────────────────────────────────────────────
COMPANIES = [
    {"name": "TCS", "location": "Mumbai, Maharashtra", "state": "Maharashtra", "domain": "IT Services / Consulting", "website": "https://www.tcs.com/", "founded": 1968, "company_type": "Services", "tags": ["enterprise", "consulting", "ai", "cloud"]},
    {"name": "Infosys", "location": "Bengaluru, Karnataka", "state": "Karnataka", "domain": "IT Services / Consulting", "website": "https://www.infosys.com/", "founded": 1981, "company_type": "Services", "tags": ["consulting", "digital", "cloud", "enterprise"]},
    {"name": "Wipro", "location": "Bengaluru, Karnataka", "state": "Karnataka", "domain": "IT Services / Consulting", "website": "https://www.wipro.com/", "founded": 1945, "company_type": "Services", "tags": ["consulting", "ai", "cloud", "engineering"]},
    {"name": "HCLTech", "location": "Noida, Uttar Pradesh", "state": "Uttar Pradesh", "domain": "IT Services / Engineering", "website": "https://www.hcltech.com/", "founded": 1976, "company_type": "Services", "tags": ["engineering", "cloud", "enterprise", "ai"]},
    {"name": "Tech Mahindra", "location": "Pune, Maharashtra", "state": "Maharashtra", "domain": "IT Services / Telecom / Digital", "website": "https://www.techmahindra.com/", "founded": 1986, "company_type": "Services", "tags": ["telecom", "digital", "consulting"]},
    {"name": "LTIMindtree", "location": "Mumbai, Maharashtra", "state": "Maharashtra", "domain": "IT Services / Digital Transformation", "website": "https://www.ltimindtree.com/", "founded": 1996, "company_type": "Services", "tags": ["enterprise", "cloud", "digital"]},
    {"name": "Cognizant", "location": "Chennai, Tamil Nadu", "state": "Tamil Nadu", "domain": "IT Services / Digital Engineering", "website": "https://www.cognizant.com/", "founded": 1994, "company_type": "Services", "tags": ["digital", "engineering", "consulting"]},
    {"name": "Accenture India", "location": "Bengaluru, Karnataka", "state": "Karnataka", "domain": "Consulting / Technology Services", "website": "https://www.accenture.com/in-en", "founded": 1989, "company_type": "Services", "tags": ["consulting", "strategy", "cloud", "ai"]},
    {"name": "Capgemini India", "location": "Mumbai, Maharashtra", "state": "Maharashtra", "domain": "Consulting / Engineering / Cloud", "website": "https://www.capgemini.com/in-en/", "founded": 1967, "company_type": "Services", "tags": ["consulting", "cloud", "engineering"]},
    {"name": "Deloitte India", "location": "Hyderabad, Telangana", "state": "Telangana", "domain": "Consulting / Risk / Technology", "website": "https://www2.deloitte.com/in/en.html", "founded": 1845, "company_type": "Services", "tags": ["consulting", "risk", "technology"]},
    {"name": "IBM India", "location": "Bengaluru, Karnataka", "state": "Karnataka", "domain": "Cloud / AI / Enterprise Technology", "website": "https://www.ibm.com/in-en", "founded": 1911, "company_type": "Global Tech", "tags": ["ai", "cloud", "enterprise", "research"]},
    {"name": "Oracle India", "location": "Bengaluru, Karnataka", "state": "Karnataka", "domain": "Cloud / Database / Enterprise Software", "website": "https://www.oracle.com/in/", "founded": 1977, "company_type": "Product", "tags": ["database", "cloud", "enterprise"]},
    {"name": "Microsoft India", "location": "Hyderabad, Telangana", "state": "Telangana", "domain": "Cloud / AI / Productivity / Platforms", "website": "https://www.microsoft.com/en-in/", "founded": 1975, "company_type": "Product", "tags": ["cloud", "ai", "product", "platform"]},
    {"name": "Google India", "location": "Bengaluru, Karnataka", "state": "Karnataka", "domain": "Search / Cloud / AI / Ads", "website": "https://about.google/intl/en_in/", "founded": 1998, "company_type": "Product", "tags": ["ai", "search", "cloud", "product"]},
    {"name": "Amazon India", "location": "Bengaluru, Karnataka", "state": "Karnataka", "domain": "E-commerce / Cloud / Product Engineering", "website": "https://www.amazon.in/", "founded": 1994, "company_type": "Product", "tags": ["cloud", "ecommerce", "product", "aws"]},
    {"name": "Adobe India", "location": "Noida, Uttar Pradesh", "state": "Uttar Pradesh", "domain": "Creative Software / Document Cloud / Product", "website": "https://www.adobe.com/in/", "founded": 1982, "company_type": "Product", "tags": ["creative", "document", "product", "saas"]},
    {"name": "SAP Labs India", "location": "Bengaluru, Karnataka", "state": "Karnataka", "domain": "Enterprise Software / Cloud", "website": "https://www.sap.com/india/index.html", "founded": 1972, "company_type": "Product", "tags": ["enterprise", "erp", "cloud", "product"]},
    {"name": "Salesforce India", "location": "Hyderabad, Telangana", "state": "Telangana", "domain": "CRM / Cloud / SaaS", "website": "https://www.salesforce.com/in/", "founded": 1999, "company_type": "Product", "tags": ["crm", "saas", "cloud"]},
    {"name": "ServiceNow India", "location": "Hyderabad, Telangana", "state": "Telangana", "domain": "Enterprise Workflow / SaaS", "website": "https://www.servicenow.com/", "founded": 2004, "company_type": "Product", "tags": ["saas", "enterprise", "workflow"]},
    {"name": "Atlassian India", "location": "Bengaluru, Karnataka", "state": "Karnataka", "domain": "Developer Tools / SaaS / Collaboration", "website": "https://www.atlassian.com/", "founded": 2002, "company_type": "Product", "tags": ["developer tools", "saas", "collaboration"]},
    {"name": "Intel India", "location": "Bengaluru, Karnataka", "state": "Karnataka", "domain": "Semiconductors / Systems / AI", "website": "https://www.intel.com/content/www/us/en/homepage.html", "founded": 1968, "company_type": "Hardware", "tags": ["chips", "semiconductor", "systems", "ai"]},
    {"name": "NVIDIA India", "location": "Bengaluru, Karnataka", "state": "Karnataka", "domain": "AI Computing / GPUs / Platforms", "website": "https://www.nvidia.com/en-in/", "founded": 1993, "company_type": "Hardware", "tags": ["ai", "gpu", "platform", "chips"]},
    {"name": "Qualcomm India", "location": "Hyderabad, Telangana", "state": "Telangana", "domain": "Semiconductors / Telecom / Embedded Systems", "website": "https://www.qualcomm.com/", "founded": 1985, "company_type": "Hardware", "tags": ["chips", "telecom", "embedded"]},
    {"name": "Cisco India", "location": "Bengaluru, Karnataka", "state": "Karnataka", "domain": "Networking / Security / Cloud", "website": "https://www.cisco.com/site/in/en/index.html", "founded": 1984, "company_type": "Hardware", "tags": ["networking", "security", "cloud"]},
    {"name": "Zoho Corporation", "location": "Chennai, Tamil Nadu", "state": "Tamil Nadu", "domain": "SaaS / Product", "website": "https://www.zoho.com/", "founded": 1996, "company_type": "Product", "tags": ["saas", "crm", "business software"]},
    {"name": "Freshworks", "location": "Chennai, Tamil Nadu", "state": "Tamil Nadu", "domain": "SaaS / CRM / Support", "website": "https://www.freshworks.com/", "founded": 2010, "company_type": "Product", "tags": ["saas", "crm", "support"]},
    {"name": "Flipkart", "location": "Bengaluru, Karnataka", "state": "Karnataka", "domain": "E-commerce / Product / Supply Chain", "website": "https://www.flipkart.com/", "founded": 2007, "company_type": "Startup", "tags": ["ecommerce", "product", "marketplace"]},
    {"name": "PhonePe", "location": "Bengaluru, Karnataka", "state": "Karnataka", "domain": "Fintech / Payments", "website": "https://www.phonepe.com/", "founded": 2015, "company_type": "Startup", "tags": ["fintech", "payments", "upi"]},
    {"name": "Razorpay", "location": "Bengaluru, Karnataka", "state": "Karnataka", "domain": "Fintech / Payments / Banking Tech", "website": "https://razorpay.com/", "founded": 2014, "company_type": "Startup", "tags": ["fintech", "payments", "banking"]},
    {"name": "Paytm", "location": "Noida, Uttar Pradesh", "state": "Uttar Pradesh", "domain": "Fintech / Payments / Commerce", "website": "https://paytm.com/", "founded": 2010, "company_type": "Startup", "tags": ["fintech", "payments", "commerce"]},
    {"name": "Swiggy", "location": "Bengaluru, Karnataka", "state": "Karnataka", "domain": "Consumer Tech / Logistics / Commerce", "website": "https://www.swiggy.com/", "founded": 2014, "company_type": "Startup", "tags": ["consumer tech", "logistics", "commerce"]},
    {"name": "Zomato", "location": "Gurugram, Haryana", "state": "Haryana", "domain": "Consumer Tech / Food Delivery", "website": "https://www.zomato.com/", "founded": 2008, "company_type": "Startup", "tags": ["consumer tech", "delivery", "food"]},
    {"name": "Zerodha", "location": "Bengaluru, Karnataka", "state": "Karnataka", "domain": "Fintech / Brokerage / Trading Platforms", "website": "https://zerodha.com/", "founded": 2010, "company_type": "Startup", "tags": ["fintech", "trading", "platform"]},
    {"name": "Tata Elxsi", "location": "Bengaluru, Karnataka", "state": "Karnataka", "domain": "Design / Embedded / Engineering R&D", "website": "https://www.tataelxsi.com/", "founded": 1989, "company_type": "Engineering", "tags": ["embedded", "design", "engineering"]},
    {"name": "L&T Technology Services", "location": "Vadodara, Gujarat", "state": "Gujarat", "domain": "Engineering / R&D Services", "website": "https://www.ltts.com/", "founded": 1997, "company_type": "Engineering", "tags": ["engineering", "rd", "manufacturing"]},
    {"name": "Mphasis", "location": "Bengaluru, Karnataka", "state": "Karnataka", "domain": "Cloud / Banking Tech / IT Services", "website": "https://www.mphasis.com/", "founded": 2000, "company_type": "Services", "tags": ["banking", "cloud", "services"]},
    {"name": "Persistent Systems", "location": "Pune, Maharashtra", "state": "Maharashtra", "domain": "Software / Digital Engineering / Cloud", "website": "https://www.persistent.com/", "founded": 1990, "company_type": "Services", "tags": ["software", "cloud", "engineering"]},
    {"name": "Hexaware", "location": "Mumbai, Maharashtra", "state": "Maharashtra", "domain": "IT Services / AI / Automation", "website": "https://hexaware.com/", "founded": 1990, "company_type": "Services", "tags": ["automation", "ai", "services"]},
]

# ─────────────────────────────────────────────
# LEADERBOARD DATA
# ─────────────────────────────────────────────
LEADERBOARD = [
    {"rank": 1, "name": "Priya Ramesh", "college": "IIT Madras", "score": 9.4, "sessions": 28, "badge": "🥇"},
    {"rank": 2, "name": "Arjun Krishnan", "college": "Anna University", "score": 9.1, "sessions": 24, "badge": "🥈"},
    {"rank": 3, "name": "Kavya Subramaniam", "college": "NIT Trichy", "score": 8.9, "sessions": 31, "badge": "🥉"},
    {"rank": 4, "name": "Rahul Murugan", "college": "SSN College", "score": 8.7, "sessions": 19, "badge": "🏅"},
    {"rank": 5, "name": "Deepika Selvam", "college": "CEG Chennai", "score": 8.5, "sessions": 22, "badge": "🏅"},
    {"rank": 6, "name": "Vikram Narayanan", "college": "Amrita University", "score": 8.3, "sessions": 17, "badge": "🏅"},
    {"rank": 7, "name": "Ananya Chandrasekaran", "college": "VIT Vellore", "score": 8.2, "sessions": 20, "badge": "🏅"},
    {"rank": 8, "name": "Siva Karthikeyan", "college": "PSG Tech", "score": 8.0, "sessions": 15, "badge": "🏅"},
    {"rank": 9, "name": "Meena Durai", "college": "Thiagarajar College", "score": 7.8, "sessions": 18, "badge": "🏅"},
    {"rank": 10, "name": "Arun Balasubramanian", "college": "SRM Institute", "score": 7.6, "sessions": 21, "badge": "🏅"},
]

# ─────────────────────────────────────────────
# FILLER WORDS
# ─────────────────────────────────────────────
FILLER_WORDS = ["um", "uh", "basically", "like", "you know", "kind of", "sort of", "actually", "literally", "right"]

# ─────────────────────────────────────────────
# AI SCORING FUNCTION
# ─────────────────────────────────────────────
def score_answer(answer, question_data):
    if not answer or len(answer.strip()) < 10:
        return 1.0, "Answer too short."

    answer_lower = answer.lower()
    words = answer_lower.split()
    word_count = len(words)

    # Keyword score (0-4)
    keywords = question_data.get("keywords", [])
    matched = sum(1 for kw in keywords if kw.lower() in answer_lower)
    keyword_score = min(4.0, (matched / max(len(keywords), 1)) * 4.0)

    # Length score (0-3): 80–200 words is ideal
    if word_count < 20:
        length_score = 0.5
    elif word_count < 50:
        length_score = 1.5
    elif word_count <= 200:
        length_score = 3.0
    elif word_count <= 350:
        length_score = 2.0
    else:
        length_score = 1.0

    # Filler word penalty (0-3)
    filler_count = sum(answer_lower.count(fw) for fw in FILLER_WORDS)
    filler_score = max(0, 3.0 - filler_count * 0.5)

    total = keyword_score + length_score + filler_score
    score = round(min(10.0, max(1.0, total)), 1)

    # Feedback
    feedback_parts = []
    if matched == 0:
        feedback_parts.append("❌ No key terms detected. Try to include relevant technical/domain vocabulary.")
    elif matched < len(keywords) // 2:
        feedback_parts.append(f"⚠️ Only {matched}/{len(keywords)} key terms covered. Expand your answer.")
    else:
        feedback_parts.append(f"✅ Good coverage of {matched}/{len(keywords)} key concepts.")

    if word_count < 50:
        feedback_parts.append("📝 Answer is too brief. Aim for 80–150 words.")
    elif word_count > 300:
        feedback_parts.append("📝 Answer is too long. Be concise—interviewers value clarity.")
    else:
        feedback_parts.append(f"📝 Good length ({word_count} words).")

    if filler_count > 3:
        feedback_parts.append(f"🔇 High filler word usage ({filler_count} found). Practice speaking without them.")
    elif filler_count > 0:
        feedback_parts.append(f"🔇 Minor filler words detected ({filler_count}). Keep improving.")
    else:
        feedback_parts.append("🔇 No filler words detected. Excellent delivery!")

    return score, " | ".join(feedback_parts)


def load_groq_api_key():
    env_key = os.getenv("GROQ_API_KEY", "").strip()
    if env_key:
        return env_key

    for file_name in os.listdir("."):
        if file_name.startswith("gsk_") and file_name.endswith(".txt"):
            with open(file_name, "r", encoding="utf-8") as handle:
                return handle.read().strip()
    return ""


def groq_chat_completion(system_prompt, user_prompt, temperature=0.2, max_tokens=900):
    api_key = load_groq_api_key()
    if not api_key:
        raise RuntimeError("Missing Groq API key. Set GROQ_API_KEY or keep the key in a local gsk_*.txt file.")

    payload = {
        "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    request = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ai-interview-coach/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        if exc.code == 403 and "1010" in detail:
            raise RuntimeError(
                "Groq rejected this request with 403/1010. This usually means the API key is blocked, revoked, "
                "restricted, or being denied by Groq's edge protection. Generate a fresh Groq API key, set it in "
                "GROQ_API_KEY, and try again."
            ) from exc
        raise RuntimeError(f"Groq request failed with HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Unable to reach Groq API: {exc.reason}") from exc

    return json.loads(data["choices"][0]["message"]["content"])


def groq_text_chat(messages, temperature=0.7, max_tokens=900):
    api_key = load_groq_api_key()
    if not api_key:
        raise RuntimeError("Missing Groq API key. Set GROQ_API_KEY or keep the key in a local gsk_*.txt file.")

    payload = {
        "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    request = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ai-interview-coach/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        if exc.code == 403 and "1010" in detail:
            raise RuntimeError(
                "Groq rejected this request with 403/1010. This usually means the API key is blocked, revoked, "
                "restricted, or being denied by Groq's edge protection. Generate a fresh Groq API key, set it in "
                "GROQ_API_KEY, and try again."
            ) from exc
        raise RuntimeError(f"Groq request failed with HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Unable to reach Groq API: {exc.reason}") from exc

    return data["choices"][0]["message"]["content"]


def local_score_answer(answer, question_data):
    if not answer or len(answer.strip()) < 10:
        return {
            "score": 1.0,
            "summary": "Answer too short.",
            "strengths": [],
            "improvements": ["Add more detail and structure before submitting."],
            "missed_keywords": question_data.get("keywords", []),
            "ideal_answer": question_data.get("sample", ""),
            "source": "rules",
        }

    answer_lower = answer.lower()
    word_count = len(answer_lower.split())
    keywords = question_data.get("keywords", [])
    matched = sum(1 for kw in keywords if kw.lower() in answer_lower)
    keyword_score = min(4.0, (matched / max(len(keywords), 1)) * 4.0)

    if word_count < 20:
        length_score = 0.5
    elif word_count < 50:
        length_score = 1.5
    elif word_count <= 200:
        length_score = 3.0
    elif word_count <= 350:
        length_score = 2.0
    else:
        length_score = 1.0

    filler_count = sum(answer_lower.count(fw) for fw in FILLER_WORDS)
    filler_score = max(0, 3.0 - filler_count * 0.5)
    score = round(min(10.0, max(1.0, keyword_score + length_score + filler_score)), 1)

    feedback_parts = []
    if matched == 0:
        feedback_parts.append("No key terms detected. Use more role-relevant vocabulary.")
    elif matched < len(keywords) // 2:
        feedback_parts.append(f"Only {matched}/{len(keywords)} key terms were covered.")
    else:
        feedback_parts.append(f"Good coverage of {matched}/{len(keywords)} key concepts.")

    if word_count < 50:
        feedback_parts.append("Answer is brief. Aim for 80 to 150 words.")
    elif word_count > 300:
        feedback_parts.append("Answer is long. Tighten the structure.")
    else:
        feedback_parts.append(f"Length is workable at {word_count} words.")

    if filler_count > 3:
        feedback_parts.append(f"High filler-word usage detected: {filler_count}.")
    elif filler_count > 0:
        feedback_parts.append(f"A few filler words showed up: {filler_count}.")
    else:
        feedback_parts.append("Delivery looks clean with no filler words detected.")

    return {
        "score": score,
        "summary": " | ".join(feedback_parts),
        "strengths": [
            f"Covered {matched}/{len(keywords)} expected concepts." if keywords else "Stayed on topic.",
            f"Response length: {word_count} words.",
        ],
        "improvements": [
            "Add one specific example, metric, or result.",
            "Use a clearer opening and closing sentence.",
        ],
        "missed_keywords": [kw for kw in keywords if kw.lower() not in answer_lower][:6],
        "ideal_answer": question_data.get("sample", ""),
        "source": "rules",
    }


def ai_score_answer(answer, question_data, interview_type):
    system_prompt = (
        "You are an expert interview evaluator. "
        "Return strict JSON with keys: score, summary, strengths, improvements, missed_keywords, ideal_answer. "
        "score must be a number from 1.0 to 10.0. "
        "strengths and improvements must be arrays of 2 to 3 short strings. "
        "ideal_answer must be a polished improved answer under 140 words."
    )
    user_prompt = json.dumps(
        {
            "interview_type": interview_type,
            "question": question_data.get("q", ""),
            "expected_keywords": question_data.get("keywords", []),
            "sample_answer": question_data.get("sample", ""),
            "tips": question_data.get("tips", ""),
            "candidate_answer": answer,
        },
        ensure_ascii=True,
    )
    result = groq_chat_completion(system_prompt, user_prompt, temperature=0.2, max_tokens=700)
    return {
        "score": round(min(10.0, max(1.0, float(result.get("score", 1.0)))), 1),
        "summary": str(result.get("summary", "AI review generated.")),
        "strengths": [str(item) for item in result.get("strengths", [])][:3],
        "improvements": [str(item) for item in result.get("improvements", [])][:3],
        "missed_keywords": [str(item) for item in result.get("missed_keywords", [])][:6],
        "ideal_answer": str(result.get("ideal_answer", question_data.get("sample", ""))),
        "source": "ai",
    }


def score_answer(answer, question_data, interview_type):
    fallback = local_score_answer(answer, question_data)
    if not answer or len(answer.strip()) < 10:
        return fallback

    try:
        return ai_score_answer(answer, question_data, interview_type)
    except Exception as exc:
        fallback["summary"] = f"{fallback['summary']} | AI review unavailable: {exc}"
        return fallback


def mentor_reply(question_data, user_prompt, topic, chat_history=None):
    system_prompt = (
        "You are an interview mentor that should feel like ChatGPT: conversational, adaptive, and helpful. "
        "Answer naturally in plain markdown. You can explain, rewrite, quiz, roleplay, or critique answers. "
        "Stay grounded in the selected interview question and topic when relevant, but answer follow-ups naturally. "
        "Do not return JSON."
    )
    question_block = (
        f"Topic: {topic}\n"
        f"Current interview question: {question_data.get('q', '')}\n"
        f"Helpful concepts: {', '.join(question_data.get('keywords', []))}\n"
        f"Reference sample answer: {question_data.get('sample', '')}\n"
        f"Interview tip: {question_data.get('tips', '')}"
    )
    messages = [{"role": "system", "content": system_prompt}]
    messages.append({"role": "system", "content": question_block})
    for item in chat_history or []:
        messages.append({"role": item["role"], "content": item["content"]})
    messages.append({"role": "user", "content": user_prompt})
    return groq_text_chat(messages, temperature=0.7, max_tokens=900)


def local_mentor_reply(question_data, user_prompt, topic, chat_history=None):
    keywords = question_data.get("keywords", [])[:5]
    prior_turns = len(chat_history or [])
    focus_line = ", ".join(keywords) if keywords else "clear structure and relevance"
    answer = (
        f"I am in fallback mode right now, but I can still coach you.\n\n"
        f"We are discussing **{topic}** and this question: **{question_data.get('q', '')}**.\n\n"
        f"The main ideas to cover are **{focus_line}**. "
        f"A strong answer usually starts with the direct point, adds one concrete example, and ends with a short takeaway.\n\n"
        f"Relevant tip: {question_data.get('tips', 'Keep the answer focused and specific.')}\n\n"
        f"You have {prior_turns} earlier turns in this chat, so I am treating this as an ongoing conversation.\n\n"
        f"For your latest message, my advice is: respond directly, stay specific, and if you want I can next do one of these:\n"
        f"1. Rewrite your answer\n"
        f"2. Ask you a follow-up interview question\n"
        f"3. Give a stronger sample answer\n"
        f"4. Critique your draft line by line"
    )
    if user_prompt.strip():
        answer += f"\n\nYour message was: _{user_prompt.strip()}_"
    return answer


def get_mentor_response(question_data, user_prompt, topic, chat_history):
    try:
        result = mentor_reply(question_data, user_prompt, topic, chat_history)
        return result, ""
    except Exception as exc:
        result = local_mentor_reply(question_data, user_prompt, topic, chat_history)
        return result, f"Live AI unavailable, using built-in coach: {exc}"

# ─────────────────────────────────────────────
# GET QUESTIONS FOR INTERVIEW TYPE
# ─────────────────────────────────────────────
def get_questions(interview_type, n):
    category_map = {
        "HR": ["HR"],
        "Technical - Python": ["Python"],
        "Technical - DBMS": ["DBMS"],
        "Technical - OS": ["OS"],
        "Technical - Data Structures": ["Data Structures"],
        "Behavioral": ["Behavioral"],
        "Company - TCS": ["TCS", "HR"],
        "Company - Google": ["Google", "Data Structures"],
        "Company - Startup": ["Startup", "Behavioral"],
    }
    cats = category_map.get(interview_type, ["HR"])
    pool = []
    for cat in cats:
        pool.extend(QUESTION_BANK.get(cat, []))
    if not pool:
        pool = QUESTION_BANK["HR"]
    selected = random.sample(pool, min(n, len(pool)))
    if len(selected) < n:
        selected += random.choices(pool, k=n-len(selected))
    return selected


def average_skill_score(skill_dict):
    if not skill_dict:
        return 0.0
    values = list(skill_dict.values())
    return round(sum(values) / len(values), 1) if values else 0.0


def build_growth_recommendations(user):
    hard_skills = user.get("hard_skills", {})
    soft_skills = user.get("soft_skills", {})
    learning_style = user.get("learning_style", "Balanced")
    weekly_hours = user.get("weekly_hours", 5)
    target_role = user.get("target_role", "Software Engineer")
    improvement_goal = user.get("improvement_goal", "Crack interviews with confidence")

    hard_avg = average_skill_score(hard_skills)
    soft_avg = average_skill_score(soft_skills)

    weakest_hard = sorted(hard_skills.items(), key=lambda item: item[1])[:2]
    weakest_soft = sorted(soft_skills.items(), key=lambda item: item[1])[:2]

    strengths = []
    if hard_skills:
        strongest_hard = max(hard_skills.items(), key=lambda item: item[1])
        strengths.append(f"Your strongest hard skill right now is {strongest_hard[0]} ({strongest_hard[1]}/10).")
    if soft_skills:
        strongest_soft = max(soft_skills.items(), key=lambda item: item[1])
        strengths.append(f"Your strongest soft skill right now is {strongest_soft[0]} ({strongest_soft[1]}/10).")

    recommendations = []
    if weakest_hard:
        recommendations.append(
            f"Prioritize technical improvement in {weakest_hard[0][0]} and {weakest_hard[1][0] if len(weakest_hard) > 1 else weakest_hard[0][0]}."
        )
    if weakest_soft:
        recommendations.append(
            f"Work on {weakest_soft[0][0]} through mock interviews, reflection, and repeated practice."
        )
    if hard_avg < 6:
        recommendations.append("Spend more time on fundamentals before attempting harder company-specific rounds.")
    if soft_avg < 6:
        recommendations.append("Practice speaking answers aloud so your delivery improves along with content.")

    weekly_plan = [
        f"Spend about {max(2, weekly_hours // 2)} hours per week on technical revision for your target role: {target_role}.",
        f"Use a {learning_style.lower()} learning style plan: mix learning, practice, and review each week.",
        "Complete at least 2 mock interview answers and review the feedback after each session.",
        "Maintain one project or coding exercise log so your improvement is visible over time.",
    ]

    if weakest_hard:
        weekly_plan.append(f"Start each week with one focused session on {weakest_hard[0][0]}.")
    if weakest_soft:
        weekly_plan.append(f"End each week by reviewing one soft-skill area: {weakest_soft[0][0]}.")

    summary = (
        f"You want to become a stronger {target_role} candidate and your current focus is '{improvement_goal}'. "
        f"Your hard-skill average is {hard_avg}/10 and your soft-skill average is {soft_avg}/10."
    )

    return {
        "summary": summary,
        "strengths": strengths,
        "recommendations": recommendations,
        "weekly_plan": weekly_plan,
        "hard_avg": hard_avg,
        "soft_avg": soft_avg,
    }


def evaluate_hard_skill_test(responses):
    per_skill = {}
    for question, selected in responses:
        skill = question["skill"]
        stats = per_skill.setdefault(skill, {"correct": 0, "total": 0})
        stats["total"] += 1
        if selected == question["answer"]:
            stats["correct"] += 1

    scores = {}
    for skill in SKILL_AREAS["hard_skills"]:
        stats = per_skill.get(skill, {"correct": 0, "total": 0})
        if stats["total"] == 0:
            scores[skill] = 0
        else:
            scores[skill] = max(1, round((stats["correct"] / stats["total"]) * 10))

    total_correct = sum(item["correct"] for item in per_skill.values())
    total_questions = sum(item["total"] for item in per_skill.values())
    overall = round((total_correct / total_questions) * 10, 1) if total_questions else 0.0
    return {
        "overall": overall,
        "scores": scores,
        "per_skill": per_skill,
    }


def get_recent_mentor_history(messages):
    if not messages:
        return []
    usable = messages[:-1]
    if len(usable) <= 10:
        return [{"role": item["role"], "content": item["content"]} for item in usable]
    return [{"role": item["role"], "content": item["content"]} for item in usable[-10:]]


def evaluate_debug_submission(question, fixed_code, explanation, selected_language):
    text = f"{fixed_code}\n{explanation}".lower()
    matched = sum(1 for signal in question["fix_signals"] if signal.lower() in text)
    is_correct = matched >= max(1, len(question["fix_signals"]) - 1)
    score = 10.0 if is_correct else round(min(9.0, max(1.0, 2 + matched * 2.0)), 1)

    syntax_notes = {
        "Python": "Use indentation correctly and handle control flow with Python syntax like `if ...:` and `for ... in ...`.",
        "Java": "Remember braces, semicolons, and explicit types in Java.",
        "C++": "Remember braces, semicolons, and standard library usage in C++.",
        "JavaScript": "Check block structure, `return` paths, and JavaScript function syntax.",
        "SQL": "Use the correct SQL clause order and the right join/filter syntax.",
    }

    incorrect_points = []
    for keyword in question["expected_keywords"][:2]:
        if keyword.lower() not in text:
            incorrect_points.append(keyword)

    if is_correct:
        feedback = (
            f"Correct fix. You identified the core bug and used the right {selected_language} fix direction. "
            "Nice work on debugging this one."
        )
    else:
        feedback = "Your answer is not fully correct yet."
        if incorrect_points:
            feedback += f" Missing ideas: {', '.join(incorrect_points)}."
        feedback += f" {syntax_notes.get(selected_language, 'Check the language syntax and control flow carefully.')}"

    return {
        "score": score,
        "feedback": feedback,
        "is_correct": is_correct,
        "incorrect_points": incorrect_points,
        "solution": question.get("correct_solution", ""),
    }


def filter_companies(companies, query="", state_filter="All", type_filter="All"):
    query_tokens = [token.strip().lower() for token in query.split() if token.strip()]
    filtered = []

    for company in companies:
        if state_filter != "All" and company.get("state", "") != state_filter:
            continue
        if type_filter != "All" and company.get("company_type", "") != type_filter:
            continue

        searchable_parts = [
            company.get("name", ""),
            company.get("location", ""),
            company.get("state", ""),
            company.get("domain", ""),
            company.get("company_type", ""),
            company.get("website", ""),
            " ".join(company.get("tags", [])),
        ]
        searchable_text = " ".join(searchable_parts).lower()

        if all(token in searchable_text for token in query_tokens):
            match_score = sum(searchable_text.count(token) for token in query_tokens) if query_tokens else 0
            filtered.append((match_score, company))

    filtered.sort(key=lambda item: (-item[0], item[1]["name"]))
    return [item[1] for item in filtered]

# ─────────────────────────────────────────────
# SIDEBAR NAVIGATION
# ─────────────────────────────────────────────
def sidebar():
    with st.sidebar:
        st.markdown("""
        <div style='text-align:center; padding: 1rem 0;'>
            <h2 style='color:#e94560; font-family:Syne,sans-serif; margin:0;'>🎯 AI Interview</h2>
            <h2 style='color:#e94560; font-family:Syne,sans-serif; margin:0;'>Coach</h2>
            <p style='color:#a8b2d8; font-size:0.8rem; margin:0.3rem 0 0 0;'>Tamil Nadu Edition</p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        if st.session_state.logged_in:
            user = st.session_state.user
            st.markdown(f"""
            <div style='background:linear-gradient(135deg,#0f3460,#16213e);border:1px solid #e94560;border-radius:10px;padding:0.8rem;margin-bottom:1rem;text-align:center;'>
                <p style='color:#e94560;font-weight:700;margin:0;font-size:1rem;'>👤 {user.get("name","User")}</p>
                <p style='color:#a8b2d8;font-size:0.75rem;margin:0;'>{user.get("college","")}</p>
                <p style='color:#a8b2d8;font-size:0.75rem;margin:0;'>{user.get("branch","")} • Year {user.get("year","")}</p>
            </div>
            """, unsafe_allow_html=True)

        pages = [
            ("🏠", "Home"),
            ("📝", "Mock Interview"),
            ("🧪", "Hard Skill Test"),
            ("🐞", "Debug Coding Test"),
            ("📚", "Question Bank"),
            ("🧩", "Practice Problems"),
            ("📊", "Progress Tracker"),
            ("🏆", "Leaderboard"),
            ("🤖", "AI Mentor"),
            ("🏢", "Top Companies"),
            ("👤", "My Profile"),
            ("📞", "Contact Us"),
        ]

        for icon, name in pages:
            label = f"{icon} {name}"
            active = st.session_state.page == label
            if st.button(label, key=f"nav_{name}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.page = label
                st.session_state.interview_active = False
                st.rerun()

        st.divider()
        if st.session_state.logged_in:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.user = {}
                st.session_state.page = "🏠 Home"
                st.rerun()

sidebar()

# ─────────────────────────────────────────────
# PAGE: HOME
# ─────────────────────────────────────────────
def page_home():
    st.markdown("""
    <div class='main-header'>
        <h1>🎯 AI Interview Coach</h1>
        <p>Your personal interview preparation platform · Tamil Nadu Edition</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.logged_in:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📋 Register")
            with st.form("register_form"):
                name = st.text_input("Full Name *")
                email = st.text_input("Email *")
                phone = st.text_input("Phone")
                college = st.text_input("College / University")
                branch = st.selectbox("Branch", ["CS", "IT", "ECE", "Mech", "Civil", "Other"])
                year = st.selectbox("Year", ["1st", "2nd", "3rd", "4th", "Alumni"])
                cgpa = st.number_input("CGPA", 0.0, 10.0, 7.5, 0.1)
                coding_knowledge = st.selectbox(
                    "Programming Knowledge",
                    ["Beginner", "Intermediate", "Advanced", "Competitive Coding", "Full Stack", "AI/ML Focused"]
                )
                interests = st.multiselect("Areas of Interest",
                    ["Python", "Web Dev", "Data Science", "ML/AI", "DevOps", "Cloud", "DSA", "System Design", "Product Management"])
                submitted = st.form_submit_button("🚀 Register & Start", use_container_width=True)

                if submitted:
                    if not name or not email:
                        st.error("Name and Email are required.")
                    else:
                        st.session_state.user = {
                            "name": name, "email": email, "phone": phone,
                            "college": college, "branch": branch, "year": year,
                            "cgpa": cgpa, "coding_knowledge": coding_knowledge, "interests": interests,
                            "target_role": "Software Engineer",
                            "learning_style": "Balanced",
                            "weekly_hours": 6,
                            "improvement_goal": "Crack interviews with confidence",
                            "hard_skills": {skill: 5 for skill in SKILL_AREAS["hard_skills"]},
                            "soft_skills": {skill: 5 for skill in SKILL_AREAS["soft_skills"]},
                        }
                        st.session_state.logged_in = True
                        st.session_state.page = "📝 Mock Interview"
                        st.success(f"Welcome, {name}! 🎉")
                        time.sleep(1)
                        st.rerun()

        with col2:
            st.markdown("### ⚡ Quick Login")
            with st.form("login_form"):
                qname = st.text_input("Your Name")
                qcollege = st.text_input("College")
                qbranch = st.selectbox("Branch ", ["CS", "IT", "ECE", "Mech", "Civil"])
                qcoding_knowledge = st.selectbox("Programming Knowledge ", ["Beginner", "Intermediate", "Advanced"])
                qlogin = st.form_submit_button("▶ Quick Start", use_container_width=True)
                if qlogin:
                    if not qname:
                        st.error("Please enter your name.")
                    else:
                        st.session_state.user = {
                            "name": qname, "college": qcollege, "branch": qbranch,
                            "email": "", "phone": "", "year": "3rd", "cgpa": 7.5,
                            "coding_knowledge": qcoding_knowledge, "interests": [],
                            "target_role": "Software Engineer",
                            "learning_style": "Balanced",
                            "weekly_hours": 6,
                            "improvement_goal": "Crack interviews with confidence",
                            "hard_skills": {skill: 5 for skill in SKILL_AREAS["hard_skills"]},
                            "soft_skills": {skill: 5 for skill in SKILL_AREAS["soft_skills"]},
                        }
                        st.session_state.logged_in = True
                        st.session_state.page = "📝 Mock Interview"
                        st.rerun()

            st.markdown("---")
            st.markdown("""
            <div style='background:linear-gradient(135deg,#1a1a2e,#16213e);border:1px solid #0f3460;border-radius:12px;padding:1.5rem;'>
                <h4 style='color:#e94560;margin-top:0;'>✨ What you get</h4>
                <p style='color:#a8b2d8;'>🎤 Mock Interviews with AI Scoring</p>
                <p style='color:#a8b2d8;'>📚 50+ Questions across all domains</p>
                <p style='color:#a8b2d8;'>📊 Progress tracking & Radar charts</p>
                <p style='color:#a8b2d8;'>🏆 Tamil Nadu Leaderboard</p>
                <p style='color:#a8b2d8;'>🤖 AI Mentor with STAR guidance</p>
                <p style='color:#a8b2d8;'>🏢 Top 10 TN Companies info</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        user = st.session_state.user
        sessions = st.session_state.sessions

        st.markdown(f"## Welcome back, {user['name']}! 👋")

        c1, c2, c3, c4 = st.columns(4)
        total_sessions = len(sessions)
        all_scores = [s for sess in sessions for s in sess["scores"]]
        avg_score = round(sum(all_scores)/len(all_scores), 1) if all_scores else 0
        best_score = round(max(all_scores), 1) if all_scores else 0

        with c1:
            st.metric("Total Sessions", total_sessions, "interviews")
        with c2:
            st.metric("Avg Score", avg_score, "/ 10")
        with c3:
            st.metric("Best Score", best_score, "/ 10")
        with c4:
            st.metric("CGPA", user.get("cgpa", "N/A"))

        st.markdown("### 🚀 Quick Actions")
        qa1, qa2, qa3, qa4 = st.columns(4)
        with qa1:
            if st.button("🎤 Start Mock Interview", use_container_width=True):
                st.session_state.page = "📝 Mock Interview"
                st.rerun()
        with qa2:
            if st.button("📚 Browse Questions", use_container_width=True):
                st.session_state.page = "📚 Question Bank"
                st.rerun()
        with qa3:
            if st.button("📊 View Progress", use_container_width=True):
                st.session_state.page = "📊 Progress Tracker"
                st.rerun()
        with qa4:
            if st.button("🤖 AI Mentor", use_container_width=True):
                st.session_state.page = "🤖 AI Mentor"
                st.rerun()

# ─────────────────────────────────────────────
# PAGE: MOCK INTERVIEW
# ─────────────────────────────────────────────
def page_interview():
    st.markdown("<div class='main-header'><h1>📝 Mock Interview</h1><p>Practice with AI-powered scoring and real-time feedback</p></div>", unsafe_allow_html=True)

    if not st.session_state.logged_in:
        st.warning("Please register or login first.")
        return

    if st.session_state.interview_done:
        show_interview_results()
        return

    if not st.session_state.interview_active:
        # Setup
        c1, c2 = st.columns(2)
        with c1:
            itype = st.selectbox("Interview Type", [
                "HR", "Technical - Python", "Technical - DBMS", "Technical - OS",
                "Technical - Data Structures", "Behavioral",
                "Company - TCS", "Company - Google", "Company - Startup"
            ])
        with c2:
            n_qs = st.slider("Number of Questions", 3, 10, 5)

        if st.button("🚀 Start Interview", use_container_width=True):
            qs = get_questions(itype, n_qs)
            st.session_state.questions = qs
            st.session_state.answers = [""] * len(qs)
            st.session_state.scores = [0.0] * len(qs)
            st.session_state.feedback = [{} for _ in qs]
            st.session_state.hints_used = [False] * len(qs)
            st.session_state.q_index = 0
            st.session_state.interview_active = True
            st.session_state.interview_done = False
            st.session_state.interview_type = itype
            st.session_state.timer_start = time.time()
            st.rerun()
    else:
        run_interview()

def run_interview():
    idx = st.session_state.q_index
    qs = st.session_state.questions
    total = len(qs)

    if idx >= total:
        finalize_interview()
        return

    q_data = qs[idx]

    # Progress
    st.progress((idx) / total)
    st.markdown(f"**Question {idx+1} of {total}** — *{st.session_state.interview_type}*")

    # Timer
    elapsed = time.time() - st.session_state.timer_start
    remaining = max(0, 60 - int(elapsed))

    if remaining > 30:
        tcol = "timer-green"
        ticon = "🟢"
    elif remaining > 10:
        tcol = "timer-yellow"
        ticon = "🟡"
    else:
        tcol = "timer-red"
        ticon = "🔴"

    st.markdown(f"<p class='{tcol}'>{ticon} Time remaining: {remaining}s</p>", unsafe_allow_html=True)

    # Question
    st.markdown(f"""
    <div class='card'>
        <h3 style='color:#e94560;margin:0;'>Q{idx+1}. {q_data['q']}</h3>
    </div>
    """, unsafe_allow_html=True)

    # Answer
    answer = st.text_area("Your Answer:", height=180, key=f"ans_{idx}",
                           placeholder="Type your answer here... (aim for 80–150 words)")
    word_count = len(answer.split()) if answer.strip() else 0
    st.caption(f"Word count: {word_count}")

    c1, c2, c3 = st.columns([2, 1, 1])

    with c1:
        if st.button("✅ Submit Answer", key=f"sub_{idx}", use_container_width=True):
            with st.spinner("Reviewing your answer with AI..."):
                feedback = score_answer(answer, q_data, st.session_state.interview_type)
            st.session_state.answers[idx] = answer
            st.session_state.scores[idx] = feedback["score"]
            st.session_state.feedback[idx] = feedback
            st.session_state.q_index = idx + 1
            st.session_state.timer_start = time.time()
            if idx + 1 >= total:
                st.session_state.interview_active = False
                st.session_state.interview_done = True
            st.rerun()

    with c2:
        if st.button("💡 Hint / Sample", key=f"hint_{idx}", use_container_width=True):
            st.session_state.hints_used[idx] = True
            st.info(f"**Sample Answer:** {q_data['sample']}\n\n**Tips:** {q_data['tips']}")

    with c3:
        if st.button("⏭ Skip", key=f"skip_{idx}", use_container_width=True):
            st.session_state.answers[idx] = ""
            st.session_state.scores[idx] = 1.0
            st.session_state.feedback[idx] = {
                "score": 1.0,
                "summary": "Question skipped.",
                "strengths": [],
                "improvements": ["Attempt the question next time, even with a short structured answer."],
                "missed_keywords": q_data.get("keywords", []),
                "ideal_answer": q_data.get("sample", ""),
                "source": "rules",
            }
            st.session_state.q_index = idx + 1
            st.session_state.timer_start = time.time()
            if idx + 1 >= total:
                st.session_state.interview_active = False
                st.session_state.interview_done = True
            st.rerun()

    # Auto-advance when timer runs out
    if remaining == 0:
        st.warning("⏰ Time's up! Auto-advancing to next question.")
        time.sleep(1)
        st.session_state.answers[idx] = answer
        st.session_state.scores[idx] = 1.0
        st.session_state.feedback[idx] = {
            "score": 1.0,
            "summary": "Time ran out before submission.",
            "strengths": [],
            "improvements": ["Practice answering within 60 seconds using a simple structure."],
            "missed_keywords": q_data.get("keywords", []),
            "ideal_answer": q_data.get("sample", ""),
            "source": "rules",
        }
        st.session_state.q_index = idx + 1
        st.session_state.timer_start = time.time()
        if idx + 1 >= len(qs):
            st.session_state.interview_active = False
            st.session_state.interview_done = True
        st.rerun()

def finalize_interview():
    qs = st.session_state.questions
    scores = st.session_state.scores
    itype = st.session_state.interview_type
    session_record = {
        "date": time.strftime("%Y-%m-%d"),
        "type": itype,
        "scores": list(scores),
        "avg": round(sum(scores)/len(scores), 1) if scores else 0,
    }
    st.session_state.sessions.append(session_record)
    st.session_state.interview_done = True
    st.rerun()

def show_interview_results():
    qs = st.session_state.questions
    scores = st.session_state.scores
    answers = st.session_state.answers
    feedback_items = st.session_state.feedback

    avg = round(sum(scores)/len(scores), 1) if scores else 0
    st.markdown(f"## 🎉 Interview Complete!")

    c1, c2, c3 = st.columns(3)
    with c1:
        color = "#00ff88" if avg >= 7 else "#ffd700" if avg >= 5 else "#e94560"
        st.markdown(f"<div class='metric-card'><h2 style='color:{color};'>{avg}/10</h2><p>Average Score</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='metric-card'><h2>{len(qs)}</h2><p>Questions Answered</p></div>", unsafe_allow_html=True)
    with c3:
        hints = sum(st.session_state.hints_used)
        st.markdown(f"<div class='metric-card'><h2>{hints}</h2><p>Hints Used</p></div>", unsafe_allow_html=True)

    # Bar chart
    labels = [f"Q{i+1}" for i in range(len(scores))]
    colors = ["#00ff88" if s >= 7 else "#ffd700" if s >= 5 else "#e94560" for s in scores]
    fig = go.Figure(go.Bar(x=labels, y=scores, marker_color=colors,
                           text=[f"{s}" for s in scores], textposition="outside"))
    fig.update_layout(
        title="Your Scores Per Question",
        paper_bgcolor="#1a1a2e", plot_bgcolor="#16213e",
        font=dict(color="#a8b2d8"),
        yaxis=dict(range=[0, 10.5]),
        height=350,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Detailed feedback
    st.markdown("### 📋 Detailed Feedback")
    for i, (q_data, answer, score, feedback) in enumerate(zip(qs, answers, scores, feedback_items)):
        with st.expander(f"Q{i+1}: {q_data['q']} — Score: {score}/10"):
            if answer:
                st.markdown(f"**Your Answer:** {answer}")
                st.info(feedback.get("summary", "No feedback available."))
                if feedback.get("strengths"):
                    st.markdown("**What worked**")
                    for item in feedback["strengths"]:
                        st.markdown(f"- {item}")
                if feedback.get("improvements"):
                    st.markdown("**What to improve**")
                    for item in feedback["improvements"]:
                        st.markdown(f"- {item}")
                if feedback.get("missed_keywords"):
                    st.markdown(f"**Missing concepts:** {', '.join(feedback['missed_keywords'])}")
            else:
                st.warning("Question was skipped.")
            st.success(f"**AI Improved Answer:** {feedback.get('ideal_answer', q_data['sample'])}")
            st.caption(f"💡 **Tip:** {q_data['tips']}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New Interview", use_container_width=True):
            st.session_state.interview_done = False
            st.session_state.interview_active = False
            st.session_state.questions = []
            st.session_state.feedback = []
            st.rerun()
    with col2:
        if st.button("📊 View Progress", use_container_width=True):
            st.session_state.page = "📊 Progress Tracker"
            st.session_state.interview_done = False
            st.rerun()

# ─────────────────────────────────────────────
# PAGE: QUESTION BANK
# ─────────────────────────────────────────────
def page_question_bank():
    st.markdown("<div class='main-header'><h1>📚 Question Bank</h1><p>Browse 50+ curated interview questions with sample answers</p></div>", unsafe_allow_html=True)

    all_cats = list(QUESTION_BANK.keys())
    selected_cat = st.selectbox("Filter by Category", ["All"] + all_cats)

    cats_to_show = all_cats if selected_cat == "All" else [selected_cat]
    search = st.text_input("🔍 Search questions", "")

    for cat in cats_to_show:
        questions = QUESTION_BANK[cat]
        filtered = [q for q in questions if search.lower() in q["q"].lower()] if search else questions

        if not filtered:
            continue

        st.markdown(f"### {cat} ({len(filtered)} questions)")
        for i, q_data in enumerate(filtered):
            with st.expander(f"Q: {q_data['q']}"):
                st.markdown(f"**🔑 Key concepts:** `{'` · `'.join(q_data['keywords'][:5])}`")
                st.markdown("---")
                st.success(f"**✅ Sample Answer:** {q_data['sample']}")
                st.info(f"**💡 Tips:** {q_data['tips']}")


def page_hard_skill_test():
    st.markdown("<div class='main-header'><h1>🧪 Hard Skill Test</h1><p>Take a technical assessment and evaluate your hard skills through performance</p></div>", unsafe_allow_html=True)

    if not st.session_state.logged_in:
        st.warning("Please login first.")
        return

    user = st.session_state.user
    user.setdefault("hard_skills", {skill: 5 for skill in SKILL_AREAS["hard_skills"]})

    if st.session_state.skill_test_done and st.session_state.skill_test_result:
        result = st.session_state.skill_test_result
        st.success(f"Overall hard-skill score: **{result['overall']}/10**")

        metric_cols = st.columns(3)
        for idx, skill in enumerate(SKILL_AREAS["hard_skills"]):
            with metric_cols[idx % 3]:
                st.metric(skill, f"{result['scores'].get(skill, 0)}/10")

        st.markdown("#### Breakdown")
        for skill in SKILL_AREAS["hard_skills"]:
            stats = result["per_skill"].get(skill, {"correct": 0, "total": 0})
            st.markdown(f"- {skill}: {stats['correct']} correct out of {stats['total']}")

        weakest = sorted(result["scores"].items(), key=lambda item: item[1])[:2]
        st.markdown("#### Improvement Focus")
        for skill, score in weakest:
            st.markdown(f"- Improve {skill} next. Current evaluated score: {score}/10")

        if st.button("Retake Test", use_container_width=True):
            st.session_state.skill_test_done = False
            st.session_state.skill_test_result = {}
            st.rerun()
        return

    st.info("This test will score core technical areas and update your hard-skill profile from your answers.")
    with st.form("hard_skill_test_form"):
        responses = []
        for idx, question in enumerate(HARD_SKILL_TEST_QUESTIONS):
            st.markdown(f"**Q{idx+1}. [{question['skill']}] {question['question']}**")
            selected = st.radio(
                f"Choose answer {idx+1}",
                question["options"],
                key=f"hard_skill_test_{idx}",
                label_visibility="collapsed",
            )
            responses.append((question, selected))

        submitted = st.form_submit_button("Submit Test", use_container_width=True)
        if submitted:
            result = evaluate_hard_skill_test(responses)
            user["hard_skills"] = result["scores"]
            st.session_state.user = user
            st.session_state.skill_test_result = result
            st.session_state.skill_test_done = True
            st.success("Your hard-skill profile has been updated from test performance.")
            st.rerun()


def page_debug_coding_test():
    st.markdown("<div class='main-header'><h1>🐞 Debug Coding Test</h1><p>Solve company-style debugging questions and review your company-wise dashboard</p></div>", unsafe_allow_html=True)

    if not st.session_state.logged_in:
        st.warning("Please login first.")
        return

    user = st.session_state.user
    history = user.get("debug_test_history", [])

    company_options = sorted({item["company"] for item in DEBUG_TEST_BANK})
    selected_company = st.selectbox("Select Company Style", company_options)
    question_pool = [item for item in DEBUG_TEST_BANK if item["company"] == selected_company]
    selected_title = st.selectbox("Select Debug Question", [item["title"] for item in question_pool])
    question = next(item for item in question_pool if item["title"] == selected_title)
    selected_language = st.selectbox("Coding Language To Debug", question.get("languages", ["Python"]))

    top1, top2 = st.columns([3, 2])
    with top1:
        st.markdown(f"### {question['title']}")
        st.caption(f"Company style: {question['company']} | Skill focus: {question['skill']}")
        st.write(question["prompt"])
        language_map = {
            "Python": "python",
            "Java": "java",
            "C++": "cpp",
            "JavaScript": "javascript",
            "SQL": "sql",
        }
        st.code(question["buggy_code"], language=language_map.get(selected_language, "python"))

    with top2:
        st.markdown("### Dashboard")
        company_history = [item for item in history if item["company"] == selected_company]
        avg_score = round(sum(item["score"] for item in company_history) / len(company_history), 1) if company_history else 0
        lang_history = [item for item in history if item.get("language") == selected_language]
        st.metric("Attempts", len(company_history))
        st.metric("Avg Score", avg_score)
        st.metric("Language Attempts", len(lang_history))
        st.markdown(f"**Supported languages:** {', '.join(question.get('languages', ['Python']))}")

    with st.form("debug_test_form"):
        fixed_code = st.text_area("Paste your fixed code", height=220, placeholder="Write the corrected code here...")
        explanation = st.text_area("Explain the bug and your fix", height=140, placeholder="Explain what was wrong and how you fixed it...")
        submitted = st.form_submit_button("Evaluate Debug Solution", use_container_width=True)

        if submitted:
            result = evaluate_debug_submission(question, fixed_code, explanation, selected_language)
            attempt = {
                "company": question["company"],
                "title": question["title"],
                "skill": question["skill"],
                "language": selected_language,
                "score": result["score"],
                "feedback": result["feedback"],
                "is_correct": result["is_correct"],
                "solution": result["solution"],
                "date": time.strftime("%Y-%m-%d"),
            }
            history.append(attempt)
            user["debug_test_history"] = history
            st.session_state.user = user
            if result["is_correct"]:
                st.success(f"Correct debug solution. Congrats! Your evaluated score is {result['score']}/10.")
                st.info(result["feedback"])
            else:
                st.error(f"Not fully correct yet. Your evaluated score is {result['score']}/10.")
                st.info(result["feedback"])
                if result["incorrect_points"]:
                    st.markdown("**What is incorrect**")
                    for item in result["incorrect_points"]:
                        st.markdown(f"- You missed or did not clearly apply: `{item}`")
                st.markdown("**Correct solution**")
                st.code(result["solution"], language=language_map.get(selected_language, "python"))

    if history:
        st.markdown("#### Company-wise Performance")
        company_scores = {}
        for item in history:
            company_scores.setdefault(item["company"], []).append(item["score"])
        for company, scores in company_scores.items():
            st.markdown(f"- {company}: {round(sum(scores)/len(scores), 1)}/10 average across {len(scores)} attempt(s)")

        st.markdown("#### Recent Debug Attempts")
        recent = list(reversed(history[-5:]))
        for item in recent:
            with st.expander(f"{item['date']} — {item['company']} — {item['title']} ({item['score']}/10)"):
                st.markdown(f"**Skill:** {item['skill']}")
                st.markdown(f"**Language:** {item.get('language', 'Not specified')}")
                st.write(item["feedback"])
                if not item.get("is_correct") and item.get("solution"):
                    st.code(item["solution"], language=language_map.get(item.get("language", "Python"), "python"))


def page_practice_problems():
    st.markdown("<div class='main-header'><h1>🧩 Practice Problems</h1><p>LeetCode and other technical problem platforms in one place</p></div>", unsafe_allow_html=True)

    user = st.session_state.user if st.session_state.logged_in else {}
    coding_level = user.get("coding_knowledge", "Intermediate")
    roadmap_key = "Intermediate"
    if "Beginner" in coding_level:
        roadmap_key = "Beginner"
    elif "Advanced" in coding_level or "Competitive" in coding_level:
        roadmap_key = "Advanced"

    st.info(
        f"Based on your programming knowledge level of **{coding_level}**, start with the **{roadmap_key}** roadmap."
    )

    st.markdown("#### Recommended Roadmap")
    for item in PROBLEM_ROADMAPS[roadmap_key]:
        st.markdown(f"- {item}")

    st.markdown("#### Major Problem Platforms")
    for platform in PRACTICE_PLATFORMS:
        with st.expander(f"{platform['name']} — {platform['focus']}"):
            st.markdown(f"**Main problem set:** {platform['problemset_url']}")
            st.markdown("**Useful tracks:**")
            for title, url in platform["tracks"]:
                st.markdown(f"- [{title}]({url})")

    st.markdown("#### Suggested Use")
    st.markdown("- Pick one main platform instead of trying everything at once.")
    st.markdown("- Use easy to medium progression before hard problems.")
    st.markdown("- Track patterns you miss, not just scores.")
    st.markdown("- Mix coding problems with CS fundamentals and interview explanation practice.")

# ─────────────────────────────────────────────
# PAGE: PROGRESS TRACKER
# ─────────────────────────────────────────────
def page_progress():
    st.markdown("<div class='main-header'><h1>📊 Progress Tracker</h1><p>Track your improvement over time</p></div>", unsafe_allow_html=True)

    if not st.session_state.logged_in:
        st.warning("Please login first.")
        return

    sessions = st.session_state.sessions

    if not sessions:
        st.info("No sessions yet. Complete a mock interview to see your progress!")

        # Show demo chart
        st.markdown("### 📈 Sample Progress Chart (Demo)")
        demo_scores = [5.2, 6.1, 5.8, 6.5, 7.0, 7.3, 7.8, 8.1]
        fig = px.line(x=list(range(1, len(demo_scores)+1)), y=demo_scores,
                      title="Sample: Score Improvement Over Sessions",
                      labels={"x": "Session", "y": "Avg Score"})
        fig.update_layout(paper_bgcolor="#1a1a2e", plot_bgcolor="#16213e",
                          font=dict(color="#a8b2d8"))
        fig.update_traces(line_color="#e94560", line_width=3)
        st.plotly_chart(fig, use_container_width=True)
        return

    # Line chart - session scores
    session_nums = list(range(1, len(sessions)+1))
    avg_scores = [s["avg"] for s in sessions]

    fig_line = px.line(x=session_nums, y=avg_scores,
                       title="📈 Average Score Per Session",
                       labels={"x": "Session", "y": "Avg Score"},
                       markers=True)
    fig_line.update_layout(paper_bgcolor="#1a1a2e", plot_bgcolor="#16213e",
                            font=dict(color="#a8b2d8"), yaxis=dict(range=[0, 10]))
    fig_line.update_traces(line_color="#e94560", line_width=3, marker_size=8)
    st.plotly_chart(fig_line, use_container_width=True)

    # Skills radar chart
    cat_scores = {
        "HR": [], "Python": [], "DBMS": [], "OS": [],
        "Data Structures": [], "Behavioral": []
    }
    for sess in sessions:
        itype = sess["type"]
        avg = sess["avg"]
        for cat in cat_scores:
            if cat.lower() in itype.lower():
                cat_scores[cat].append(avg)

    radar_vals = []
    for cat in cat_scores:
        vals = cat_scores[cat]
        radar_vals.append(round(sum(vals)/len(vals), 1) if vals else random.uniform(4, 7))

    categories = list(cat_scores.keys())
    fig_radar = go.Figure(go.Scatterpolar(
        r=radar_vals + [radar_vals[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(233,69,96,0.2)',
        line=dict(color='#e94560', width=2),
        marker=dict(size=8, color='#e94560')
    ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor="#16213e",
            radialaxis=dict(visible=True, range=[0, 10], color="#a8b2d8"),
            angularaxis=dict(color="#a8b2d8")
        ),
        paper_bgcolor="#1a1a2e",
        font=dict(color="#a8b2d8"),
        title="🕸️ Skills Radar Chart",
        height=450,
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # Session table
    st.markdown("### 📋 Session History")
    df = pd.DataFrame([{
        "Session": i+1,
        "Date": s["date"],
        "Type": s["type"],
        "Questions": len(s["scores"]),
        "Avg Score": s["avg"],
        "Best": max(s["scores"]),
        "Worst": min(s["scores"]),
    } for i, s in enumerate(sessions)])
    st.dataframe(df, use_container_width=True)

# ─────────────────────────────────────────────
# PAGE: LEADERBOARD
# ─────────────────────────────────────────────
def page_leaderboard():
    st.markdown("<div class='main-header'><h1>🏆 Leaderboard</h1><p>Top performers in Tamil Nadu</p></div>", unsafe_allow_html=True)

    st.markdown("### 🥇 Top 10 Tamil Nadu Students")
    for entry in LEADERBOARD:
        rank = entry["rank"]
        badge = entry["badge"]
        color = "#ffd700" if rank == 1 else "#c0c0c0" if rank == 2 else "#cd7f32" if rank == 3 else "#a8b2d8"
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#16213e,#1a1a2e);border:1px solid #0f3460;
             border-radius:10px;padding:0.8rem 1.2rem;margin-bottom:0.5rem;
             display:flex;align-items:center;'>
            <span style='font-size:1.3rem;margin-right:1rem;'>{badge}</span>
            <span style='color:{color};font-weight:700;width:2rem;'>#{rank}</span>
            <span style='color:#ffffff;font-weight:600;flex:1;'>{entry["name"]}</span>
            <span style='color:#a8b2d8;margin-right:2rem;'>{entry["college"]}</span>
            <span style='color:#e94560;font-weight:700;'>{entry["score"]}/10</span>
            <span style='color:#a8b2d8;margin-left:1rem;font-size:0.85rem;'>{entry["sessions"]} sessions</span>
        </div>
        """, unsafe_allow_html=True)

    # User stats
    if st.session_state.logged_in:
        st.markdown("---")
        st.markdown("### 📊 Your Stats")
        user = st.session_state.user
        sessions = st.session_state.sessions
        all_scores = [s for sess in sessions for s in sess["scores"]]
        avg = round(sum(all_scores)/len(all_scores), 1) if all_scores else 0

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Name", user["name"])
        with c2:
            st.metric("Sessions", len(sessions))
        with c3:
            st.metric("Avg Score", avg)
        with c4:
            st.metric("College", user.get("college", "—"))

        if avg > 0:
            rank_estimate = sum(1 for e in LEADERBOARD if e["score"] > avg) + 1
            st.info(f"Based on your average score of {avg}, your estimated rank is **#{rank_estimate}** in our leaderboard. Keep practicing!")

# ─────────────────────────────────────────────
# PAGE: AI MENTOR
# ─────────────────────────────────────────────
def page_mentor():
    st.markdown("<div class='main-header'><h1>🤖 AI Mentor</h1><p>Get expert guidance and STAR method tips</p></div>", unsafe_allow_html=True)

    if not st.session_state.logged_in:
        st.warning("Please login first.")
        return

    topic = st.selectbox("Select Topic", list(QUESTION_BANK.keys()))
    questions_in_topic = QUESTION_BANK[topic]
    q_labels = [q["q"] for q in questions_in_topic]
    selected_q_label = st.selectbox("Select Question", q_labels)
    q_data = next((q for q in questions_in_topic if q["q"] == selected_q_label), None)

    if q_data:
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### ✅ Sample Answer")
            st.success(q_data["sample"])

            st.markdown("#### 🔑 Key Concepts to Cover")
            for kw in q_data["keywords"]:
                st.markdown(f"• `{kw}`")

        with col2:
            st.markdown("#### 💡 Pro Tips")
            st.info(q_data["tips"])

            if topic == "Behavioral":
                st.markdown("#### ⭐ STAR Method Guidance")
                st.markdown("""
                <div class='card'>
                    <p style='color:#e94560;font-weight:700;'>S — Situation</p>
                    <p style='color:#a8b2d8;'>Set the scene. What was the context? Be specific but brief.</p>
                    <p style='color:#e94560;font-weight:700;'>T — Task</p>
                    <p style='color:#a8b2d8;'>What was your responsibility? What challenge needed solving?</p>
                    <p style='color:#e94560;font-weight:700;'>A — Action</p>
                    <p style='color:#a8b2d8;'>What did YOU specifically do? Use "I", not "we". Be detailed here.</p>
                    <p style='color:#e94560;font-weight:700;'>R — Result</p>
                    <p style='color:#a8b2d8;'>What was the outcome? Quantify where possible (%, time saved, impact).</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("#### 🎯 Practice Tips by Category")
        category_tips = {
            "HR": "Research the company before every HR interview. Know their mission, recent news, and products. Prepare your 'Tell me about yourself' in advance.",
            "Python": "Practice coding without an IDE. Be ready to explain time/space complexity. Review Python-specific idioms and PEP8.",
            "DBMS": "Bring a pen and draw schema diagrams. Practice SQL queries on HackerRank. Know normalization inside-out.",
            "OS": "Understand the OS concepts with diagrams. The Silberschatz textbook is gold. Focus on process scheduling and memory management.",
            "Data Structures": "LeetCode daily. Focus on patterns: sliding window, two pointers, BFS/DFS, DP. Time yourself.",
            "Behavioral": "Prepare 6–8 STAR stories that can adapt to different questions. Record yourself to catch filler words.",
            "TCS": "TCS interviews are structured. Prepare: NQT exam topics, technical MCQs on C/Java/Python, and HR rounds.",
            "Google": "System design is crucial. Study Designing Data-Intensive Applications. Practice on Pramp.com.",
            "Startup": "Show passion and versatility. Have side projects ready to demo. Know the startup's product deeply.",
        }
        st.info(f"**{topic} Strategy:** {category_tips.get(topic, 'Practice consistently and review sample answers.')}")

        st.markdown("### Ask The AI Mentor")
        context_key = f"{topic}::{selected_q_label}"
        if st.session_state.mentor_context_key != context_key:
            st.session_state.mentor_context_key = context_key
            st.session_state.mentor_messages = [
                {
                    "role": "assistant",
                    "content": (
                        f"I am your interview mentor for **{topic}**.\n\n"
                        f"We are focused on **{q_data['q']}**. You can talk to me normally, like ChatGPT. "
                        f"Ask for rewrites, mock interviews, better examples, follow-up questions, or feedback on your draft."
                    ),
                }
            ]
            st.session_state.mentor_error = ""

        if st.session_state.mentor_error:
            st.warning(st.session_state.mentor_error)

        for message in st.session_state.mentor_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        mentor_prompt = st.chat_input("Message your mentor...")
        if mentor_prompt:
            st.session_state.mentor_messages.append({"role": "user", "content": mentor_prompt})

            history_for_model = get_recent_mentor_history(st.session_state.mentor_messages)
            with st.chat_message("assistant"):
                with st.spinner("Thinking like an interview coach..."):
                    result, error_message = get_mentor_response(q_data, mentor_prompt, topic, history_for_model)
                st.markdown(result)

            st.session_state.mentor_messages.append(
                {
                    "role": "assistant",
                    "content": result,
                }
            )
            st.session_state.mentor_error = error_message
            st.rerun()

# ─────────────────────────────────────────────
# PAGE: TOP COMPANIES
# ─────────────────────────────────────────────
def page_companies():
    st.markdown("<div class='main-header'><h1>🏢 Top Companies in India</h1><p>Explore major employers across India with smarter search and filters</p></div>", unsafe_allow_html=True)

    states = ["All"] + sorted({company["state"] for company in COMPANIES})
    company_types = ["All"] + sorted({company["company_type"] for company in COMPANIES})

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        search = st.text_input("🔍 Search by company, city, state, domain, tags, or website", "")
    with c2:
        state_filter = st.selectbox("State", states)
    with c3:
        type_filter = st.selectbox("Company Type", company_types)

    filtered = filter_companies(COMPANIES, search, state_filter, type_filter)

    st.caption(f"Showing {len(filtered)} of {len(COMPANIES)} companies")

    company_tips = {
        "TCS": "NQT test + Technical + HR. Focus on aptitude, C or Java basics, and communication.",
        "Infosys": "InfyTQ style prep, logical reasoning, verbal ability, and coding basics are useful.",
        "Wipro": "Practice data structures, aptitude, and campus-style technical rounds.",
        "Cognizant": "Expect coding + aptitude + HR for GenC style roles.",
        "HCLTech": "Focus on strong fundamentals, communication, and practical technical questions.",
        "Zoho Corporation": "Very coding and debugging heavy. Written rounds can be tough and merit based.",
        "Freshworks": "Coding, design thinking, and product mindset matter.",
        "L&T Technology Services": "Aptitude, engineering basics, and domain fundamentals matter.",
        "Hexaware": "Automation, AI awareness, and practical technical interviews are useful.",
        "Microsoft India": "Strong DSA, coding rounds, and system thinking are expected.",
        "Google India": "Prepare deeply for algorithms, data structures, and problem solving.",
        "Amazon India": "DSA plus leadership-principle style behavioral prep helps a lot.",
        "Flipkart": "Backend fundamentals, scale thinking, and DSA are valuable.",
        "PhonePe": "Payments systems, APIs, and backend fundamentals are important.",
        "Razorpay": "Expect fintech backend scenarios, debugging, and API-focused thinking.",
    }

    for c in filtered:
        with st.expander(f"🏢 {c['name']} — {c['domain']}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"📍 **Location:** {c['location']}")
                st.markdown(f"🏭 **Domain:** {c['domain']}")
            with col2:
                st.markdown(f"🗺 **State:** {c.get('state', '—')}")
                st.markdown(f"🌐 **Website:** {c['website']}")
            with col3:
                st.markdown(f"🧭 **Type:** {c.get('company_type', '—')}")
                st.markdown(f"📅 **Founded:** {c['founded']}")
            if c.get("tags"):
                st.caption(f"Tags: {', '.join(c['tags'])}")

            st.info(f"🎯 **Interview Tip:** {company_tips.get(c['name'], 'Research the company, role, and interview format before applying.')}")

# ─────────────────────────────────────────────
# PAGE: MY PROFILE
# ─────────────────────────────────────────────
def page_profile():
    st.markdown("<div class='main-header'><h1>👤 My Profile</h1><p>Your account details and performance summary</p></div>", unsafe_allow_html=True)

    if not st.session_state.logged_in:
        st.warning("Please login first.")
        return

    user = st.session_state.user
    user.setdefault("target_role", "Software Engineer")
    user.setdefault("learning_style", "Balanced")
    user.setdefault("weekly_hours", 6)
    user.setdefault("improvement_goal", "Crack interviews with confidence")
    user.setdefault("hard_skills", {skill: 5 for skill in SKILL_AREAS["hard_skills"]})
    user.setdefault("soft_skills", {skill: 5 for skill in SKILL_AREAS["soft_skills"]})
    sessions = st.session_state.sessions
    all_scores = [s for sess in sessions for s in sess["scores"]]

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(f"""
        <div class='card'>
            <div style='text-align:center;margin-bottom:1rem;'>
                <div style='width:80px;height:80px;background:linear-gradient(135deg,#e94560,#c23152);
                     border-radius:50%;display:flex;align-items:center;justify-content:center;
                     font-size:2rem;margin:0 auto;'>
                    👤
                </div>
            </div>
            <h3 style='color:#e94560;text-align:center;margin:0;'>{user.get("name","—")}</h3>
            <p style='color:#a8b2d8;text-align:center;margin:0.3rem 0;'>{user.get("college","—")}</p>
            <hr style='border-color:#0f3460;'>
            <p style='color:#a8b2d8;'><b style='color:#e94560;'>📧</b> {user.get("email","—")}</p>
            <p style='color:#a8b2d8;'><b style='color:#e94560;'>📞</b> {user.get("phone","—")}</p>
            <p style='color:#a8b2d8;'><b style='color:#e94560;'>🎓</b> {user.get("branch","—")} • Year {user.get("year","—")}</p>
            <p style='color:#a8b2d8;'><b style='color:#e94560;'>📊</b> CGPA: {user.get("cgpa","—")}</p>
            <p style='color:#a8b2d8;'><b style='color:#e94560;'>Skill</b> Programming Knowledge: {user.get("coding_knowledge","Not specified")}</p>
            <p style='color:#a8b2d8;'><b style='color:#e94560;'>💡</b> {", ".join(user.get("interests",[])) or "Not specified"}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("#### 📊 Session Statistics")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total Sessions", len(sessions))
        with c2:
            avg = round(sum(all_scores)/len(all_scores), 1) if all_scores else 0
            st.metric("Avg Score", avg)
        with c3:
            best = round(max(all_scores), 1) if all_scores else 0
            st.metric("Best Score", best)

        if sessions:
            # Score distribution
            fig = px.histogram(x=all_scores, nbins=10, title="Score Distribution",
                               labels={"x": "Score", "y": "Count"},
                               color_discrete_sequence=["#e94560"])
            fig.update_layout(paper_bgcolor="#1a1a2e", plot_bgcolor="#16213e",
                              font=dict(color="#a8b2d8"))
            st.plotly_chart(fig, use_container_width=True)

            # Recent sessions
            st.markdown("#### 📋 Recent Sessions")
            recent = sessions[-5:][::-1]
            for s in recent:
                col_a, col_b, col_c = st.columns([2, 2, 1])
                with col_a:
                    st.markdown(f"📅 {s['date']} — {s['type']}")
                with col_b:
                    st.progress(s["avg"]/10)
                with col_c:
                    st.markdown(f"**{s['avg']}/10**")
        else:
            st.info("Complete mock interviews to see your stats here!")

    st.markdown("---")
    st.markdown("#### Skill Assessment")
    st.caption("Tell us about your hard skills, soft skills, and goals so the app can recommend how to improve.")

    with st.form("skill_assessment_form"):
        top1, top2, top3 = st.columns(3)
        role_options = [
            "Software Engineer",
            "Backend Developer",
            "Frontend Developer",
            "Full Stack Developer",
            "Data Analyst",
            "Data Scientist",
            "AI/ML Engineer",
        ]
        learning_options = ["Balanced", "Hands-on", "Theory First", "Fast-paced", "Slow and Deep"]

        with top1:
            target_role = st.selectbox(
                "Target Role",
                role_options,
                index=role_options.index(user.get("target_role", "Software Engineer"))
            )
        with top2:
            learning_style = st.selectbox(
                "Learning Style",
                learning_options,
                index=learning_options.index(user.get("learning_style", "Balanced"))
            )
        with top3:
            weekly_hours = st.slider("Hours Per Week", 1, 25, int(user.get("weekly_hours", 6)))

        improvement_goal = st.text_input(
            "Main Improvement Goal",
            value=user.get("improvement_goal", "Crack interviews with confidence")
        )

        st.markdown("##### Hard Skills")
        hard_cols = st.columns(2)
        hard_inputs = {}
        for idx, skill in enumerate(SKILL_AREAS["hard_skills"]):
            with hard_cols[idx % 2]:
                hard_inputs[skill] = st.slider(
                    skill, 1, 10, int(user.get("hard_skills", {}).get(skill, 5)), key=f"hard_{skill}"
                )

        st.markdown("##### Soft Skills")
        soft_cols = st.columns(2)
        soft_inputs = {}
        for idx, skill in enumerate(SKILL_AREAS["soft_skills"]):
            with soft_cols[idx % 2]:
                soft_inputs[skill] = st.slider(
                    skill, 1, 10, int(user.get("soft_skills", {}).get(skill, 5)), key=f"soft_{skill}"
                )

        save_assessment = st.form_submit_button("Save Assessment", use_container_width=True)

        if save_assessment:
            user["target_role"] = target_role
            user["learning_style"] = learning_style
            user["weekly_hours"] = weekly_hours
            user["improvement_goal"] = improvement_goal
            user["hard_skills"] = hard_inputs
            user["soft_skills"] = soft_inputs
            st.session_state.user = user
            st.success("Assessment updated. Your personalized guidance is ready below.")
            st.rerun()

    growth = build_growth_recommendations(st.session_state.user)

    st.markdown("#### Personalized Guidance")
    g1, g2 = st.columns(2)
    with g1:
        st.markdown(
            f"<div class='metric-card'><h2>{growth['hard_avg']}/10</h2><p>Hard Skills Average</p></div>",
            unsafe_allow_html=True,
        )
    with g2:
        st.markdown(
            f"<div class='metric-card'><h2>{growth['soft_avg']}/10</h2><p>Soft Skills Average</p></div>",
            unsafe_allow_html=True,
        )

    st.info(growth["summary"])

    st.markdown("##### What You Already Do Well")
    for item in growth["strengths"]:
        st.markdown(f"- {item}")

    st.markdown("##### Recommendations")
    for item in growth["recommendations"]:
        st.markdown(f"- {item}")

    st.markdown("##### Weekly Betterment Plan")
    for item in growth["weekly_plan"]:
        st.markdown(f"- {item}")

# ─────────────────────────────────────────────
# PAGE: CONTACT US
# ─────────────────────────────────────────────
def page_contact():
    st.markdown("<div class='main-header'><h1>📞 Contact Us</h1><p>Reach out to our team in Chennai, Tamil Nadu</p></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class='card'>
            <h3 style='color:#e94560;'>🏢 AI Interview Coach HQ</h3>
            <p style='color:#a8b2d8;'>📍 <b>Address:</b><br>
            Level 5, Tower A, Tidel Park,<br>
            Rajiv Gandhi Salai (OMR),<br>
            Taramani, Chennai – 600 113,<br>
            Tamil Nadu, India</p>
            <hr style='border-color:#0f3460;'>
            <p style='color:#a8b2d8;'>📞 <b>Phone:</b> +91-44-6677-8899</p>
            <p style='color:#a8b2d8;'>📱 <b>WhatsApp:</b> +91-98400-12345</p>
            <p style='color:#a8b2d8;'>📧 <b>Email:</b> support@aiinterviewcoach.in</p>
            <p style='color:#a8b2d8;'>🌐 <b>Website:</b> www.aiinterviewcoach.in</p>
            <hr style='border-color:#0f3460;'>
            <p style='color:#a8b2d8;'>🕐 <b>Working Hours:</b><br>
            Mon–Fri: 9:00 AM – 6:00 PM IST<br>
            Sat: 10:00 AM – 2:00 PM IST<br>
            Sun: Closed</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 📍 Our Location")
        location_df = pd.DataFrame({"lat": [13.0105], "lon": [80.2441]})
        st.map(location_df, zoom=13)

    with col2:
        st.markdown("#### 💬 Send Us a Message")
        with st.form("contact_form"):
            fname = st.text_input("Your Name *")
            femail = st.text_input("Your Email *")
            fphone = st.text_input("Phone (optional)")
            fsubject = st.selectbox("Subject", [
                "General Inquiry", "Technical Support", "Feedback",
                "Partnership", "Report a Bug", "Other"
            ])
            fmessage = st.text_area("Message *", height=160,
                                    placeholder="Tell us how we can help...")
            fsend = st.form_submit_button("📨 Send Message", use_container_width=True)

            if fsend:
                if not fname or not femail or not fmessage:
                    st.error("Please fill in all required fields.")
                else:
                    st.success(f"✅ Thank you, {fname}! Your message has been received. We'll respond to {femail} within 24 hours.")
                    st.balloons()

        st.markdown("""
        <div class='card' style='margin-top:1rem;'>
            <h4 style='color:#e94560;margin-top:0;'>🔗 Connect With Us</h4>
            <p style='color:#a8b2d8;'>🔵 LinkedIn: /company/ai-interview-coach-tn</p>
            <p style='color:#a8b2d8;'>🐦 Twitter/X: @AICoachTN</p>
            <p style='color:#a8b2d8;'>📸 Instagram: @ai.interview.coach.tn</p>
            <p style='color:#a8b2d8;'>▶️ YouTube: AI Interview Coach TN</p>
            <p style='color:#a8b2d8;'>💬 Telegram: t.me/AIInterviewCoachTN</p>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────
page = st.session_state.page

if page == "🏠 Home":
    page_home()
elif page == "📝 Mock Interview":
    page_interview()
elif page == "🧪 Hard Skill Test":
    page_hard_skill_test()
elif page == "🐞 Debug Coding Test":
    page_debug_coding_test()
elif page == "📚 Question Bank":
    page_question_bank()
elif page == "🧩 Practice Problems":
    page_practice_problems()
elif page == "📊 Progress Tracker":
    page_progress()
elif page == "🏆 Leaderboard":
    page_leaderboard()
elif page == "🤖 AI Mentor":
    page_mentor()
elif page == "🏢 Top Companies":
    page_companies()
elif page == "👤 My Profile":
    page_profile()
elif page == "📞 Contact Us":
    page_contact()
else:
    page_home()
