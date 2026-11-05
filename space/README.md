---
title: Payer Policy Copilot
emoji: 💊
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 8501
pinned: false
short_description: Cited insurer-coverage answers for Repatha, Prolia, Otezla
---

# Payer Policy Copilot

A password-protected chat assistant that answers questions about US insurer coverage
policies (Aetna, Cigna, UnitedHealthcare) and FDA labels for three Amgen drugs:
Repatha, Prolia and Otezla. Every answer cites the policy section it came from.

- Retrieval: section-aware chunks embedded with `nomic-ai/nomic-embed-text-v1.5`,
  stored in Chroma, filtered by insurer and drug.
- Generation: Claude Haiku 5.5, answering only from the retrieved sources.
- Usage limits: 20 questions per session, 150 per day.

A portfolio demo, not coverage or medical advice. The search index is loaded at startup
from a private dataset.
