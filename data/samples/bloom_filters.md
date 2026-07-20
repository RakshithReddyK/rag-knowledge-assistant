# What a Bloom Filter Is

A Bloom filter is a space-efficient probabilistic data structure that
answers one question very cheaply: "have I possibly seen this item before?"
It can never produce a false negative, but it can produce a false positive —
it may say "maybe present" for an item that was never actually added.

## How It Works

A Bloom filter is a bit array of size `m`, initially all zeros, plus `k`
independent hash functions. To add an item, you hash it with all `k`
functions and set the corresponding `k` bit positions to 1. To check
membership, you hash the item the same way and check whether all `k` bit
positions are set. If even one bit is 0, the item is definitely not in the
set. If all `k` bits are 1, the item is probably in the set — but other
insertions could have coincidentally set those same bits, which is the
source of false positives.

## Why Not Just Use a Set?

A hash set stores every element (or a full hash of it), which grows
linearly with the number of items and requires either a lot of memory or a
lookup over the network/disk. A Bloom filter trades exactness for a fixed,
much smaller memory footprint — often a small number of bits per element
regardless of how large the elements themselves are. This makes it useful
when you need to answer millions of membership checks with tight memory
constraints and can tolerate a small false-positive rate.

## Tuning the False-Positive Rate

Given `n` expected items and a target false-positive probability `p`, you
can compute the optimal bit array size `m` and number of hash functions
`k`. More bits per element and more hash functions reduce the false
positive rate, up to a point — too many hash functions actually saturate
the bit array and increase collisions.

## Common Uses

- Database engines (e.g., checking whether a key *might* exist on disk
  before doing an expensive read).
- Web crawlers (avoiding re-visiting URLs already seen).
- Network routers and CDNs (fast "have we cached this?" checks).
- Distributed systems, to cheaply skip a remote call when the item is
  definitely absent.

## Limitation

You cannot remove an item from a standard Bloom filter, because clearing
its bits could also clear bits shared by other items. A variant called a
"counting Bloom filter" uses small counters instead of single bits to
support deletion, at the cost of more memory.
