# Consistent Hashing, Briefly

Consistent hashing is a technique for distributing keys across a changing
set of servers (or shards, or cache nodes) while minimizing how many keys
have to move when a server is added or removed.

## The Naive Approach and Its Problem

A simple way to shard `n` servers is `server = hash(key) % n`. This works
until `n` changes. Adding or removing even one server changes the modulus,
which reassigns nearly every key to a different server — for a cache, that
means a massive wave of cache misses all at once; for a data store, it
means an expensive full reshuffle.

## The Ring

Consistent hashing places both servers and keys on a conceptual ring
(imagine hash values from 0 to some maximum, wrapping back to 0). Each
server is hashed onto a point on the ring. A key is assigned to the first
server encountered walking clockwise from the key's own hash position.

When a server is removed, only the keys that mapped to it move — to the
next server clockwise on the ring. Every other key-to-server assignment is
untouched. Adding a server works the same way in reverse: it only takes
over a portion of the ring from its clockwise neighbor.

## Virtual Nodes

A single hash point per physical server can lead to uneven load, since the
ring's gaps between servers are randomly sized. The standard fix is
"virtual nodes": each physical server is hashed onto many points on the
ring (e.g., 100–200), so the ring is divided into many small, roughly
even segments, and each physical server ends up owning a fair share of
total ring space even though the placement is still random.

## Where It Shows Up

- Distributed caches (e.g., partitioning keys across cache nodes).
- Distributed databases and object stores, for sharding and replica
  placement.
- Load balancers, to route a given client consistently to the same
  backend without a central routing table.

## Trade-off

Consistent hashing sacrifices perfectly even load distribution (the naive
modulus approach is perfectly even when `n` is stable) in exchange for
"only affected keys move" behavior when the cluster size changes — a good
trade for systems where membership changes are frequent and full
reshuffles are expensive.
