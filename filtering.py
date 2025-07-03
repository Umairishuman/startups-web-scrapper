import json
from keywords import KEYWORDS

# Normalize and prepare keyword sets
full_keywords = set([kw.lower() for kw in KEYWORDS])
keyword_words = set()
for keyword in KEYWORDS:
    keyword_words.update(keyword.lower().split())

def get_matched_keywords(text):
    matched = set()

    text_lower = text.lower()

    # Check full phrase matches
    for keyword in full_keywords:
        if keyword in text_lower:
            matched.add(keyword)

    # Check individual word matches
    for word in text_lower.split():
        if word in keyword_words:
            matched.add(word)

    return list(matched)

# Load your data
with open('email_scraped.json', 'r') as f:
    data = json.load(f)

# Filter items
filtered = []
for item in data:
    description = item.get('description', '')
    paragraphs = item.get('allParagraphs', [])

    all_texts = [description] + paragraphs

    matched_keywords = set()
    for text in all_texts:
        matched_keywords.update(get_matched_keywords(text))

    if matched_keywords:
        item['matched_keywords'] = list(matched_keywords)
        filtered.append(item)

# Save filtered results
with open('filtered.json', 'w') as f:
    json.dump(filtered, f, indent=2)

print(f"Filtered {len(filtered)} matching items saved to 'filtered.json'")
