**webhook dispatcher design** (pasted from #integrations, thread was long so i cut it)

**dani:** ok so here's the summary of where we landed, pls correct me

**What it is**
the dispatcher (some people say "sender", some "hook service", same thing) takes events from platform services, puts a delivery in delivery-queue for every merchant that subscribed, then calls the merchant callback endpoints. retries w/ backoff i think? not 100% sure on the exact numbers

**API** (5 calls)
• `POST /v1/subscriptions` - register endpoint (url, event_types, description) -> id, url, status
• `GET /v1/subscriptions/{subscriptionId}` -> id, url, status
• `POST /v1/subscriptions/{subscriptionId}/rotate-secret` - body has grace_period_hours
• `GET /v1/deliveries` - list, can filter by status -> id, event_type, status, attempts
• `POST /v1/deliveries/{deliveryId}/replay` - needs a reason

**lena:** and security stuff?

**dani:** right, so from what i remember:

*auth / access*
• Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.
• Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it.
• Administrative and debug endpoints are not reachable from the public internet.
• Access rights to production systems are reviewed at least quarterly.

*transport / crypto*
• All external traffic uses TLS 1.2 or higher.
• Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.

*secrets / network*
• delivery-queue and the databases sit in private subnets and are not publicly reachable.

**lena:** what about logging? and how does the sender get its keys

**dani:** The dispatcher writes logs to the central logging stack like every other service. and The dispatcher starts up with its configuration and connects to delivery-queue and the databases. (lena can you confirm both? i'm hazy)

**lena:** will do, TBD

*more*
• All external inputs are validated against a schema and rejected if invalid.

**dani:** one more thing about filtering. The status filter on GET /v1/deliveries is passed from the query string and a raw SQL fragment from it is appended to the delivery query. it was the quickest way to support all the filter combos, we can clean it up later

**dani:** Personal data is never placed in URLs. i think that's from the old spec

**lena:** ok. open: how many subscriptions per merchant? TBD

**dani:** yeah. will write it up properly next week
