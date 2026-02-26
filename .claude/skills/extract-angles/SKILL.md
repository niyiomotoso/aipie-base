---
name: extract-angles
description: Generate 4 content angles for each top trending topic. Use after score-topics has been run.
allowed-tools: Read, Write
---

Generate content angles for the top scored topics.

1. Read `data/scored_topics.json`
2. For each of the top 10 topics, generate exactly 4 angles:
   - **AGREE**: Side with the majority opinion but add unique insight
   - **DISAGREE**: Push back on the consensus with a credible counter-argument
   - **CONTRARIAN**: Take a surprising, counterintuitive position
   - **PRACTICAL**: Skip the debate entirely, give actionable advice

3. For each angle, provide:
   - A compelling hook (first sentence of the script)
   - A one-sentence thesis
   - The target emotion (excitement, outrage, curiosity, fear, empowerment, etc.)
   - Risk level: "safe", "moderate", or "spicy"

4. Also score each topic's scriptability (0-1):
   - Emotional charge
   - Controversy level
   - Practical takeaway potential
   - Can it be explained in 60 seconds?

5. Filter out topics with scriptability below 0.6
6. Save to `data/angles.json`
7. Present the top 5-7 topics with their best angles
