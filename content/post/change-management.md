---
title: "Change management"
date: 2022-01-28T09:00:00-03:00
tags: [engineering, incidents, prevention, sre, sre-tenets]
author: Tom M G
draft: false
---

> This following content is a transcript from [Site Reliability Engineering](https://books.google.com.br/books/about/Site_Reliability_Engineering.html?id=tYrPCwAAQBAJ) with some, maybe none, personal adjustments.

Probably, >70% of the outages are due to changes in a live system.

Best practices in this domain are to use automation to accomplish the following:
- Implementing progressive rollouts
- Quickly and accurately detecting problems
- Rolling back changes safely when problems arise

This trio of practices effectively minimizes the aggregate number of users and operations exposed to harmful changes. By removing humans from the loop, these practices avoid the common problems of fatigue, familiarity/contempt, and inattention to highly repetitive tasks. As a result, both release velocity and safety increase.
