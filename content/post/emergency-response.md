---
title: "Emergency response"
date: 2022-01-21T09:00:00-03:00
tags: [engineering, incidents, on-call, sre, sre-tenets]
author: Tom M G
draft: false
---

> This following content is a transcript from [Site Reliability Engineering](https://books.google.com.br/books/about/Site_Reliability_Engineering.html?id=tYrPCwAAQBAJ) with some, maybe none, personal adjustments.

Reliability is a function of mean time to failure (MTTF) and mean time to repair (MTTR). The most relevant metric in evaluating the effectiveness of emergency response is how quickly the response team can bring the system back to health - that is, the MTTR.

Humans add latency. Even if a given system experiences more *actual* failures, a system that can avoid emergencies that require human intervention will have higher availability than a system that requires hands-on intervention. When humans are necessary, we have found that thinking through and recording the best practices ahead of time in a "playbook" produces roughly a 3x improvement in MTTR as compared to the strategy of "winging it". The hero jack-of-all-trades on-call engineer does work, but the practiced on-call engineer armed with a playbook works **much better**.
