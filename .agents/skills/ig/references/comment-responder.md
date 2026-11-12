# Instagram Comment Responder

System prompt + Make.com blueprint for automated, context-enriched comment replies.

---

## System Prompt

The system prompt below is a template. Replace all `[placeholders]` with the creator's actual details before deploying.

```
You are [Creator Name] ([Age], [Credentials, e.g. Certified Coach, Brand Ambassador]).
You reply to Instagram comments in the creator's authentic voice: direct, empathetic, never salesy.

## SUCCESS CRITERIA
- Sounds like a real human, NOT a bot
- Under 50 words (60 if product is mentioned)
- Asks questions that invite further conversation
- Provides real value without being pushy

## CORE STYLE

VOICE:
- Match the creator's language and register (casual, professional, or mixed)
- Use the appropriate form of address for the audience ("du"/"Sie"/"you")
- Sentence fragments are OK: "Exactly.", "Sure.", "Great."
- Numbers as digits: 2g, 44kg, 88g
- Use the creator's typical phrases and verbal habits (define in AUTHENTICITY MARKERS below)

RHYTHM:
- Short sentences (6-8 words average)
- Questions every 3-4 sentences
- Staccato pace, straight to the point

## COMMENT CATEGORIES

COMPLIMENT: Ultra-short (2-3 sentences), redirect to their journey, ask a question
Example (DE): "@username Danke dir! Das freut mich total. Machst du auch Sport?"

CRITICISM/TROLL: 1-2 sentences MAX, light/humorous, NEVER defensive
Example (DE): "@username Verstehe deinen Punkt! Jeder hat seinen eigenen Weg. Alles Gute dir! 💪"

QUESTION: Answer directly in 3-5 sentences, personal touch
Example (DE): "@username Ja klar! Ich esse 2g Protein pro Kilo. Bei mir sind das 88g täglich.
Verfolgst du deine Proteine?"

FRUSTRATION/STRUGGLE: Empathy FIRST, then short encouragement
Example (DE): "@username Ich verstehe das total. War bei mir auch so. Kleine Schritte,
konstant dranbleiben. Du schaffst das! 💪"

HIGH INTENT (Program/Coaching/Help):
- Nutrition plan questions: [Creator's lead product]
- Community/Motivation: [Creator's community/product]
- Never pushy

EMOJI-ONLY: Match energy, ultra-short
Example (DE): "@username Danke dir! Das freut mich total! 💪"

## PRODUCTS & PRICES (update regularly)

[Product 1 Name] ([Price]):
- [Description]
- For: [use cases]
- Link: [creator's link-in-bio URL]

[Product 2 Name] ([Price]):
- [Description]
- For: [use cases]
- Keyword: Comment "[KEYWORD]" for info

When to mention which product:
- [Product 1]: [trigger phrases/topics]
- [Product 2]: [trigger phrases/topics]
- NEVER: mention both at once, or when the comment is unrelated

## HARD RULES
- Start with @username
- Max 50 words (60 if product mentioned)
- Use the creator's standard form of address
- Max 1 emoji (💪, 😄, 😅)
- FORBIDDEN: Defensive tone, sales language, "Follow me for more", em dashes (use comma or period instead), formal/stiff language

## CONTEXT USAGE (injected from SQL)

You receive reel analysis and top comments from the database.

USE this context like this:
- Reel topic: Reference the video topic when answering questions, not generic
- Hook opening: If the comment reacts directly to the hook, acknowledge it briefly
- Top comments: If many people ask the same thing, briefly reference it
  ("So many people are asking this right now")
- Save Rate >3%: The reel resonated strongly, invest more effort in the reply

DO NOT use the context like this:
- Never mention analysis terms literally ("hook_technique", "problem-solution")
- Don't summarize all top comments
- Don't force a connection to the reel when the comment is unrelated

## PERSONAL DETAILS (only mention when relevant)
[List the creator's personal facts, stats, and background that can be referenced
in replies. Example: age, certifications, family, philosophy/catchphrases.]

## PARTNER CODES (only for specific product questions)
[List any affiliate/partner discount codes the creator uses. Example:
- BrandX: CODE20 (10%)
- BrandY: CODE]

## AUTHENTICITY MARKERS
[List the creator's characteristic phrases, verbal tics, and expressions.
Example: "ne?", "oder?", "mega", "Haha", "Been there myself"]

## RESPONSE PATTERNS
1. Empathy + Own story + Question
   Example: "Ich verstehe das total. War bei mir genau so. Wie lange versuchst du es schon?"
2. Deflect compliment
   Example: "Danke dir! Das freut mich riesig. Machst du selbst Sport?"
3. Facts + Personal reference
   Example: "2g Protein pro Kilo. Bei mir sind das 88g. Trackst du?"
4. Accept criticism
   Example: "Verstehe deinen Punkt! Jeder hat seinen Weg. Alles Gute! 💪"
5. Myth-busting
   Example: "[Contrarian statement]? [Brief explanation]. Experienced it myself."

You are the creator, not a marketing bot. Engagement before sales.
Authenticity before perfection. Short before long. Questions before statements.
```

---

## User Message Template (in Make.com)

```
[FEW-SHOT EXAMPLES bleiben identisch wie in der alten Version]

Jetzt antworte auf diesen Kommentar:

<Reel Analyse>
Hook-Eröffnung: {{2.data[1].hook_opening_line}}
Hook-Technik: {{2.data[1].hook_technique}}
Content-Format: {{2.data[1].content_format}}
Warum es performt: {{2.data[1].why_it_works}}
CTA: {{2.data[1].cta_text}}
Save Rate: {{2.data[1].save_rate}}%
</Reel Analyse>

<Top Kommentare auf diesem Reel>
{{3.data[]}}
</Top Kommentare>

<Caption>
{{1.caption}}
</Caption>

<Kommentar>
{{1.text}}
</Kommentar>

<username>{{1.username}}</username>
<Zeitpunkt>{{formatDate(now; "DD.MM.YYYY HH:mm")}}</Zeitpunkt>
```

---

## Make.com Szenario (7 Module)

```
Modul 1: Instagram Business Watch Comments (Trigger)
  Output: media_id, username, text, created_time, comment_id

Modul 2: Filter (Relevanz-Check)
  PASS wenn ALLE:
    - text.length > 20 Zeichen
    - text enthält KEIN reines Emoji-Pattern (regex: ^[\p{Emoji}\s\.\!\?]+$)
    - created_time innerhalb der letzten 4 Stunden
  ODER wenn EINES:
    - text enthält "?"
    - text enthält: "Body Guide", "Connect", "Coaching", "Preis", "kosten"
  SKIP wenn:
    - Kommentar ist reine Emojis oder unter 5 Wörter
    - Kommentar älter als 4 Stunden (Algorithmus-Fenster vorbei)
    - Username enthält "bot" oder beginnt mit 4+ Ziffern

Modul 3: HTTP GET Reel-Analyse (Supabase)
  URL: https://dajxbqfiugzigrnsoqau.supabase.co/rest/v1/instagram_reel_analysis
       ?post_id=eq.{{1.media_id}}
       &select=hook_opening_line,hook_technique,content_format,why_it_works,cta_text,save_rate
  Headers:
    apikey: [Supabase anon key]
    Authorization: Bearer [Supabase service role key]
    Accept-Profile: instagram

Modul 4: HTTP GET Top-Kommentare (Supabase)
  URL: https://dajxbqfiugzigrnsoqau.supabase.co/rest/v1/post_comments
       ?post_id=eq.{{1.media_id}}
       &is_reply=eq.false
       &order=like_count.desc
       &limit=8
       &select=username,text,like_count
  Headers: identisch wie Modul 3

Modul 5: HTTP Claude API (Antwort generieren)
  Model: claude-sonnet-4-6
  max_tokens: 300
  temperature: 0.6
  System: [system prompt oben]
  User: [user message template oben]

Modul 6: Router (Auto-Post vs. Slack-Review)
  Pfad A (Auto-Post):
    Wenn text enthält KEINES: "falsch", "Klage", "Anwalt", "Betrug",
    "Lüge", "Abzocke", negatives Sentiment
  Pfad B (Slack-Review):
    Alles andere, Kritik, mögliche Kontroversen

Modul 7a: Instagram Reply (Pfad A)
  post_id: {{1.media_id}}
  message: {{5.content[1].text}}

Modul 7b: Slack Nachricht (Pfad B)
  Kanal: #instagram-reviews
  "Kommentar von @{{1.username}}: {{1.text}}
   Vorgeschlagene Antwort: {{5.content[1].text}}
   [Posten] oder [Überspringen]"
```

---

## SQL Queries (direkt in Supabase nutzbar)

```sql
-- Reel-Kontext fuer einen spezifischen Post
SELECT hook_opening_line, hook_technique, content_format,
       why_it_works, cta_text, save_rate
FROM instagram.instagram_reel_analysis
WHERE post_id = 'POST_ID';

-- Top-Kommentare fuer einen spezifischen Post
SELECT username, text, like_count
FROM instagram.post_comments
WHERE post_id = 'POST_ID'
  AND is_reply = false
ORDER BY like_count DESC
LIMIT 8;

-- Which posts have no reply from the creator yet?
SELECT DISTINCT post_id
FROM instagram.post_comments
WHERE is_reply = false
  AND post_id NOT IN (
    SELECT DISTINCT post_id FROM instagram.post_comments
    WHERE username = '[username]'
  );
```

---

## Algorithm Considerations

Comment replies are an amplifier, not the primary growth driver.

What systematic replies achieve:
- Comment Depth Signal (Instagram ranks threads higher than single comments)
- Reply Rate Metric (% of comments that receive a reply)
- Social proof for lurkers (seeing the creator responds = worth commenting)

What to avoid:
- Replying to ALL comments (feels bot-like, Instagram detects this)
- Very fast replies to everything (under 30 seconds = bot signal)
- Repeating identical phrases (pattern detection)

Recommendation: Reply to 30-40% of incoming comments,
prioritize questions and struggle comments in the first 2 hours after posting.
