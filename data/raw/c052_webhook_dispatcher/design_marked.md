# Webhook Dispatcher - my first design doc

Written by Sven (junior, Integrations). Please be kind, this is my first one. Reviewer: Anita.

## 1. What we are building

Merchants want to be told when something happens to their payments. The Webhook Dispatcher is the service that does the telling. A merchant registers an adress (a url) and a list of event types, and after that, every time a matching event happens on the platform, the dispatcher sends a message to that url. I learned this is called a "webhook". The dispatcher also keeps track of which messages arrived and which did not, so that nothing gets lost.

I used the template from the wiki and filled it in as well as I could. Where I was not sure I wrote it down in section 11.

## 2. The three parts

1. **dispatcher** - the main service, one deployable. It takes events from the other platform services, decides which merchants want them, and sends them out.
2. **delivery-queue** - a topic (I think the correct word is queue, but the team says topic) where every delivery waits until the dispatcher picks it up.
3. **Merchant callback endpoints** - the urls of the merchants. They are not ours, we only call them.

The path is: Platform services -> dispatcher -> delivery-queue -> dispatcher -> Merchant callback endpoints. Yes, the dispatcher is there twice, because it first puts the work in the queue and then takes it out again to do the sending. Anita told me this is normal.

## 3. The API

There are five operations. All of them are under /v1.

- **POST /v1/subscriptions** - register a callback endpoint. The merchant sends `url`, `event_types` and `description` and gets back `id`, `url` and `status`.
- **GET /v1/subscriptions/{subscriptionId}** - get one subscription. It returns `id`, `url` and `status`.
- **POST /v1/subscriptions/{subscriptionId}/rotate-secret** - make a new signing secret. The merchant sends `grace_period_hours`, which says for how many hours the old secret still works. The reply is the subscription again.
- **GET /v1/deliveries** - list delivery attempts. Each item has `id`, `event_type`, `status` and `attempts`. It can be filtered by status.
- **POST /v1/deliveries/{deliveryId}/replay** - send a delivery again. The merchant gives a `reason` and gets back the delivery with `id`, `event_type`, `status` and `attempts`.

## 4. Who is allowed to call this?

Not everybody. So if merchant A asks for the delivery of merchant B, the answer is "not found" or "forbidden". I checked with Anita and this is how all our services work.

⟦S:AUTHZ-04|Nothing administrative or meant for debugging can be called from outside our network.⟧ Those are only for our own people, from inside the company network.

Now the part I am less sure about. ⟦F3|Calls from known partners are accepted without credentials because contracts already identify them.⟧ The reason is that the big partners have a signed contract with us, so we already know who they are and it would be double work to also give them a token. The business team liked this because onboarding is faster. Anita said I should write it down and let security decide.

## 5. Encrypted traffic

I read that traffic should be encrypted so nobody on the way can read it. For the dispatcher this is mostly about the calls to the merchants, because those leave our network. ⟦F1|The service accepts both HTTP and HTTPS and does not redirect HTTP requests.⟧ We did it like this because some old merchants still call us on plain HTTP and we did not want to break them.

⟦S:CRYPTO-05|Only approved algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are not.⟧

## 6. Secrets

A secret is something like a password or a key, which lets you in. The signing secret from section 3 is one example. ⟦S:SECRET-01|Credentials are never committed to code, configuration, specifications or infrastructure-as-code files.⟧ ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧ So when the dispatcher starts, it asks the store for what it needs.

⟦S:OPS-02|Workloads are non-root, and read-only root filesystems are used wherever they can be.⟧

⟦S:NET-05|Public API traffic passes through a web application firewall with rate limits.⟧

## 7. Network

 Only the dispatcher can talk to them.

## 8. Logging

Logs are like a diary which the service writes while it works. ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are written to the logs.⟧ We use the same logging library as the other services.

⟦S:CRYPTO-04|Connections to the database and between internal services use TLS.⟧

⟦S:API-01|All external input is validated against a schema, and invalid requests are rejected.⟧
⟦S:AUTH-02|We do not trust the internal network by itself: every internal call is authenticated with mTLS or workload identity tokens.⟧

## 9. Limits and input

 This protects us when one merchant sends too many requests by mistake.

Requests are validated against strict schemas. The schema comes from the API definition, so what is allowed in each field is written in one place.

⟦S:API-05|User input reaches the database only as query parameters, never as part of the query text.⟧

⟦S:API-06|Browser-facing APIs allow only approved origins in CORS.⟧ (CORS is the thing which says which websites may call our api from a browser. I had to look it up.)

## 10. Updates

⟦F2|Third-party libraries are never updated unless something breaks.⟧ The idea is that a working version should not be touched, because every update can bring new bugs. We have about forty libraries and updating them takes time that the team does not have before the next release.

## 11. How a delivery lives, and what I do not know

A delivery starts as queued. When the merchant answers with success it becomes delivered. When the merchant answers with an error or does not answer, the dispatcher waits and tries again, each time a bit longer. After too many tries it becomes failed, and the merchant can see it in the list and replay it. A replay is a new attempt and the reason is saved.

Events are delivered at least once, so a merchant may get the same event twice and has to check the event id.

A subscription can be active, paused or disabled. The merchant can pause and resume. We disable a subscription after a long series of failures and tell the merchant.

Open questions:
- How many subscriptions can one merchant have? TBD.
- How long do we keep the delivery history? TBD, I asked Anita.
