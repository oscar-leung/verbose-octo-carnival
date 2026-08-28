import { NextRequest, NextResponse } from "next/server";
import type Stripe from "stripe";
import { getStripe, isStripeConfigured } from "@/lib/stripe";
import { getRedis, isRedisConfigured } from "@/lib/redis";

export const runtime = "nodejs";

async function writeSubscription(
  userId: string,
  sub: Pick<Stripe.Subscription, "status" | "current_period_end" | "customer">,
) {
  if (!isRedisConfigured()) return;
  const redis = getRedis()!;
  const customerId = typeof sub.customer === "string" ? sub.customer : sub.customer.id;
  await redis.set(`sub:${userId}`, {
    status: sub.status,
    current_period_end: sub.current_period_end,
    customer_id: customerId,
  });
  await redis.set(`uid:${userId}:stripe_customer`, customerId);
  await redis.set(`stripe_customer:${customerId}:uid`, userId);
}

async function userIdForCustomer(customerId: string): Promise<string | null> {
  if (!isRedisConfigured()) return null;
  const redis = getRedis()!;
  return (await redis.get<string>(`stripe_customer:${customerId}:uid`)) ?? null;
}

export async function POST(req: NextRequest) {
  if (!isStripeConfigured()) {
    return NextResponse.json({ error: "Stripe is not configured." }, { status: 501 });
  }

  const stripe = getStripe();
  const signature = req.headers.get("stripe-signature");
  if (!signature) {
    return NextResponse.json({ error: "Missing stripe-signature header." }, { status: 400 });
  }

  const rawBody = await req.text();

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(
      rawBody,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET!,
    );
  } catch (err) {
    const message = err instanceof Error ? err.message : "Invalid signature";
    return NextResponse.json({ error: message }, { status: 400 });
  }

  try {
    switch (event.type) {
      case "checkout.session.completed": {
        const session = event.data.object as Stripe.Checkout.Session;
        const userId =
          session.client_reference_id ?? (session.metadata?.qa_uid as string | undefined);
        if (userId && session.subscription) {
          const subId =
            typeof session.subscription === "string"
              ? session.subscription
              : session.subscription.id;
          const sub = await stripe.subscriptions.retrieve(subId);
          await writeSubscription(userId, sub);
        }
        break;
      }
      case "customer.subscription.updated":
      case "customer.subscription.created":
      case "customer.subscription.deleted": {
        const sub = event.data.object as Stripe.Subscription;
        const userId =
          (sub.metadata?.qa_uid as string | undefined) ??
          (await userIdForCustomer(
            typeof sub.customer === "string" ? sub.customer : sub.customer.id,
          ));
        if (userId) await writeSubscription(userId, sub);
        break;
      }
      default:
        break;
    }
    return NextResponse.json({ received: true });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
