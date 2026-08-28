import { NextRequest, NextResponse } from "next/server";
import { getOrCreateUserId } from "@/lib/session";
import { getStripe, isStripeConfigured } from "@/lib/stripe";
import { getRedis, isRedisConfigured } from "@/lib/redis";

export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  if (!isStripeConfigured()) {
    return NextResponse.json({ error: "Stripe is not configured." }, { status: 501 });
  }

  const { id: userId } = getOrCreateUserId();
  const origin =
    process.env.NEXT_PUBLIC_APP_URL ??
    req.headers.get("origin") ??
    `https://${req.headers.get("host")}`;

  const stripe = getStripe();

  // Reuse customer if we've seen this user before.
  let customerId: string | undefined;
  if (isRedisConfigured()) {
    const redis = getRedis()!;
    customerId = (await redis.get<string>(`uid:${userId}:stripe_customer`)) ?? undefined;
  }

  try {
    const session = await stripe.checkout.sessions.create({
      mode: "subscription",
      line_items: [{ price: process.env.STRIPE_PRICE_ID!, quantity: 1 }],
      success_url: `${origin}/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${origin}/?canceled=1`,
      client_reference_id: userId,
      customer: customerId,
      metadata: { qa_uid: userId },
      subscription_data: { metadata: { qa_uid: userId } },
      allow_promotion_codes: true,
    });
    return NextResponse.json({ url: session.url });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
