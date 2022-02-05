---
title: "Monitoring"
date: 2022-01-14T09:00:00-03:00
tags: [sre, sre-tenets, monitoring, engineering]
author: Tom M G
draft: false
---

> This following content is a transcript from [Site Reliability Engineering](https://books.google.com.br/books/about/Site_Reliability_Engineering.html?id=tYrPCwAAQBAJ) with some, maybe none, personal adjustments.

Monitoring is one of the primary means by which service owners keep track of a system's health and availability. As such, monitoring strategy should be constructed thoughtfully. A classic and common approach to monitoring is to watch for a specific value or condition, and then trigger an alert when that value is exceeded or that condition occurs. However, this type of alerting is not an effective solution: a system that requires a human to read a message and decide whether or not some type of action needs to be taken in response is fundamentally flawed. Monitoring should never require a human to interpret any part of the alerting domain. Instead, software should do the interpreting, and humans should be notified only when they need to take action.

There are three kinds of valid monitoring output:
## Alerts 
Signify that a human needs to take action immediately in response to something that is either happening or about to happen, in order to improve the situation.

## Tickets
Signify that a human needs to take action, but not immediately. The system can't automatically handle the situation, but if a human takes action in a few days, no damage will result.

## Logging
No one needs to look at this information, but it is recorded for diagnostic or forensic puporses. The expectation is that no one reads logs unless something else prompts them to do so.
