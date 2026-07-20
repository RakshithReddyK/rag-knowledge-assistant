# API Rate Limiting Strategies

Rate limiting caps how many requests a client can make in a given time
window, protecting a service from overload, abuse, or runaway clients. The
choice of algorithm affects both fairness and burst behavior.

## Fixed Window Counter

Count requests in discrete windows (e.g., per calendar minute). Simple to
implement with a single counter and a TTL, but has a boundary problem: a
client can send the full quota at the very end of one window and the full
quota again at the start of the next, doubling the effective rate over a
short span that straddles the boundary.

## Sliding Window Log

Store a timestamp for every request and count how many fall within the
trailing window (e.g., the last 60 seconds) on each check. This is
accurate — no boundary burst problem — but memory cost grows with request
volume, since every timestamp must be retained until it ages out.

## Sliding Window Counter

A practical middle ground: keep counts for the current and previous fixed
windows, and estimate the sliding count as a weighted combination based on
how far into the current window you are. This approximates the sliding log
with a fixed, small memory footprint per client.

## Token Bucket

A bucket holds up to `B` tokens and refills at a steady rate `r` tokens per
second. Each request consumes one token; a request is rejected (or
delayed) if the bucket is empty. This naturally allows short bursts up to
the bucket size while enforcing a steady average rate over time, which is
why it's a common default for API gateways.

## Leaky Bucket

Requests enter a queue (the "bucket") and are processed at a fixed output
rate, like water leaking from a hole at a constant speed. Excess requests
either wait in the queue or are dropped once it's full. Unlike token
bucket, leaky bucket smooths bursts into a constant output rate rather than
allowing them through.

## Where the Limit Is Enforced

Rate limits can be applied per API key, per user, per IP address, or
globally per endpoint, and are often layered — a generous global limit at
the load balancer plus a stricter per-user limit at the application layer.
Distributed rate limiting (across multiple servers) typically needs a
shared store like Redis so counters are consistent across instances.
