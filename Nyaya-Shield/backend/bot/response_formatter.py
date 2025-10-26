"""
User-Friendly Response Formatter
=================================
Formats legal answers in a detailed, easy-to-understand way
"""

import re
from typing import Dict, List


def format_user_friendly_response(query: str, answer: str, category: str = None) -> str:
    """
    Format legal response in a user-friendly, detailed manner
    
    Args:
        query: User's question
        answer: Raw answer from dataset
        category: Legal category (ipc, crpc, consumer, etc.)
    
    Returns:
        Formatted, detailed, user-friendly response
    """
    
    category = (category or 'general').lower()
    query_lower = query.lower()
    
    # Build response parts
    parts = []
    
    # 1. Extract key information from answer
    sections = extract_sections(answer)
    acts = extract_acts(answer)
    
    # 2. Start with clear header based on category
    header = get_category_header(query_lower, category)
    if header:
        parts.append(header)
        parts.append("")
    
    # 3. Main answer content - format nicely
    formatted_answer = format_answer_text(answer)
    parts.append("### 📖 Here's what you need to know:\n")
    parts.append(formatted_answer)
    parts.append("")
    
    # 4. Add section references if found
    if sections:
        parts.append("### 📋 Relevant Legal Sections:\n")
        for section in sections[:3]:  # Top 3 sections
            parts.append(f"• **{section}**")
        parts.append("")
    
    # 5. Add practical steps based on query type
    practical_steps = get_practical_steps(query_lower, category)
    if practical_steps:
        parts.append("### 🎯 Practical Steps:\n")
        for i, step in enumerate(practical_steps, 1):
            parts.append(f"{i}. {step}")
        parts.append("")
    
    # 6. Add important notes based on category
    notes = get_important_notes(query_lower, category)
    if notes:
        parts.append("### ⚠️ Important Points:\n")
        for note in notes:
            parts.append(f"• {note}")
        parts.append("")
    
    # 7. Add helpful resources
    resources = get_helpful_resources(category)
    if resources:
        parts.append("### 🔗 Helpful Resources:\n")
        for resource in resources:
            parts.append(f"• {resource}")
        parts.append("")
    
    return "\n".join(parts)


def get_category_header(query: str, category: str) -> str:
    """Get a friendly header based on category and query"""
    
    if 'punishment' in query or 'penalty' in query:
        return "# ⚖️ Punishment & Penalties"
    elif 'procedure' in query or 'process' in query or 'how to' in query:
        return "# 📝 Legal Procedure"
    elif 'rights' in query:
        return "# 🛡️ Your Legal Rights"
    elif 'file' in query or 'complaint' in query:
        return "# 📋 Filing Process"
    elif category == 'ipc':
        return "# 📜 Indian Penal Code (IPC)"
    elif category == 'crpc':
        return "# ⚖️ Criminal Procedure Code (CrPC)"
    elif category == 'consumer':
        return "# 🛒 Consumer Protection"
    elif category == 'family':
        return "# 👨‍👩‍👧 Family Law"
    elif category == 'property':
        return "# 🏠 Property Law"
    elif category in ['it_act', 'cyber']:
        return "# 💻 Cyber & IT Law"
    
    return "# ⚖️ Legal Information"


def extract_sections(text: str) -> List[str]:
    """Extract section references from text"""
    sections = []
    
    # Pattern: Section 123, Section 456A, etc.
    section_pattern = r'[Ss]ection\s+(\d+[A-Za-z]?)'
    matches = re.findall(section_pattern, text)
    for match in matches:
        sections.append(f"Section {match}")
    
    # Pattern: IPC 123, CrPC 456, etc.
    code_pattern = r'(IPC|CrPC|IT Act)\s+(\d+[A-Za-z]?)'
    matches = re.findall(code_pattern, text, re.IGNORECASE)
    for code, num in matches:
        sections.append(f"{code.upper()} Section {num}")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_sections = []
    for section in sections:
        if section not in seen:
            seen.add(section)
            unique_sections.append(section)
    
    return unique_sections


def extract_acts(text: str) -> List[str]:
    """Extract act references from text"""
    acts = []
    
    act_patterns = [
        r'Indian Penal Code',
        r'Criminal Procedure Code',
        r'Consumer Protection Act',
        r'Information Technology Act',
        r'Motor Vehicles Act',
        r'Evidence Act',
        r'Constitution of India',
    ]
    
    for pattern in act_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            acts.append(pattern)
    
    return acts


def format_answer_text(answer: str) -> str:
    """Format answer text to be more readable"""
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', answer)
    
    # Format each sentence
    formatted = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        # Add bullet points for multiple sentences
        if len(sentences) > 3:
            formatted.append(f"• {sentence}")
        else:
            formatted.append(sentence)
    
    return "\n".join(formatted)


def get_practical_steps(query: str, category: str) -> List[str]:
    """Get practical next steps based on query and category"""
    
    steps = []
    
    # Query-specific steps
    if 'file' in query or 'complaint' in query:
        steps.extend([
            "**Gather all relevant documents** (evidence, receipts, communications)",
            "**Write a detailed complaint** with facts, dates, and witnesses",
            "**Submit to the appropriate authority** (police station, consumer forum, court)",
            "**Keep copies** of all submitted documents and receipts"
        ])
    
    elif 'bail' in query:
        steps.extend([
            "**Contact a lawyer immediately** - bail applications require legal expertise",
            "**Prepare bail application** with surety details and documents",
            "**File in appropriate court** (Magistrate/Sessions/High Court based on offense)",
            "**Attend hearings** and follow court directions"
        ])
    
    elif 'fir' in query:
        steps.extend([
            "**Visit the nearest police station** or file online FIR (if available)",
            "**Provide complete details** - what happened, when, where, who",
            "**Get FIR copy** with FIR number and date",
            "**Follow up** on investigation status regularly"
        ])
    
    elif 'divorce' in query:
        steps.extend([
            "**Consult a family lawyer** to understand grounds and process",
            "**Try mediation** if possible (courts encourage this)",
            "**Prepare documents** (marriage certificate, evidence of grounds)",
            "**File petition** in Family Court with lawyer's help"
        ])
    
    elif category == 'consumer':
        steps.extend([
            "**Send legal notice** to seller/service provider (mandatory first step)",
            "**Wait 15-30 days** for response",
            "**File complaint** in District/State/National Consumer Forum",
            "**Attend hearings** with evidence and documents"
        ])
    
    elif category == 'property':
        steps.extend([
            "**Verify property documents** (title deed, encumbrance certificate)",
            "**Check for disputes** at Sub-Registrar office",
            "**Get property valued** by approved valuer",
            "**Complete registration** with proper stamp duty"
        ])
    
    elif category in ['it_act', 'cyber']:
        steps.extend([
            "**Preserve digital evidence** (screenshots, emails, messages)",
            "**Don't delete** anything - even threatening messages are evidence",
            "**Report to Cyber Cell** or file complaint on cybercrime.gov.in",
            "**Block/report** on respective platforms"
        ])
    
    # Default steps for IPC/CrPC
    if not steps and category in ['ipc', 'crpc']:
        steps.extend([
            "**Understand the offense** and applicable sections",
            "**Consult a criminal lawyer** for case-specific advice",
            "**Preserve all evidence** related to the incident",
            "**Follow legal procedures** strictly"
        ])
    
    return steps


def get_important_notes(query: str, category: str) -> List[str]:
    """Get important warnings/notes based on context"""
    
    notes = []
    
    # Bail-related notes
    if 'bail' in query:
        notes.extend([
            "**Time is critical** - apply for bail as soon as possible",
            "Bail is a **right, not a privilege** for most offenses",
            "**Anticipatory bail** must be filed before arrest"
        ])
    
    # FIR-related notes
    if 'fir' in query:
        notes.extend([
            "**Police cannot refuse** to file FIR for cognizable offenses",
            "**Zero FIR** can be filed at any police station",
            "You have the **right to free copy** of FIR"
        ])
    
    # Consumer cases
    if category == 'consumer':
        notes.extend([
            "**Time limit: 2 years** from date of cause of action",
            "**No court fee** for claims up to ₹5 lakhs",
            "Keep all **bills and warranty cards**"
        ])
    
    # Property cases
    if category == 'property':
        notes.extend([
            "Always **verify ownership** before any transaction",
            "**Registration is mandatory** for validity",
            "Check for **encumbrances and disputes**"
        ])
    
    # Cyber crimes
    if category in ['it_act', 'cyber']:
        notes.extend([
            "**Act immediately** - digital evidence can be deleted",
            "**Don't pay** ransom or money to blackmailers",
            "**Report within 24-48 hours** for best results"
        ])
    
    # General warning for serious crimes
    serious_crimes = ['murder', 'rape', 'kidnapping', 'terrorism']
    if any(crime in query for crime in serious_crimes):
        notes.extend([
            "This is a **serious offense** - seek immediate legal help",
            "**Legal representation is crucial** for such cases",
            "**Do not delay** in taking action"
        ])
    
    return notes


def get_helpful_resources(category: str) -> List[str]:
    """Get helpful resources based on category"""
    
    resources = []
    
    if category == 'ipc':
        resources.extend([
            "**Police helpline**: 100 or 112 (emergency)",
            "**Legal aid**: District Legal Services Authority (free for eligible)",
            "**Online FIR**: Your state police website"
        ])
    
    elif category == 'crpc':
        resources.extend([
            "**Court website**: For case status and hearing dates",
            "**Legal aid**: Contact DLSA for free legal assistance",
            "**Lawyer referral**: State Bar Council websites"
        ])
    
    elif category == 'consumer':
        resources.extend([
            "**National Consumer Helpline**: 1800-11-4000",
            "**Online complaint**: consumerhelpline.gov.in",
            "**Consumer forum locator**: confonet.nic.in"
        ])
    
    elif category == 'family':
        resources.extend([
            "**Family Court**: Locate your nearest family court",
            "**Mediation centers**: Free mediation services available",
            "**Women helpline**: 181 (for women in distress)"
        ])
    
    elif category == 'property':
        resources.extend([
            "**Land records**: Check online at your state's Bhoomi/land records portal",
            "**Sub-Registrar**: For registration and document verification",
            "**Encumbrance certificate**: Available at Sub-Registrar office"
        ])
    
    elif category in ['it_act', 'cyber']:
        resources.extend([
            "**Cyber crime portal**: cybercrime.gov.in",
            "**Cyber helpline**: 1930",
            "**Report financial fraud**: report.cybercrime.gov.in"
        ])
    
    return resources


# Test function
if __name__ == "__main__":
    # Test the formatter
    sample_query = "What is the punishment for theft under IPC?"
    sample_answer = "Under Section 378 to 382 of the Indian Penal Code, theft is punishable with imprisonment up to 3 years or fine or both. If the theft is committed in a dwelling house, the punishment can extend to 7 years."
    
    formatted = format_user_friendly_response(sample_query, sample_answer, 'ipc')
    print(formatted)
