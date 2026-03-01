import random
import pandas as pd
from datetime import datetime, timedelta

random.seed(42)

# ---------- Config ----------
N = 1000
regions = ["TN", "KA", "KL", "AP", "TS", "MH", "DL"]
platforms = ["twitter", "instagram", "youtube", "reviews", "support"]
aspects = ["delivery", "price", "quality", "service", "packaging", "app", "refund"]
languages = ["mix", "ta", "en"]

# Sentiment distribution (approx)
sentiment_pool = (["negative"] * 450) + (["neutral"] * 250) + (["positive"] * 300)
random.shuffle(sentiment_pool)

# Language distribution (approx)
language_pool = (["mix"] * 450) + (["ta"] * 300) + (["en"] * 250)
random.shuffle(language_pool)

# ---------- Word banks ----------
pos_words = ["super", "semma", "mass", "worth", "vera level", "good", "nice", "excellent"]
neg_words = ["worst", "waste", "mokka", "kadupu", "bad", "cheap", "poor", "hate"]
neu_words = ["ok", "normal", "average", "received", "will check", "not sure", "fine"]

issues = ["screen issue", "battery drain", "camera blur", "sound problem", "overheating", "damaged item"]
bad_events = ["broke in 1 day", "stopped working", "came damaged", "missing parts", "late delivery"]
wait_times = ["1 hour", "2 hours", "1 day", "3 days", "no response for 24 hours"]

# ---------- Templates ----------
templates = {
    "delivery": {
        "positive": [
            "Fast delivery, {days} days la vandhuduchu ✅",
            "Delivery super! on-time arrived.",
            "Courier smooth-a deliver pannanga."
        ],
        "negative": [
            "Delivery romba late, {days} days delay 😡",
            "Courier rude, package damage aayiduchu.",
            "Delivery worst. Tracking update illa."
        ],
        "neutral": [
            "Product received today, open pannala.",
            "Delivery ok, but pakalam.",
            "Arrived. Will test and update."
        ],
    },
    "quality": {
        "positive": [
            "Quality {pos}! build strong 💯",
            "Product {pos}, satisfied.",
            "Material good, value for money."
        ],
        "negative": [
            "Quality {neg}. {issue} iruku.",
            "{days} days la itself {bad_event}.",
            "Cheap feel. Not recommended."
        ],
        "neutral": [
            "Quality ok. Normal usage ku podhum.",
            "Looks fine. Long-term paakanum.",
            "First impression average."
        ],
    },
    "price": {
        "positive": [
            "Offer la super deal, {pos} price.",
            "Price ok for this quality.",
            "Worth for money ✅"
        ],
        "negative": [
            "Price romba high, not worth.",
            "Same product elsewhere cheaper.",
            "Costly and quality poor."
        ],
        "neutral": [
            "Price average.",
            "Price ok, but features compare pannitu paakanum.",
            "Not sure if worth yet."
        ],
    },
    "service": {
        "positive": [
            "Support team helpful, issue solve pannitanga.",
            "Customer service {pos}. Quick response.",
            "Replacement fast-a arrange pannanga."
        ],
        "negative": [
            "Support reply pannala, {wait_time} wait 😤",
            "Service worst, nobody answered.",
            "Complaint raise panniten, no update."
        ],
        "neutral": [
            "Support ticket raised, waiting.",
            "Customer care number busy.",
            "Will contact support later."
        ],
    },
    "packaging": {
        "positive": [
            "Packing super, safe-a vandhuduchu.",
            "Packaging neat, no damage.",
            "Well packed ✅"
        ],
        "negative": [
            "Packing poor, box torn.",
            "Packaging damage, product scratch.",
            "No bubble wrap, worst packing."
        ],
        "neutral": [
            "Packaging ok.",
            "Box normal-a irundhuchu.",
            "No comments on packaging."
        ],
    },
    "app": {
        "positive": [
            "App UI smooth, easy to use.",
            "App performance {pos}.",
            "Login and checkout easy ✅"
        ],
        "negative": [
            "App crash aagudhu, {issue}.",
            "Bug romba, worst experience.",
            "Payment failure repeatedly."
        ],
        "neutral": [
            "App ok, sometimes slow.",
            "Installed. Will try later.",
            "UI average."
        ],
    },
    "refund": {
        "positive": [
            "Refund quick-a process aayiduchu ✅",
            "Return/refund smooth experience.",
            "Refund came within {days} days."
        ],
        "negative": [
            "Refund romba slow, {wait_time} aachu.",
            "Return approve pannala.",
            "Refund stuck, no update."
        ],
        "neutral": [
            "Return initiated, waiting.",
            "Refund status pending.",
            "Requested refund today."
        ],
    },
}

sarcasm_templates = [
    "Wow amazing… {bad_event} 🙃",
    "Great service 👏 {wait_time} wait pannanum",
    "Super quality… {days} days la {bad_event} 😏"
]

def make_text(sentiment, aspect, lang):
    days = random.randint(1, 10)
    pos = random.choice(pos_words)
    neg = random.choice(neg_words)
    issue = random.choice(issues)
    bad_event = random.choice(bad_events)
    wait_time = random.choice(wait_times)

    # Base template
    t = random.choice(templates[aspect][sentiment]).format(
        days=days, pos=pos, neg=neg, issue=issue, bad_event=bad_event, wait_time=wait_time
    )

    # Language flavor (simple)
    if lang == "en":
        # convert lightly to English-ish
        t = t.replace("romba", "very").replace("la", "in").replace("vandhuduchu", "arrived").replace("pannanga", "did")
        t = t.replace("mokka", "bad").replace("waste", "waste").replace("kadupu", "annoying")
    elif lang == "ta":
        # add some Tamil-ish words (still romanized for ease)
        t = "Idhu " + t.replace("super", "nalla").replace("worst", "romba mosam")
    else:
        # mix: keep as is
        pass

    return t

# Decide sarcasm rows (about 10%)
sarcasm_indices = set(random.sample(range(N), k=100))

# Generate date range (last 90 days)
today = datetime.today()
start_date = today - timedelta(days=90)

rows = []
for i in range(N):
    sentiment = sentiment_pool[i]
    lang = language_pool[i]
    aspect = random.choice(aspects)
    region = random.choice(regions)
    platform = random.choice(platforms)
    d = start_date + timedelta(days=random.randint(0, 90))
    sarcasm = 1 if i in sarcasm_indices else 0

    if sarcasm == 1:
        # sarcasm is usually negative, but can be forced
        text = random.choice(sarcasm_templates).format(
            bad_event=random.choice(bad_events),
            wait_time=random.choice(wait_times),
            days=random.randint(1, 10)
        )
        sentiment = "negative"  # make sarcasm negative for realism
    else:
        text = make_text(sentiment, aspect, lang)

    rows.append({
        "id": i + 1,
        "text": text,
        "language": lang,
        "platform": platform,
        "region": region,
        "date": d.strftime("%Y-%m-%d"),
        "aspect": aspect,
        "sentiment": sentiment,
        "sarcasm": sarcasm
    })

df = pd.DataFrame(rows)
df.to_csv("brand_sentiment_1000.csv", index=False, encoding="utf-8-sig")

print("✅ Saved: brand_sentiment_1000.csv")
print(df.head(10))