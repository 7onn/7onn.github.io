---
title: "Ensuring a durable focus on engineering"
date: 2022-02-05T12:00:00-03:00
tags: [sre, sre-tenets, focus, engineering]
author: Tom M G
draft: false
---

> This following content is a transcript from [Site Reliability Engineering](https://books.google.com.br/books/about/Site_Reliability_Engineering.html?id=tYrPCwAAQBAJ) with some, maybe none, personal adjustments.

SREs shouldn't dedicate more than 50% of their time in operational tasks.

That being said, their remaining time should be spent using their coding skills on project work. In practice, this is accomplished by monitoring the amount of operational work being done, and redirecting excess operational work to the product development teams: reassigning bugs and tickets to development managers, [re]integrating developers into on-call pager rotations, and so on. The redirection ends when the operational load drops back to 50% or lower. This also provides an effective feedback mechanism, guiding developers to build systems that don't need manual intervention. This approach works well when the entire organization - SRE and development alike - understands why the safety valve mechanism exists and supports the goal of having no overflow events because the production doesn't generate enough operational load to require it.

When they are focused on operations work, on average, SREs should receive a maximum of two events per 8-12-hour on-call shift. This target volume gives the on-call engineer enough time to handle the event accurately and quickly, clean up and restore normal service, and then conduct a postmortem. If more than two events occur regularly per on-call shift, problems can't be investigated thoroughly and engineers are sufficiently overwhelmed to prevent them from learning from these events. A scenario of pager fatigue also won't improve with scale. Conversely, if on-call SREs consistently receive fewer than one event per shift, keeping them on point is a waste of their time.

Postmortems should be written for all significant incidents, regardless of whether or not they paged; postmortems that did not trigger a page are even more valuable, as they likely point to clear monitoring gaps. This investigation should establish what happened in detail, find all root causes of the event, and assign actions to correct the problem or improve how it is addressed next time. Ideally, we should operate under a `blame-free postmortem culture` to expose faults and apply engineering to fix these faults rather than avoiding or minimizing them.
