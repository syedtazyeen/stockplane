export function createIdempotencyKey() {
  return crypto.randomUUID();
}

export function idempotencyHeaders(idempotencyKey) {
  if (!idempotencyKey) {
    return undefined;
  }

  return {
    "Idempotency-Key": idempotencyKey,
  };
}
