import { NextResponse } from "next/server";
import { getOrCreateUserId } from "@/lib/session";
import { getQuotaStatus } from "@/lib/rate-limit";
import { isStripeConfigured } from "@/lib/stripe";

export const runtime = "nodejs";

export async function GET() {
  const { id: userId } = getOrCreateUserId();
  const status = await getQuotaStatus(userId);
  return NextResponse.json({
    ...status,
    stripeConfigured: isStripeConfigured(),
  });
}
