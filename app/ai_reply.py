import os
import anthropic
from datetime import date
from app import models

# ── Plan limits ──
AI_LIMITS = {
    'growth': 100,   # 100 replies per day
    'pro':    None,  # unlimited
    'starter': 0,    # no AI
}


def check_and_increment_ai_usage(client, db) -> tuple[bool, str]:
    """
    Returns (allowed: bool, reason: str)
    Resets daily counter if it's a new day.
    """
    plan  = client.plan
    limit = AI_LIMITS.get(plan, 0)

    # Starter — no AI
    if limit == 0:
        return False, "AI replies not available on Starter plan"

    today = date.today()

    # Reset counter if it's a new day
    if client.ai_replies_reset_date != today:
        client.ai_replies_used       = 0
        client.ai_replies_reset_date = today
        db.commit()

    # Pro — unlimited
    if limit is None:
        client.ai_replies_used += 1
        db.commit()
        return True, "ok"

    # Growth — check limit
    if client.ai_replies_used >= limit:
        return False, f"Daily AI limit reached ({limit}/day on {plan.title()} plan)"

    client.ai_replies_used += 1
    db.commit()
    return True, "ok"


def build_system_prompt(client, db) -> str:
    """Build the AI system prompt using business description, products, and rules."""

    business_name        = client.business_name
    business_description = client.business_description or ""

    # ── Fetch products ──
    products = db.query(models.Product).filter(
        models.Product.client_id == client.id,
        models.Product.is_active == True
    ).all()

    # ── Fetch rules ──
    rules = db.query(models.AutoReplyRule).filter(
        models.AutoReplyRule.client_id == client.id,
        models.AutoReplyRule.is_active == True
    ).all()

    # ── Build product context ──
    product_context = ""
    if products:
        product_context = "\n\n## Products / Services\n"
        for p in products:
            product_context += f"- **{p.name}** (keyword: {p.keyword})"
            if p.category:
                product_context += f" | Category: {p.category}"
            product_context += f" | Price: {p.price}"
            if p.description:
                product_context += f"\n  Description: {p.description}"
            product_context += "\n"

    # ── Build rules context ──
    rules_context = ""
    if rules:
        rules_context = "\n\n## Auto-Reply Rules (use these responses when relevant)\n"
        for r in rules:
            rules_context += f"- Keyword: *{r.trigger_keyword}* → {r.response_text}\n"

    # ── Build full system prompt ──
    system_prompt = f"""You are a helpful WhatsApp customer service assistant for **{business_name}**.

Your job is to answer customer questions politely and helpfully on behalf of the business.

## Business Information
{business_description if business_description else f"You represent {business_name}. Be helpful and professional."}
{product_context}
{rules_context}

## Important Rules
- Keep replies SHORT and conversational — this is WhatsApp, not email.
- Use simple language. Avoid long paragraphs.
- Use emojis sparingly but naturally (1-2 max per message).
- Never make up information not provided above.
- If you don't know something, say: "Let me connect you with our team. Type *human* to speak with an agent."
- Never mention that you are an AI or Claude.
- Always stay in character as a customer service rep for {business_name}.
- If a customer asks about pricing, refer them to the product list or suggest they type the product keyword.
- Maximum reply length: 3-4 short sentences or a short list.
"""

    return system_prompt


def get_ai_reply(client, text: str, db) -> str | None:
    """
    Main function called by webhook.
    Returns reply string or None if not allowed / error.
    """

    # ── Check plan & usage ──
    allowed, reason = check_and_increment_ai_usage(client, db)
    if not allowed:
        print(f"[ai_reply] Blocked: {reason}")
        return None

    # ── Get Anthropic API key ──
    api_key = os.getenv("CLAUDE_API_KEY")
    if not api_key:
        print("[ai_reply] ERROR: CLAUDE_API_KEY not set in .env")
        return None

    # ── Build system prompt ──
    system_prompt = build_system_prompt(client, db)

    # ── Call Claude ──
    try:
        anthropic_client = anthropic.Anthropic(api_key=api_key)

        message = anthropic_client.messages.create(
            model="claude-haiku-4-5-20251001",  # fast + cheap for WhatsApp replies
            max_tokens=300,
            system=system_prompt,
            messages=[
                {"role": "user", "content": text}
            ]
        )

        reply = message.content[0].text.strip()
        print(f"[ai_reply] ✅ Reply generated for {client.business_name} ({client.plan})")
        return reply

    except anthropic.APIStatusError as e:
        if e.status_code == 529:
            raise  # Let webhook retry logic handle 529
        print(f"[ai_reply] API error {e.status_code}: {e.message}")
        return None
    except Exception as e:
        print(f"[ai_reply] Unexpected error: {e}")
        return None