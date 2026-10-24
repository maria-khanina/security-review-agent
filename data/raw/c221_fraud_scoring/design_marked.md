# Fraud Scoring: Intelligent Risk Decisions at the Speed of Payments

## Executive summary

Fraud Scoring is the intelligence layer that protects Meridian Pay and its merchants from payment fraud. Every payment is evaluated in milliseconds by a state-of-the-art scoring engine, which turns the signals of a payment into a clear risk decision. The result is fewer fraudulent payments, fewer false declines and a better experience for honest customers.

## Business value

- Lower fraud losses through faster and more accurate decisions.
- Fewer false declines, which protects revenue and merchant satisfaction.
- A single scoring platform for all payment products, so that new products get fraud protection from day one.
- Analysts spend their time on real cases instead of long review queues.

## How it works

Fraud Scoring is event driven. The payment-events topic (MSK) delivers one event for every payment, together with the attributes of the customer, such as country, device and the history counters. The scoring-engine reads each event, computes a score with the current model and writes a decision to decisions-db (PostgreSQL). The decision is one of `allow`, `review` or `block`. Decisions of the type `review` are collected into a queue that the fraud analysts work through every morning.

⟦F2|decisions-db keeps every decision together with the customer attributes that were scored, and analysts use it for their investigations and for the weekly reports.⟧

The scoring-engine runs as two copies that share one consumer group, so that the load of the payment events is split between them. If one copy stops, the other takes over its share of the partitions within a minute.

## The model

The model is updated every month by the Risk Engineering team. A new model first scores the events in shadow mode for one week, without its decisions being used, and the team compares its results with the current model. The new model goes live when it finds at least as much fraud at the same false decline rate.

## Operations

⟦F1|The alert rule for suspicious spikes in failed logins and privilege changes runs once a day and reports to the fraud team channel together with the daily summary.⟧ The team looks at the dashboards of the scoring latency and the consumer lag every morning.

## Success measures

- Median scoring time under 100 milliseconds from the arrival of the event.
- Share of `review` decisions below two percent of all payments.
- Fraud loss rate below the target of the finance team for the year.

## Roadmap

In the first quarter the engine scores card payments. In the second quarter it adds wallet transfers, and in the third quarter it adds refunds. A graph-based signal that links devices and accounts is under evaluation for the fourth quarter.
