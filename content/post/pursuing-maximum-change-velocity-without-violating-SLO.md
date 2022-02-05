---
title: "Pursuing maximum change velocity without violating SLO"
date: 2022-01-07T10:00:00-03:00
tags: [sre, sre-tenets, change, velocity, slo, engineering]
author: Tom M G
draft: false
---

> This following content is a transcript from [Site Reliability Engineering](https://books.google.com.br/books/about/Site_Reliability_Engineering.html?id=tYrPCwAAQBAJ) with some, maybe none, personal adjustments.

Product development and SRE teams can enjoy a productive working relationship by eliminating the structural conflict in their respective goals. The structural conflict is between the pace of innovation and product stability. This conflict often is expressed indirectly. In SRE we bring this conflict to the fore, and then resolve it with the introduction of an `error budget`.

The error budget stems from the observation that 100% is the *wrong reliability target for almost everything*. In general, for any software service or system, 100% is not the right reliability target because no user can tell the difference between a system being 100% available and 99.999% available. There are many other systems in the path between user and service (their laptop, their WiFi, their Internet service provider, the power grid...) and those systems collectively are far less than 99.999% available. Thus, the marginal difference between 99.999% and 100% gets lost in the noise of other unavailability, and the user receives no benefit from the enormous effort required to add that last 0.001% of availability.

If 100% us the wrong reliability target for a system, what, then, is the right reliability target for the system? This actually isn't a technical question at all - it's a product question, which should take the following considerations into account:
- What level of availability will the users be happy with, given how they use the product?
- What alternatives are available to users who are dissatisfied with the product's availability?
- What happens to users' product usage at different availability levels?

The business or the product must establish the system's availability target. Once that target is set, the error budget is `100 - $AVAILABILITY_TARGET`. A service that's 99.99% available is 0.01% unavailable. That permitted 0.01% unavailability is the service's *error budget*. We might spend the budget on anything we want, as long as we don't overspend it.

So how do we want to spend the error budget? The development team wants to launch features and attract new users. Ideally, we would spend all of our error budget taking risks to launch features quickly. This basic premise describes the whole model of error budgets. As soon as we conceptualize SRE activities in this framework, freeing up the error budget through tactics such as phased rollouts and 1% experiments can optimize for quicker launches.

The use of an error budget resolves the structural conflict of incentives between development teams and SRE. SRE's goal is no longer "zero outages"; rather SREs and product developers aim to spend the error budget getting maximum feature velocity. This change makes all the difference. An outage is no longer a "bad" thing - it is an expected part of the process of innovation and an occurrence that both development and SRE teams manage rather than fear.
