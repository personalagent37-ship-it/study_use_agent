"""Universal Academic Subjects & Authoritative References Database."""

UNIVERSAL_SUBJECTS = {
    "AUTO": {
        "code": "AUTO",
        "name": "General & Interdisciplinary Studies",
        "icon": "🌐",
        "primary_book": "Authoritative Academic & University References",
        "standard_textbooks": [
            "Standard University Academic Reference Textbooks",
            "Authoritative Research Literature & IEEE/ACM Publications"
        ]
    },
    "CS_AI": {
        "code": "CS_AI",
        "name": "Computer Science & Artificial Intelligence",
        "icon": "💻",
        "primary_book": "Stuart Russell, Peter Norvig & Gary Bradski",
        "standard_textbooks": [
            "Artificial Intelligence: A Modern Approach by Stuart Russell & Peter Norvig (Pearson)",
            "Learning OpenCV: Computer Vision with OpenCV by Gary Bradski & Adrian Kaehler (O'Reilly)",
            "Introduction to Algorithms by Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, Clifford Stein (MIT Press)",
            "Computer Networks / Operating Systems by Andrew S. Tanenbaum (Pearson)",
            "Programming in ANSI C by E. Balagurusamy (McGraw Hill)"
        ]
    },
    "MATHS": {
        "code": "MATHS",
        "name": "Mathematics & Applied Calculus",
        "icon": "📐",
        "primary_book": "B.S. Grewal & Erwin Kreyszig",
        "standard_textbooks": [
            "Higher Engineering Mathematics by B.S. Grewal (Khanna Publishers)",
            "Advanced Engineering Mathematics by Erwin Kreyszig (Wiley)",
            "Linear Algebra and Its Applications by Gilbert Strang (Cengage Learning)"
        ]
    },
    "PHYSICS": {
        "code": "PHYSICS",
        "name": "Engineering & Applied Physics",
        "icon": "⚛️",
        "primary_book": "David Halliday & Robert Resnick",
        "standard_textbooks": [
            "Fundamentals of Physics by David Halliday, Robert Resnick & Jearl Walker (Wiley)",
            "A Textbook of Engineering Physics by M.N. Avadhanulu & P.G. Kshirsagar (S. Chand)"
        ]
    },
    "ELECTRICAL": {
        "code": "ELECTRICAL",
        "name": "Electrical & Electronics Engineering",
        "icon": "⚡",
        "primary_book": "Boylestad, Nashelsky & Theraja",
        "standard_textbooks": [
            "Electronic Devices and Circuit Theory by Robert L. Boylestad & Louis Nashelsky (Pearson)",
            "A Textbook of Electrical Technology by B.L. Theraja & A.K. Theraja (S. Chand)",
            "Engineering Circuit Analysis by William H. Hayt & Jack E. Kemmerly (McGraw Hill)"
        ]
    },
    "MECHANICAL": {
        "code": "MECHANICAL",
        "name": "Mechanical & Civil Engineering",
        "icon": "⚙️",
        "primary_book": "Beer & Johnston / N.D. Bhatt",
        "standard_textbooks": [
            "Engineering Drawing by N.D. Bhatt (Charotar Publishing House)",
            "Vector Mechanics for Engineers by Ferdinand P. Beer & E. Russell Johnston (McGraw Hill)",
            "Engineering Thermodynamics by R.K. Rajput (Laxmi Publications)"
        ]
    }
}

# Alias for backwards compatibility
HYDERABAD_1ST_YEAR_AIML_SUBJECTS = UNIVERSAL_SUBJECTS

def detect_subject_from_query(query: str) -> tuple[str, dict]:
    """Smart classification across academic disciplines."""
    q = query.lower()

    # 1. Computer Science, AI, Programming, Computer Vision
    cs_keywords = [
        "opencv", "computer vision", "machine learning", "deep learning", "neural",
        "artificial intelligence", "python", "pointer", "array", "recursion",
        "c lang", "c++", "data structure", "algorithm", "dsa", "database", "sql",
        "operating system", "react", "cloud", "docker", "llm", "rag", "transformer model",
        "compiler", "graph traversal", "binary tree", "sorting", "api", "git", "web development"
    ]
    if any(kw in q for kw in cs_keywords):
        return "CS_AI", UNIVERSAL_SUBJECTS["CS_AI"]

    # 2. Mathematics, Calculus, Matrices
    math_keywords = [
        "matrix", "matrices", "eigen", "calculus", "differential equation", "derivative",
        "integral", "taylor series", "maclaurin", "fourier", "laplace", "probability",
        "statistics", "linear algebra", "vector calculus", "jacobian", "cauchy", "rolle"
    ]
    if any(kw in q for kw in math_keywords):
        return "MATHS", UNIVERSAL_SUBJECTS["MATHS"]

    # 3. Physics & Optics
    physics_keywords = [
        "physics", "optics", "laser", "quantum", "schrodinger", "de broglie",
        "dielectric", "magnetic materials", "diffraction", "interference", "thin film",
        "newton ring", "polarization", "he-ne", "ruby laser", "wave optics"
    ]
    if any(kw in q for kw in physics_keywords):
        return "PHYSICS", UNIVERSAL_SUBJECTS["PHYSICS"]

    # 4. Electrical & Electronics
    elec_keywords = [
        "electrical", "electronic", "diode", "transistor", "rectifier", "bjt",
        "fet", "mosfet", "op-amp", "thevenin", "norton", "kvl", "kcl", "ohm's law",
        "ohms law", "transformer", "dc circuit", "ac circuit", "impedance", "resonance", "rlc"
    ]
    if any(kw in q for kw in elec_keywords):
        return "ELECTRICAL", UNIVERSAL_SUBJECTS["ELECTRICAL"]

    # 5. Mechanical & Civil
    mech_keywords = [
        "drawing", "projection", "isometric", "thermodynamics", "stress", "strain",
        "fluid", "bernoulli", "carnot", "engine", "solid mechanics", "orthographic", "cad"
    ]
    if any(kw in q for kw in mech_keywords):
        return "MECHANICAL", UNIVERSAL_SUBJECTS["MECHANICAL"]

    # Fallback to General & Interdisciplinary
    return "AUTO", UNIVERSAL_SUBJECTS["AUTO"]

def get_subject_by_query(query: str) -> tuple[str, dict] | None:
    return detect_subject_from_query(query)

