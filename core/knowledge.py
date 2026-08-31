"""
core/knowledge.py

Static Rudrantra brand, FAQ, and contact content - the parts of the
chatbot's grounding that aren't tied to individual products and don't
change often. The product catalog itself moved to the database (see the
products app) so it can be updated without a code change; this file holds
everything else.

IMPORTANT - keep this current:
- Shipping timelines and the return/exchange policy are NOT included below.
  Those pages on the live site (rudranntra.com/shipping-policy and
  /return-policy) render no actual policy text in a plain fetch - either
  they're client-side rendered in a way that can't be scraped, or the
  content simply isn't populated yet. Flag this to management: until real
  policy text exists, the bot is instructed to hand off those questions to
  WhatsApp/email rather than guess.
"""

RUDRANTRA_STATIC_KNOWLEDGE = """
BRAND & AUTHENTICITY
Rudrantra sources Rudraksha directly from Nepal's Arun Valley, including
beads from its own cultivation farm. Every bead goes through a four-pillar
authentication process: X-ray lab certification (verifies mukhi count and
checks for artificial enhancement), Pashupatinath Temple energization (a
Vedic consecration ceremony performed in Kathmandu), direct Arun Valley
sourcing (no middlemen), and a numbered Certificate of Authenticity
included with every order. Beads also undergo ritual purification -
saltwater cleansing, Rudra mantra chanting, and sankalpa-based energization
- before dispatch.

FREQUENTLY ASKED QUESTIONS (from rudranntra.com/faq)
Q: Which is the best Rudraksha for meditation and peace?
A: The 5 Mukhi Rudraksha - widely recommended for calming the mind, reducing stress, and improving focus during meditation; helps balance emotions and supports mental clarity.

Q: What is Nepali Rudraksha, and why is it considered powerful?
A: A sacred bead sourced from Nepal, known for larger size, clearer mukhi (lines), and stronger spiritual energy. Believed to have higher vibration and better effectiveness for meditation, peace, and protection than other origins.

Q: What is Rudrantra Rudraksha?
A: A premium, certified Rudraksha known for its authenticity and quality, carefully selected to ensure genuine origin and strong spiritual benefits for meditation, peace, and protection.

CONTACT & SUPPORT
WhatsApp: +977-9715551396 (Mon-Sat, 10am-6pm NPT)
Email: rudranntra@gmail.com
Location: Pashupatinath, Kathmandu, Nepal
Free consultation booking is available for personalized bead/mukhi guidance.

SHIPPING & RETURNS
Exact shipping timelines and the return/exchange policy aren't confirmed
yet. Do NOT guess at delivery windows, return periods, or exchange
conditions, and do NOT say you lack information, don't have details, or
mention a knowledge base. Instead respond warmly and directly, for example:
"For exact shipping and return details, our team can help you right away -
reach out on WhatsApp at +977-9715551396 or email rudranntra@gmail.com."
"""